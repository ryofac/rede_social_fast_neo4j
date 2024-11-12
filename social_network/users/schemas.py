from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field
from pyneo4j_ogm.queries.query_builder import RelationshipMatchDirection

from social_network.core.schemas import OrmModel
from social_network.posts.models import Post
from social_network.users.models import User


class PostDetailsWithoutOwner(OrmModel):
    """Modelo usado para obter um post específico"""

    uid: UUID
    content: str
    created_at: datetime
    updated_at: datetime

    comments: list["Self"] | None

    @classmethod
    async def from_post(cls, post: Post):
        likes_amount = await post.count(
            {
                "uid": str(post.uid),
                "$patterns": [
                    {
                        "$relationship": {
                            "$type": "LIKED",
                        },
                        "$exists": True,
                        "$direction": RelationshipMatchDirection.INCOMING,
                    }
                ],
            },
        )
        dislikes_amount = await post.count(
            {
                "uid": str(post.uid),
                "$patterns": [
                    {
                        "$relationship": {
                            "$type": "DISLIKED",
                        },
                        "$exists": True,
                        "$direction": RelationshipMatchDirection.INCOMING,
                    }
                ],
            }
        )

        # Função recursiva para carregar todos os comentários em profundidade
        async def load_comments_recursive(comment_post):
            # Conta likes e dislikes de cada comentário
            likes = await comment_post.count(
                {
                    "uid": str(comment_post.uid),
                    "$patterns": [
                        {
                            "$relationship": {
                                "$type": "LIKED",
                            },
                            "$exists": True,
                            "$direction": RelationshipMatchDirection.INCOMING,
                        }
                    ],
                },
            )
            dislikes = await comment_post.count(
                {
                    "uid": str(comment_post.uid),
                    "$patterns": [
                        {
                            "$relationship": {
                                "$type": "DISLIKED",
                            },
                            "$exists": True,
                            "$direction": RelationshipMatchDirection.INCOMING,
                        }
                    ],
                }
            )

            # Carrega o proprietário de cada comentário
            # Cria a instância de comentário com todos os campos obrigatórios preenchidos
            comment_details = cls(
                **comment_post.model_dump(exclude=["comments", "likes", "deslikes"]),
                likes=likes,
                dislikes=dislikes,
                liked_by_me=False,  # Se precisar, pode adaptar para verificar likes por usuário
                disliked_by_me=False,  # idem acima
                comments=[],
            )

            # Busca os subcomentários
            sub_comments = await comment_post.find_connected_nodes(
                {
                    "$node": {"$labels": ["Post"]},
                    "$direction": RelationshipMatchDirection.INCOMING,
                    "$relationships": [{"$type": "LINKED_TO"}],
                }
            )

            # Formata e adiciona os subcomentários
            comment_details.comments = [await load_comments_recursive(sub_comment) for sub_comment in sub_comments]
            return comment_details

        # Carrega e formata todos os comentários de forma recursiva
        top_level_comments = await post.find_connected_nodes(
            {
                "$node": {"$labels": ["Post"]},
                "$direction": RelationshipMatchDirection.INCOMING,
                "$relationships": [{"$type": "LINKED_TO"}],
            }
        )
        formatted_comments = [await load_comments_recursive(comment) for comment in top_level_comments]

        return cls(
            **post.model_dump(exclude=["comments"]),
            comments=formatted_comments,
            likes=likes_amount,
            dislikes=dislikes_amount,
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
    async def from_user(cls, user: User):
        user_following = [UserPublic.from_user(user) for user in user.following.nodes]
        posts = [await PostDetailsWithoutOwner.from_post(post) for post in user.posts.nodes]
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
    name: str | None
    name_i: str | None
    username: str | None
    username_i: str | None
