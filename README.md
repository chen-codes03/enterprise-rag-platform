# 企业知识库 RAG 智能问答平台

基于 RAG 检索增强生成的企业知识管理与智能问答平台，让 AI 能"读懂"企业私有文档（PDF/Word/Markdown）并准确回答业务问题。

## 技术栈
Python · FastAPI · LangChain · Chroma 向量库 · Redis · Docker

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env            # 并填入你的 API Key

# 3. 运行测试
pytest

# 4. 启动服务
uvicorn app.main:app --reload
```

## Docker 一键启动
```bash
docker compose up -d
```

## 项目结构
```
app/
├── config.py          配置管理
├── core/              日志、异常
├── models/            统一模型调用层（DeepSeek/Qwen，同步/异步/SSE）
├── rag/               文档解析、分块、Embedding、向量库、检索、RAG链路
├── cache/             Redis 缓存（问答结果/向量）
├── api/               FastAPI 路由、鉴权、Schemas
└── evaluation/        评估指标
tests/                 单元/集成测试
```

详细目标见 [GOAL.md](GOAL.md)，实施计划见 [PLAN.md](PLAN.md)。
