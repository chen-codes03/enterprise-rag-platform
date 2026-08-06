# 实施计划：企业知识库 RAG 智能问答平台

## 总体策略
- **开发方法**：TDD（Red → Green → Refactor），每个任务先写失败测试再实现。
- **提交节奏**：每个阶段（P0–P6）完成且全量测试通过后提交一次，提交信息预规划。
- **验收方式**：单元测试 + 集成测试 + 阶段退出条件手动验证。
- **外部依赖处理**：LLM 调用用 FakeLLM/Mock 测试；Redis 用 fakeredis；Chroma 用临时持久化目录。真实 API 仅在集成/部署阶段联调。
- **依赖顺序**：P0 → P1 → P2 → P3 → P4 → P5 → P6，严格按序推进。

## 阶段总览
| 阶段 | 名称 | 关键产出 | 对应目标 | 提交信息 |
|------|------|----------|----------|----------|
| P0 | 项目骨架与基础设施 | 目录结构/配置/测试框架/Git | G1-G5 基座 | `chore: 初始化项目骨架与测试框架` |
| P1 | 统一模型调用层 | DeepSeek/Qwen 抽象，同步/异步/SSE | G1, M1 | `feat(models): 统一模型调用层支持同步异步与SSE流式` |
| P2 | 文档处理与向量库 | 解析/分块/Embedding/Chroma 存储 | G2, M2 | `feat(rag): 文档解析分块与Chroma向量存储` |
| P3 | RAG 问答链路 | 检索/上下文拼接/生成/溯源 | G2,G3, M3 | `feat(rag): RAG问答链路与语义检索优化` |
| P4 | Redis 缓存与性能 | 问答/Embedding 缓存与失效策略 | G4, M4 | `feat(cache): Redis缓存问答与向量结果` |
| P5 | FastAPI API 与鉴权 | RESTful/SSE/API Key/校验 | G5, M5 | `feat(api): FastAPI接口SSE流式与APIKey鉴权` |
| P6 | 评估体系与 Docker 部署 | 评估脚本/Docker Compose | S1, M6 | `feat(eval,deploy): 评估体系与Docker一键部署` |

---

## P0: 项目骨架与基础设施
**目标**: 搭建可运行的项目骨架、配置管理、测试框架与 Git 仓库，为后续 TDD 提供基座。
**入口条件**: GOAL.md 已确认。

**目录结构**:
```
enterprise-rag-platform/
├── GOAL.md / PLAN.md / README.md
├── pyproject.toml / requirements.txt / .env.example / .gitignore
├── docker-compose.yml / Dockerfile
├── app/
│   ├── __init__.py / main.py / config.py
│   ├── core/        (logging.py, exceptions.py)
│   ├── models/      (base.py, deepseek.py, qwen.py, factory.py)
│   ├── rag/         (loaders.py, splitters.py, embeddings.py, vectorstore.py, retriever.py, prompts.py, chain.py)
│   ├── cache/       (redis_client.py, qa_cache.py, embedding_cache.py)
│   ├── api/         (deps.py, schemas.py, routes/{chat,documents,health}.py)
│   └── evaluation/  (metrics.py, dataset.json)
├── tests/           (conftest.py + 各模块测试目录)
└── data/            (sample docs, chroma persist)
```

**任务清单**（脚手架为主，配置模块走 TDD）:
- [ ] T0.1 创建目录结构与空 `__init__.py`
- [ ] T0.2 编写 `pyproject.toml` / `requirements.txt`（fastapi, uvicorn, langchain, langchain-openai, chromadb, redis, fakeredis, pypdf, python-docx, markdown, pydantic-settings, pytest, pytest-asyncio, httpx, coverage）
- [ ] T0.3 RED: 写 `tests/test_config.py` 断言 Settings 能从 env 读取（API key、模型名、chunk 参数等）
- [ ] T0.4 GREEN: 实现 `app/config.py`（pydantic-settings Settings），补 `.env.example`
- [ ] T0.5 RED: 写 `tests/test_logging.py` 断言 get_logger 返回带 name 的 logger
- [ ] T0.6 GREEN: 实现 `app/core/logging.py`
- [ ] T0.7 编写 `conftest.py`（通用 fixtures：tmp_chroma_dir、fake_llm 占位、fakeredis 占位）
- [ ] T0.8 编写 `.gitignore`（venv, .env, data/chroma, __pycache__, .pytest_cache, htmlcov）
- [ ] T0.9 `git init` + 初始提交

**退出条件**: `pytest` 全绿；`python -c "import app"` 可导入；Git 仓库已初始化。
**提交信息**: `chore: 初始化项目骨架与测试框架`

---

