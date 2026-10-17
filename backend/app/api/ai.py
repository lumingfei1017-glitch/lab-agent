import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.common.response import Response
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import ChatMessage, ChatRequest
from app.services import agent_service, ai_service

router = APIRouter(prefix="/ai", tags=["ai相关的api"])


# @router.post("/chat")
# def chat(
#     data: ChatRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     content = ai_service.chat(db, data)
#     return Response.success(data=ChatMessage(role="assistant", content=content))


@router.post("/chat")
def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    content = agent_service.run_agent(current_user, data)
    return Response.success(data=ChatMessage(role="assistant", content=content))


def _sse_line(payload: dict) -> str:
    """拼接一条SSE帧：必须使用data：开头，且以空行(\n\n)结束"""
    return f"data:{json.dumps(payload,ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
def chat_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    async def event_gen():
        async for event in agent_service.stream_agent(current_user, data):
            yield _sse_line(event)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "x-Accel_Buffer": "no",
        },
    )
