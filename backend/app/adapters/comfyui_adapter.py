import json
import logging
import uuid
import os
from pathlib import Path

import httpx

from app.adapters.base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class ComfyUIAdapter(BaseAdapter):
    def __init__(self):
        self.base_url = settings.comfyui_base_url.rstrip("/")
        self.workflows_dir = Path(__file__).parent.parent.parent.parent / "workflows"

    async def execute(self, **kwargs) -> dict:
        workflow_type = kwargs.get("workflow_type", "")
        prompt = kwargs.get("prompt", "")
        images = kwargs.get("images", [])
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        duration = kwargs.get("duration", 5)
        return await self.run_workflow(workflow_type, prompt, images, width, height, duration)

    def _load_workflow(self, workflow_type: str) -> dict | None:
        mapping = {
            "z_image": "ZIT.json",
            "qwen_edit_1": "QWEN edit 1 pic.json",
            "qwen_edit_2": "QWEN edit 2 pic.json",
            "qwen_edit_3": "QWEN edit 3 pic.json",
            "text_to_video": "text_to_video.json",
            "image_to_video": "image_to_video.json",
        }
        filename = mapping.get(workflow_type)
        if not filename:
            logger.error(f"Unknown workflow type: {workflow_type}")
            return None
        filepath = self.workflows_dir / filename
        if not filepath.exists():
            logger.error(f"Workflow file not found: {filepath}")
            return None
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    def _apply_prompt(self, workflow: dict, prompt: str, images: list[str] = None) -> dict:
        img_iter = iter(images or [])
        for node in workflow.values():
            if not isinstance(node, dict):
                continue
            inputs = node.get("inputs", {})
            if not isinstance(inputs, dict):
                continue
            class_type = node.get("class_type", "")

            if class_type == "LoadImage" and "image" in inputs:
                try:
                    inputs["image"] = next(img_iter)
                except StopIteration:
                    break
            else:
                if "text" in inputs and isinstance(inputs["text"], str) and not inputs["text"] and prompt:
                    inputs["text"] = prompt
                if "prompt" in inputs and isinstance(inputs["prompt"], str) and not inputs["prompt"] and prompt:
                    inputs["prompt"] = prompt
        return workflow

    async def upload_image(self, file_path: str) -> str | None:
        filename = os.path.basename(file_path)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(file_path, "rb") as f:
                    files = {"image": (filename, f, "image/png")}
                    response = await client.post(
                        f"{self.base_url}/upload/image",
                        files=files,
                        data={"overwrite": "true"},
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data.get("name", filename)
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return None

    async def run_workflow(self, workflow_type: str, prompt: str, images: list[str] = None, width: int = 1024, height: int = 1024, duration: int = 5) -> dict:
        workflow = self._load_workflow(workflow_type)
        if not workflow:
            return {"success": False, "error": f"Workflow {workflow_type} not found"}

        uploaded_images = []
        if images:
            for img_path in images:
                result = await self.upload_image(img_path)
                if not result:
                    return {"success": False, "error": f"Failed to upload {img_path}"}
                uploaded_images.append(result)

        workflow = self._apply_prompt(workflow, prompt, uploaded_images)

        prompt_id = str(uuid.uuid4())
        payload = {"prompt": workflow, "client_id": "accos"}

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/prompt",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                queue_prompt_id = data.get("prompt_id", prompt_id)
                return await self._poll_result(client, queue_prompt_id)
        except httpx.TimeoutException:
            logger.error("ComfyUI request timed out")
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            logger.error(f"ComfyUI error: {e}")
            return {"success": False, "error": str(e)}

    async def download_image(self, filename: str, subfolder: str = "", image_type: str = "output", save_path: str = "") -> str | None:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {"filename": filename, "subfolder": subfolder, "type": image_type}
                response = await client.get(
                    f"{self.base_url}/view",
                    params=params,
                )
                response.raise_for_status()
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return save_path
        except Exception as e:
            logger.error(f"Failed to download image {filename}: {e}")
            return None

    async def _poll_result(self, client: httpx.AsyncClient, prompt_id: str, max_attempts: int = 60) -> dict:
        import asyncio
        for attempt in range(max_attempts):
            try:
                response = await client.get(
                    f"{self.base_url}/history/{prompt_id}",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    if prompt_id in data:
                        outputs = data[prompt_id].get("outputs", {})
                        images = []
                        for node_id, node_output in outputs.items():
                            for key, value in node_output.items():
                                if isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, dict) and "filename" in item:
                                            images.append({
                                                "filename": item["filename"],
                                                "subfolder": item.get("subfolder", ""),
                                                "type": item.get("type", "output"),
                                            })
                        if images:
                            return {"success": True, "images": images, "prompt_id": prompt_id}
            except Exception:
                pass
            await asyncio.sleep(2)
        return {"success": False, "error": "Timeout waiting for result"}
