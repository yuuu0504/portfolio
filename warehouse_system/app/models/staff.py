from typing import Optional
from sqlmodel import Field, SQLModel
from app.schemas.staff import StaffBase

class Staff(StaffBase, SQLModel, table=True):
    StaffID: Optional[int] = Field(default=None, primary_key=True)