import axios from 'axios'
import { authService } from './auth.js'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// Add auth interceptor
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('saytrix_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const api = {
  sendMessage: (message, conversationId) =>
    axios.post(`${API_BASE}/chat`, { message, conversation_id: conversationId }),
  
  quickAction: (action) =>
    axios.post(`${API_BASE}/quick-action`, { action }),
  
  getMarketData: () =>
    axios.get(`${API_BASE}/market-data`),
  
  analyzeStock: (symbol) =>
    axios.post(`${API_BASE}/stock-analysis`, { symbol }),
  
  calculatePortfolio: (holdings) =>
    axios.post(`${API_BASE}/portfolio-calculate`, { holdings }),
  
  getConversations: () =>
    axios.get(`${API_BASE}/conversations`),
  
  getConversationHistory: (conversationId) =>
    axios.get(`${API_BASE}/conversations/${conversationId}/history`),
  
  getUserUsage: (days = 30) =>
    axios.get(`${API_BASE}/analytics/usage?days=${days}`),
  
  // Direct Alpha Vantage calls (if needed)
  getStockDirect: (symbol) => {
    const apiKey = import.meta.env.VITE_ALPHA_VANTAGE_API_KEY
    if (apiKey) {
      return axios.get(`https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${apiKey}`)
    }
    return Promise.reject('No API key')
  }
}