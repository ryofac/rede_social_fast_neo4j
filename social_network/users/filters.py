# from pyneo4j_ogm.queries.query_builder import QueryBuilder

# from social_network.users.models import User
# from social_network.users.schemas import UserFilterSchema


from social_network.users.schemas import UserFilterSchema


def filter_user(filter_parameters: UserFilterSchema):
    filters = {}

    if filter_parameters.name:
        filters["name"] = {"$eq": filter_parameters.name}

    if filter_parameters.name_i:
        if not filters.get("name"):
            filters["name"] = {"$icontains": filter_parameters.name_i}
        else:
            filters["name"].update({"$icontains": filter_parameters.name_i})

    if filter_parameters.username:
        filters["username"] = {"$eq": filter_parameters.username}

    if filter_parameters.username_i:
        if not filters.get("username"):
            filters["username"] = {"$icontains": filter_parameters.username_i}
        else:
            filters["username"].update({"$icontains": filter_parameters.username_i})

    return filters
