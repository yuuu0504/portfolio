from pydantic import BaseModel
from typing import Optional


class ProductBase(BaseModel):
    prName: str
    prSpec: Optional[str] = None
    prCategory: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    ProductID: int

    class Config:
        from_attributes = True