## P1: 统一模型调用层
**目标**: 封装统一模型调用层，支持 DeepSeek/通义千问，提供同步/异步/SSE 流式，配置驱动切换。（G1, M1）
**入口条件**: P0 完成。
**设计**: 定义 `ModelProvider` 抽象基类（`chat`/`async_chat`/`stream`），各 provider 基于 LangChain `ChatOpenAI`（DeepSeek/Qwen 均兼容 OpenAI 接口），`factory.py` 按 Settings 返回 provider。测试用 `FakeLLM` 注入，不触达真实 API。

**任务清单**（TDD）:
- [ ] T1.1 RED: `test_models/test_base.py` — 断言 `ModelProvider` 为 ABC，定义 `chat/async_chat/stream` 抽象方法；子类未实现抛 TypeError
- [ ] T1.2 GREEN: 实现 `app/models/base.py`（ABC + `AIMessage`/`StreamChunk` dataclass）
- [ ] T1.3 RED: `test_models/test_deepseek.py` — 用 FakeChatModel 断言 `chat(messages)` 返回 AIMessage，内容非空
- [ ] T1.4 GREEN: 实现 `app/models/deepseek.py`（封装 LangChain ChatOpenAI，base_url/模型可配）
- [ ] T1.5 RED: `test_models/test_qwen.py` — 断言 Qwen provider 同步调用返回 AIMessage
- [ ] T1.6 GREEN: 实现 `app/models/qwen.py`
- [ ] T1.7 RED: `test_models/test_async.py` — 断言 `async_chat` 可 await 且返回 AIMessage（pytest-asyncio）
- [ ] T1.8 GREEN: 实现 provider 的 async 方法（基于 LangChain ainvoke）
- [ ] T1.9 RED: `test_models/test_stream.py` — 断言 `stream()` 产出多个 StreamChunk，按序到达
- [ ] T1.10 GREEN: 实现 stream（基于 LangChain astream，async generator）
- [ ] T1.11 RED: `test_models/test_factory.py` — 断言 factory 按 Settings.provider 返回对应 provider 实例；未知 provider 抛 ValueError
- [ ] T1.12 GREEN: 实现 `app/models/factory.py`
- [ ] T1.13 REFACTOR: 抽取公共 LangChain 封装逻辑，消除 DeepSeek/Qwen 重复代码

**退出条件**: 模型层单测全绿；FakeLLM 下同步/异步/SSE 三种调用均验证通过；切换 provider 仅改配置。
**提交信息**: `feat(models): 统一模型调用层支持同步异步与SSE流式`

---

## P2: 文档处理与向量库
**目标**: 打通文档解析 → 分块 → Embedding → Chroma 存储全链路。（G2, M2）
**入口条件**: P1 完成。
**设计**: loaders 支持 PDF/Word/Markdown；splitters 基于 LangChain RecursiveCharacterTextSplitter，chunk_size/overlap 可配；embeddings 抽象（默认 OpenAI 兼容 embedding，测试用 FakeEmbeddings）；vectorstore 封装 Chroma 持久化。

**任务清单**（TDD）:
- [ ] T2.1 RED: `test_rag/test_loaders.py` — Markdown loader 解析测试 md 返回 Document（含文本与 metadata source）
- [ ] T2.2 GREEN: 实现 `loaders.py` 的 markdown loader
- [ ] T2.3 RED: PDF loader 解析测试 PDF（用 reportlab 生成 fixture PDF）
- [ ] T2.4 GREEN: 实现 PDF loader（pypdf）
- [ ] T2.5 RED: Word loader 解析测试 docx（用 python-docx 生成 fixture）
- [ ] T2.6 GREEN: 实现 Word loader（python-docx）
- [ ] T2.7 RED: `test_rag/test_splitters.py` — 断言给定文本 + chunk_size=100/overlap=20，块数与首尾重叠正确
- [ ] T2.8 GREEN: 实现 `splitters.py`
- [ ] T2.9 RED: `test_rag/test_embeddings.py` — 用 FakeEmbeddings 断言 embed_documents 返回定长向量列表
- [ ] T2.10 GREEN: 实现 `embeddings.py`（抽象 + OpenAI 兼容实现 + Fake 实现）
- [ ] T2.11 RED: `test_rag/test_vectorstore.py` — 断言 add_documents 后 persist 目录存在；query 返回 top-k 且带 metadata
- [ ] T2.12 GREEN: 实现 `vectorstore.py`（Chroma 持久化封装）
- [ ] T2.13 RED: `test_rag/test_ingest.py` — 端到端：文档 → 块 → 向量 → 存储，断言入库后可检索
- [ ] T2.14 GREEN: 实现 `ingest` 管道（编排 loader→splitter→embeddings→vectorstore）
- [ ] T2.15 REFACTOR: 统一 Document 元数据格式（source/section/chunk_index）

