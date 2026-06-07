from pydantic_settings import BaseSettings
from typing import List
import json


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

    @property
    def cors_origin_list(self) -> List[str]:
        return json.loads(self.cors_origins)

    model_config = {"env_file": "config/.env", "env_file_encoding": "utf-8"}


settings = Settings()
