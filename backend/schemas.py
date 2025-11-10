from typing import Optional

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPayload(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class AuthResponse(BaseModel):
    user_id: str
    email: EmailStr
    token: Optional[TokenPayload] = None


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr


class Product(BaseModel):
    id: int
    name: str
    headline: Optional[str] = None
    description: Optional[str] = None
    price_cents: Optional[int] = None
    image_url: Optional[str] = None
