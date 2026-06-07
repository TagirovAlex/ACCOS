from pydantic import BaseModel


class BaseResponse(BaseModel):
    success: bool = True
    error: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseResponse):
    access_token: str
    token_type: str = "bearer"


class UserInfoResponse(BaseResponse):
    id: str
    username: str
    email: str | None = None
    full_name: str | None = None
    balance: float
    is_admin: bool


class BalanceResponse(BaseResponse):
    balance: float
