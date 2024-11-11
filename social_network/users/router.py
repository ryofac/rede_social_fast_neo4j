import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pyneo4j_ogm.queries.query_builder import RelationshipMatchDirection

# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
from social_network import security
from social_network.auth import auth_bearer
from social_network.auth.router import get_current_user

# from social_network.database import get_session
# from social_network.users.filters import UserFilterSchema, filter_user
from social_network.users.models import User
from social_network.users.schemas import UserCreate, UserList, UserPublic, UserUpdate

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublic,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "User with the same data already exists."},
    },
)
async def create_user(user: UserCreate):
    db_user: User = User(**user.model_dump(exclude="password"))

    existent_user = await User.find_one({"username": user.username})
    if not existent_user:
        existent_user = await User.find_one({"email": user.email})

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

    db_user.password = security.get_password_hash(user.password)
    await db_user.create()
    await db_user.refresh()

    return UserPublic.from_user(db_user)


@user_router.post(
    "/follow/{user_to_follow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User to follow does not exist."},
        status.HTTP_400_BAD_REQUEST: {
            "description": "User is currently following the user",
        },
    },
)
async def follow_user(user_to_follow_id: str, current_user: User = Depends(get_current_user)):
    user_to_follow = await User.find_one({"uid": user_to_follow_id})

    if not user_to_follow:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User to follow does not exist.")

    is_already_following = len(await current_user.find_connected_nodes({"$node": {"$labels": "User"}, "uid": user_to_follow_id})) > 0

    if is_already_following:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You are already following this user")

    await current_user.following.connect(user_to_follow)
    return current_user


@user_router.get(
    "/",
    response_model=UserList,
)
async def get_users(
    dt_created_from: datetime | None = Query(None, description="Data de criação a partir de"),
    dt_created_to: datetime | None = Query(None, description="Data de criação limite"),
    name: str | None = Query(None, description="Busca por nome exato"),
    name_i: str | None = Query(None, description="Busca por nome parecido"),
    username: str | None = Query(None, description="Busca por username exato"),
    username_i: str | None = Query(None, description="Busca por username parecido"),
    limit: int = 100,
    offset: int = 0,
):
    # query = filter_user(
    #     UserFilterSchema(
    #         dt_created_from=dt_created_from,
    #         dt_created_to=dt_created_to,
    #         name_i=name_i,
    #         name=name,
    #         username=username,
    #         username_i=username_i,
    #     )
    # )

    results = await User.find_many(auto_fetch_nodes=True)

    for ind, user in enumerate(results):
        results[ind] = UserPublic.from_user(user)

    all_users = UserList.model_validate({"users": results})
    return all_users


@user_router.get(
    "/me",
    response_model=UserPublic,
)
async def me(current_user: User = Depends(get_current_user)):
    return UserPublic.from_user(current_user)


@user_router.get(
    "/{user_id}",
    response_model=UserPublic,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def get_user_by_id(user_id: str):
    user_db = await User.find_one({"uid": user_id})

    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!",
        )

    return UserPublic.from_user(user_db)


@user_router.put(
    "/{user_id}",
    response_model=UserPublic,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def update_user(user_id: str, user_update: UserUpdate):
    exist_user: User = await User.find_one({"uid": user_id}, auto_fetch_nodes=True)

    if not exist_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!",
        )

    exist_user.password = security.get_password_hash(user_update.password)
    exist_user.full_name = user_update.full_name

    await exist_user.update()
    await exist_user.refresh()

    return UserPublic.from_user(exist_user)


@user_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def delete_user(user_id: str):
    exist_user = await User.find_one({"uid": user_id})

    if not exist_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!",
        )

    await exist_user.delete()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@user_router.get(
    "/recommendations/",
    response_model=list[UserPublic],
)
async def recomendations(current_user: User = Depends(get_current_user)):
    recommendations = await User.find_many(
        {
            "$patterns": [
                {
                    "$exists": True,
                    "$direction": RelationshipMatchDirection.OUTGOING,
                    "$node": {
                        "$id": 0,
                        "$labels": ["User"],
                    },
                    "$relationship": {
                        "$type": "FOLLOWING",
                    },
                },
                {
                    "$exists": True,
                    "$direction": RelationshipMatchDirection.OUTGOING,
                    "$node": {
                        "$id": 1,
                        "$labels": ["User"],
                    },
                    "$relationship": {
                        "$type": "FOLLOWING",
                    },
                },
                {
                    "$exists": False,
                    "$direction": RelationshipMatchDirection.OUTGOING,
                    "$node": {
                        "$id": 2,
                        "$labels": ["User"],
                        "uid": str(current_user.uid),
                    },
                    "$relationship": {
                        "$type": "FOLLOWING",
                    },
                },
            ]
        }
    )

    return [UserPublic.from_user(user) for user in recommendations]
