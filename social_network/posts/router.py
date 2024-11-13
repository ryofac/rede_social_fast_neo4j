import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pyneo4j_ogm.queries.query_builder import RelationshipMatchDirection

from social_network.dependencies import get_current_user
from social_network.posts.filters import filter_post
from social_network.posts.models import Post
from social_network.posts.schemas import PostBase, PostCreate, PostDetails, PostFilterSchema, PostList, PostUpdate
from social_network.users.models import User

post_router = APIRouter(prefix="/posts", tags=["posts"])


@post_router.get(
    "/feed",
    response_model=PostList,
)
async def get_posts(
    content: str | None = Query(None, description="Busca por conteúdo exato"),
    content_i: str | None = Query(None, description="Busca por conteúdo parecido"),
    current_user: User = Depends(get_current_user),
):
    filters = filter_post(
        PostFilterSchema(
            content=content,
            content_i=content_i,
        )
    )

    results = await Post.find_many(
        filters,
        auto_fetch_nodes=True,
    )

    for ind, post in enumerate(results):
        results[ind] = await PostDetails.from_post(post, current_user)

    all_posts = PostList.model_validate({"posts": results})
    return all_posts


@post_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PostBase,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Content can't be empty"},
    },
)
async def create_post(post: PostCreate, current_user: User = Depends(get_current_user)):
    db_post: Post = Post(**post.model_dump())

    if not post.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content can't be empty",
        )

    await db_post.create()
    await db_post.refresh()
    await current_user.posts.connect(db_post)

    return await PostDetails.from_post(db_post, current_user)


@post_router.get(
    "/{post_id}",
    response_model=PostDetails,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Post not found"},
    },
)
async def get_post_by_id(post_id: str, current_user: User = Depends(get_current_user)):
    post_db = await Post.find_one({"uid": post_id}, auto_fetch_nodes=True)

    if not post_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found!",
        )

    return await PostDetails.from_post(post_db, current_user)


@post_router.put(
    "/{post_id}",
    response_model=PostDetails,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Post not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "User doesn't owns that post"},
    },
)
async def update_post(post_id: str, post_update: PostUpdate, current_user: User = Depends(get_current_user)):
    exist_post: Post = await Post.find_one({"uid": post_id}, auto_fetch_nodes=True)

    if not exist_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found!",
        )

    elif exist_post not in await current_user.posts.find_connected_nodes():  # Todo: isso funciona?
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User doesn't owns that post!",
        )

    # Atualização de campos do post
    exist_post.content = post_update.content
    exist_post.updated_at = datetime.now()

    await exist_post.update()
    await exist_post.refresh()

    return await PostDetails.from_post(exist_post, current_user)


@post_router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Post not found"},
    },
)
async def delete_post(post_id: str, current_user: User = Depends(get_current_user)):
    exist_post = await Post.find_one({"uid": post_id})

    if not exist_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found!",
        )

    comments = await exist_post.find_connected_nodes(
        {
            "$node": {"$labels": ["Post"]},
            "$direction": RelationshipMatchDirection.INCOMING,
            "$relationships": [{"$type": "LINKED_TO"}],
        },
        auto_fetch_nodes=True,
    )

    for post in comments:
        await post.delete()

    await exist_post.delete()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@post_router.post(
    "/{post_id}/comment",
    status_code=status.HTTP_200_OK,
    response_model=PostDetails,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Post not found"},
    },
)
async def comment_post(post_id: str, post: PostCreate, current_user: User = Depends(get_current_user)):
    to_be_commented_post = await Post.find_one({"uid": post_id}, auto_fetch_nodes=True)

    if not to_be_commented_post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    db_post: Post = Post(**post.model_dump())

    if not post.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content can't be empty",
        )

    await db_post.create()
    await current_user.posts.connect(db_post)
    await db_post.linked_to.connect(to_be_commented_post)
    await db_post.refresh()
    await db_post.owner.find_connected_nodes(auto_fetch_nodes=True)

    return await PostDetails.from_post(db_post, current_user)


@post_router.post(
    "/{post_id}/toggle-dislike",
    status_code=status.HTTP_200_OK,
    response_model=PostDetails,
    responses={
        status.HTTP_200_OK: {"description": "Post disliked"},
        status.HTTP_400_BAD_REQUEST: {"description": "Post already disliked!"},
    },
)
async def dislike_post(post_id: str, current_user: User = Depends(get_current_user)):
    post_db = await Post.find_one({"uid": post_id}, auto_fetch_nodes=True)

    if not post_db:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    already_disliked = len(await current_user.dilikes.find_connected_nodes({"uid": post_id})) > 0
    if already_disliked:
        await current_user.dilikes.disconnect(post_db)
        await post_db.refresh()
        return await PostDetails.from_post(post_db, current_user)

    liked = len(await current_user.likes.find_connected_nodes({"uid": post_id}))

    if liked:
        await current_user.likes.disconnect(post_db)

    await current_user.dilikes.connect(post_db)
    await current_user.refresh()

    await post_db.refresh()
    return await PostDetails.from_post(post_db, current_user)


@post_router.post(
    "/{post_id}/toggle-like",
    status_code=status.HTTP_200_OK,
    response_model=PostDetails,
    responses={
        status.HTTP_200_OK: {"description": "Post liked"},
        status.HTTP_404_NOT_FOUND: {"description": "Post not found"},
    },
)
async def like_post(post_id: str, current_user: User = Depends(get_current_user)):
    post_db = await Post.find_one({"uid": post_id}, auto_fetch_nodes=True)

    if not post_db:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    already_liked = len(await current_user.likes.find_connected_nodes({"uid": post_id})) > 0

    if already_liked:
        await current_user.likes.disconnect(post_db)
        await post_db.refresh()
        return await PostDetails.from_post(post_db, current_user)

    disliked = len(await current_user.dilikes.find_connected_nodes({"uid": post_id}))

    if disliked:
        await current_user.dilikes.disconnect(post_db)

    await current_user.likes.connect(post_db)
    await current_user.refresh()
    await post_db.refresh()

    return await PostDetails.from_post(post_db, current_user)
