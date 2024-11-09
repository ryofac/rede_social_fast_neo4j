# from sqlalchemy import select

# from social_network.users.models import User
# from social_network.users.schemas import UserFilterSchema


# def filter_user(filter_parameters: UserFilterSchema):
#     final_query = select(User)

#     if filter_parameters.dt_created_from:
#         final_query = final_query.filter(User.created_at > filter_parameters.dt_created_from)

#     if filter_parameters.dt_created_to:
#         final_query = final_query.filter(User.created_at <= filter_parameters.dt_created_to)

#     if filter_parameters.name:
#         final_query = final_query.filter(User.full_name.contains(filter_parameters.name))

#     if filter_parameters.name_i:
#         final_query = final_query.filter(User.full_name.icontains(filter_parameters.name_i))

#     if filter_parameters.username:
#         final_query = final_query.filter(User.username == filter_parameters.username)

#     if filter_parameters.username_i:
#         final_query = final_query.filter(User.username.icontains(filter_parameters.username_i))

#     return final_query
