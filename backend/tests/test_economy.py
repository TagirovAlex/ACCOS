import pytest
from app.services.economy_service import EconomyService
from app.core.config import settings


@pytest.mark.asyncio
async def test_calculate_llm_cost():
    cost = EconomyService.calculate_cost("llm", tokens_input=100, tokens_output=50)
    assert isinstance(cost, float)
    assert cost > 0


@pytest.mark.asyncio
async def test_calculate_image_gen_cost():
    cost = EconomyService.calculate_cost("image_gen", width=1024, height=768)
    assert isinstance(cost, float)
    assert cost > 0


@pytest.mark.asyncio
async def test_calculate_image_edit_cost():
    cost = EconomyService.calculate_cost("image_edit", width=1024, height=768, avg_ref_size=512)
    assert isinstance(cost, float)
    assert cost > 0


@pytest.mark.asyncio
async def test_calculate_video_gen_cost():
    cost = EconomyService.calculate_cost("video_gen", resolution=1920, duration=5)
    assert isinstance(cost, float)
    assert cost > 0


@pytest.mark.asyncio
async def test_unknown_strategy():
    with pytest.raises(ValueError):
        EconomyService.calculate_cost("unknown")
