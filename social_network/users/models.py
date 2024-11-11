from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import Field
from pyneo4j_ogm import NodeModel, RelationshipModel, RelationshipProperty, RelationshipPropertyCardinality, RelationshipPropertyDirection, WithOptions

from social_network import security
from social_network.posts.models import Owns, Post

if TYPE_CHECKING:
    pass
    # from social_network.posts.models import Owns, Post


class User(NodeModel):
    uid: WithOptions(UUID, unique=True) = Field(init=False, default_factory=uuid4)
    username: WithOptions(str, unique=True)
    email: WithOptions(str, unique=True)
    full_name: WithOptions(str, text_index=True)
    password: str = Field(init=False, default="")
    created_at: WithOptions(datetime) = Field(init=False, default_factory=datetime.now)
    updated_at: WithOptions(datetime) = Field(init=False, default_factory=datetime.now)

    def verify_password(self, plain_password: str):
        return security.verify_password(plain_password, self.password)

    def update(self):
        self.updated_at = datetime.now()
        return super().update()

    following: RelationshipProperty["User", "Following"] = RelationshipProperty(
        target_model="User",
        relationship_model="Following",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=True,
    )

    posts: RelationshipProperty["Post", "Owns"] = RelationshipProperty(
        target_model="Post",
        relationship_model="Owns",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )


class Following(RelationshipModel):
    pass
