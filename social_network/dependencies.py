from pyneo4j_ogm import Pyneo4jClient

from social_network.posts.models import Comments, LinkedTo, Owns, Post
from social_network.settings import settings
from social_network.users.models import Following, User

# from social_network.users.repository import UserRepository


async def init_neo4j():
    # We initialize a new `Pyneo4jClient` instance and connect to the database.
    client = Pyneo4jClient()

    # Replace `<connection-uri-to-database>`, `<username>` and `<password>` with the
    # actual values.
    await client.connect(uri="bolt://neo4j:7687", auth=("neo4j", settings.NEO_PASSWORD))

    # To use our models for running queries later on, we have to register
    # them with the client.
    # **Note**: You only have to register the models that you want to use
    # for queries and you can even skip this step if you want to use the
    # `Pyneo4jClient` instance for running raw queries.
    await client.register_models([User, Post, Owns, Comments, Following, LinkedTo])


# def get_user_repository():
#     return UserRepository
