from datetime import datetime
from uuid import UUID

from social_network.core.schemas import OrmModel
from social_network.posts.models import Post
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


class PostDetails(OrmModel):
    """Modelo usado para obter um post específico"""

    uid: UUID
    content: str
    owner: UserPublic
    created_at: datetime
    updated_at: datetime
    linked_to: list[PostBase] | None

    @classmethod
    def from_post(cls, post: Post):
        owner = UserPublic.from_user(post.owner.nodes[0])
        linked_to = post.linked_to.nodes
        return cls(**post.model_dump(exclude=["linked_to", "owner"]), linked_to=linked_to, owner=owner)
