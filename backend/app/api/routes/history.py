"""对话历史路由：获取 / 保存 / 删除（单条/批量/清空）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import verify_api_key
from app.db import (
    clear_all_conversations,
    delete_conversation,
    delete_conversations,
    list_conversations,
    save_conversation,
)

router = APIRouter(prefix="/api/v1", tags=["history"])


class ConversationSaveRequest(BaseModel):
    """保存对话请求。"""

    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., min_length=1)
    sources: list[dict] = Field(default_factory=list)


class ConversationOut(BaseModel):
    """对话记录输出。"""

    id: int
    question: str
    answer: str
    sources: list[dict]
    createdAt: str


class ConversationListResponse(BaseModel):
    """对话列表响应。"""

    conversations: list[ConversationOut]
    total: int


class BatchDeleteRequest(BaseModel):
    """批量删除请求。"""

    ids: list[int] = Field(..., min_length=1)


class DeleteCountResponse(BaseModel):
    """删除计数响应。"""

    deleted: int


@router.get(
    "/history",
    response_model=ConversationListResponse,
    dependencies=[Depends(verify_api_key)],
)
def get_history() -> ConversationListResponse:
    """获取全部对话历史（按时间正序）。"""
    rows = list_conversations()
    return ConversationListResponse(
        conversations=[ConversationOut(**r) for r in rows],
        total=len(rows),
    )


@router.post(
    "/history",
    response_model=ConversationOut,
    dependencies=[Depends(verify_api_key)],
)
def save_history(req: ConversationSaveRequest) -> ConversationOut:
    """保存一轮对话（问答完成后由前端调用）。"""
    row = save_conversation(req.question, req.answer, req.sources)
    return ConversationOut(**row)


@router.delete(
    "/history/all",
    response_model=DeleteCountResponse,
    dependencies=[Depends(verify_api_key)],
)
def clear_history() -> DeleteCountResponse:
    """清空全部对话（必须在 /history/{id} 之前注册，否则 all 会被当作 id）。"""
    count = clear_all_conversations()
    return DeleteCountResponse(deleted=count)


@router.delete(
    "/history",
    response_model=DeleteCountResponse,
    dependencies=[Depends(verify_api_key)],
)
def batch_delete_history(req: BatchDeleteRequest) -> DeleteCountResponse:
    """批量删除对话。"""
    count = delete_conversations(req.ids)
    return DeleteCountResponse(deleted=count)


@router.delete(
    "/history/{conversation_id}",
    response_model=DeleteCountResponse,
    dependencies=[Depends(verify_api_key)],
)
def delete_history(conversation_id: int) -> DeleteCountResponse:
    """删除单条对话。"""
    if not delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="对话记录不存在")
    return DeleteCountResponse(deleted=1)
