from fastapi import Depends, HTTPException, status
from jwt import InvalidTokenError
from pyneo4j_ogm import Pyneo4jClient

from social_network.auth.auth_bearer import JWTBearer
from social_network.auth.auth_handler import decode_jwt
from social_network.posts.models import Comments, LinkedTo, Owns, Post
from social_network.settings import settings
from social_network.users.models import Disliked, Following, Liked, User

# from social_network.users.repository import UserRepository7


async def get_current_user(token: str = Depends(JWTBearer())) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        decoded_token = decode_jwt(token)
        if not decoded_token:
            return credentials_exception
    except InvalidTokenError:
        return credentials_exception

    username = decoded_token.get("user_id", None)
    if not username:
        raise credentials_exception

    user = await User.find_one({"username": username}, auto_fetch_nodes=True)
    if not user:
        raise credentials_exception
    return user


async def init_neo4j():
    # We initialize a new `Pyneo4jClient` instance and connect to the database.
    client = Pyneo4jClient()

    # Replace `<connection-uri-to-database>`, `<username>` and `<password>` with the
    # actual values.
    await client.connect(uri=settings.neo4j_url, auth=("neo4j", settings.NEO_PASSWORD))

    # To use our models for running queries later on, we have to register
    # them with the client.
    # **Note**: You only have to register the models that you want to use
    # for queries and you can even skip this step if you want to use the
    # `Pyneo4jClient` instance for running raw queries.
    await client.register_models([User, Post, Owns, Comments, Following, LinkedTo, Liked, Disliked])


# def get_user_repository():
#     return UserRepository
