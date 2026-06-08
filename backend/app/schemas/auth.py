from pydantic import BaseModel


class BaseResponse(BaseModel):
    success: bool = True
    error: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseResponse):
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"
    is_admin: bool = False


class UserInfoResponse(BaseResponse):
    id: str
    username: str
    email: str | None = None
    full_name: str | None = None
    balance: float
    permissions: str = "chat"
    is_admin: bool


class BalanceResponse(BaseResponse):
    balance: float
