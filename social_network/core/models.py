# from uuid import UUID, uuid4

# from pydantic import Field
# from pyneo4j_ogm import NodeModel, WithOptions


# class Base(NodeModel):
#     id: WithOptions(UUID, unique=True) = Field(init=False, primary_key=True)

 
# class DatedModelMixin:
#     created_at: Mapped[datetime] = mapped_column(
#         init=False,
#         server_default=func.now(),
#     )
#     updated_at: Mapped[datetime] = mapped_column(
#         init=False,
#         server_default=func.now(),
#         onupdate=func.now(),
#     )
