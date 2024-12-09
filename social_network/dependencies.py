import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import Depends, FastAPI, HTTPException, status
from jwt import InvalidTokenError
import neo4j
import neo4j.exceptions
import neo4j.warnings
from pyneo4j_ogm import Pyneo4jClient

from social_network.auth.auth_bearer import JWTBearer
from social_network.auth.auth_handler import decode_jwt
from social_network.posts.models import Comments, LinkedTo, Owns, Post
from social_network.settings import settings
from social_network.users.models import Disliked, Following, Liked, User


logger = logging.getLogger(__name__)


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

async def try_to_connect_neo4j(client):
    error_ocurred = False
    while not client.is_connected or error_ocurred:
        try:
            await client.connect(uri=settings.neo4j_url, auth=("neo4j", settings.NEO_PASSWORD))
            await client.register_models([User, Post, Owns, Comments, Following, LinkedTo, Liked, Disliked])
            print(f"✅ Servidor Neo4j {settings.neo4j_url} conectado com sucesso")
            error_ocurred = False
        except neo4j.exceptions.ServiceUnavailable:
            print("❌ Servidor Neo4j momentaneamente indisponível, retentando conexão...")
            error_ocurred = True
            await asyncio.sleep(1)
            continue

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = Pyneo4jClient()
    await try_to_connect_neo4j(client)
    yield
    await client.close()


   
