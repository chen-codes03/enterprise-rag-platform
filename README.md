# 企业知识库 RAG 智能问答平台

基于 **RAG 检索增强生成**的企业知识管理与智能问答平台，让 AI 能"读懂"企业私有文档（PDF/Word/Markdown）并准确回答业务问题，支撑智能客服、知识助手等场景。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | **Vue 3** + Vite + Pinia + Axios（前后端分离） |
| 后端 | **Python** · **FastAPI** · LangChain |
| AI | **Chroma** 向量库 · Redis 缓存 · DeepSeek/豆包 |
| 部署 | **Docker Compose** · Nginx |

## 架构

```
┌──────────────────┐  HTTP/JSON   ┌──────────────────┐
│                  │  /api/v1/*   │                  │
│  Vue 3 前端      │ ───────────> │  FastAPI 后端     │
│  (Nginx 托管)    │  /health     │  (Python)        │
│                  │  <────────── │                  │
└──────────────────┘  响应数据    └────────┬─────────┘
                                           │
                                     ┌─────▼─────┐
                                     │  Chroma + │
                                     │  Redis    │
                                     └───────────┘
```

- **前端**：独立项目，Nginx 托管静态文件，通过反向代理转发 API 请求到后端
- **后端**：纯 API 服务，提供 RAG 链路、文档管理、问答接口
- **通信**：前端通过 Axios 调用后端 RESTful API，支持 CORS 跨域

## 核心能力
- **统一模型调用层**：封装 DeepSeek / 通义千问（均兼容 OpenAI 接口），支持同步 / 异步 / SSE 流式输出，改配置即可切换模型
- **RAG 全链路**：文档解析 → 文本分块（Chunk 策略可调）→ Embedding → Chroma 存储 → 语义检索 → 上下文拼接 → LLM 生成 → 溯源
- **Redis 缓存**：高频问答结果 + Embedding 向量缓存，TTL 失效 + 知识库更新主动失效
- **FastAPI 接口**：RESTful + SSE 流式对话 + API Key 鉴权 + 参数校验
- **评估体系**：问答准确率 / 检索召回率 / 响应延迟，支持 RAG vs 无 RAG 基线对比
- **Docker 一键部署**：多阶段构建 + docker compose 编排 app + redis

## 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
docker compose up -d
```

服务启动后：
- **前端界面**：http://localhost:8080
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

默认使用 `fake` 离线模式，无需任何大模型 API key 即可完整体验。

### 方式二：本地开发（前后端分别启动）

```bash
# 1. 后端
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # 填入 API Key
uvicorn app.main:app --reload   # http://localhost:8000

# 2. 前端（新终端）
cd frontend
npm install                     # 安装依赖
npm run dev                     # http://localhost:5173
```

前端 Vite 已配置代理，`/api/*` 和 `/health` 请求会自动转发到后端 `localhost:8000`。

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
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-API-Key: sk-rag-demo-key-change-me" \
  -F "file=@data/docs/财务制度.md"

# 同步问答
curl -X POST http://localhost:8000/api/v1/chat \
  -H "X-API-Key: sk-rag-demo-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question": "如何报销费用？"}'

# SSE 流式问答
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
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
enterprise-rag-platform/
├── backend/              # 后端（Python / FastAPI）
│   ├── app/
│   │   ├── config.py      # 配置管理
│   │   ├── main.py        # 应用入口 + CORS
│   │   ├── api/           # API 路由、鉴权
│   │   ├── rag/           # RAG 链路
│   │   ├── models/        # 模型调用层
│   │   ├── cache/         # Redis 缓存
│   │   └── evaluation/    # 评估体系
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/             # 前端（Vue 3 / Vite）
│   ├── src/
│   │   ├── App.vue        # 主组件
│   │   ├── api/index.js   # Axios 封装
│   │   └── stores/chat.js # Pinia 状态
│   ├── nginx.conf         # Nginx 配置
│   ├── Dockerfile
│   ├── vite.config.js
│   └── package.json
├── tests/                 # 测试（144 项）
├── scripts/               # 脚本
├── data/                  # 数据
├── docker-compose.yml    # 编排三服务
├── .env.example
└── README.md
```

## 测试
```bash
cd backend
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
