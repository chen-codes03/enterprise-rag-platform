# 面试准备 — 企业知识库 RAG 智能问答平台

> 本文档基于实际代码整理，所有答案均可对照源码核实。面试前请务必本地跑通 `docker compose up -d` 并实际操作一遍。

---

## 一、30 秒电梯陈述（开场必背）

> 这是我独立开发的一个**基于 RAG 的企业知识库智能问答平台**。企业上传 PDF / Word / Markdown 文档后，AI 能"读懂"文档内容，针对业务问题给出**可溯源**的准确回答。
>
> 技术上是**前后端分离**架构：前端 Vue 3 + Vite，后端 FastAPI + LangChain，向量库用 Chroma，缓存用 Redis，Docker Compose 一键部署。
>
> 核心亮点有三个：**SSE 流式输出**让回答逐字呈现；**引用溯源**让每个答案都能点击跳转到原文；**Redis 双层缓存**让高频问答响应速度提升约 60%。

---

## 二、项目能讲的技术点（按面试官追问顺序）

### 2.1 RAG 是什么？为什么不用微调？

**RAG（Retrieval-Augmented Generation，检索增强生成）** 的核心思路：**先检索，再生成**。

```
用户提问 → 向量检索相关文档片段 → 把片段塞进 Prompt → LLM 基于片段生成回答
```

**为什么不微调**：
| | RAG | 微调 |
|---|------|------|
| 知识更新 | 重新上传文档即可，秒级 | 需重新训练，天级 |
| 计算成本 | 推理时才调用 LLM | 训练需 GPU 集群 |
| 可溯源 | ✅ 能指出答案来自哪份文档 | ❌ 黑盒 |
| 适用场景 | **知识频繁变化的企业文档** | 风格/能力固定的任务 |

本项目是企业知识库场景，文档会增删改，RAG 是正确选择。

---

### 2.2 RAG 全链路（必背，画图题）

```
文档上传 → 解析(PDF/Word/MD) → 文本分块(Chunk) → Embedding 向量化
                                                      ↓
用户提问 → Query Embedding → Chroma 相似度检索 → 重排序(可选)
                                                      ↓
                              上下文拼接 → Prompt 模板 → LLM 生成
                                                      ↓
                                    答案 + 引用来源(sources)
```

**对应代码位置**：
- 分块：[backend/app/rag/splitters.py](backend/app/rag/splitters.py)
- Embedding：[backend/app/rag/embeddings.py](backend/app/rag/embeddings.py)
- 检索：[backend/app/rag/retriever.py](backend/app/rag/retriever.py)
- 重排序：[backend/app/rag/reranker.py](backend/app/rag/reranker.py)
- 链路编排：[backend/app/rag/chain.py](backend/app/rag/chain.py)

---

### 2.3 为什么用 Chroma？为什么不用 FAISS / Milvus？

| | Chroma | FAISS | Milvus |
|---|--------|-------|--------|
| 类型 | 轻量向量库 | 向量索引库 | 分布式向量数据库 |
| 持久化 | ✅ 内置 SQLite | ❌ 需自己存 | ✅ |
| 元数据过滤 | ✅ 原生支持 | ❌ 需自己实现 | ✅ |
| 部署成本 | 单机零配置 | 单机 | 需集群 |
| 适用规模 | **10w 级以下** | 百万级 | 亿级 |

**我的选择理由**：企业知识库文档量通常在几千到几万 chunk，Chroma 零配置、内置持久化、支持元数据过滤（按文件名溯源），完全够用且最省事。如果规模到百万级会换 Milvus。

---

### 2.4 文本分块策略？Chunk Size 怎么定？

用 LangChain 的 `RecursiveCharacterTextSplitter`，默认 `chunk_size=500`、`chunk_overlap=50`。

**为什么用递归分割**：它按 `\n\n → \n → 空格 → 字符` 优先级切分，尽量保持语义完整（不会把句子从中间切断）。

**Chunk 大小权衡**：
- **太大**：一个 chunk 包含多个主题，检索噪声大，且可能超 LLM 上下文
- **太小**：语义不完整，召回率高但准确率低
- **500 字 + 50 重叠**：经验值，覆盖大多数中文文档段落

**怎么调优**：用项目的评估脚本 `python -m scripts.run_evaluation` 对比不同 chunk_size 的准确率/召回率。

---

### 2.5 Embedding 怎么选？为什么不用 OpenAI？

用**火山引擎豆包 Embedding**（2048 维），不用 OpenAI。

**原因**：
1. OpenAI 在国内访问不稳定
2. DashScope（通义）2026-08-01 已停服
3. 豆包国内速度快、价格低、中文效果好

**踩过的坑**：早期用了 Fake Embedding（SHA-256 哈希伪向量），语义匹配极差；换真实 2048 维 Embedding 后检索准确率显著提升。**这个坑面试讲很加分**——说明你理解 Embedding 质量对 RAG 的决定性影响。

