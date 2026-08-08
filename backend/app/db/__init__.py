"""对话历史持久化存储（SQLite）。

数据文件：data/chat_history.db（通过 Docker 卷映射持久化到宿主机，
与 Chroma 向量库同级目录，同样安全可靠）。

表结构：
  conversations - 每行一轮对话（用户问题 + AI回答 + 来源 + 时间戳）
"""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from app.config import get_settings

_lock = threading.Lock()


def _get_db_path() -> Path:
    """返回 SQLite 数据库文件路径（与 Chroma 同级，持久化到宿主机）。"""
    persist_dir = Path(get_settings().chroma_persist_dir)
    db_path = persist_dir.parent / "chat_history.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接（启用 WAL 模式，提升并发读性能）。"""
    conn = sqlite3.connect(str(_get_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """初始化数据库表（幂等，首次启动时调用）。"""
    with _lock:
        conn = _get_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    question    TEXT    NOT NULL,
                    answer      TEXT    NOT NULL,
                    sources     TEXT    NOT NULL DEFAULT '[]',
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_created "
                "ON conversations(created_at DESC)"
            )
            conn.commit()
        finally:
            conn.close()


def save_conversation(
    question: str,
    answer: str,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """保存一轮对话，返回新记录（含 id 和时间戳）。"""
    with _lock:
        conn = _get_conn()
        try:
            cursor = conn.execute(
                "INSERT INTO conversations (question, answer, sources) "
                "VALUES (?, ?, ?)",
                (question, answer, json.dumps(sources, ensure_ascii=False)),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
            return _row_to_dict(row)
        finally:
            conn.close()


def list_conversations() -> list[dict[str, Any]]:
    """获取全部对话（按时间正序，最早的在前）。"""
    with _lock:
        conn = _get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY id ASC"
            ).fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            conn.close()


def delete_conversation(conversation_id: int) -> bool:
    """删除单条对话，返回是否删除成功。"""
    with _lock:
        conn = _get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


def delete_conversations(conversation_ids: list[int]) -> int:
    """批量删除对话，返回删除条数。"""
    if not conversation_ids:
        return 0
    with _lock:
        conn = _get_conn()
        try:
            placeholders = ",".join("?" * len(conversation_ids))
            cursor = conn.execute(
                f"DELETE FROM conversations WHERE id IN ({placeholders})",
                conversation_ids,
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()


def clear_all_conversations() -> int:
    """清空全部对话，返回删除条数。"""
    with _lock:
        conn = _get_conn()
        try:
            cursor = conn.execute("DELETE FROM conversations")
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """将数据库行转为字典（sources 自动反序列化）。"""
    return {
        "id": row["id"],
        "question": row["question"],
        "answer": row["answer"],
        "sources": json.loads(row["sources"]) if row["sources"] else [],
        "createdAt": row["created_at"],
    }
