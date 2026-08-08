# 项目结构说明

## 目录树

```
enterprise-rag-platform/
│
├── 📁 backend/                    # 后端（Python / FastAPI）
│   └── app/
│       ├── 📄 main.py             # 应用入口 + CORS 中间件
│       ├── 📄 config.py           # 配置管理（pydantic-settings）
│       │
│       ├── 📁 api/                # API 层
│       │   ├── 📄 deps.py         # 依赖注入（鉴权、RAG 组件）
│       │   ├── 📄 schemas.py      # 请求/响应数据模型
│       │   └── 📁 routes/         # 路由
│       │       ├── 📄 health.py   # 健康检查
│       │       ├── 📄 chat.py     # 问答接口（同步/SSE）
│       │       └── 📄 documents.py # 文档管理
│       │
│       ├── 📁 rag/                # RAG 链路
│       │   ├── 📄 chain.py       # RAG 主链路
│       │   ├── 📄 retriever.py   # 语义检索
│       │   ├── 📄 embeddings.py   # Embedding（豆包/DeepSeek/Fake）
│       │   ├── 📄 vectorstore.py  # Chroma 向量库
│       │   ├── 📄 splitters.py   # 文本分块
│       │   ├── 📄 loaders.py     # 文档加载（PDF/Word/MD）
│       │   ├── 📄 ingest.py      # 文档入库
│       │   ├── 📄 context.py    # 上下文拼接
│       │   └── 📄 prompts.py    # Prompt 模板
│       │
│       ├── 📁 models/             # 模型调用层
│       │   ├── 📄 base.py        # 抽象基类
│       │   ├── 📄 factory.py     # 模型工厂
│       │   ├── 📄 deepseek.py    # DeepSeek 实现
│       │   ├── 📄 qwen.py       # 通义千问实现
│       │   └── 📄 fake.py       # 演示模式实现
│       │
│       ├── 📁 cache/              # 缓存层
│       │   ├── 📄 redis_client.py # Redis 客户端
│       │   ├── 📄 qa_cache.py    # QA 结果缓存
│       │   └── 📄 embedding_cache.py # Embedding 向量缓存
│       │
│       ├── 📁 evaluation/         # 评估体系
│       │   ├── 📄 runner.py      # 评估运行器
│       │   ├── 📄 metrics.py    # 准确率/召回率/延迟
│       │   └── 📄 dataset.json  # 评估数据集
│       │
│       └── 📁 core/               # 核心工具
│           └── 📄 logging.py    # 日志配置
│
├── 📁 frontend/                    # 前端（Vue 3 / Vite）
│   ├── 📁 src/
│   │   ├── 📄 main.js             # 入口（Pinia 挂载）
│   │   ├── 📄 App.vue            # 主组件（聊天 + 文档管理）
│   │   ├── 📄 style.css          # 全局样式
│   │   ├── 📁 api/                # API 封装
│   │   │   └── 📄 index.js       # Axios 实例 + 接口方法
│   │   └── 📁 stores/            # 状态管理
│   │       └── 📄 chat.js        # Pinia Chat Store
│   │
│   ├── 📄 index.html              # HTML 模板
│   ├── 📄 package.json            # 依赖配置
│   ├── 📄 vite.config.js          # Vite 配置（API 代理）
│   └── 📄 Dockerfile             # Nginx 容器化
│
├── 📁 tests/                       # 测试（144 项）
│   ├── 📁 test_api/              # API 测试
│   ├── 📁 test_rag/              # RAG 链路测试
│   ├── 📁 test_models/           # 模型层测试
│   ├── 📁 test_cache/            # 缓存测试
│   ├── 📁 test_evaluation/       # 评估测试
│   ├── 📄 conftest.py            # 全局 fixture
│   └── 📄 test_config.py         # 配置测试
│
├── 📁 scripts/                     # 脚本
│   ├── 📄 run_evaluation.py      # 运行评估
│   └── 📄 verify_deploy.py       # 部署验证
│
├── 📁 data/                        # 数据目录
│   ├── 📁 docs/                  # 示例文档
│   └── 📁 fixtures/              # 测试数据
│
├── 📄 docker-compose.yml           # 编排三服务
├── 📄 .env.example                 # 环境变量示例
├── 📄 .dockerignore                # Docker 忽略
├── 📄 .gitignore                   # Git 忽略
│
├── 📄 README.md                    # 项目说明
├── 📄 PROJECT_STRUCTURE.md         # 结构文档
├── 📄 GOAL.md                       # 项目目标
├── 📄 PLAN.md                       # 实施计划
└── 📄 DELIVERY.md                   # 交付报告
```

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          客户端（浏览器）                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/JSON
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  前端层 (Vue 3 + Nginx :8080)                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  App.vue    │  │ Pinia Store │  │  Axios API 封装         │  │
│  │  (UI 组件)  │  │  (状态管理) │  │  (请求拦截 + 鉴权)      │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────┬───────────────┘  │
│         │                │                   │                   │
│         └────────────────┼───────────────────┘                   │
│                          │                                       │
│                    Nginx 反向代理                                 │
│                    /api/* → :8000                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  后端层 (FastAPI :8000)                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CORS Middleware（跨域支持）                              │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                     │
│  ┌──────────────┐ ┌────────┴────────┐ ┌───────────────────────┐  │
│  │  Health API  │ │   Chat API      │ │  Document API         │  │
│  │  (/health)   │ │  (/api/v1/chat) │ │  (/api/v1/documents) │  │
│  └──────┬───────┘ └────────┬────────┘ └──────────┬──────────────┘  │
│         │                 │                      │               │
│         └─────────────────┼──────────────────────┘               │
│                           ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    依赖注入层 (deps.py)                    │    │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────────┐ │    │
│  │  │ get_store  │ │get_provider│ │   get_qa_cache      │ │    │
│  │  └─────┬──────┘ └─────┬──────┘ └──────────┬───────────┘ │    │
│  └────────┼──────────────┼───────────────────┼─────────────┘    │
│           │              │                   │                    │
│  ┌────────┼──────────────┼───────────────────┼──────────────┐    │
│  │        ▼              ▼                   ▼              │    │
│  │  ┌─────────────────────────────────────────────────┐     │    │
│  │  │              RAG Chain (rag/)                    │     │    │
│  │  │  ┌─────────────┐  ┌───────────┐  ┌─────────┐  │     │    │
│  │  │  │  Retriever  │  │ Embedding │  │Prompt   │  │     │    │
│  │  │  │ (Chroma)   │  │ (豆包)    │  │ Template│  │     │    │
│  │  │  └──────┬──────┘  └─────┬─────┘  └────┬────┘  │     │    │
│  │  │         │               │              │        │     │    │
│  │  │         └───────────────┼──────────────┘        │     │    │
│  │  │                         ▼                        │     │    │
│  │  │              ┌─────────────────┐                 │     │    │
│  │  │              │  LLM (DeepSeek) │                 │     │    │
│  │  │              └─────────────────┘                 │     │    │
│  │  └─────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  数据层                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Chroma 向量库  │  │  Redis 缓存     │  │  文件存储       │  │
│  │  (语义检索)     │  │  (问答/向量)   │  │  (上传文档)   │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 技术栈

| 层 | 技术 | 版本 |
|---|---|---|
| 前端框架 | Vue 3 | ^3.4.0 |
| 状态管理 | Pinia | ^2.1.0 |
| HTTP 客户端 | Axios | ^1.6.0 |
| 构建工具 | Vite | ^5.0.0 |
| Web 服务器 | Nginx | alpine |
| 后端框架 | FastAPI | ^0.110.0 |
| 模型编排 | LangChain | ^0.3.0 |
| 向量数据库 | Chroma | ^0.5.0 |
| 缓存 | Redis | 7-alpine |
| 大模型 | DeepSeek / 豆包 | - |
| 运行时 | Python | 3.11 |
| 容器化 | Docker | 27.x |
| 数据格式化 | pydantic | ^2.0.0 |

## API 接口

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/health` | 健康检查 | 否 |
| POST | `/api/v1/documents/upload` | 上传文档 | 是 |
| POST | `/api/v1/chat` | 同步问答 | 是 |
| POST | `/api/v1/chat/stream` | SSE 流式问答 | 是 |

## 测试覆盖

```
tests/
├── test_api/              # API 测试（9 个文件）
│   ├── conftest.py       # API fixture
│   ├── test_auth.py      # 鉴权测试
│   ├── test_chat.py      # 同步问答测试
│   ├── test_chat_stream.py # SSE 流式测试
│   ├── test_documents.py # 文档管理测试
│   ├── test_health.py    # 健康检查测试
│   ├── test_deps_cache.py # 缓存依赖测试
│   └── test_validation.py # 参数校验测试
├── test_rag/              # RAG 测试（11 个文件）
├── test_models/           # 模型测试（7 个文件）
├── test_cache/            # 缓存测试（6 个文件）
└── test_evaluation/       # 评估测试（3 个文件）
```

**总计：144 个测试用例**

## 快速启动

### Docker 部署（推荐）

```bash
docker compose up -d
```

访问：
- 前端：http://localhost:8080
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```
