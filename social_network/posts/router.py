from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from social_network import security
from social_network.auth.router import get_current_user
from social_network.posts.models import Post
from social_network.posts.schemas import PostBase, PostCreate, PostDetails, PostList, PostUpdate
from social_network.users.models import User

post_router = APIRouter(prefix="/posts", tags=["posts"])


@post_router.get(
    "/feed",
    response_model=PostList,
)
async def get_posts(current_user: User = Depends(get_current_user)):
    # query = filter_user(
    #     UserFilterSchema(
    #         dt_created_from=dt_created_from,
    #         dt_created_to=dt_created_to,
    #         name_i=name_i,
    #         name=name,
    #         username=username,
    #         username_i=username_i,
    #     )
    # )

    results = await Post.find_many(auto_fetch_nodes=True)

    for ind, post in enumerate(results):
        results[ind] = PostDetails.from_post(post)

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

    return db_post


@post_router.get(
    "/{post_id}",
    response_model=PostDetails,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Post not found"},
    },
)
async def get_post_by_id(post_id: str):
    post_db = await Post.find_one({"uid": post_id}, auto_fetch_nodes=True)

    if not post_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found!",
        )

    return PostDetails.from_post(post_db)


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

    elif exist_post not in current_user.posts.find_connected_nodes():  # Todo: isso funciona?
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User doesn't owns that post!",
        )

    # Atualização de campos do post
    exist_post.title = post_update.title
    exist_post.content = post_update.content
    exist_post.updated_at = datetime.now(datetime.timezone.utc)

    await exist_post.update()
    await exist_post.refresh()

    return PostDetails.from_post(exist_post)


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

    await exist_post.delete()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@post_router.post(
    "/{post_id}/comment",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Post not found"},
    },
)
async def comment_post(post_id: str, post: PostCreate, current_user: User = Depends(get_current_user)):
    to_be_commented_post = await Post.find_one({"uid": post_id}, auto_fetch_nodes=True)

    if not to_be_commented_post:
        raise HTTPException("Post not found")

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

    return PostDetails.from_post(to_be_commented_post)
