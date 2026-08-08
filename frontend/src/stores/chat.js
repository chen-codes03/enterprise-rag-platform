import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiService } from '../api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const documents = ref([])
  const serviceStatus = ref('connecting')
  const loading = ref(false)
  const deletingDocument = ref(null)
  // 多选模式：选中的对话 id 集合
  const selectedIds = ref(new Set())
  const selectMode = ref(false)

  async function checkHealth() {
    try {
      const data = await apiService.health()
      serviceStatus.value = data.status === 'ok' ? 'ok' : 'error'
    } catch {
      serviceStatus.value = 'error'
    }
  }

  async function loadDocuments() {
    try {
      const data = await apiService.listDocuments()
      documents.value = data.documents || []
    } catch {
      documents.value = []
    }
  }

  async function uploadFile(file) {
    const result = await apiService.uploadDocument(file)
    await loadDocuments()
    return result
  }

  async function deleteDocument(filename) {
    deletingDocument.value = filename
    try {
      const result = await apiService.deleteDocument(filename)
      await loadDocuments()
      return result
    } finally {
      deletingDocument.value = null
    }
  }

  /** 启动时从后端加载历史对话 */
  async function loadHistory() {
    try {
      const data = await apiService.listHistory()
      // 后端每条记录是一轮对话（question + answer），拆成两条前端消息
      const msgs = []
      for (const conv of data.conversations || []) {
        msgs.push({ id: conv.id, role: 'user', content: conv.question })
        msgs.push({
          id: conv.id,
          role: 'ai',
          content: conv.answer,
          sources: conv.sources || [],
          createdAt: conv.createdAt,
        })
      }
      messages.value = msgs
    } catch {
      messages.value = []
    }
  }

  /** 流式问答：先推送用户消息，再逐 token 填充 AI 回答，完成后保存到后端 */
  async function sendMessage(question) {
    loading.value = true
    messages.value.push({ role: 'user', content: question })

    const aiMsg = ref({ role: 'ai', content: '', sources: [], streaming: true })
    messages.value.push(aiMsg.value)

    try {
      await apiService.chatStream(question, {
        onSources: (sources) => {
          aiMsg.value.sources = sources || []
        },
        onToken: (token) => {
          aiMsg.value.content += token
        },
      })
      aiMsg.value.streaming = false
      if (!aiMsg.value.content) {
        aiMsg.value.content = '（无回答）'
      }

      // 问答完成，持久化到后端 SQLite
      try {
        const saved = await apiService.saveHistory(
          question,
          aiMsg.value.content,
          aiMsg.value.sources
        )
        // 给消息打上后端 id，用于后续删除
        const len = messages.value.length
        if (len >= 2) {
          messages.value[len - 2].id = saved.id
          messages.value[len - 1].id = saved.id
          messages.value[len - 1].createdAt = saved.createdAt
        }
      } catch {
        // 保存历史失败不影响问答本身
      }
    } catch (err) {
      aiMsg.value.streaming = false
      aiMsg.value.content = `❌ 请求失败：${err.message}`
    } finally {
      loading.value = false
    }
  }

  /** 删除单条对话（同时删用户消息和 AI 回答） */
  async function deleteConversation(id) {
    await apiService.deleteHistory(id)
    messages.value = messages.value.filter((m) => m.id !== id)
    selectedIds.value.delete(id)
  }

  /** 批量删除选中的对话 */
  async function batchDeleteSelected() {
    const ids = Array.from(selectedIds.value)
    if (!ids.length) return 0
    await apiService.batchDeleteHistory(ids)
    messages.value = messages.value.filter((m) => !selectedIds.value.has(m.id))
    const count = ids.length
    selectedIds.value = new Set()
    return count
  }

  /** 清空全部对话 */
  async function clearAllMessages() {
    await apiService.clearAllHistory()
    messages.value = []
    selectedIds.value = new Set()
  }

  // ===== 多选操作 =====
  function toggleSelectMode() {
    selectMode.value = !selectMode.value
    if (!selectMode.value) {
      selectedIds.value = new Set()
    }
  }

  function toggleSelect(id) {
    const s = new Set(selectedIds.value)
    if (s.has(id)) s.delete(id)
    else s.add(id)
    selectedIds.value = s
  }

  function selectAll() {
    const uniqueIds = new Set(
      messages.value.filter((m) => m.id).map((m) => m.id)
    )
    selectedIds.value = uniqueIds
  }

  return {
    messages,
    documents,
    serviceStatus,
    loading,
    deletingDocument,
    selectedIds,
    selectMode,
    checkHealth,
    loadDocuments,
    uploadFile,
    deleteDocument,
    loadHistory,
    sendMessage,
    deleteConversation,
    batchDeleteSelected,
    clearAllMessages,
    toggleSelectMode,
    toggleSelect,
    selectAll,
  }
})
