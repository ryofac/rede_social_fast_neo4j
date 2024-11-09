from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_network.auth.auth_bearer import JWTBearer
from social_network.categories.models import Category
from social_network.categories.schemas import CategoryCreateOrUpdateSchema, CategoryList, CategorySchema
from social_network.database import get_session

category_router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    dependencies=[
        Depends(JWTBearer()),
    ],
)


@category_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryCreateOrUpdateSchema,
)
async def create_category(category: CategoryCreateOrUpdateSchema, session: AsyncSession = Depends(get_session)):
    db_category: Category = Category(**category.model_dump())

    session.add(db_category)
    await session.commit()
    await session.refresh(db_category)
    return db_category


@category_router.get(
    "/",
    response_model=CategoryList,
)
async def get_categories(limit: int = 100, offset: int = 0, session: AsyncSession = Depends(get_session)):
    result = await session.scalars(select(Category).offset(offset).limit(limit))
    categories = result.all()
    return {"categories": categories}


@category_router.get(
    "/{category_id}",
    response_model=CategorySchema,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Category not found!"},
    },
)
async def get_category_by_id(category_id: int, session: AsyncSession = Depends(get_session)):
    category_db = await session.scalar(select(Category).where(Category.id == category_id))

    if not category_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found!",
        )

    return category_db


@category_router.put(
    "/{category_id}",
    response_model=CategorySchema,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Category not found!"},
    },
)
async def update_category(category_id: int, category_update: CategoryCreateOrUpdateSchema, session: AsyncSession = Depends(get_session)):
    exist_category: Category = await session.scalar(select(Category).where(category_id == Category.id))

    if not exist_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catgory not found!",
        )

    exist_category.name = category_update.name
    exist_category.description = category_update.description

    await session.commit()
    await session.refresh(exist_category)

    return exist_category


@category_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Category not found!"},
    },
)
async def delete_category(category_id: int, session: AsyncSession = Depends(get_session)):
    exist_category = await session.scalar(select(Category).where(category_id == Category.id))

    if not exist_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found!",
        )

    await session.delete(exist_category)
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
