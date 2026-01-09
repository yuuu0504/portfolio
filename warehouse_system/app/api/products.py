from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.product import Product as ProductSchema, ProductCreate
from app.models.product import Product as ProductModel
from app.core.database import get_db
from sqlalchemy.exc import IntegrityError
from app.schemas.error import HTTPError

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[ProductSchema])
async def get_products(
    skip: int = Query(0, ge=0, description="跳過前 N 筆"),
    limit: int = Query(10, le=100, description="限制回傳 N 筆"),
    q: Optional[str] = Query(None, description="搜尋產品名稱或分類"),
    db: AsyncSession = Depends(get_db)
):
    statement = select(ProductModel)
    if q:
        statement = statement.where(
            (ProductModel.prName.contains(q)) | (ProductModel.prCategory.contains(q))
        )
    
    if limit > 0:
        statement = statement.offset(skip).limit(limit)
    result = await db.exec(statement)
    return result.all()

@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(ProductModel, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    new_product = ProductModel.model_validate(product)
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, updated_product: ProductCreate, db: AsyncSession = Depends(get_db)):
    db_product = await db.get(ProductModel, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    data = updated_product.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_product, key, value)
        
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.delete(
    "/{product_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": HTTPError, "description": "Integrity Error: Staff has linked orders"},
    }
)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    db_product = await db.get(ProductModel, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        await db.delete(db_product)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無法刪除：該商品尚有庫存紀錄或存在於交易單據中(如進貨單、領料單)。"
        )
    return None