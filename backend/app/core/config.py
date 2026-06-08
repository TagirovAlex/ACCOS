from pathlib import Path

from pydantic_settings import BaseSettings
from typing import List
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/accos"
    jwt_secret_key: str = "super-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    ldap_server: str = "ldap://localhost:389"
    ldap_domain: str = "DOMAIN"
    ldap_base_dn: str = "DC=domain,DC=local"
    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_model: str = "default"
    lmstudio_api_key: str = ""
    comfyui_base_url: str = "http://localhost:8188"
    comfyui_api_key: str = ""
    admin_username: str = "admin"
    admin_password: str = "admin123"
    cors_origins: str = '["http://localhost:3000","http://localhost:5173"]'
    log_level: str = "DEBUG"
    rate_limits_enabled: bool = True
    ldap_enabled: bool = False

    @property
    def cors_origin_list(self) -> List[str]:
        return json.loads(self.cors_origins)

    @property
    def DB_HOST(self) -> str:
        return self.database_url.split("://")[1].split("@")[1].split(":")[0]

    @property
    def DB_PORT(self) -> str:
        return self.database_url.split("://")[1].split("@")[1].split(":")[1].split("/")[0]

    @property
    def DB_NAME(self) -> str:
        return self.database_url.split("://")[1].split("@")[1].split("/")[1]

    @property
    def DB_USER(self) -> str:
        return self.database_url.split("://")[1].split(":")[0]

    @property
    def DB_PASSWORD(self) -> str:
        user_pass = self.database_url.split("://")[1].split("@")[0]
        return user_pass.split(":")[1] if ":" in user_pass else ""

    model_config = {"env_file": str(Path(__file__).parent.parent.parent.parent / "config" / ".env"), "env_file_encoding": "utf-8"}


settings = Settings()