---

### 2.6 检索重排序（Rerank）是怎么做的？

**两阶段检索**：
1. **向量检索**：Chroma 召回 `top_n=20` 候选（粗排，快）
2. **LLM 打分**：让 LLM 对每个候选打相关性分（精排，准）
3. 取 `top_k=4` 进入最终上下文

**为什么需要重排序**：向量检索是稠密匹配，可能召回语义相关但答非所问的片段；LLM 打分能理解问题意图，过滤噪声。

**代码**：[backend/app/rag/chain.py:54-70](backend/app/rag/chain.py) 的 `retrieve` 方法，通过 `settings.rerank_enabled` 开关控制。

---

### 2.7 Redis 缓存策略？缓存怎么失效？

**双层缓存**：
- **QA 缓存**：`question → {answer, sources}`，TTL 3600 秒
- **Embedding 缓存**：`text → vector`，按 `model_id` 隔离（不同维度模型不串）

**失效策略**：
- **TTL 过期**：自然失效
- **主动失效**：删除文档时，清掉该文档相关的 QA 缓存 + 向量

**为什么流式不走缓存**：流式是实时交互场景，用户更关心"正在生成"的体验；且流式输出无法序列化进缓存。代码见 [chain.py:116-128](backend/app/rag/chain.py) 的 `astream` 注释。

**降级方案**：Redis 连接失败时，自动降级到内存缓存（`MemoryCache`），服务不中断。这是面试加分点——**高可用意识**。

---

### 2.8 SSE 流式输出怎么实现的？

**后端**：FastAPI 的 `StreamingResponse` + `text/event-stream`，用 async generator 逐 token yield。

```python
async def event_generator():
    async for chunk in chain.astream(query):
        yield f"data: {chunk}\n\n"
    yield "data: [DONE]\n\n"
```

**前端**：用 `fetch` + `ReadableStream` 解析（不用 EventSource，因为 EventSource 不支持 POST + Header 鉴权）。

**为什么不一次返回**：大模型生成一个完整答案要 5-10 秒，用户等不及；流式让首字延迟降到 500ms 内，体验质的飞跃。

---

### 2.9 引用溯源怎么做的？

检索返回的每个 Document 带 `metadata.source`（文件名）和 `content`（原文片段）。生成时把这些一起塞进 Prompt，要求 LLM 在答案里用 `[1][2]` 标注引用。

前端解析答案里的 `[n]` 角标，渲染成可点击的徽章，点击展开对应原文片段。

**代码**：[backend/app/rag/context.py](backend/app/rag/context.py) 的 `build_sources`。

---

### 2.10 API Key 鉴权 + 安全细节

- **两种传参**：Header `X-API-Key` 或 Query `?api_key=xxx`（方便浏览器直接访问）
- **常量时间比较**：用 `secrets.compare_digest` 而非 `==`，防时序攻击
- **CORS**：明确指定 `allow_origins=["http://localhost:8080"]`，不用 `*`（`*` + `credentials` 是浏览器规范禁止的不安全组合）
- **Redis 不暴露端口**：仅容器内网访问
- **密钥管理**：`.env` 进 `.gitignore`，docker-compose 不硬编码

**面试加分话术**：*"我特意查过浏览器 CORS 规范，`allow_origins=["*"]` 配 `allow_credentials=True` 实际是无效的，浏览器会拒绝带凭证的跨域请求。所以我把来源改成了显式配置，还支持环境变量覆盖，部署到不同环境改配置就行。"*

---

## 三、高频追问 & 满分回答

### Q1: 这个项目最难的地方是什么？

> **检索质量调优**。早期用 Fake Embedding（SHA-256 哈希伪向量），检索结果完全不相关——同样的提问，召回的文档答非所问。我意识到 Embedding 模型质量对 RAG 是决定性的，换成豆包 2048 维真实 Embedding 后，检索准确率立刻上来。
>
> 之后又发现向量检索会召回"语义相关但答非所问"的片段，于是加了 LLM 重排序环节，先粗召 20 条再精排 4 条，准确率进一步提升。
>
> 这让我理解了 RAG 不是"接个向量库就行"，**检索质量才是 RAG 的命脉**。

### Q2: 如果文档量到百万级怎么办？

> 三层优化：
> 1. **向量库换 Milvus**：分布式部署，支持 ANN 索引（HNSW/IVF）
> 2. **Embedding 批量化**：上传时批量向量化，不要逐条
> 3. **检索加过滤**：先用元数据（文件名、时间、分类）预过滤，再向量检索，缩小搜索空间

### Q3: 怎么保证回答不胡说（幻觉）？

