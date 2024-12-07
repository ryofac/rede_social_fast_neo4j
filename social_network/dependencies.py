from fastapi import Depends, HTTPException, status
from jwt import InvalidTokenError
from pyneo4j_ogm import Pyneo4jClient

from social_network.auth.auth_bearer import JWTBearer
from social_network.auth.auth_handler import decode_jwt
from social_network.posts.models import Comments, LinkedTo, Owns, Post
from social_network.settings import settings
from social_network.users.models import Disliked, Following, Liked, User


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
    client = Pyneo4jClient()

    await client.connect(uri=settings.neo4j_url, auth=("neo4j", settings.NEO_PASSWORD))
    await client.register_models([User, Post, Owns, Comments, Following, LinkedTo, Liked, Disliked])
