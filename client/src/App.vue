<template>
  <!-- Login Form -->
  <LoginForm v-if="!isAuthenticated" @login-success="handleLoginSuccess" />
  
  <!-- Main App -->
  <div v-else class="min-h-screen relative overflow-hidden text-white font-sans" style="background: linear-gradient(135deg, #0D1117 0%, #1a1f2e 50%, #0D1117 100%);">
    <!-- Animated Background -->
    <div class="absolute inset-0 opacity-20">
      <div class="absolute top-0 -left-4 w-72 h-72 bg-fuchsia-400 rounded-full mix-blend-multiply filter blur-xl animate-blob"></div>
      <div class="absolute top-0 -right-4 w-72 h-72 bg-sky-400 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000"></div>
      <div class="absolute -bottom-8 left-20 w-72 h-72 bg-indigo-400 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000"></div>
    </div>
    
    <!-- Header -->
    <header class="relative z-10 backdrop-blur-md bg-white/5 border-b border-white/10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-r from-fuchsia to-electric-blue rounded-xl flex items-center justify-center animate-pulse-fast">
              <ChartBarIcon class="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 class="text-xl font-bold bg-gradient-to-r from-white to-electric-blue bg-clip-text text-transparent">Saytrix AI</h1>
              <p class="text-light-gray text-xs hidden sm:block">Advanced Financial Intelligence</p>
            </div>
          </div>

          <!-- Navigation -->
          <nav class="hidden md:flex items-center space-x-6">
            <button class="text-white/70 hover:text-white transition-colors text-sm font-medium">Dashboard</button>
            <button class="text-white/70 hover:text-white transition-colors text-sm font-medium">Portfolio</button>
            <button class="text-white/70 hover:text-white transition-colors text-sm font-medium">Analytics</button>
          </nav>

          <!-- User Menu -->
          <div class="flex items-center space-x-4">
            <div class="hidden lg:flex items-center space-x-2 px-3 py-1 bg-white/5 rounded-full border border-white/10">
              <div class="w-2 h-2 bg-stock-green rounded-full animate-pulse-slow"></div>
              <span class="text-white/70 text-xs font-medium">Live Data</span>
            </div>
            
            <button @click="toggleUserMenu" class="flex items-center space-x-3 px-3 py-2 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all duration-200">
              <div class="w-8 h-8 bg-gradient-to-r from-electric-blue to-neon-green rounded-full flex items-center justify-center">
                <UserIcon class="w-5 h-5 text-white" />
              </div>
              <div class="hidden sm:block text-left">
                <div class="text-white text-sm font-medium">{{ user?.name || 'User' }}</div>
                <div class="text-light-gray text-xs">{{ user?.email }}</div>
              </div>
              <ChevronDownIcon class="w-4 h-4 text-white/70 transition-transform duration-200" :class="{ 'rotate-180': showUserMenu }" />
            </button>
          </div>
        </div>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="relative z-10 max-w-6xl mx-auto py-6 px-4 sm:px-6 min-h-[calc(100vh-80px)] transition-all duration-300" :class="{ 'pr-80': sidebarOpen }">
      <div class="flex flex-col min-h-[600px] space-y-6">
        <div class="flex-grow overflow-y-auto">
          <ChatHistory :messages="messages" :loading="loading" />
        </div>
        <div class="space-y-4">
          <QuickActions @action="handleQuickAction" />
          <MessageInput @send="handleMessage" :disabled="loading" />
        </div>
      </div>
    </main>
    
    <!-- Sidebar -->
    <Sidebar :messages="messages" @sidebar-toggle="handleSidebarToggle" />
    
    <!-- User Dropdown -->
    <Teleport to="body">
      <div v-if="showUserMenu" class="fixed top-16 right-4 w-48 bg-deep-charcoal/95 backdrop-blur-md rounded-lg border border-white/20 shadow-xl py-2 z-[9999]">
        <div class="px-4 py-2 border-b border-white/10">
          <div class="text-white text-sm font-medium">{{ user?.name }}</div>
          <div class="text-light-gray text-xs">{{ user?.email }}</div>
        </div>
        <button class="w-full text-left px-4 py-2 text-white/70 hover:text-white hover:bg-white/5 transition-colors text-sm">Settings</button>
        <button class="w-full text-left px-4 py-2 text-white/70 hover:text-white hover:bg-white/5 transition-colors text-sm">Analytics</button>
        <div class="border-t border-white/10 mt-2 pt-2">
          <button @click="handleLogout" class="w-full text-left px-4 py-2 text-fuchsia hover:text-white hover:bg-fuchsia/10 transition-colors text-sm">Logout</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import ChatHistory from './components/ChatHistory.vue'
