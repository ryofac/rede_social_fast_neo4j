from datetime import datetime
from typing import ForwardRef
from uuid import UUID, uuid4

from pydantic import Field
from pyneo4j_ogm import NodeModel, RelationshipModel, RelationshipProperty, RelationshipPropertyCardinality, RelationshipPropertyDirection, WithOptions

from social_network.core.models import DatedModelMixin

# from social_network.users.models import User


class Post(NodeModel, DatedModelMixin):
    uid: UUID = Field(unique=True, default_factory=uuid4)
    content: str
    owner: RelationshipProperty[ForwardRef("User"), ForwardRef("Owns")] = RelationshipProperty(
        target_model="User",
        relationship_model="Owns",
        direction=RelationshipPropertyDirection.INCOMING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_ONE,
        allow_multiple=False,
    )

    linked_to: RelationshipProperty["Post", "LinkedTo"] = RelationshipProperty(
        target_model="Post",
        relationship_model="LinkedTo",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=True,
    )

    def update(self):
        self.updated_at = datetime.now()
        return super().update()


class LinkedTo(RelationshipModel):
    pass


class Comments(RelationshipModel):
    pass


class Owns(RelationshipModel):
    pass
