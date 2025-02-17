from datetime import datetime
from typing import Optional, Self
from uuid import UUID

from pydantic import BaseModel, Field
from pyneo4j_ogm.queries.query_builder import RelationshipMatchDirection

from social_network.core.schemas import OrmModel
from social_network.posts.models import Post
from social_network.users.models import User


class UserMinimal(OrmModel):
    uid: UUID
    avatar_link: str
    bio: str
    username: str
    full_name: str


class PostDetailsWithoutOwner(OrmModel):
    """Modelo usado para obter um post específico"""

    uid: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    likes: int
    dislikes: int
    liked_by_me: bool = False
    disliked_by_me: bool = False
    comments: list["Self"] | None

    @classmethod
    async def from_post(cls, post: Post, current_user: User):
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
                likes=likes,
                dislikes=dislikes,
                liked_by_me=bool(await current_user.likes.find_connected_nodes({"uid": str(comment_post.uid)})),
                disliked_by_me=bool(await current_user.dilikes.find_connected_nodes({"uid": str(comment_post.uid)})),
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
            liked_by_me=bool(await current_user.likes.find_connected_nodes({"uid": str(post.uid)})),
            disliked_by_me=bool(await current_user.dilikes.find_connected_nodes({"uid": str(post.uid)})),
            likes=await count_reactions(post, "LIKED"),
            dislikes=await count_reactions(post, "DISLIKED"),
        )


class UserBase(OrmModel):
    uid: UUID
    username: str
    full_name: str
    password: str
    # debits: list[DebitSchema]
    created_at: datetime
    updated_at: datetime


class UserPublic(OrmModel):
    """Modelo usado no retorno de dados do usuário"""

    uid: UUID
    username: str
    full_name: str
    email: str
    bio: str | None = Field(default=None)
    avatar_link: str | None = Field(default=None)
    posts: list[PostDetailsWithoutOwner]
    following: list["UserMinimal"]
    followed_by: list["UserMinimal"]
    created_at: datetime
    updated_at: datetime

    @classmethod
    async def from_user(cls, user: User, current_user: User):
        if not current_user:
            current_user = user

        users_following_raw = await user.following.find_connected_nodes({"$maxHops": 1})
        user_following = [UserMinimal(**user.model_dump()) for user in users_following_raw]

        users_followed = await user.find_connected_nodes(
            {
                "$node": {"$labels": ["User"]},
                "$direction": RelationshipMatchDirection.INCOMING,
                "$relationships": [{"$type": "FOLLOWS"}],
                "$maxHops": 1,
            },
        )

        users_followed = [UserMinimal(**user.model_dump()) for user in users_followed]

        posts_raw = await user.posts.find_connected_nodes({"$maxHops": 1})
        posts = [await PostDetailsWithoutOwner.from_post(post, current_user) for post in posts_raw]
        return cls(
            **user.model_dump(
                exclude=["posts", "following", "followed_by"],
            ),
            posts=posts,
            following=user_following,
            followed_by=users_followed,
        )


class UserList(OrmModel):
    users: list[UserMinimal]


class UserCreate(OrmModel):
    """Modelo usado na criação de dados do usuário"""

    username: str
    email: str
    full_name: str
    password: str
    bio: str
    avatar_link: str


class UserUpdate(OrmModel):
    """Modelo usado na atualização de dados do usuário"""

    full_name: str
    password: str
    avatar_link: str
    bio: str


class UserUpdatePartial(OrmModel):
    """Modelo usado na atualização de dados do usuário"""

    full_name: Optional[str] = None
    password: Optional[str] = None
    avatar_link: Optional[str] = None
    bio: Optional[str] = None


class UserFilterSchema(BaseModel):
    name: str | None
    name_i: str | None
    username: str | None
    username_i: str | None
