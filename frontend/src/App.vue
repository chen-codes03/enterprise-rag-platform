<template>
  <div class="app">
    <!-- ===== 顶部导航 ===== -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a10 10 0 1 0 10 10" />
            <path d="M12 2v10l7 7" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </div>
        <div class="header-title">
          <h1>企业知识库 RAG 智能问答平台</h1>
          <p>基于检索增强生成，让 AI 读懂企业私有文档</p>
        </div>
      </div>

      <div class="header-right">
        <div class="stat" title="知识库文档数">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span>{{ store.documents.length }} 文档</span>
        </div>
        <button class="icon-btn" @click="showSettings = true" title="设置">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </button>
        <div class="status" :class="store.serviceStatus">
          <span class="status-dot"></span>
          <span>{{ statusText }}</span>
        </div>
      </div>
    </header>

    <div class="main">
      <!-- ===== 左侧：知识库管理 ===== -->
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        </div>

        <template v-if="!sidebarCollapsed">
          <div class="sidebar-section">
            <div class="section-title">知识库管理</div>

            <label class="upload-zone" :class="{ dragging: isDragging }" @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="handleDrop">
              <div class="upload-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              </div>
              <div class="upload-text">
                <strong>点击上传</strong> 或拖拽到此
              </div>
              <div class="upload-hint">PDF · Word · Markdown · TXT</div>
              <input type="file" ref="fileInput" multiple accept=".pdf,.doc,.docx,.md,.txt" @change="handleFileChange" style="display: none" />
            </label>

            <div v-if="uploading" class="upload-progress">
              <div class="spinner"></div>
              <span>{{ uploading }}</span>
            </div>
          </div>

          <div class="sidebar-section flex-fill">
            <div class="section-title">
              <span>已上传文档</span>
              <span class="count">{{ store.documents.length }}</span>
            </div>
            <div class="file-list">
              <div v-if="store.documents.length === 0" class="empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <p>暂无文档</p>
                <span>上传文档后即可开始问答</span>
              </div>
              <div v-for="doc in store.documents" :key="doc.filename" class="file-item">
                <div class="file-icon" :class="fileType(doc.filename)">
                  {{ fileExt(doc.filename) }}
                </div>
                <div class="file-info">
                  <div class="file-name" :title="doc.filename">{{ doc.filename }}</div>
                  <div class="file-meta">
                    {{ doc.chunk_count }} 个文本块
                    <span v-if="doc.size != null"> · {{ formatSize(doc.size) }}</span>
                  </div>
                </div>
                <div class="file-actions">
                  <button
                    v-if="doc.previewable"
                    class="file-action-btn"
                    @click="openPreview(doc)"
                    title="在线预览"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  </button>
                  <button
                    v-if="doc.size != null"
                    class="file-action-btn"
                    @click="handleDownload(doc.filename)"
                    title="下载原文件"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  </button>
                  <span
                    v-if="doc.size == null"
                    class="file-action-hint"
                    title="原文件未保留（历史文档），仅支持问答检索"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  </span>
                  <button
                    class="file-action-btn danger"
                    :disabled="store.deletingDocument === doc.filename"
                    @click="handleDelete(doc.filename)"
                    title="删除文档"
                  >
                    <svg v-if="store.deletingDocument !== doc.filename" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                    <span v-else class="spinner mini"></span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </aside>

      <!-- ===== 右侧：聊天区 ===== -->
      <main class="chat">
        <div class="chat-toolbar" v-if="store.messages.length">
          <div class="toolbar-left">
            <button class="toolbar-btn" :class="{ active: store.selectMode }" @click="store.toggleSelectMode()">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
              <span>{{ store.selectMode ? '退出多选' : '多选' }}</span>
            </button>
            <template v-if="store.selectMode">
              <button class="toolbar-btn" @click="store.selectAll()" :disabled="!store.messages.length">
                <span>全选</span>
              </button>
              <button class="toolbar-btn danger" @click="handleBatchDelete" :disabled="!store.selectedIds.size">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                <span>删除选中 ({{ store.selectedIds.size }})</span>
              </button>
            </template>
          </div>
          <button class="toolbar-btn danger" @click="handleClearAll" v-if="!store.selectMode">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            <span>清空对话</span>
          </button>
        </div>

        <div class="chat-messages" ref="messagesContainer">
          <!-- 欢迎页 -->
          <div v-if="store.messages.length === 0" class="welcome">
            <div class="welcome-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </div>
            <h2>开始智能问答</h2>
            <p>上传企业文档后，AI 将基于知识库内容精准回答您的业务问题</p>

            <div class="example-questions">
              <div class="example-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                试试问我
              </div>
              <button
                v-for="(q, qi) in exampleQuestions"
                :key="q"
                class="example-item"
                :style="{ animationDelay: qi * 60 + 'ms' }"
                @click="quickAsk(q)"
              >
                <span class="example-prefix">Q</span>
                <span class="example-text">{{ q }}</span>
                <svg class="example-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </div>
          </div>

          <!-- 消息列表 -->
          <template v-for="(msg, idx) in store.messages" :key="idx">
            <div class="message" :class="msg.role">
              <!-- 多选模式：显示复选框 -->
              <div
                v-if="store.selectMode && msg.id"
                class="select-checkbox"
                :class="{ checked: store.selectedIds.has(msg.id) }"
                @click="store.toggleSelect(msg.id)"
              >
                <svg v-if="store.selectedIds.has(msg.id)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
              <div class="avatar">
                <svg v-if="msg.role === 'user'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>
              </div>
              <div class="message-body">
                <div class="message-header">
                  <span class="role-name">{{ msg.role === 'user' ? '我' : 'AI 助手' }}</span>
                  <span class="msg-time" v-if="msg.createdAt && msg.role === 'ai'">{{ msg.createdAt }}</span>
                  <div class="message-actions" v-if="msg.role === 'ai' && !msg.streaming && !store.selectMode">
                    <button class="action-btn" @click="copyMessage(msg)" title="复制回答">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                    </button>
                    <button class="action-btn danger" @click="handleDeleteConversation(msg.id)" title="删除此对话" v-if="msg.id">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                  </div>
                </div>
                <div class="bubble" :class="{ streaming: msg.streaming }">
                  <div v-if="msg.role === 'ai'" class="markdown" v-html="renderAiContent(msg, idx)" @click="handleCitationClick($event, idx)"></div>
                  <template v-else>{{ msg.content }}</template>
                  <span v-if="msg.streaming && !msg.content" class="typing">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                  </span>
                  <span v-if="msg.streaming && msg.content" class="cursor"></span>
                </div>

                <!-- 参考文档 -->
                <div v-if="msg.sources && msg.sources.length && !msg.streaming" class="sources">
                  <div class="sources-header" @click="toggleSource(idx)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                    <span>参考文档（{{ msg.sources.length }}）</span>
                    <svg class="chevron" :class="{ open: expandedSources.has(idx) }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
                  </div>
                  <div v-if="expandedSources.has(idx)" class="sources-list">
                    <div v-for="(s, si) in msg.sources" :key="si" class="source-item" :id="`src-${idx}-${s.index}`">
                      <div class="source-head">
                        <span class="source-badge">#{{ s.index }}</span>
                        <span class="source-file" :title="s.source">{{ s.source }}</span>
                      </div>
                      <div class="source-content">{{ s.content }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- 输入区 -->
        <div class="chat-input">
          <div class="input-wrapper">
            <textarea
              v-model="input"
              placeholder="输入您的问题... (Enter 发送 · Shift+Enter 换行)"
              rows="1"
              :disabled="store.loading"
              @keydown="handleKey"
              ref="textarea"
            ></textarea>
          </div>
          <button class="send-btn" @click="send" :disabled="store.loading || !input.trim()">
            <span v-if="!store.loading">发送</span>
            <span v-else class="sending">
              <span class="spinner small"></span>
            </span>
          </button>
        </div>
      </main>
    </div>

    <!-- ===== 设置弹窗 ===== -->
    <div class="modal-overlay" v-if="showSettings" @click.self="showSettings = false">
      <div class="modal">
        <div class="modal-header">
          <h3>设置</h3>
          <button class="close-btn" @click="showSettings = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>API Key</label>
            <input type="password" v-model="apiKey" @change="saveApiKey" placeholder="输入访问密钥" />
            <p class="form-hint">用于接口鉴权，默认已填入演示密钥</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 文档预览弹窗 ===== -->
    <div class="modal-overlay preview-overlay" v-if="previewDoc" @click.self="closePreview">
      <div class="preview-modal">
        <div class="modal-header">
          <h3 :title="previewDoc.filename">{{ previewDoc.filename }}</h3>
          <div class="preview-header-actions">
            <button class="preview-action-btn" @click="handleDownload(previewDoc.filename)" title="下载">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </button>
            <button class="close-btn" @click="closePreview">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div class="preview-body">
          <!-- 加载中 -->
          <div v-if="previewLoading" class="preview-loading">
            <div class="spinner"></div>
            <span>加载中...</span>
          </div>
          <!-- 加载失败 -->
          <div v-else-if="previewError" class="preview-error">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <p>{{ previewError }}</p>
            <button class="preview-fallback-btn" @click="handleDownload(previewDoc.filename)">下载查看</button>
          </div>
          <!-- PDF 预览 -->
          <iframe
            v-else-if="previewType === 'pdf'"
            :src="previewUrl"
            class="preview-iframe"
          ></iframe>
          <!-- Markdown 预览 -->
          <div v-else-if="previewType === 'md'" class="preview-markdown markdown" v-html="previewContent"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { marked } from 'marked'
import { useChatStore } from './stores/chat'
import { apiService } from './api'

const store = useChatStore()
const input = ref('')
const textarea = ref(null)
const fileInput = ref(null)
const messagesContainer = ref(null)
const isDragging = ref(false)
const uploading = ref('')
const apiKey = ref(localStorage.getItem('apiKey') || 'sk-rag-demo-key-change-me')
const showSettings = ref(false)
const sidebarCollapsed = ref(false)
const expandedSources = ref(new Set())

// ===== 文档预览/下载 =====
const previewDoc = ref(null)         // 当前预览的文档对象
const previewType = ref('')          // 'pdf' | 'md'
const previewUrl = ref('')           // PDF iframe 的 URL
const previewContent = ref('')       // Markdown 渲染后的 HTML
const previewLoading = ref(false)
const previewError = ref('')

const exampleQuestions = computed(() => {
  const all = new Set()
  for (const doc of store.documents) {
    for (const q of doc.suggested_questions || []) {
      if (q && q.trim()) all.add(q.trim())
    }
  }
  const base = [
    '报销流程是什么？',
    '如何申请年假？',
    '公司的考勤制度有哪些？',
    '社保公积金缴纳比例是多少？',
  ]
  const merged = [...all, ...base]
  // 随机取 5 条
  return merged.sort(() => Math.random() - 0.5).slice(0, 5)
})

const statusText = computed(() => {
  const map = { ok: '服务正常', error: '服务异常', connecting: '连接中...' }
  return map[store.serviceStatus] || '服务异常'
})

marked.setOptions({ breaks: true, gfm: true })

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text
  }
}

