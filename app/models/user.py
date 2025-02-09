from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    confirmation_code: Optional[str] = None

class ConfirmUser(BaseModel):
    username: str
    confirmation_code: str
