from social_network.core.schemas import OrmModel


class CategorySchema(OrmModel):
    id: int
    name: str
    description: str


class CategoryCreateOrUpdateSchema(OrmModel):
    name: str
    description: str


class CategoryList(OrmModel):
    categories: list[CategorySchema]
