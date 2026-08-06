"""Docker 部署端到端验证脚本。

验证项：
1. /health 健康检查
2. /api/v1/documents/upload 上传文档入库
3. /api/v1/chat 问答（fake 模式）
4. /api/v1/chat/stream SSE 流式问答

用法：
    python -m scripts.verify_deploy --base http://localhost:8010 --api-key sk-rag-demo-key-change-me
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent


def wait_health(base: str, timeout: int = 60) -> bool:
    """轮询健康检查。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{base}/health", timeout=5)
            if r.status_code == 200:
                print(f"[OK] /health -> {r.json()}")
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def upload(base: str, api_key: str, path: Path) -> dict:
    """上传文档。"""
    with path.open("rb") as f:
        files = {"file": (path.name, f, "text/markdown")}
        r = httpx.post(
            f"{base}/api/v1/documents/upload",
            headers={"X-API-Key": api_key},
            files=files,
            timeout=30,
        )
    r.raise_for_status()
    return r.json()


def chat(base: str, api_key: str, query: str) -> dict:
    """同步问答。"""
    r = httpx.post(
        f"{base}/api/v1/chat",
        headers={"X-API-Key": api_key},
        json={"question": query},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def chat_stream(base: str, api_key: str, query: str) -> str:
    """SSE 流式问答，返回拼接后的文本（跳过 sources 事件）。"""
    collected = []
    skip_next_data = False
    with httpx.stream(
        "POST",
        f"{base}/api/v1/chat/stream",
        headers={"X-API-Key": api_key},
        json={"question": query},
        timeout=60,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line.startswith("event: sources"):
                skip_next_data = True
                continue
            if line.startswith("data: "):
                payload = line[6:]
                if payload == "[DONE]":
                    break
                if skip_next_data:
                    # 这是 sources 事件的 data，跳过
                    skip_next_data = False
                    continue
                collected.append(payload)
    return "".join(collected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8010")
    parser.add_argument("--api-key", default="sk-rag-demo-key-change-me")
    args = parser.parse_args()

    print("=" * 60)
    print("Docker 部署端到端验证")
    print("=" * 60)

    # 1. 健康检查
    print("\n[1/4] 健康检查 ...")
    if not wait_health(args.base):
        print("[FAIL] /health 超时")
        return 1

    # 2. 上传文档
    print("\n[2/4] 上传文档入库 ...")
    doc = ROOT / "data" / "docs" / "财务制度.md"
    try:
        resp = upload(args.base, args.api_key, doc)
        print(f"[OK] upload -> {resp}")
    except Exception as e:
        print(f"[FAIL] upload: {e}")
        return 1

    # 3. 同步问答
    print("\n[3/4] 同步问答 ...")
    try:
        resp = chat(args.base, args.api_key, "如何报销费用？")
        print(f"[OK] /chat answer={resp.get('answer','')[:80]}")
        print(f"     sources={resp.get('sources')}")
    except Exception as e:
        print(f"[FAIL] /chat: {e}")
        return 1

    # 4. SSE 流式问答
    print("\n[4/4] SSE 流式问答 ...")
    try:
        text = chat_stream(args.base, args.api_key, "报销需要附什么材料？")
        print(f"[OK] /chat/stream 拼接回答={text[:80]}")
    except Exception as e:
        print(f"[FAIL] /chat/stream: {e}")
        return 1

    print("\n" + "=" * 60)
    print("✅ Docker 部署端到端验证全部通过")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
