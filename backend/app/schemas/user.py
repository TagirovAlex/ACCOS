from pydantic import BaseModel


class ProfileUpdateRequest(BaseModel):
    default_system_prompt: str | None = None
    full_name: str | None = None
    email: str | None = None


class ProfileResponse(BaseModel):
    id: str
    username: str
    email: str | None = None
    full_name: str | None = None
    default_system_prompt: str | None = None
    avatar_path: str | None = None
    balance: float
    permissions: str = "chat"
    is_admin: bool = False


class AvatarResponse(BaseModel):
    avatar_url: str