/** 渲染 AI 回答：先转 markdown，再将 [1] [2] 等替换为可点击的引用徽章 */
function renderAiContent(msg, msgIdx) {
  const html = renderMarkdown(msg.content)
  if (!msg.sources || !msg.sources.length) return html
  // 将 [1] [2] 等编号替换为可点击的上标徽章
  return html.replace(/\[(\d+)\]/g, (match, num) => {
    const idx = parseInt(num)
    if (idx >= 1 && idx <= msg.sources.length) {
      return `<sup class="citation-badge" data-source-index="${idx}">${idx}</sup>`
    }
    return match
  })
}

/** 点击引用徽章：展开来源列表 + 滚动到对应来源 + 高亮闪烁 */
function handleCitationClick(e, msgIdx) {
  const badge = e.target.closest('.citation-badge')
  if (!badge) return
  const sourceIndex = parseInt(badge.dataset.sourceIndex)

  // 展开来源列表（如果未展开）
  if (!expandedSources.value.has(msgIdx)) {
    const s = new Set(expandedSources.value)
    s.add(msgIdx)
    expandedSources.value = s
  }

  // 等 DOM 更新后滚动 + 高亮
  nextTick(() => {
    const el = document.getElementById(`src-${msgIdx}-${sourceIndex}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      el.classList.add('highlight')
      setTimeout(() => el.classList.remove('highlight'), 2000)
    }
  })
}

function fileExt(name) {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  return ext.slice(0, 4)
}

function fileType(name) {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  if (['pdf'].includes(ext)) return 'pdf'
  if (['doc', 'docx'].includes(ext)) return 'doc'
  if (['md'].includes(ext)) return 'md'
  return 'txt'
}

function saveApiKey() {
  apiService.setApiKey(apiKey.value)
  showToast('设置已保存', 'success')
}

function toggleSource(idx) {
  const s = new Set(expandedSources.value)
  if (s.has(idx)) s.delete(idx)
  else s.add(idx)
  expandedSources.value = s
}

function copyMessage(msg) {
  navigator.clipboard.writeText(msg.content).then(() => {
    showToast('已复制到剪贴板', 'success')
  })
}

function quickAsk(q) {
  input.value = q
  send()
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

async function send() {
  const q = input.value.trim()
  if (!q || store.loading) return
  await store.sendMessage(q)
  input.value = ''
  await nextTick()
  autoResize()
}

function autoResize() {
  if (textarea.value) {
    textarea.value.style.height = 'auto'
    textarea.value.style.height = Math.min(textarea.value.scrollHeight, 120) + 'px'
  }
}

function handleFileChange(e) {
  handleFiles(e.target.files)
  fileInput.value.value = ''
}

function handleDrop(e) {
  isDragging.value = false
  handleFiles(e.dataTransfer.files)
}

async function handleDelete(filename) {
  if (!confirm(`确定要删除「${filename}」吗？此操作不可恢复。`)) return
  try {
    const result = await store.deleteDocument(filename)
    showToast(`已删除「${filename}」（${result.deleted_chunks} 块）`, 'success')
  } catch (e) {
    showToast(e.message, 'error')
  }
}

// 格式化文件大小
function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// 下载文档
async function handleDownload(filename) {
  try {
    showToast(`正在下载 ${filename}...`, 'info')
    await apiService.downloadDocument(filename)
    showToast(`已下载 ${filename}`, 'success')
  } catch (e) {
    showToast(e.message, 'error')
  }
}

// 打开预览
async function openPreview(doc) {
  previewDoc.value = doc
  previewLoading.value = true
  previewError.value = ''
  previewContent.value = ''
  previewUrl.value = ''
  previewType.value = ''

  const ext = doc.filename.split('.').pop()?.toLowerCase() || ''
  try {
    if (ext === 'pdf') {
      // PDF：直接用 iframe 加载（URL 带 api_key query 参数）
      previewType.value = 'pdf'
      previewUrl.value = apiService.getPreviewUrl(doc.filename)
    } else if (ext === 'md' || ext === 'markdown') {
      // Markdown：拉取文本，前端 marked 渲染
      previewType.value = 'md'
      const text = await apiService.fetchMarkdownContent(doc.filename)
      previewContent.value = renderMarkdown(text)
    } else {
      throw new Error('该文件类型不支持在线预览')
    }
  } catch (e) {
    previewError.value = e.message || '预览失败'
  } finally {
    previewLoading.value = false
  }
}

function closePreview() {
  previewDoc.value = null
  previewContent.value = ''
  previewUrl.value = ''
  previewError.value = ''
}

async function handleDeleteConversation(id) {
  if (!confirm('确定要删除这条对话吗？')) return
  try {
    await store.deleteConversation(id)
    showToast('对话已删除', 'success')
  } catch (e) {
    showToast(e.message, 'error')
  }
}

async function handleBatchDelete() {
  if (!store.selectedIds.size) return
  if (!confirm(`确定要删除选中的 ${store.selectedIds.size} 条对话吗？`)) return
  try {
    const count = await store.batchDeleteSelected()
    showToast(`已删除 ${count} 条对话`, 'success')
  } catch (e) {
    showToast(e.message, 'error')
  }
}

async function handleClearAll() {
  if (!confirm('确定要清空全部对话吗？此操作不可恢复。')) return
  try {
    await store.clearAllMessages()
    showToast('已清空全部对话', 'success')
  } catch (e) {
    showToast(e.message, 'error')
  }
}

async function handleFiles(files) {
  for (const file of Array.from(files)) {
    uploading.value = `正在上传 ${file.name}...`
    try {
      await store.uploadFile(file)
      showToast(`${file.name} 上传成功`, 'success')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }
  uploading.value = ''
}

function showToast(msg, type = 'info') {
  const toast = document.createElement('div')
  toast.className = `toast ${type}`
  toast.textContent = msg
  document.body.appendChild(toast)
  setTimeout(() => toast.remove(), 3000)
}

// 输入框自适应高度
watch(input, async () => {
  await nextTick()
  autoResize()
})

// 新消息自动滚到底部
watch(
  () => store.messages.length,
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

// 流式输出时持续滚动
watch(
  () => store.messages.map((m) => m.content).join(''),
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(async () => {
  apiService.setApiKey(apiKey.value)
  await store.checkHealth()
  await store.loadDocuments()
  await store.loadHistory()
  setInterval(() => store.checkHealth(), 30000)
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* ===== 顶部导航 ===== */
.header {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #818cf8 100%);
  color: white;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  flex-shrink: 0;
  box-shadow: 0 2px 12px rgba(79, 70, 229, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.logo svg {
  width: 22px;
  height: 22px;
}

.header-title h1 {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.header-title p {
  font-size: 12px;
  opacity: 0.8;
  margin-top: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.15);
  padding: 6px 12px;
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.stat svg {
  width: 15px;
  height: 15px;
  opacity: 0.9;
}

.icon-btn {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.icon-btn svg {
  width: 18px;
  height: 18px;
}

.status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger);
  box-shadow: 0 0 0 0 currentColor;
}

.status.ok .status-dot {
  background: #4ade80;
  animation: pulse 2s infinite;
}

.status.error .status-dot {
  background: #f87171;
}

.status.connecting .status-dot {
  background: #fbbf24;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.5);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(74, 222, 128, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
  }
}

/* ===== 主区域 ===== */
.main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 300px;
  background: linear-gradient(180deg, var(--card) 0%, var(--bg-soft) 100%);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: relative;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 0;
}

.sidebar-toggle {
  position: absolute;
  right: -14px;
  top: 20px;
  width: 28px;
  height: 28px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
}

.sidebar-toggle:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.sidebar.collapsed .sidebar-toggle svg {
  transform: rotate(180deg);
}

.sidebar-toggle svg {
  width: 14px;
  height: 14px;
  transition: transform 0.3s;
}

.sidebar-section {
  padding: 20px;
}

.sidebar-section.flex-fill {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-top: 0;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-lighter);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title .count {
  background: var(--primary-bg);
  color: var(--primary);
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.upload-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 28px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s;
  background: var(--bg-soft);
  display: block;
}

.upload-zone:hover,
.upload-zone.dragging {
  border-color: var(--primary);
  background: var(--primary-bg);
  transform: translateY(-1px);
}

.upload-icon {
  width: 40px;
  height: 40px;
  margin: 0 auto 10px;
  color: var(--primary);
}

.upload-icon svg {
  width: 100%;
  height: 100%;
}

.upload-text {
  font-size: 13px;
  color: var(--text-light);
}

.upload-text strong {
  color: var(--primary);
  font-weight: 600;
}

.upload-hint {
  font-size: 11px;
  color: var(--text-lighter);
  margin-top: 6px;
  letter-spacing: 0.3px;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--primary);
  padding: 8px 12px;
  background: var(--primary-bg);
  border-radius: var(--radius-sm);
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--primary-bg);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner.small {
  width: 16px;
  height: 16px;
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.file-list {
  flex: 1;
  overflow-y: auto;
  margin: 0 -4px;
  padding: 0 4px;
}

.empty {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-lighter);
}

.empty svg {
  width: 40px;
  height: 40px;
  margin: 0 auto 8px;
  opacity: 0.5;
}

.empty p {
  font-size: 13px;
  color: var(--text-light);
  margin-bottom: 4px;
}

.empty span {
  font-size: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  margin-bottom: 6px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
  position: relative;
  overflow: hidden;
  border: 1px solid transparent;
}

.file-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 3px 0 0 3px;
  opacity: 0;
  transition: opacity 0.2s;
}

.file-item:hover {
  background: var(--card);
  border-color: var(--border);
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}

.file-item:hover::before {
  opacity: 1;
}

.file-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: white;
  flex-shrink: 0;
}

.file-icon.pdf {
  background: linear-gradient(135deg, #ef4444, #f87171);
}

.file-icon.doc {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
}

.file-icon.md {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
}

.file-icon.txt {
  background: linear-gradient(135deg, #64748b, #94a3b8);
}

.file-info {
  flex: 1;
  overflow: hidden;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 11px;
  color: var(--text-lighter);
  margin-top: 2px;
}

.file-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}

.file-item:hover .file-actions {
  opacity: 1;
}

.file-action-btn {
  background: none;
  border: none;
  color: var(--text-lighter);
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
}

.file-action-btn:hover:not(:disabled) {
  background: var(--primary-bg);
  color: var(--primary);
}

.file-action-btn.danger:hover:not(:disabled) {
  background: var(--danger-bg);
  color: var(--danger);
}

.file-action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.file-action-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  color: var(--text-lighter);
  opacity: 0.6;
}

.file-action-hint svg {
  width: 14px;
  height: 14px;
}

.file-action-btn svg {
  width: 14px;
  height: 14px;
}

.spinner.mini {
  width: 14px;
  height: 14px;
  border: 2px solid var(--bg-soft);
  border-top-color: var(--text-lighter);
}

/* ===== 聊天区 ===== */
.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  min-width: 0;
}

.chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 32px;
  background: var(--card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-light);
  cursor: pointer;
  transition: all 0.15s;
}

.toolbar-btn svg {
  width: 14px;
  height: 14px;
}

.toolbar-btn:hover:not(:disabled) {
  background: var(--primary-bg);
  color: var(--primary);
  border-color: var(--primary-light);
}

.toolbar-btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.toolbar-btn.danger:hover:not(:disabled) {
  background: var(--danger-bg);
  color: var(--danger);
  border-color: var(--danger);
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select-checkbox {
  width: 22px;
  height: 22px;
  border: 2px solid var(--border);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
  margin-top: 8px;
  background: var(--card);
}

.select-checkbox:hover {
  border-color: var(--primary);
}

.select-checkbox.checked {
  background: var(--primary);
  border-color: var(--primary);
}

.select-checkbox svg {
  width: 14px;
  height: 14px;
  color: white;
}

.msg-time {
  font-size: 11px;
  color: var(--text-lighter);
  margin-left: auto;
}

.action-btn.danger:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  scroll-behavior: smooth;
  background:
    radial-gradient(ellipse at top, rgba(99, 102, 241, 0.04) 0%, transparent 60%),
    var(--bg);
}

/* 欢迎页 */
.welcome {
  text-align: center;
  padding: 8vh 20px 40px;
  max-width: 560px;
  margin: 0 auto;
}

.welcome-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 12px 28px rgba(99, 102, 241, 0.3);
}

.welcome-icon svg {
  width: 36px;
  height: 36px;
}

.welcome h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 10px;
}

.welcome p {
  font-size: 14px;
  color: var(--text-light);
  line-height: 1.7;
}

.example-questions {
  margin-top: 32px;
  text-align: left;
  max-width: 560px;
  margin-left: auto;
  margin-right: auto;
}

.example-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-light);
  margin-bottom: 12px;
}

.example-label svg {
  width: 14px;
  height: 14px;
  color: var(--primary);
}

.example-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 18px;
  background: linear-gradient(135deg, var(--card) 0%, var(--primary-bg) 100%);
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 14px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 10px;
  text-align: left;
  opacity: 0;
  animation: itemFadeIn 0.4s ease forwards;
  position: relative;
  overflow: hidden;
}

.example-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 3px 0 0 3px;
  opacity: 0;
  transition: opacity 0.25s;
}

@keyframes itemFadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.example-item:hover {
  border-color: var(--primary-light);
  background: linear-gradient(135deg, var(--primary-bg) 0%, var(--card) 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.12);
}

.example-item:hover::before {
  opacity: 1;
}

.example-item:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.example-prefix {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--primary);
  color: white;
  font-size: 12px;
  font-weight: 700;
  border-radius: 6px;
  flex-shrink: 0;
}

.example-text {
  flex: 1;
  line-height: 1.5;
}

.example-arrow {
  width: 18px;
  height: 18px;
  color: var(--text-lighter);
  flex-shrink: 0;
  transition: all 0.25s;
}

.example-item:hover .example-arrow {
  color: var(--primary);
  transform: translateX(3px);
}

/* 消息 */
.message {
  display: flex;
  gap: 14px;
  margin-bottom: 24px;
  max-width: 900px;
  margin-left: auto;
  margin-right: auto;
  animation: msgIn 0.35s ease;
}

@keyframes msgIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.avatar svg {
  width: 20px;
  height: 20px;
}

.message.ai .avatar {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.message.user .avatar {
  background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
}

.message-body {
  display: flex;
  flex-direction: column;
  max-width: 75%;
}

.message.user .message-body {
  align-items: flex-end;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  padding: 0 4px;
}

.role-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-light);
}

.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message:hover .message-actions {
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  color: var(--text-lighter);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.action-btn:hover {
  background: var(--bg-soft);
  color: var(--primary);
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

.bubble {
  padding: 12px 16px;
  border-radius: var(--radius);
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
  position: relative;
}

.message.user .bubble {
  background: var(--user-bubble);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.28);
}

.message.ai .bubble {
  background: var(--card);
  color: var(--text);
  border: 1px solid var(--border-light);
  border-bottom-left-radius: 4px;
  border-top-left-radius: var(--radius-lg);
  border-top-right-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}

.bubble.streaming {
  min-height: 40px;
}

/* 打字动画 */
.typing {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 4px 0;
}

.typing-dot {
  width: 7px;
  height: 7px;
  background: var(--text-lighter);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

.cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: var(--primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

/* 参考文档 */
.sources {
  margin-top: 8px;
  max-width: 100%;
}

.sources-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-light);
  cursor: pointer;
  padding: 6px 10px;
  background: var(--bg-soft);
  border-radius: var(--radius-sm);
  transition: background 0.15s;
  width: fit-content;
}

.sources-header:hover {
  background: var(--primary-bg);
  color: var(--primary);
}

.sources-header svg {
  width: 14px;
  height: 14px;
}

.chevron {
  transition: transform 0.2s;
}

.chevron.open {
  transform: rotate(180deg);
}

.sources-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  background: var(--bg-soft);
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border-light);
  border-left: 3px solid var(--primary-light);
  transition: all 0.2s;
}

.source-item:hover {
  background: var(--primary-bg);
  border-left-color: var(--primary);
}

.source-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-light);
}

.source-badge {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25);
}

.source-file {
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-content {
  font-size: 12px;
  color: var(--text-light);
  line-height: 1.6;
  padding: 10px 12px;
  max-height: 160px;
  overflow-y: auto;
  white-space: pre-wrap;
}

/* 引用徽章 */
.citation-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  font-size: 10px;
  font-weight: 700;
  color: white;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  vertical-align: super;
  margin: 0 2px;
  line-height: 1;
  transition: all 0.15s;
  text-decoration: none;
  user-select: none;
}

.citation-badge:hover {
  background: var(--primary-dark);
  transform: scale(1.15);
}

/* 来源高亮动画（点击引用徽章时触发） */
.source-item.highlight {
  animation: sourceHighlight 2s ease;
}

@keyframes sourceHighlight {
  0%, 100% {
    background: var(--bg-soft);
    border-color: var(--border-light);
  }
  20%, 60% {
    background: var(--primary-bg);
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
  }
}

/* 输入区 */
.chat-input {
  background: var(--card);
  border-top: 1px solid var(--border);
  padding: 16px 32px;
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex-shrink: 0;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  box-shadow: 0 -4px 16px rgba(15, 23, 42, 0.04);
  position: relative;
  z-index: 2;
}

.input-wrapper {
  flex: 1;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: all 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--primary);
  background: var(--card);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.chat-input textarea {
  width: 100%;
  resize: none;
  border: none;
  background: transparent;
  padding: 12px 16px;
  font-size: 14px;
  font-family: inherit;
  max-height: 120px;
  min-height: 44px;
  line-height: 1.5;
  color: var(--text);
}

.chat-input textarea:focus {
  outline: none;
}

.chat-input textarea::placeholder {
  color: var(--text-lighter);
}

.clear-btn {
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--text-light);
  width: 44px;
  height: 44px;
  border-radius: var(--radius);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.clear-btn:hover {
  border-color: var(--danger);
  color: var(--danger);
  background: var(--danger-bg);
}

.clear-btn svg {
  width: 18px;
  height: 18px;
}

.send-btn {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  padding: 0 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  height: 44px;
  min-width: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.32);
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.42);
  transform: translateY(-1px);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0);
}

.send-btn:disabled {
  background: var(--text-lighter);
  cursor: not-allowed;
  box-shadow: none;
}

/* ===== 设置弹窗 ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal {
  background: var(--card);
  border-radius: var(--radius-lg);
  width: 420px;
  max-width: 90vw;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.25s ease;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-light);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
}

.close-btn:hover {
  background: var(--bg-soft);
  color: var(--text);
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

.modal-body {
  padding: 24px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  display: block;
  margin-bottom: 8px;
}

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: monospace;
  color: var(--text);
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-hint {
  font-size: 12px;
  color: var(--text-lighter);
  margin-top: 8px;
}

/* ===== 文档预览弹窗 ===== */
.preview-overlay {
  padding: 24px;
}

.preview-modal {
  background: var(--card);
  border-radius: var(--radius-lg);
  width: 90vw;
  max-width: 1100px;
  height: 90vh;
  max-height: 800px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.25s ease;
  overflow: hidden;
}

.preview-modal .modal-header h3 {
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.preview-action-btn {
  background: none;
  border: none;
  color: var(--text-light);
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
}

.preview-action-btn:hover {
  background: var(--primary-bg);
  color: var(--primary);
}

.preview-action-btn svg {
  width: 18px;
  height: 18px;
}

.preview-body {
  flex: 1;
  overflow: hidden;
  position: relative;
  background: var(--bg-soft);
}

.preview-loading,
.preview-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-light);
  font-size: 14px;
}

.preview-error svg {
  width: 48px;
  height: 48px;
  color: var(--danger);
  opacity: 0.7;
}

.preview-error p {
  font-size: 13px;
  color: var(--text-light);
}

.preview-fallback-btn {
  margin-top: 4px;
  padding: 8px 16px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.preview-fallback-btn:hover {
  background: var(--primary-dark);
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

.preview-markdown {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 32px 40px;
  background: var(--card);
  font-size: 14px;
  line-height: 1.7;
}

.preview-markdown h1,
.preview-markdown h2,
.preview-markdown h3 {
  margin-top: 24px;
  margin-bottom: 12px;
  font-weight: 600;
}

.preview-markdown h1 { font-size: 22px; }
.preview-markdown h2 { font-size: 18px; }
.preview-markdown h3 { font-size: 16px; }

.preview-markdown p {
  margin-bottom: 12px;
}

.preview-markdown code {
  background: var(--bg-soft);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: monospace;
}

.preview-markdown pre {
  background: var(--bg-soft);
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  overflow-x: auto;
  margin: 12px 0;
}

.preview-markdown pre code {
  background: none;
  padding: 0;
}

.preview-markdown table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.preview-markdown th,
.preview-markdown td {
  border: 1px solid var(--border);
  padding: 8px 12px;
  text-align: left;
}

.preview-markdown th {
  background: var(--bg-soft);
  font-weight: 600;
}

.preview-markdown blockquote {
  border-left: 3px solid var(--primary);
  padding-left: 12px;
  margin: 12px 0;
  color: var(--text-light);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }

  .header-title p {
    display: none;
  }

  .stat {
    display: none;
  }

  .sidebar {
    position: absolute;
    z-index: 50;
    height: 100%;
    box-shadow: var(--shadow-lg);
  }

  .sidebar.collapsed {
    width: 0;
  }

  .chat-messages {
    padding: 16px;
  }

  .chat-input {
    padding: 12px 16px;
  }

  .message-body {
    max-width: 85%;
  }
}
</style>
