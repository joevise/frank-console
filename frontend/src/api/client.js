import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('frank_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const authApi = {
  login: (username, password) => client.post('/auth/login', { username, password }),
  register: (username, password, display_name) =>
    client.post('/auth/register', { username, password, display_name }),
  me: () => client.get('/auth/me'),
}

export const watchlistApi = {
  list: () => client.get('/watchlist'),
  add: (stock_code, stock_name) => client.post('/watchlist', { stock_code, stock_name }),
  remove: (id) => client.delete(`/watchlist/${id}`),
}

export const reportsApi = {
  trigger: () => client.post('/reports/trigger'),
  today: () => client.get('/reports/today'),
  history: (stockCode, days = 7) => client.get(`/reports/history/${stockCode}`, { params: { days } }),
}

// ============================================================
// Session API（v3 多会话）
// ============================================================

export const chatApi = {
  // 会话管理
  sessions: () => client.get('/chat/sessions'),
  createSession: (title) => client.post('/chat/sessions', { title }),
  deleteSession: (id) => client.delete(`/chat/sessions/${id}`),
  renameSession: (id, title) => client.patch(`/chat/sessions/${id}`, { title }),
  sessionMessages: (id) => client.get(`/chat/sessions/${id}/messages`),

  // 聊天
  send: (message, conversation_id) => client.post('/chat/send', { message, conversation_id }),

  // 兼容旧 API
  conversations: () => client.get('/chat/conversations'),
  messages: (conversationId) => client.get(`/chat/conversations/${conversationId}/messages`),
}

// ============================================================
// 新三层架构数据接口
// ============================================================

export const marketApi = {
  overview: () => client.get('/market/overview'),
  mainlines: () => client.get('/market/mainlines'),
  signals: () => client.get('/market/signals'),
}

export const analyzeApi = {
  stock: (stock_code) => client.post('/analyze', { stock_code }),
}

export const briefApi = {
  generate: () => client.post('/brief/generate'),
  today: () => client.get('/brief/today'),
}

export default client
