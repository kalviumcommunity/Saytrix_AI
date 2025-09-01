import axios from 'axios'
import { authService } from './auth.js'

const API_BASE = import.meta.env.VITE_API_BASE_URL

// Add auth interceptor
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('saytrix_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const api = {
  // Authentication
  login: (email, password) =>
    axios.post(`${API_BASE}/auth/login`, { email, password }),
  
  register: (email, password, name) =>
    axios.post(`${API_BASE}/auth/register`, { email, password, name }),
  
  verifyToken: () =>
    axios.get(`${API_BASE}/auth/verify`),
  
  // Chat
  sendMessage: (message, conversationId) =>
    axios.post(`${API_BASE}/chat`, { message, conversation_id: conversationId }),
  
  quickAction: (action) =>
    axios.post(`${API_BASE}/quick-action`, { action }),
  
  clearMode: () =>
    axios.post(`${API_BASE}/clear-mode`),
  
  // Market Data
  getMarketData: () =>
    axios.get(`${API_BASE}/market-data`),
  
  analyzeStock: (symbol) =>
    axios.post(`${API_BASE}/stock-analysis`, { symbol }),
  
  // Portfolio
  calculatePortfolio: (holdings) =>
    axios.post(`${API_BASE}/portfolio-calculate`, { holdings }),
  
  // Analytics
  getUserUsage: (days = 30) =>
    axios.get(`${API_BASE}/analytics/usage?days=${days}`),
  
  // Direct stock data (fallback)
  getStockDirect: async (symbol) => {
    try {
      const response = await axios.post(`${API_BASE}/stock-analysis`, { symbol })
      return response
    } catch (error) {
      console.error('Stock API error:', error)
      throw error
    }
  }
}