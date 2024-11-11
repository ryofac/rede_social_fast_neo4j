from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field

from social_network.core.schemas import OrmModel
from social_network.posts.models import Post
from social_network.users.models import User


class PostDetailsWithoutOwner(OrmModel):
    """Modelo usado para obter um post específico"""

    uid: UUID
    content: str
    created_at: datetime
    updated_at: datetime

    linked_to: list["Self"] | None

    @classmethod
    def from_post(cls, post: Post):
        linked_to = post.linked_to.nodes
        return cls(
            **post.model_dump(exclude=["linked_to"]),
            linked_to=linked_to,
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
    following: list["UserPublic"]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_user(cls, user: User):
        user_following = [UserPublic.from_user(user) for user in user.following.nodes]
        posts = [PostDetailsWithoutOwner.from_post(post) for post in user.posts.nodes]
        return cls(
            **user.model_dump(
                exclude=["posts", "following"],
            ),
            posts=posts,
            following=user_following,
        )


class UserList(OrmModel):
    users: list[UserPublic]


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


class UserFilterSchema(BaseModel):
    dt_created_from: datetime | None
    dt_created_to: datetime | None
    name: str | None
    name_i: str | None
    username: str | None
    username_i: str | None
