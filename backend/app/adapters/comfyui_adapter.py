import asyncio
import json
import logging
import random
import uuid
import os
from pathlib import Path

import httpx

from app.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class ComfyUIAdapter(BaseAdapter):
    def __init__(self, base_url: str = "", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.workflows_dir = Path(__file__).parent.parent.parent.parent / "workflows"

    async def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def execute(self, **kwargs) -> dict:
        workflow_type = kwargs.get("workflow_type", "")
        prompt = kwargs.get("prompt", "")
        images = kwargs.get("images", [])
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        duration = kwargs.get("duration", 5)
        seed = kwargs.get("seed", -1)
        poll_timeout_minutes = kwargs.get("poll_timeout_minutes", 30)
        poll_interval = kwargs.get("poll_interval", 3)
        return await self.run_workflow(
            workflow_type, prompt, images, width, height, duration, seed,
            poll_timeout_minutes=poll_timeout_minutes,
            poll_interval=poll_interval,
        )

    async def _load_workflow(self, workflow_type: str) -> dict | None:
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
        return await asyncio.to_thread(self._read_json, filepath)

    def _read_json(self, path: Path) -> dict:
        with path.open(encoding="utf-8") as f:
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

    def _apply_resolution(self, workflow: dict, width: int, height: int) -> dict:
        for node in workflow.values():
            if not isinstance(node, dict):
                continue
            if not node.get("class_type", "").endswith("LatentImage"):
                continue
            inputs = node.get("inputs", {})
            if not isinstance(inputs, dict):
                continue
            if isinstance(inputs.get("width"), (int, float)):
                inputs["width"] = width
            if isinstance(inputs.get("height"), (int, float)):
                inputs["height"] = height
        return workflow

    def _apply_seed(self, workflow: dict, seed: int) -> dict:
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        for node in workflow.values():
            if not isinstance(node, dict):
                continue
            inputs = node.get("inputs", {})
            if not isinstance(inputs, dict):
                continue
            if "seed" in inputs:
                inputs["seed"] = seed
        return workflow

    async def upload_image(self, file_path: str) -> str | None:
        filename = os.path.basename(file_path)
        try:
            file_bytes = await asyncio.to_thread(lambda: open(file_path, "rb").read())
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {"image": (filename, file_bytes, "image/png")}
                response = await client.post(
                    f"{self.base_url}/upload/image",
                    files=files,
                    data={"overwrite": "true"},
                    headers={"x-api-key": self.api_key} if self.api_key else {},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("name", filename)
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return None

    async def run_workflow(self, workflow_type: str, prompt: str, images: list[str] = None,
                           width: int = 1024, height: int = 1024, duration: int = 5, seed: int = -1,
                           poll_timeout_minutes: int = 30, poll_interval: int = 3) -> dict:
        workflow = await self._load_workflow(workflow_type)
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
        workflow = self._apply_resolution(workflow, width, height)
        workflow = self._apply_seed(workflow, seed)

        prompt_id = str(uuid.uuid4())
        payload = {"prompt": workflow, "client_id": "accos"}

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/prompt",
                    json=payload,
                    headers=await self._headers(),
                )
                response.raise_for_status()
                data = response.json()
                queue_prompt_id = data.get("prompt_id", prompt_id)
                attempts = int((poll_timeout_minutes * 60) / poll_interval)
                return await self._poll_result(client, queue_prompt_id, max_attempts=attempts, interval=poll_interval)
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
                    headers={"x-api-key": self.api_key} if self.api_key else {},
                )
                response.raise_for_status()
                await asyncio.to_thread(self._write_file, save_path, response.content)
                return save_path
        except Exception as e:
            logger.error(f"Failed to download image {filename}: {e}")
            return None

    def _write_file(self, path: str, content: bytes) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)

    async def _poll_result(self, client: httpx.AsyncClient, prompt_id: str,
                           max_attempts: int = 600, interval: int = 3) -> dict:
        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.get(
                    f"{self.base_url}/history/{prompt_id}",
                    timeout=10.0,
                    headers={"x-api-key": self.api_key} if self.api_key else {},
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
                                        if isinstance(item, dict) and "filename" in item and item.get("type", "output") == "output":
                                            images.append({
                                                "filename": item["filename"],
                                                "subfolder": item.get("subfolder", ""),
                                                "type": item.get("type", "output"),
                                            })
                        if images:
                            return {"success": True, "images": images, "prompt_id": prompt_id}
            except Exception as e:
                logger.debug(f"Polling attempt {attempt}/{max_attempts}: {e}")
            if attempt % 20 == 0:
                logger.info(f"Still waiting for prompt {prompt_id}... ({attempt}/{max_attempts}, "
                            f"elapsed: {attempt * interval}s)")
            await asyncio.sleep(interval)
        logger.error(f"Polling timed out after {max_attempts * interval}s for prompt {prompt_id}")
        return {"success": False, "error": f"Timeout waiting for result after {max_attempts * interval}s"}
