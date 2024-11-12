from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel
from pyneo4j_ogm.queries.query_builder import RelationshipMatchDirection

from social_network.core.schemas import OrmModel
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
    comments: list[PostBase] | None

    @classmethod
    async def from_post(cls, post: Post, current_user: User):
        liked_by_me = len(await current_user.likes.find_connected_nodes({"uid": str(post.uid)})) > 0
        disliked_by_me = len(await current_user.dilikes.find_connected_nodes({"uid": str(post.uid)})) > 0

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

        owner = await UserPublic.from_user(current_user)

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
            comment_owner = await UserPublic.from_user(current_user)

            # Cria a instância de comentário com todos os campos obrigatórios preenchidos
            comment_details = cls(
                **comment_post.model_dump(exclude=["comments", "owner", "likes", "deslikes"]),
                owner=comment_owner,
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
            **post.model_dump(exclude=["comments", "owner"]),
            comments=formatted_comments,
            owner=owner,
            liked_by_me=liked_by_me,
            disliked_by_me=disliked_by_me,
            likes=likes_amount,
            dislikes=dislikes_amount,
        )


class PostDetailsWithoutOwner(OrmModel):
    """Modelo usado para obter um post específico"""

    uid: UUID
    content: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    liked_by_me: bool = False
    disliked_by_me: bool = False
    comments: list["Self"] | None

    @classmethod
    async def from_post(cls, post: Post, current_user: User):
        liked_by_me = len(await current_user.likes.find_connected_nodes({"uid": str(post.uid)})) > 0
        disliked_by_me = len(await current_user.dilikes.find_connected_nodes({"uid": str(post.uid)})) > 0

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

        owner = await UserPublic.from_user(current_user)

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
            comment_owner = await UserPublic.from_user(current_user)

            # Cria a instância de comentário com todos os campos obrigatórios preenchidos
            comment_details = cls(
                **comment_post.model_dump(exclude=["comments", "owner", "likes", "dislikes"]),
                owner=comment_owner,
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
            **post.model_dump(exclude=["comments", "owner"]),
            comments=formatted_comments,
            owner=owner,
            liked_by_me=liked_by_me,
            disliked_by_me=disliked_by_me,
            likes=likes_amount,
            dislikes=dislikes_amount,
        )


class PostFilterSchema(BaseModel):
    content: str | None
    content_i: str | None
    # owner_username: str | None
    # owner_id: str | None
