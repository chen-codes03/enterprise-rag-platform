# 企业知识库 RAG 智能问答平台

基于 **RAG（检索增强生成）** 的企业知识管理与智能问答平台。上传企业私有文档（PDF / Word / Markdown），AI 即可"读懂"文档内容，针对业务问题给出**可溯源**的准确回答，支撑智能客服、员工知识助手等场景。

> **一句话亮点**：前端 Vue 3 + 后端 FastAPI + LangChain RAG 链路 + Chroma 向量库 + Redis 缓存，Docker Compose 一键启动，支持 SSE 流式输出、引用溯源、对话历史持久化。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | **Vue 3** · Vite · Pinia · Axios · Nginx |
| 后端 | **Python 3.11** · **FastAPI** · LangChain · pydantic-settings |
| AI | **Chroma** 向量库 · **Redis** 缓存 · DeepSeek（生成）· 火山引擎豆包（Embedding）|
| 部署 | **Docker Compose** 多容器编排 · 多阶段镜像构建 |

---

## 架构

```
┌──────────────────┐  /api/v1/*    ┌──────────────────┐
│  Vue 3 前端      │ ────────────> │  FastAPI 后端     │
│  (Nginx 托管)    │  反向代理     │  (Python)        │
│                  │ <──────────── │                  │
└──────────────────┘   响应数据    └────────┬─────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              │              │              │
                        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
                        │  Chroma   │  │  Redis    │  │  SQLite   │
                        │  向量库    │  │  缓存     │  │  对话历史  │
                        └───────────┘  └───────────┘  └───────────┘
```

- **前端**：Vue 3 SPA，Nginx 托管静态文件，`/api/*` 与 `/health` 通过 Nginx 反向代理转发到后端
- **后端**：FastAPI 纯 API 服务，承载 RAG 链路、文档管理、问答接口
- **存储**：Chroma 持久化向量数据（bind mount 到宿主 `./data`）、Redis 缓存 QA 与 Embedding、SQLite 存对话历史

---

## 核心能力

### RAG 链路
- **统一模型调用层**：封装 DeepSeek / 通义千问（均兼容 OpenAI 接口），支持同步 / 异步 / SSE 流式输出，改配置即可切换
- **完整检索增强**：文档解析 → 文本分块（Chunk 策略可调）→ Embedding 向量化 → Chroma 存储 → 语义检索 → 上下文拼接 → LLM 生成 → 溯源
- **检索策略**：支持 `similarity` / `mmr` 两种检索，可调 `top_k`、`chunk_size`、`chunk_overlap`
- **Redis 双层缓存**：高频问答结果 + Embedding 向量缓存，TTL 失效 + 文档删除主动失效

### 前端交互
- **SSE 流式问答**：逐 token 输出，实时呈现生成过程
- **引用溯源**：答案内嵌 `[1][2]` 角标，点击跳转到来源文档原文片段
- **对话历史**：左侧会话列表，支持多选 / 批量删除 / 清空，持久化到 SQLite
- **文档管理**：拖拽上传、文档列表预览(👁)/下载(⬇)/删除（含向量同步清理）
- **智能推荐问题**：上传文档时由 LLM 生成 3 个建议问题，展示在欢迎页"试试问我"
- **API Key 密码框**：小眼睛图标切换可见性，弹窗关闭自动重置为隐藏

### 工程化
- **API Key 鉴权**：支持 Header(`X-API-Key`) 与 Query(`?api_key=`) 两种方式，常量时间比较防时序攻击
- **CORS 安全配置**：明确指定允许来源，避免 `*` + `credentials` 的不安全组合
- **Docker 一键部署**：多阶段构建，`docker compose up -d` 启动前端 + 后端 + Redis
- **评估体系**：问答准确率 / 检索召回率 / 响应延迟，支持 RAG vs 无 RAG 基线对比
- **测试覆盖**：144 项单元测试，使用 FakeLLM / fakeredis / 临时 Chroma，不依赖真实 API

---

## 快速开始

### 前置要求
- Docker & Docker Compose
- 大模型 API Key（DeepSeek）+ Embedding API Key（火山引擎豆包）

### 方式一：Docker 一键启动（推荐）

1. 复制环境变量样例并填入密钥：
   ```bash
   cp .env.example .env
   # 编辑 .env，填入 DEEPSEEK_API_KEY 和 EMBEDDING_API_KEY
   ```

2. 启动所有服务：
   ```bash
   docker compose up -d
   ```

3. 访问：
   - **前端界面**：http://localhost:8080
   - **后端 API**：http://localhost:8000
   - **API 文档（Swagger）**：http://localhost:8000/docs
   - **健康检查**：http://localhost:8000/health

> 首次启动需构建镜像，约 1-2 分钟。首次加载文档列表有约 2 秒 Chroma 冷查询延迟，属正常现象。

### 方式二：本地开发（前后端分别启动）

