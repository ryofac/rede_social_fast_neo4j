from datetime import datetime
from typing import Self
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel
from pyneo4j_ogm.queries.query_builder import RelationshipMatchDirection

from social_network.core.schemas import OrmModel
from social_network.dependencies import get_current_user
from social_network.posts.models import Post
from social_network.users.models import User
from social_network.users.schemas import UserPublic


class UserMinimal(OrmModel):
    uid: UUID
    avatar_link: str
    bio: str
    username: str
    full_name: str


class PostUpdate(OrmModel):
    """Modelo usado na edição do conteúdo do post"""

    content: str


class PostInteract(OrmModel):
    """Modelo usado para o usuário curtir/descurtir um post"""

    type: str


class PostCreate(OrmModel):
    """Modelo usado para criar um post"""

    content: str


class PostBase(OrmModel):
    """Modelo usado na listagem de post"""

    uid: UUID
    content: str
    created_at: datetime
    updated_at: datetime


class PostList(OrmModel):
    """Modelo usado na listagem dos posts"""

    posts: list["PostDetails"]


class PostFeedList(OrmModel):
    """Modelo usado na listagem dos posts"""

    posts: list["PostDetailsWithoutOwner"]


class PostDetails(OrmModel):
    """Modelo usado para obter um post específico"""

    uid: UUID
    content: str
    owner: UserMinimal
    created_at: datetime
    updated_at: datetime
    likes: int
    dislikes: int
    liked_by_me: bool = False
    disliked_by_me: bool = False
    comments: list["Self"] | None

    @classmethod
    async def from_post(cls, post: Post, current_user: User):
        # Carrega dados principais do post
        owner = await UserPublic.from_user((await post.owner.find_connected_nodes())[0], current_user)

        async def count_reactions(node, reaction_type):
            return await node.count(
                {
                    "uid": str(node.uid),
                    "$patterns": [
                        {
                            "$relationship": {"$type": reaction_type},
                            "$exists": True,
                            "$direction": RelationshipMatchDirection.INCOMING,
                        }
                    ],
                }
            )

        async def load_comments_recursive(comment_post):
            comment_owner = await UserPublic.from_user((await comment_post.owner.find_connected_nodes())[0], current_user)
            likes = await count_reactions(comment_post, "LIKED")
            dislikes = await count_reactions(comment_post, "DISLIKED")

            # Carrega subcomentários
            sub_comments = await comment_post.find_connected_nodes(
                {
                    "$node": {"$labels": ["Post"]},
                    "$direction": RelationshipMatchDirection.INCOMING,
                    "$relationships": [{"$type": "LINKED_TO"}],
                    "$maxHops": 1,
                }
            )

            # Constrói o comentário com os campos obrigatórios
            return cls(
                **comment_post.model_dump(exclude=["comments", "owner"]),
                owner=comment_owner,
                likes=likes,
                dislikes=dislikes,
                liked_by_me=bool(await current_user.likes.find_connected_nodes({"uid": str(comment_post.uid)})),
                disliked_by_me=bool(await current_user.dilikes.find_connected_nodes({"uid": str(comment_post.uid)})),
                comments=[await load_comments_recursive(sub_comment) for sub_comment in sub_comments],
            )

        top_comments = await post.find_connected_nodes(
            {
                "$node": {"$labels": ["Post"]},
                "$direction": RelationshipMatchDirection.INCOMING,
                "$relationships": [{"$type": "LINKED_TO"}],
                "$maxHops": 1,
            }
        )

        return cls(
            **post.model_dump(exclude=["comments", "owner"]),
            comments=[await load_comments_recursive(comment) for comment in top_comments],
            owner=owner,
            liked_by_me=bool(await current_user.likes.find_connected_nodes({"uid": str(post.uid)})),
            disliked_by_me=bool(await current_user.dilikes.find_connected_nodes({"uid": str(post.uid)})),
            likes=await count_reactions(post, "LIKED"),
            dislikes=await count_reactions(post, "DISLIKED"),
        )


class PostDetailsWithoutOwner(OrmModel):
    """Modelo usado para obter um post específico"""

    uid: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    liked_by_me: bool = False
    disliked_by_me: bool = False
    comments: list["Self"] | None

    @classmethod
    async def from_post(cls, post: Post, user_owner: User):
        async def count_reactions(node, reaction_type):
            return await node.count(
                {
                    "uid": str(node.uid),
                    "$patterns": [
                        {
                            "$relationship": {"$type": reaction_type},
                            "$exists": True,
                            "$direction": RelationshipMatchDirection.INCOMING,
                        }
                    ],
                }
            )

        async def load_comments_recursive(comment_post):
            comment_owner = await UserPublic.from_user(user_owner)
            likes = await count_reactions(comment_post, "LIKED")
            dislikes = await count_reactions(comment_post, "DISLIKED")

            # Carrega subcomentários
            sub_comments = await comment_post.find_connected_nodes(
                {
                    "$node": {"$labels": ["Post"]},
                    "$direction": RelationshipMatchDirection.INCOMING,
                    "$relationships": [{"$type": "LINKED_TO"}],
                }
            )

            # Constrói o comentário com os campos obrigatórios
            return cls(
                **comment_post.model_dump(exclude=["comments", "owner"]),
                owner=comment_owner,
                likes=likes,
                dislikes=dislikes,
                liked_by_me=False,
                disliked_by_me=False,
                comments=[await load_comments_recursive(sub_comment) for sub_comment in sub_comments],
            )

        # Carrega dados principais do post
        top_comments = await post.find_connected_nodes(
            {
                "$node": {"$labels": ["Post"]},
                "$direction": RelationshipMatchDirection.INCOMING,
                "$relationships": [{"$type": "LINKED_TO"}],
            }
        )

        return cls(
            **post.model_dump(exclude=["comments"]),
            comments=[await load_comments_recursive(comment) for comment in top_comments],
            liked_by_me=bool(await user_owner.likes.find_connected_nodes({"uid": str(post.uid)})),
            disliked_by_me=bool(await user_owner.dilikes.find_connected_nodes({"uid": str(post.uid)})),
            likes=await count_reactions(post, "LIKED"),
            dislikes=await count_reactions(post, "DISLIKED"),
        )


class PostFilterSchema(BaseModel):
    content: str | None
    content_i: str | None
    # owner_username: str | None
    # owner_id: str | None