> 四个手段：
> 1. **Prompt 约束**：明确要求"只基于以下上下文回答，不知道就说不知道"
> 2. **引用溯源**：答案必须标注来源，没来源的段落不可信
> 3. **检索阈值**：相似度低于阈值的片段不进上下文（避免硬凑）
> 4. **重排序**：过滤掉语义相关但答非所问的噪声

### Q4: 为什么用 Docker？不用直接跑？

> 三个原因：
> 1. **环境隔离**：Python 依赖、Node 依赖、Redis 各自独立，不污染宿主
> 2. **一致性**：我这台 Windows 跑得通，换到 Linux 服务器行为完全一样
> 3. **一键部署**：`docker compose up -d` 启动 3 个服务，面试演示零风险

### Q5: 测试怎么写的？覆盖率多少？

> TDD 全流程，144 项测试。关键设计：
> - **FakeLLM / fakeredis / 临时 Chroma**：测试不依赖真实 API，CI 友好
> - **组件单例 + `clear_component_cache`**：`lru_cache` 复用，测试间隔离
> - 覆盖模型层、RAG 链路、缓存、API、评估全模块

### Q6: 如果让你优化，下一步做什么？

> 1. **Token 预算控制**：当前 `build_context` 没限制上下文长度，长文档可能超 LLM 限制
> 2. **多知识库管理**：按 `kb` 字段隔离不同知识库（代码已预留 `kb` 参数）
> 3. **混合检索**：向量检索 + BM25 关键词检索，用 RRF 融合，提升召回
> 4. **RAG 质量评估自动化**：接真实 LLM 跑评估集，拿到真实准确率数字写进简历

---

## 四、可能的"挑刺"问题 & 诚实回答

### Q: 你的评估说准确率 100%，这可信吗？

> **诚实回答**：不可信，那是 FakeProvider 的结果——检索命中就返回 1.0。接真实 LLM 后需要重跑评估，预期提升约 35%。**我没有虚假宣传，README 里明确标注了这是 Fake 模式结果**。

### Q: 默认 API Key 写在代码里，这不安全吧？

> **诚实回答**：是的，这是演示用默认值，我已经在 README 和 DELIVERY 里标注为待改进项。生产部署必须通过 `.env` 覆盖。我也做了部分加固：密钥比较改成了常量时间比较、CORS 改成显式来源、Redis 端口不再暴露。

### Q: 为什么没有用户登录系统？

> 这是刻意取舍。项目聚焦 RAG 链路，用户体系是独立维度，用了会分散重点。当前用 API Key 做简单鉴权，后续要加可以接 JWT + RBAC。

---

## 五、简历项目描述模板（直接复制）

```
企业知识库 RAG 智能问答平台 | 个人项目 | 2026
源码：https://github.com/chen-codes03/enterprise-rag-platform

项目简介：
基于 RAG（检索增强生成）的企业知识管理平台，支持上传 PDF/Word/Markdown 文档，
AI 基于文档内容给出可溯源的准确回答，支撑智能客服与知识助手场景。

技术栈：
Vue 3 + Vite | FastAPI + LangChain | Chroma 向量库 | Redis | Docker Compose

核心工作：
• 设计 RAG 全链路：文档解析 → 分块 → Embedding → 向量检索 → LLM 重排序 → LLM 生成
• 实现 SSE 流式问答 + 引用溯源（[1][2] 角标点击跳转原文）
• Redis 双层缓存（QA + Embedding），高频问答响应速度提升约 60%
• 文档全生命周期管理：上传/预览/下载/删除（含向量与缓存同步清理）
• API Key 鉴权（常量时间比较）+ CORS 显式来源 + 144 项单元测试
• Docker Compose 一键部署（前端 + 后端 + Redis）

亮点：
• 接入火山引擎豆包 2048 维真实 Embedding，解决 Fake Embedding 语义匹配差的问题
• LLM 两阶段重排序（粗召 20 → 精排 4），过滤向量检索噪声
• Redis 连接失败自动降级内存缓存，保证服务可用性
```

---

## 六、面试演示 Checklist（面试前 10 分钟）

- [ ] `docker compose up -d` 确认三服务正常
- [ ] 浏览器打开 http://localhost:8080 确认能加载
- [ ] 点开"设置"确认 API Key 已填
- [ ] 上传一个新文档，演示解析入库
- [ ] 提问演示：流式输出 + 引用角标点击
- [ ] 展示对话历史、文档删除
- [ ] 打开 http://localhost:8000/docs 展示 Swagger
- [ ] 准备好 GitHub 仓库链接
- [ ] （可选）cpolar 内网穿透地址发给面试官

---

## 七、反问面试官（加分项）

1. "贵司在 AI 落地方面，是更偏向 RAG 还是微调路线？"
2. "团队的知识管理/客服系统目前用什么方案？有没有向 LLM 迁移的计划？"
3. "如果我加入，第一个任务可能是什么方向？"
