from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field
from pyneo4j_ogm import NodeModel, RelationshipModel, RelationshipProperty, RelationshipPropertyCardinality, RelationshipPropertyDirection, WithOptions

from social_network import security


class User(NodeModel):
    uid: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    username: WithOptions(str, unique=True)
    email: WithOptions(str, unique=True)
    full_name: WithOptions(str, text_index=True)
    _password: WithOptions(str)
    created_at: WithOptions(datetime)
    updated_at: WithOptions(datetime)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, new_password: str):
        self._password = security.get_password_hash(new_password)

    def verify_password(self, plain_password: str):
        return security.verify_password(plain_password, self.password)

    # following: RelationshipProperty["User", "Following"] = RelationshipProperty(
    #     target_model="User",
    #     relationship_model="Following",
    #     direction=RelationshipPropertyDirection.OUTGOING,
    #     cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
    #     allow_multiple=True,
    # )