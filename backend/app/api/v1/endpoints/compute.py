from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.dependencies import get_current_user_id
from app.services import compute_service

router = APIRouter(prefix="/compute", tags=["compute"])


class ComputeRequest(BaseModel):
    session_id: str
    code_lines: list[str]


class ComputeResponse(BaseModel):
    success: bool = True
    error: str | None = None
    results: list[str] = []
    variables: dict[str, str] = {}


@router.post("/evaluate", response_model=ComputeResponse)
async def evaluate(
    request: Request,
    body: ComputeRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        result = compute_service.execute(body.session_id, body.code_lines)
        return ComputeResponse(**result)
    except Exception as e:
        return ComputeResponse(success=False, error=str(e))
