"""问答路由：同步问答与 SSE 流式问答。"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_rag_chain, verify_api_key
from app.api.schemas import ChatRequest, ChatResponse, SourceOut
from app.rag.chain import RAGChain
from app.rag.context import build_sources

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
def chat(req: ChatRequest, chain: RAGChain = Depends(get_rag_chain)) -> ChatResponse:
    """同步问答，返回答案与溯源来源。"""
    chain.kb = req.kb
    result = chain.ask(req.question)
    return ChatResponse(
        answer=result.answer,
        sources=[SourceOut(**s) for s in result.sources],
    )


@router.post("/chat/stream", dependencies=[Depends(verify_api_key)])
async def chat_stream(
    req: ChatRequest, chain: RAGChain = Depends(get_rag_chain)
) -> StreamingResponse:
    """SSE 流式问答：先推送来源事件，再逐 token 推送回答，最后 [DONE]。"""
    chain.kb = req.kb

    async def event_generator():
        docs = chain.retrieve(req.question)
        sources = build_sources(docs)
        yield f"event: sources\ndata: {json.dumps(sources, ensure_ascii=False)}\n\n"
        async for chunk in chain.astream(req.question, docs=docs):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