**退出条件**: 三种格式文档均可解析入库；Chroma 持久化可重载；ingest 管道单测全绿。
**提交信息**: `feat(rag): 文档解析分块与Chroma向量存储`

---

## P3: RAG 问答链路
**目标**: 语义检索 → 上下文拼接 → LLM 生成，端到端问答可用，支持溯源与 chunk 参数优化。（G2, G3, M3）
**入口条件**: P2 完成。
**设计**: retriever 封装 Chroma similarity_search（top-k 可配）；prompts 构建 RAG 模板（含来源编号）；chain 用 LangChain LCEL 组装；输出含 answer + sources。FakeLLM 验证链路。

**任务清单**（TDD）:
- [ ] T3.1 RED: `test_rag/test_retriever.py` — 入库 fixture 文档后，retriever.invoke(query, k=3) 返回 ≤3 且按相似度排序
- [ ] T3.2 GREEN: 实现 `retriever.py`
- [ ] T3.3 RED: `test_rag/test_prompts.py` — 断言 RAG prompt 含 context、question、来源编号占位
- [ ] T3.4 GREEN: 实现 `prompts.py`（ChatPromptTemplate）
- [ ] T3.5 RED: `test_rag/test_context.py` — 断言上下文拼接含来源元数据与编号
- [ ] T3.6 GREEN: 实现上下文拼接工具
- [ ] T3.7 RED: `test_rag/test_chain.py` — FakeLLM 下 chain.invoke(query) 返回 {answer, sources}；sources 含 source/section
- [ ] T3.8 GREEN: 实现 `chain.py`（LCEL：retriever | prompt | llm | parser）
- [ ] T3.9 RED: `test_rag/test_chunk_tuning.py` — 参数化 chunk_size/overlap，断言不同配置下召回文档集合不同（为 G3 优化提供基线）
- [ ] T3.10 GREEN: 实现参数化检索入口
- [ ] T3.11 RED: `test_rag/test_tracing.py` — 断言返回的 sources 可映射回原文档片段
- [ ] T3.12 GREEN: 完善溯源元数据透传
- [ ] T3.13 REFACTOR: 抽取 RAGChain 配置对象（top_k, chunk_size, overlap, prompt 版本）

**退出条件**: 端到端问答（FakeLLM）返回答案 + 溯源；chunk 参数可调；单测全绿。
**提交信息**: `feat(rag): RAG问答链路与语义检索优化`

---

## P4: Redis 缓存与性能优化
**目标**: Redis 缓存高频问答结果与 Embedding 向量，设计失效策略，核心接口提速 ~60%。（G4, M4）
**入口条件**: P3 完成。
**设计**: 用 fakeredis 做单测；QA 缓存 key=query+kb_hash，value=answer+sources；Embedding 缓存 key=text_hash；失效策略：TTL + 知识库更新主动失效。

**任务清单**（TDD）:
- [ ] T4.1 RED: `test_cache/test_redis_client.py` — fakeredis 下 set/get/exists/delete 正确
- [ ] T4.2 GREEN: 实现 `redis_client.py`（封装连接 + key 规范）
- [ ] T4.3 RED: `test_cache/test_qa_cache.py` — 同一问题第二次命中缓存返回相同结果；miss 时回源
- [ ] T4.4 GREEN: 实现 `qa_cache.py`（get/set + key 计算）
- [ ] T4.5 RED: `test_cache/test_embedding_cache.py` — 相同文本命中 Embedding 缓存，不再调用真实 embed
- [ ] T4.6 GREEN: 实现 `embedding_cache.py`（装饰 embeddings 接口）
- [ ] T4.7 RED: `test_cache/test_invalidation.py` — TTL 到期后 miss；知识库更新（invalidate_kb）后相关 key 失效
- [ ] T4.8 GREEN: 实现失效策略（TTL + invalidate_kb）
- [ ] T4.9 RED: `test_cache/test_performance.py` — 模拟 N 次相同请求，有缓存比无缓存 P95 延迟显著降低（用 time.monotonic 统计）
- [ ] T4.10 GREEN: 将缓存接入 RAGChain（先查缓存，miss 再走链路并回填）
- [ ] T4.11 REFACTOR: 缓存抽象为可插拔（支持 no-cache 模式便于对比）

**退出条件**: 缓存命中/失效逻辑单测全绿；性能对比测试证明缓存显著降低延迟。
**提交信息**: `feat(cache): Redis缓存问答与向量结果`

---

