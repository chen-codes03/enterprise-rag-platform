import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('apiKey') || 'sk-rag-demo-key-change-me'
  config.headers['X-API-Key'] = apiKey
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

/**
 * SSE 流式问答：逐 token 读取回答。
 * 后端先推送 sources 事件，再逐 token 推送 data，最后 [DONE]。
 */
async function chatStream(question, { onSources, onToken } = {}) {
  const apiKey = localStorage.getItem('apiKey') || 'sk-rag-demo-key-change-me'
  const resp = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    },
    body: JSON.stringify({ question }),
  })

  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({}))
    throw new Error(detail.detail || `请求失败 (${resp.status})`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // 按 SSE 协议拆分（双换行分隔事件）
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''

    for (const block of blocks) {
      const lines = block.split('\n')
      let dataLine = ''
      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          dataLine = line.slice(5).trim()
        }
      }

      if (currentEvent === 'sources' && dataLine) {
        try {
          const sources = JSON.parse(dataLine)
          onSources?.(sources)
        } catch {
          /* 忽略解析错误 */
        }
      } else if (dataLine && dataLine !== '[DONE]') {
        onToken?.(dataLine)
      }
      currentEvent = ''
    }
  }
}

export const apiService = {
  health: () => api.get('/health'),

  uploadDocument: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  listDocuments: () => api.get('/api/v1/documents/list'),

  deleteDocument: (filename) => api.delete(`/api/v1/documents/${encodeURIComponent(filename)}`),

  // 拼接带 API Key 的下载 URL（用 fetch 触发浏览器下载）
  async downloadDocument(filename) {
    const apiKey = localStorage.getItem('apiKey') || 'sk-rag-demo-key-change-me'
    const url = `/api/v1/documents/${encodeURIComponent(filename)}/download`
    const resp = await fetch(url, { headers: { 'X-API-Key': apiKey } })
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({}))
      throw new Error(detail.detail || `下载失败 (${resp.status})`)
    }
    const blob = await resp.blob()
    // 触发浏览器下载
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(objectUrl)
  },

  // 预览：返回拼接好 API Key 的 URL，供 iframe 直接加载（PDF 场景）
  getPreviewUrl(filename) {
    const apiKey = localStorage.getItem('apiKey') || 'sk-rag-demo-key-change-me'
    // iframe 不能加自定义 header，因此用 query 参数携带 key（后端 verify_api_key 兼容）
    return `/api/v1/documents/${encodeURIComponent(filename)}/preview?api_key=${encodeURIComponent(apiKey)}`
  },

  // 预览：Markdown 文本内容（用 axios 拉取，前端 marked 渲染）
  async fetchMarkdownContent(filename) {
    const apiKey = localStorage.getItem('apiKey') || 'sk-rag-demo-key-change-me'
    const url = `/api/v1/documents/${encodeURIComponent(filename)}/preview`
    const resp = await fetch(url, { headers: { 'X-API-Key': apiKey } })
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({}))
      throw new Error(detail.detail || `预览失败 (${resp.status})`)
    }
    return await resp.text()
  },

  chat: (question) => api.post('/api/v1/chat', { question }),

  chatStream,

  // ===== 对话历史 =====
  listHistory: () => api.get('/api/v1/history'),

  saveHistory: (question, answer, sources) =>
    api.post('/api/v1/history', { question, answer, sources }),

  deleteHistory: (id) => api.delete(`/api/v1/history/${id}`),

  batchDeleteHistory: (ids) =>
    api.delete('/api/v1/history', { data: { ids } }),

  clearAllHistory: () => api.delete('/api/v1/history/all'),

  setApiKey(key) {
    localStorage.setItem('apiKey', key)
  },
}
