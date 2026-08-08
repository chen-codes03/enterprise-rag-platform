"""文档上传路由：解析并入库，同时持久化原始文件以支持下载/预览。"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.api.deps import get_qa_cache, get_store, verify_api_key
from app.api.schemas import DocumentDeleteResponse, DocumentUploadResponse
from app.config import get_settings
from app.rag.ingest import (
    delete_suggested_questions,
    generate_suggested_questions,
    ingest_file,
    load_suggested_questions,
    save_suggested_questions,
)

router = APIRouter(prefix="/api/v1", tags=["documents"])

_SUPPORTED_EXTS = {".md", ".markdown", ".pdf", ".docx"}
# 可在线预览的扩展名（PDF 直接 iframe，Markdown 前端 marked 渲染）
_PREVIEWABLE_EXTS = {".md", ".markdown", ".pdf"}


def _uploads_root() -> Path:
    """返回上传文件根目录，并保证其存在。"""
    root = Path(get_settings().uploads_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_resolve(filename: str) -> Path:
    """根据文件名定位上传目录中的真实文件，防止路径穿越。

    要求最终路径必须位于 uploads_dir 内部。
    """
    if not filename:
        raise HTTPException(status_code=400, detail="文件名缺失")
    root = _uploads_root()
    target = (root / filename).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法的文件名")
    return target


def _unique_target(filename: str) -> Path:
    """为上传文件分配一个不冲突的目标路径（重名时追加数字后缀）。"""
    root = _uploads_root()
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    candidate = root / filename
    idx = 1
    while candidate.exists():
        candidate = root / f"{stem} ({idx}){suffix}"
        idx += 1
    return candidate


class DocumentListResponse(BaseModel):
    documents: list[dict]
    total: int


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    dependencies=[Depends(verify_api_key)],
)
async def upload_document(
    file: UploadFile = File(...),
    store=Depends(get_store),
    qa_cache=Depends(get_qa_cache),
) -> DocumentUploadResponse:
    """上传文档（PDF/Word/Markdown），解析分块后入库，返回入库块数。

    入库后主动失效问答缓存，避免返回基于旧知识库的过时答案。
    同时把原始文件持久化到 data/uploads/，以支持下载与在线预览。
    入库完成后，自动基于文档内容生成推荐问题并写入元数据。
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名缺失")
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in _SUPPORTED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {suffix}，可选: {sorted(_SUPPORTED_EXTS)}",
        )

    content = await file.read()

    # 1) 持久化原始文件（重名追加数字后缀）
    target = _unique_target(file.filename)
    target.write_bytes(content)
    saved_name = target.name  # 真正落盘后的文件名（可能与原始名不同）

    # 2) 写临时文件交给 ingest 管道解析入库
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(content)
        tmp.close()
        # source 使用落盘后的文件名，确保与 list/download 路径一致
        chunks = ingest_file(tmp.name, store=store, source_name=saved_name)
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    # 3) 基于文档内容生成推荐问题（不阻断上传主流程）
    try:
        results = store.get(
            where={"source": saved_name},
            include=["documents"],
        )
        texts = results.get("documents", [])
        if texts and texts[0]:
            from app.api.deps import _get_provider_cached

            provider = _get_provider_cached()
            questions = generate_suggested_questions(texts[0], provider)
            if questions:
                save_suggested_questions(
                    get_settings().uploads_dir, saved_name, questions
                )
    except Exception:
        pass  # 推荐问题生成失败不影响上传

    # 知识库已变更，失效问答缓存（上传为低频管理操作，全量失效可接受）
    qa_cache.invalidate_all()
    return DocumentUploadResponse(filename=saved_name, chunks=chunks)


@router.get(
    "/documents/list",
    response_model=DocumentListResponse,
    dependencies=[Depends(verify_api_key)],
)
def list_documents(store=Depends(get_store)) -> DocumentListResponse:
    """列出知识库中已上传的文档，附带原始文件大小、可预览标志和推荐问题。"""
    try:
        results = store.get(include=["metadatas", "documents"])
        if not results or not results["metadatas"]:
            return DocumentListResponse(documents=[], total=0)

        root = _uploads_root()
        uploads_dir = get_settings().uploads_dir
        # 按 source 分组统计
        doc_map: dict[str, dict] = {}
        for metadata in results["metadatas"]:
            source = metadata.get("source", "未知文档")
            if source not in doc_map:
                doc_map[source] = {
                    "filename": source,
                    "chunk_count": 0,
                    "suggested_questions": load_suggested_questions(uploads_dir, source),
                }
            doc_map[source]["chunk_count"] += 1

        # 补充原始文件元信息
        documents = []
        for source, info in doc_map.items():
            file_path = root / source
            size = file_path.stat().st_size if file_path.exists() else None
            ext = Path(source).suffix.lower()
            documents.append({
                **info,
                "size": size,                                   # 字节数，None 表示原文件已丢失
                "previewable": ext in _PREVIEWABLE_EXTS and file_path.exists(),
            })
        return DocumentListResponse(documents=documents, total=len(documents))
    except Exception:
        return DocumentListResponse(documents=[], total=0)


@router.get(
    "/documents/{filename}/download",
    dependencies=[Depends(verify_api_key)],
)
def download_document(filename: str):
    """下载指定文档的原始文件。"""
    target = _safe_resolve(filename)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"文件 '{filename}' 不存在或原始文件未保留")
    return FileResponse(
        path=str(target),
        filename=target.name,
        media_type="application/octet-stream",
    )


@router.get(
    "/documents/{filename}/preview",
    dependencies=[Depends(verify_api_key)],
)
def preview_document(filename: str):
    """在线预览：直接返回原始文件流。

    前端按扩展名渲染：
      - PDF  → <iframe :src="url">
      - MD   → axios 拉取文本，marked 渲染
      - 其他 → 不支持预览，回退到下载
    """
    target = _safe_resolve(filename)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"文件 '{filename}' 不存在或原始文件未保留")
    ext = target.suffix.lower()
    if ext == ".pdf":
        media_type = "application/pdf"
    elif ext in {".md", ".markdown"}:
        media_type = "text/markdown; charset=utf-8"
    else:
        raise HTTPException(status_code=400, detail="该文件类型不支持在线预览，请下载查看")
    return FileResponse(path=str(target), media_type=media_type)


@router.delete(
    "/documents/{filename}",
    response_model=DocumentDeleteResponse,
    dependencies=[Depends(verify_api_key)],
)
def delete_document(
    filename: str,
    store=Depends(get_store),
    qa_cache=Depends(get_qa_cache),
) -> DocumentDeleteResponse:
    """删除指定文档的所有向量块及原始文件，返回删除的块数。"""
    try:
        # 先查找该文档有多少块
        results = store.get(
            where={"source": filename},
            include=["metadatas"],
        )
        chunk_count = len(results.get("ids", []))

        if chunk_count == 0:
            raise HTTPException(status_code=404, detail=f"文档 '{filename}' 不存在")

        # 删除所有匹配 source 的向量
        store.delete(where={"source": filename})

        # 同步删除原始文件（丢失不影响向量库已删的数据）
        try:
            target = _safe_resolve(filename)
            if target.exists():
                target.unlink()
        except Exception:
            # 删除文件失败不阻断主流程
            pass

        # 同步删除推荐问题元数据文件
        delete_suggested_questions(get_settings().uploads_dir, filename)

        # 知识库已变更，失效问答缓存
        qa_cache.invalidate_all()

        return DocumentDeleteResponse(
            filename=filename,
            deleted_chunks=chunk_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")
