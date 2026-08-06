"""文档上传路由：解析并入库。"""
from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_store, verify_api_key
from app.api.schemas import DocumentUploadResponse
from app.rag.ingest import ingest_file

router = APIRouter(prefix="/api/v1", tags=["documents"])

_SUPPORTED_EXTS = {".md", ".markdown", ".pdf", ".docx"}


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    dependencies=[Depends(verify_api_key)],
)
async def upload_document(
    file: UploadFile = File(...), store=Depends(get_store)
) -> DocumentUploadResponse:
    """上传文档（PDF/Word/Markdown），解析分块后入库，返回入库块数。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名缺失")
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in _SUPPORTED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {suffix}，可选: {sorted(_SUPPORTED_EXTS)}",
        )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = await file.read()
        tmp.write(content)
        tmp.close()
        chunks = ingest_file(tmp.name, store=store)
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    return DocumentUploadResponse(filename=file.filename, chunks=chunks)
