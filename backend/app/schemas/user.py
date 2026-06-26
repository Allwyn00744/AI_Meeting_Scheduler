from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


# Used when creating a new user
class UserCreate(BaseModel):
    name: str
    email: EmailStr


# Used when updating a user
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


# Used when returning user data
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)