```bash
# 1. 后端
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp ../.env.example ../.env      # 填入 API Key
uvicorn app.main:app --reload   # http://localhost:8000

# 2. 前端（新终端）
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

前端 Vite 已配置代理，`/api/*` 和 `/health` 请求会自动转发到后端 `localhost:8000`。

---

## API 说明

所有接口（除 `/health`）需在 Header 携带 `X-API-Key`，或在 Query 中带 `?api_key=xxx`。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（无需鉴权） |
| GET | `/api/v1/documents/list` | 文档列表（含 chunk 数、大小、建议问题） |
| POST | `/api/v1/documents/upload` | 上传文档（PDF/Word/Markdown）解析入库 |
| GET | `/api/v1/documents/{filename}/preview` | 在线预览文档 |
| GET | `/api/v1/documents/{filename}/download` | 下载原始文档 |
| DELETE | `/api/v1/documents/{filename}` | 删除文档（含向量、缓存、原文件同步清理） |
| POST | `/api/v1/chat` | 同步问答，返回答案 + 溯源来源 |
| POST | `/api/v1/chat/stream` | SSE 流式问答 |
| GET | `/api/v1/history` | 获取对话历史列表 |
| DELETE | `/api/v1/history` | 删除指定/全部对话历史 |

### 请求示例

```bash
# 上传文档
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-API-Key: sk-rag-demo-key-change-me" \
  -F "file=@docs/考勤管理制度.docx"

# SSE 流式问答
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "X-API-Key: sk-rag-demo-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question": "考勤制度有哪些？"}'
```

完整接口文档访问 http://localhost:8000/docs 。

---

## 配置项

通过环境变量 / `.env` 配置，完整列表见 `.env.example`。关键项：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | - | DeepSeek 大模型密钥（生成回答） |
| `EMBEDDING_API_KEY` | - | 火山引擎豆包 Embedding 密钥（文档向量化） |
| `API_KEY` | `sk-rag-demo-key-change-me` | 本平台接口鉴权密钥（**生产务必修改**） |
| `MODEL_PROVIDER` | `deepseek` | 模型提供方：`deepseek` / `qwen` / `fake` |
| `EMBEDDING_PROVIDER` | `openai` | Embedding：`openai` / `fake` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 500 / 50 | 文本分块大小与重叠度 |
| `RETRIEVE_TOP_K` | 4 | 检索返回的文档片段数 |
| `QA_CACHE_TTL` | 3600 | 问答缓存 TTL（秒） |
| `CORS_ORIGINS` | `http://localhost:8080` | CORS 允许的前端来源（逗号分隔） |

> ⚠️ `.env` 文件已在 `.gitignore` 中排除，不会进入版本库。

---

## 项目结构

```
enterprise-rag-platform/
├── backend/                # 后端（Python / FastAPI）
│   ├── app/
│   │   ├── config.py        # 配置管理（Settings + 属性）
│   │   ├── main.py          # 应用入口 + CORS 中间件
│   │   ├── api/             # 路由（chat/documents/history）、鉴权、schemas
│   │   ├── rag/             # RAG 链路（分块/Embedding/检索/Chain/Prompt）
│   │   ├── models/          # 统一模型调用层
│   │   ├── cache/           # Redis 缓存（QA / Embedding）
│   │   ├── db/              # SQLite 对话历史
│   │   └── evaluation/      # 评估体系
│   ├── Dockerfile           # 多阶段构建
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/               # 前端（Vue 3 / Vite）
│   ├── src/
│   │   ├── App.vue          # 主组件（聊天 / 文档 / 设置）
│   │   ├── api/index.js     # Axios + SSE 封装
│   │   └── stores/chat.js   # Pinia 状态
│   ├── nginx.conf           # Nginx 反向代理 + 缓存策略
│   ├── Dockerfile
│   └── package.json
├── tests/                  # 单元测试（144 项）
├── scripts/                # 评估 / 部署验证脚本
├── data/                   # 运行时数据（向量库 / 上传文件 / 历史）
├── docker-compose.yml      # 编排 frontend + backend + redis
├── .env.example            # 环境变量样例
└── README.md
```

---

## 测试

```bash
cd backend
pytest                  # 全量测试
pytest --cov=app        # 带覆盖率
```

测试全程使用 FakeLLM / fakeredis / 临时 Chroma 目录，不依赖真实 API。

---

## 评估

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

---

## 安全实践

本项目已通过 TRAE-security-review 审查并完成以下加固：

| 项 | 措施 |
|----|------|
| API Key 比较 | 使用 `secrets.compare_digest` 常量时间比较，防时序攻击 |
| CORS 配置 | 明确指定允许来源，避免 `allow_origins=["*"]` + `allow_credentials=True` 不安全组合 |
| Redis 端口 | 不对外暴露，仅容器内部网络访问 |
| 密钥管理 | `.env` 通过 `.gitignore` 排除，docker-compose 不硬编码密钥 |
| 密码输入框 | 小眼睛切换可见性，弹窗关闭自动重置为隐藏 |

> 演示用默认 API Key `sk-rag-demo-key-change-me` 仅供本地测试，生产部署务必通过 `.env` 覆盖为强随机值。

---

## 开发过程

- **方法**：TDD（Red → Green → Refactor），7 个阶段（P0–P6）逐阶段提交验证
- **代码审查**：TRAE-code-review（结构化审查 + 子代理交叉验证）
- **安全审查**：TRAE-security-review
- **评估**：`python -m scripts.run_evaluation` 跑 RAG vs 基线对比
- **部署验证**：`python -m scripts.verify_deploy` 端到端验证健康检查/上传/问答/SSE

详细目标见 [GOAL.md](GOAL.md)，实施计划见 [PLAN.md](PLAN.md)，交付报告见 [DELIVERY.md](DELIVERY.md)。
