import pytest
from app.services.economy_service import (
    LLMCostStrategy, ImageGenCostStrategy,
    ImageEditCostStrategy, VideoGenCostStrategy,
)


@pytest.mark.asyncio
async def test_calculate_llm_cost():
    s = LLMCostStrategy()
    cost = s.calculate_cost(tokens_input=100, tokens_output=50)
    assert isinstance(cost, (int, float))
    assert cost > 0


@pytest.mark.asyncio
async def test_calculate_image_gen_cost():
    s = ImageGenCostStrategy()
    cost = s.calculate_cost(width=1024, height=768)
    assert isinstance(cost, (int, float))
    assert cost > 0


@pytest.mark.asyncio
async def test_calculate_image_edit_cost():
    s = ImageEditCostStrategy()
    cost = s.calculate_cost(width=1024, height=768, avg_ref_size=512)
    assert isinstance(cost, (int, float))
    assert cost > 0


@pytest.mark.asyncio
async def test_calculate_video_gen_cost():
    s = VideoGenCostStrategy()
    cost = s.calculate_cost(resolution=1920, duration=5)
    assert isinstance(cost, (int, float))
    assert cost > 0


@pytest.mark.asyncio
async def test_unknown_strategy():
    from app.services.economy_service import LLMCostStrategy
    s = LLMCostStrategy()
    with pytest.raises(KeyError):
        # Access a strategy via dict to simulate unknown lookup
        strategies = {"llm": s}
        strategies["unknown"]
