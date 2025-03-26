from pydantic import BaseModel, EmailStr
from datetime import datetime

# Schemas for Book:
class BookBase(BaseModel):
    title: str
    author: str
    year: int

class BookCreate(BookBase):
    pass

class BookDelete(BookBase):
    pass

class BookReserve(BookBase):
    is_reserved: bool

class Book(BookBase):
    id: int

    class Config:
        orm_mode = True

# Schemas for User:
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RevokedToken(BaseModel):
    jti: str
    revoked_at: datetime

class TokenData(BaseModel):
    username: str = None
