from fastapi import FastAPI

from app.api.v1.endpoints import generation
from app.modules.base import BaseModule, ModuleSettingDef


class ComfyUIModule(BaseModule):
    name = "comfyui"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        app.include_router(generation.router, prefix="/api/v1")

    def get_settings_schema(self) -> list[ModuleSettingDef]:
        return [
            ModuleSettingDef(key="comfyui_base_url", label="Base URL", type="string", category="connection", default="http://localhost:8188", is_admin_setting=True, description="ComfyUI server URL"),
            ModuleSettingDef(key="comfyui_api_key", label="API key", type="password", category="connection", default="", is_admin_setting=True, description="ComfyUI API key"),
            ModuleSettingDef(key="comfyui_generate_base_url", label="Generate URL", type="string", category="connection", default="", is_admin_setting=True, description="Override for image generation"),
            ModuleSettingDef(key="comfyui_edit_base_url", label="Edit URL", type="string", category="connection", default="", is_admin_setting=True, description="Override for image editing"),
            ModuleSettingDef(key="comfyui_video_base_url", label="Video URL", type="string", category="connection", default="", is_admin_setting=True, description="Override for video generation"),
            ModuleSettingDef(key="comfyui_poll_interval", label="Poll interval (s)", type="number", category="connection", default=3, is_admin_setting=True, description="Seconds between progress polls"),
            ModuleSettingDef(key="comfyui_poll_timeout_minutes", label="Poll timeout (min)", type="number", category="connection", default=30, is_admin_setting=True, description="Max wait before giving up"),
            ModuleSettingDef(key="image_gen_base_cost", label="Generation base cost", type="number", category="pricing", default=0, is_admin_setting=True, description="Fixed base cost for image gen"),
            ModuleSettingDef(key="image_gen_rate_pixel", label="Generation rate per MP", type="number", category="pricing", default=2, is_admin_setting=True, description="Cost per megapixel"),
            ModuleSettingDef(key="image_edit_base_cost", label="Edit base cost", type="number", category="pricing", default=0, is_admin_setting=True, description="Fixed base cost for image edit"),
            ModuleSettingDef(key="image_edit_rate_pixel", label="Edit rate per MP", type="number", category="pricing", default=2, is_admin_setting=True, description="Cost per megapixel for edit"),
            ModuleSettingDef(key="image_pixels_per_unit", label="Pixels per unit", type="number", category="pricing", default=1000000, is_admin_setting=True, description="Pixel count per pricing unit"),
            ModuleSettingDef(key="video_gen_base_cost", label="Video base cost", type="number", category="pricing", default=10, is_admin_setting=True, description="Fixed base cost for video gen"),
            ModuleSettingDef(key="video_gen_rate_sec", label="Video rate per sec", type="number", category="pricing", default=2, is_admin_setting=True, description="Cost per second of video"),
        ]
