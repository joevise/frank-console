import axios from "axios";

const BASE = "/api";
const client = axios.create({ baseURL: BASE, timeout: 30000 });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("frank_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("frank_token");
      window.location.hash = "#/login";
    }
    return Promise.reject(err);
  }
);

/* ------------------------------------------------------------------ */

export const authApi = {
  register: (username, password) =>
    client.post("/auth/register", { username, password }),
  login: (username, password) =>
    client.post("/auth/login", { username, password }),
  me: () => client.get("/auth/me"),
};

export const chatApi = {
  send: (message, conversationId) =>
    client.post("/chat/send", { message, conversation_id: conversationId }),
  conversations: (source) =>
    client.get("/chat/conversations", {
      params: source ? { source } : {},
    }),
  messages: (id) => client.get(`/chat/conversations/${id}/messages`),
  deleteConversation: (id) => client.delete(`/chat/conversations/${id}`),
};

export const watchlistApi = {
  list: () => client.get("/watchlist"),
  add: (stockCode, stockName, mainline, action, note) =>
    client.post("/watchlist", {
      stock_code: stockCode,
      stock_name: stockName,
      mainline,
      action,
      note,
    }),
  update: (id, data) => client.put(`/watchlist/${id}`, data),
  remove: (id) => client.delete(`/watchlist/${id}`),
};

export const marketApi = {
  overview: () => client.get("/market/overview"),
  mainlines: () => client.get("/market/mainlines"),
  signals: () => client.get("/market/signals"),
};

export const briefApi = {
  generate: () => client.post("/brief/generate", {}, { timeout: 120000 }),
  today: () => client.get("/brief/today"),
  history: (days = 30) =>
    client.get("/brief/history", { params: { days } }),
  byId: (id) => client.get(`/brief/${id}`),
};

export const analyzeApi = {
  stock: (code) => client.get(`/analyze/stock/${code}`),
};

export default client;
