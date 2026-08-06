# 企业知识库 RAG 智能问答平台

基于 **RAG 检索增强生成**的企业知识管理与智能问答平台，让 AI 能"读懂"企业私有文档（PDF/Word/Markdown）并准确回答业务问题，支撑智能客服、知识助手等场景。

## 技术栈
Python · FastAPI · LangChain · Chroma 向量库 · Redis · Docker

## 核心能力
- **统一模型调用层**：封装 DeepSeek / 通义千问（均兼容 OpenAI 接口），支持同步 / 异步 / SSE 流式输出，改配置即可切换模型
- **RAG 全链路**：文档解析 → 文本分块（Chunk 策略可调）→ Embedding → Chroma 存储 → 语义检索 → 上下文拼接 → LLM 生成 → 溯源
- **Redis 缓存**：高频问答结果 + Embedding 向量缓存，TTL 失效 + 知识库更新主动失效
- **FastAPI 接口**：RESTful + SSE 流式对话 + API Key 鉴权 + 参数校验
- **评估体系**：问答准确率 / 检索召回率 / 响应延迟，支持 RAG vs 无 RAG 基线对比
- **Docker 一键部署**：多阶段构建 + docker compose 编排 app + redis

## 快速开始

### 方式一：Docker 一键启动（推荐，开箱即用）
默认使用 `fake` 离线模式，无需任何大模型 API key 即可完整体验上传文档 → 问答全链路。

```bash
docker compose up -d              # 启动 app(8010) + redis(6380)
# 健康检查
curl http://localhost:8010/health
```

接入真实大模型：编辑 `docker-compose.yml` 中 app 服务的环境变量
```
MODEL_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxx
EMBEDDING_PROVIDER=openai
EMBEDDING_API_KEY=sk-xxx
```

### 方式二：本地开发
```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env            # 并填入你的 API Key（或使用 fake 模式离线体验）

# 3. 运行测试
pytest

# 4. 启动服务
uvicorn app.main:app --reload
```

## API 说明

所有接口需在 Header 携带 `X-API-Key`（默认 `sk-rag-demo-key-change-me`，生产请修改）。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（无需鉴权） |
| POST | `/api/v1/documents/upload` | 上传文档（PDF/Word/Markdown）解析入库 |
| POST | `/api/v1/chat` | 同步问答，返回答案 + 溯源来源 |
| POST | `/api/v1/chat/stream` | SSE 流式问答 |

### 请求示例
```bash
# 上传文档
curl -X POST http://localhost:8010/api/v1/documents/upload \
  -H "X-API-Key: sk-rag-demo-key-change-me" \
  -F "file=@data/docs/财务制度.md"

# 同步问答
curl -X POST http://localhost:8010/api/v1/chat \
  -H "X-API-Key: sk-rag-demo-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question": "如何报销费用？"}'

# SSE 流式问答
curl -N -X POST http://localhost:8010/api/v1/chat/stream \
  -H "X-API-Key: sk-rag-demo-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question": "报销需要附什么材料？"}'
```

## 评估体系

在评估数据集上对比 RAG 链路 vs 无 RAG 基线，输出准确率 / 召回率 / 延迟。

```bash
python -m scripts.run_evaluation
```

输出示例：
```
RAG:        answer_accuracy=1.0  retrieval_recall=0.58  p95=5.7ms
no_rag:     answer_accuracy=0.0  retrieval_recall=0.0   p95=0.2ms
improvement: +1.0   （RAG 显著优于无 RAG 基线）
```

## 配置项

通过环境变量 / `.env` 配置，完整列表见 `.env.example`。关键项：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MODEL_PROVIDER` | `deepseek` | 模型提供方：`deepseek` / `qwen` / `fake`（离线演示）|
| `EMBEDDING_PROVIDER` | `openai` | Embedding：`openai` / `fake`（确定性哈希向量）|
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 500 / 50 | 文本分块大小与重叠度，影响召回效果 |
| `RETRIEVE_TOP_K` | 4 | 检索返回的文档片段数 |
| `QA_CACHE_TTL` | 3600 | 问答缓存 TTL（秒）|
| `API_KEY` | `sk-rag-demo-key-change-me` | 接口鉴权密钥（生产务必修改）|

## 项目结构
```
app/
├── config.py          配置管理（pydantic-settings）
├── core/              日志、异常
├── models/            统一模型调用层（DeepSeek/Qwen/Fake，同步/异步/SSE）
├── rag/               文档解析、分块、Embedding、向量库、检索、RAG链路
├── cache/             Redis 缓存（问答结果/向量，TTL+主动失效）
├── api/               FastAPI 路由、鉴权、Schemas
└── evaluation/        评估指标、数据集、运行器
scripts/               评估演示、部署验证脚本
tests/                 单元/集成测试（144 项，全程 TDD）
```

## 测试
```bash
pytest                  # 全量测试
pytest --cov=app        # 带覆盖率
```
测试全程使用 FakeLLM / fakeredis / 临时 Chroma 目录，不依赖真实 API。

## 已知安全注意事项

经 TRAE-security-review 审查，以下为已知待改进项（演示项目优先级低，生产部署前应处理）：

| 项 | 说明 | 建议 |
|----|------|------|
| 默认 API Key | `config.py` 与 `docker-compose.yml` 含默认密钥 `sk-rag-demo-key-change-me`，部署方未修改则等于无鉴权 | 生产强制覆盖 `API_KEY`，缺失则启动失败 |
| 密钥比较 | `verify_api_key` 用 `!=` 比较，非常量时间 | 改用 `secrets.compare_digest` |
| Redis 暴露 | `docker-compose.yml` 将 redis 端口映射至宿主机且无密码 | 生产移除端口映射或启用 `requirepass` |

## 开发过程

- **方法**：TDD（Red → Green → Refactor），7 个阶段（P0–P6）逐阶段提交验证
- **审查**：TRAE-code-review（发现 5 项，修复 A/B/C 三项 major）+ TRAE-security-review（发现 3 项，记录待改进）
- **评估**：`python -m scripts.run_evaluation` 跑 RAG vs 基线对比
- **部署验证**：`python -m scripts.verify_deploy` 端到端验证健康检查/上传/问答/SSE

详细目标见 [GOAL.md](GOAL.md)，实施计划见 [PLAN.md](PLAN.md)。
