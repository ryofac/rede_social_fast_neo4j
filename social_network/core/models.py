# from uuid import UUID, uuid4

# from pydantic import Field
# from pyneo4j_ogm import NodeModel, WithOptions


# class Base(NodeModel):
#     id: WithOptions(UUID, unique=True) = Field(init=False, primary_key=True)

 
from datetime import datetime

from pydantic import Field, field_validator, validator


class DatedModelMixin:
    @field_validator("created_at", "updated_at", mode="before")
    def convert_datetime(cls, value):
        if hasattr(value, "to_native"):  
            return value.to_native()          
        return value
    
    created_at: datetime = Field(init=False, default_factory=datetime.now)
    updated_at: datetime = Field(init=False, default_factory=datetime.now)
    
