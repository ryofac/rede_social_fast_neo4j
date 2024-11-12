from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from jwt import InvalidTokenError

# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
from social_network.auth.auth_bearer import JWTBearer
from social_network.auth.auth_handler import decode_jwt, sign_jwt
from social_network.auth.schemas import TokenResponse, UserAuthSchema
from social_network.security import get_password_hash

# from social_network.database import get_session
# from social_network.dependencies import get_user_repository
from social_network.users.models import User
from social_network.users.schemas import UserCreate, UserPublic

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/register",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
async def register(user: UserCreate):
    db_user: User = User(**user.model_dump(exclude="password"))

    existent_user = await User.find_one({"username": user.username, "email": user.email})

    if existent_user:
        if existent_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with the same username exists",
            )
        elif existent_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with the same email exists",
            )

    db_user.password = get_password_hash(user.password)
    await db_user.create()
    await db_user.refresh()
    return UserPublic(**db_user.model_dump(exclude=["posts"]), posts=db_user.posts.nodes)


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
async def login(user: UserAuthSchema):
    existent_user = await User.find_one({"username": user.username})
    if not existent_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User credentials not valid 👎")

    if existent_user.verify_password(user.password):
        return sign_jwt(user.username)
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User credentials not valid 👎")
