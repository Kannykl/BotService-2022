"""User schemas"""

import uuid
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """Base user schema."""
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    email: EmailStr


class UserDb(User):
    """User database representation."""
    hashed_password: str
    is_admin: bool = False