import MessageInput from './components/MessageInput.vue'
import QuickActions from './components/QuickActions.vue'
import Sidebar from './components/Sidebar.vue'
import LoginForm from './components/LoginForm.vue'
import { api } from './services/api.js'
import { authService } from './services/auth.js'
import { ChartBarIcon, UserIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'App',
  components: {
    ChatHistory, MessageInput, QuickActions, Sidebar, LoginForm,
    ChartBarIcon, UserIcon, ChevronDownIcon
  },
  setup() {
    const messages = ref([])
    const loading = ref(false)
    const user = ref(null)
    const conversationId = ref(null)
    const isAuthenticated = ref(false)
    const showUserMenu = ref(false)
    const sidebarOpen = ref(false)

    onMounted(async () => {
      if (authService.isAuthenticated()) {
        const tokenValid = await authService.verifyToken()
        if (tokenValid) {
          user.value = authService.getUser()
          isAuthenticated.value = true
          initializeChat()
        } else {
          authService.logout()
        }
      }
      document.addEventListener('click', closeUserMenu)
    })

    const initializeChat = () => {
      messages.value.push({
        type: 'ai',
        content: `Hello ${user.value?.name || 'there'}! I'm Saytrix AI, your personal financial assistant. I can help with stock analysis, portfolio management, and market insights. What would you like to know?`,
        timestamp: new Date()
      })
    }

    const handleMessage = async (message) => {
      messages.value.push({ type: 'user', content: message, timestamp: new Date() })
      loading.value = true

      try {
        const response = await api.sendMessage(message, conversationId.value)
        conversationId.value = response.data.conversation_id
        messages.value.push({
          type: 'ai',
          content: response.data.response,
          timestamp: new Date(response.data.timestamp)
        })
      } catch (error) {
        messages.value.push({
          type: 'error',
          content: 'Failed to get response. Please try again.',
          timestamp: new Date()
        })
      } finally {
        loading.value = false
      }
    }

    const handleQuickAction = async (action) => {
      messages.value.push({
        type: 'user',
        content: `Quick Action: ${action}`,
        timestamp: new Date()
      })

      loading.value = true
      try {
        const response = await api.quickAction(action)
        messages.value.push({
          type: 'ai',
          content: response.data.response,
          timestamp: new Date()
        })
      } catch (error) {
        messages.value.push({
          type: 'error',
          content: 'Quick action failed. Please try again.',
          timestamp: new Date()
        })
      } finally {
        loading.value = false
      }
    }

    const handleLoginSuccess = (userData) => {
      user.value = userData
      isAuthenticated.value = true
      initializeChat()
    }

    const handleLogout = () => {
      authService.logout()
      user.value = null
      isAuthenticated.value = false
      messages.value = []
      conversationId.value = null
      showUserMenu.value = false
    }

    const toggleUserMenu = () => {
      showUserMenu.value = !showUserMenu.value
    }

    const closeUserMenu = (event) => {
      if (!event.target.closest('.relative')) {
        showUserMenu.value = false
      }
    }

    const handleSidebarToggle = (isOpen) => {
      sidebarOpen.value = isOpen
    }

    return {
      messages, loading, user, isAuthenticated, showUserMenu, sidebarOpen,
      handleMessage, handleQuickAction, handleLoginSuccess, handleLogout,
      toggleUserMenu, handleSidebarToggle
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', system-ui, sans-serif; }

@keyframes blob {
  0% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0px, 0px) scale(1); }
}

.animate-blob { animation: blob 7s infinite; }
.animation-delay-2000 { animation-delay: 2s; }
.animation-delay-4000 { animation-delay: 4s; }

@keyframes pulse-fast {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
}

.animate-pulse-fast { animation: pulse-fast 1.5s ease-in-out infinite; }

@keyframes pulse-slow {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.02); opacity: 0.8; }
}

.animate-pulse-slow { animation: pulse-slow 3s ease-in-out infinite; }
</style>