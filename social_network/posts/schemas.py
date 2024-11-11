from datetime import datetime
from typing import Self
from uuid import UUID

from pyneo4j_ogm.queries.query_builder import RelationshipMatchDirection

from social_network.core.schemas import OrmModel
from social_network.posts.models import Post
from social_network.users.models import User
from social_network.users.schemas import UserPublic


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
    owner: UserPublic

    created_at: datetime
    updated_at: datetime
    likes: int
    dislikes: int
    liked_by_me: bool = False
    disliked_by_me: bool = False
    linked_to: list[PostBase] | None

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

        owner = UserPublic.from_user(current_user)
        linked_to = post.linked_to.nodes
        return cls(
            **post.model_dump(exclude=["linked_to", "owner"]),
            linked_to=linked_to,
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
    linked_to: list["Self"] | None

    @classmethod
    async def from_post(cls, post: Post, current_user: User):
        liked_by_me = len(await current_user.likes.find_connected_nodes({"uid": str(post.uid)})) > 0
        disliked_by_me = len(await current_user.dilikes.find_connected_nodes({"uid": str(post.uid)})) > 0

        owner_id = str(post.owner.nodes[0].uid)
        linked_to = post.linked_to.nodes
        return cls(
            **post.model_dump(exclude=["linked_to"]),
            linked_to=linked_to,
            owner_id=owner_id,
            liked_by_me=liked_by_me,
            disliked_by_me=disliked_by_me,
        )
