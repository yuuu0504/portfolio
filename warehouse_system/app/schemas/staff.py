from pydantic import BaseModel

class StaffBase(BaseModel):
    stName: str
    stDept: str

class StaffCreate(StaffBase):
    pass

class Staff(StaffBase):
    StaffID: int

    class Config:
        from_attributes = True