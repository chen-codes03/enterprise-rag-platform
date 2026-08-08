"""API 请求/响应 Schema（参数校验）。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """问答请求。"""

    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    kb: str = Field(default="default", description="知识库标识，用于缓存隔离")


class SourceOut(BaseModel):
    """溯源来源。"""

    index: int
    source: str
    section: str = ""
    content: str


class ChatResponse(BaseModel):
    """问答响应。"""

    answer: str
    sources: list[SourceOut]


class DocumentUploadResponse(BaseModel):
    """文档上传响应。"""

    filename: str
    chunks: int


class DocumentDeleteResponse(BaseModel):
    """文档删除响应。"""

    filename: str
    deleted_chunks: int