## P5: FastAPI API 与鉴权
**目标**: FastAPI RESTful + SSE 流式 + API Key 鉴权 + 参数校验。（G5, M5）
**入口条件**: P4 完成。
**设计**: 路由分 chat/documents/health；鉴权用 APIKey 依赖（Header X-API-Key）；SSE 用 StreamingResponse；schemas 用 pydantic 校验。测试用 httpx AsyncClient + FakeLLM/fakeredis。

**任务清单**（TDD）:
- [ ] T5.1 RED: `test_api/test_auth.py` — 无/错 API Key 返回 401；正确 Key 通过
- [ ] T5.2 GREEN: 实现 `api/deps.py`（verify_api_key 依赖）
- [ ] T5.3 RED: `test_api/test_documents.py` — 上传文档触发 ingest，返回入库文档数
- [ ] T5.4 GREEN: 实现 `/api/v1/documents/upload`
- [ ] T5.5 RED: `test_api/test_chat.py` — /chat 返回 200 + {answer, sources}
- [ ] T5.6 GREEN: 实现 `/api/v1/chat`
- [ ] T5.7 RED: `test_api/test_chat_stream.py` — /chat/stream 返回 SSE，含多个 data: chunk 且以 [DONE] 结束
- [ ] T5.8 GREEN: 实现 `/api/v1/chat/stream`（StreamingResponse + model.stream）
- [ ] T5.9 RED: `test_api/test_validation.py` — 非法入参（空 query 等）返回 422
- [ ] T5.10 GREEN: 完善 `schemas.py` 校验
- [ ] T5.11 RED: `test_api/test_health.py` — /health 返回 200 + 状态
- [ ] T5.12 GREEN: 实现 `/health`（含 redis/chroma 依赖检查）
- [ ] T5.13 REFACTOR: 统一异常处理（全局异常 → JSON 错误响应）

**退出条件**: 全部接口单测绿；SSE 流式可验证；鉴权与校验生效。
**提交信息**: `feat(api): FastAPI接口SSE流式与APIKey鉴权`

---

## P6: 评估体系与 Docker 部署
**目标**: 评估脚本（准确率/召回率/延迟）+ Docker Compose 一键启动。（S1, M6）
**入口条件**: P5 完成。
**设计**: 评估脚本读取 QA 数据集，对比基线（关键词检索）vs RAG，输出指标；Dockerfile 多阶段构建；docker-compose 编排 app + redis。

**任务清单**（TDD + 工程）:
- [ ] T6.1 RED: `test_evaluation/test_metrics.py` — 断言 accuracy/recall/latency 计算正确（给定预测与真值）
- [ ] T6.2 GREEN: 实现 `evaluation/metrics.py`
- [ ] T6.3 准备 `evaluation/dataset.json`（10-20 条 QA + 参考答案）
- [ ] T6.4 RED: `test_evaluation/test_runner.py` — 评估 runner 跑数据集输出指标报告（FakeLLM）
- [ ] T6.5 GREEN: 实现 `evaluation/runner.py`（支持 baseline vs rag 对比）
- [ ] T6.6 编写 `Dockerfile`（多阶段：builder 装 deps → slim 运行）
- [ ] T6.7 编写 `docker-compose.yml`（services: app, redis；volumes: chroma data；healthcheck）
- [ ] T6.8 验证：`docker compose up` 启动，/health 健康，上传→问答链路通
- [ ] T6.9 编写 `README.md`（快速开始、API 说明、配置项、评估方式）
- [ ] T6.10 REFACTOR: 统一配置默认值，确保开箱即用

**退出条件**: 评估脚本可跑出 baseline vs RAG 对比指标；docker compose up 一键启动且端到端问答成功。
**提交信息**: `feat(eval,deploy): 评估体系与Docker一键部署`

---

## 依赖关系图
```
P0 (骨架) → P1 (模型层) → P2 (文档/向量库) → P3 (RAG链路) → P4 (缓存) → P5 (API) → P6 (评估/部署)
```

## 风险与缓解
| 风险 | 缓解措施 |
|------|----------|
| 真实 LLM API 不可用导致测试不稳定 | 全程用 FakeLLM 注入，真实 API 仅集成联调 |
| Chroma 持久化在并发下冲突 | 单测用临时目录隔离；生产限制单写 |
| Embedding 模型与向量维度不匹配 | embeddings 抽象层校验维度；FakeEmbeddings 固定维度 |
| SSE 在测试中难断言 | 用 httpx 流式读取 + 逐行解析断言 |
| Docker 构建体积大 | 多阶段构建 + slim 基础镜像 + .dockerignore |
| API Key 泄露 | .env 不入库；.env.example 仅占位；Docker 用环境变量注入 |
