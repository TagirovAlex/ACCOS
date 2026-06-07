import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_generate_workflow(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    with patch("app.adapters.comfyui_adapter.ComfyUIAdapter.execute") as mock_run:
        mock_run.return_value = {"success": True, "images": [{"filename": "img1.png", "subfolder": "", "type": "output"}]}
        res = await client.post("/api/v1/generate/", json={
            "workflow_type": "ZIT.json",
            "prompt": "test prompt",
            "width": 64,
            "height": 64,
        }, headers=headers)
    data = res.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_generate_history(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    res = await client.get("/api/v1/generate/history", headers=headers)
    data = res.json()
    assert "generations" in data
