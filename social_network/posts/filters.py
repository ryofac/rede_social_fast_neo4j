from pyneo4j_ogm.queries.query_builder import RelationshipMatchDirection

from social_network.posts.schemas import PostFilterSchema


def filter_post(filters_parameters: PostFilterSchema):
    filters = {}
    filters["$patterns"] = []

    if filters_parameters.content:
        filters["content"] = {"$eq": filters_parameters.content}

    if filters_parameters.content_i:
        if not filters.get("content"):
            filters["content"] = {"$icontains": filters_parameters.content_i}
        else:
            filters["content"].update({"$icontains": filters_parameters.content_i})

    # if filters_parameters.owner_username:
    #     filters["$patterns"].append(
    #         {
    #             "$exists": True,
    #             "$direction": RelationshipMatchDirection.OUTGOING,
    #             "$node": {
    #                 "$labels": ["User"],
    #                 "username": {"$icontains": filters_parameters.owner_username},
    #             },
    #             "$relashionship": {"$type": "OWNS"},
    #         }
    #     )

    # if filters_parameters.owner_id:
    #     filters["$patterns"].append(
    #         {
    #             "$exists": True,
    #             "$direction": RelationshipMatchDirection.OUTGOING,
    #             "$node": {
    #                 "$labels": ["User"],
    #                 "uid": {"$eq": filters_parameters.owner_id},
    #             },
    #             "$relashionship": {"$type": "OWNS"},
    #         }
    #     )

    return filters
