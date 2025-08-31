<template>
  <div class="backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 p-4 shadow-lg">
    <h3 class="text-lg font-bold text-white mb-4 flex items-center">
      <NewspaperIcon class="w-6 h-6 mr-3 animate-pulse-fast text-electric-blue" />
      Latest News
    </h3>
    
    <div v-if="loading" class="flex items-center justify-center h-32 text-white/60">
      <div class="dot-typing-dark"></div>
      <span class="ml-3 text-sm">Loading news...</span>
    </div>
    
    <div v-else-if="error" class="text-red-400 text-sm text-center py-8">
      {{ error }}
    </div>
    
    <div v-else-if="news.length > 0" class="space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
      <div v-for="(item, index) in news" :key="index" 
           class="p-3 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all duration-200 cursor-pointer transform hover:scale-[1.02] active:scale-[0.98] hover:shadow-lg"
           @click="openNews(item.url)">
        <div class="text-white text-xs font-medium mb-1 line-clamp-2">
          {{ item.title }}
        </div>
        <div class="text-white/60 text-xs">
          {{ item.source }} • {{ formatDate(item.published) }}
        </div>
      </div>
    </div>
    
    <div v-else class="text-white/60 text-sm text-center py-8">
      No news available
    </div>
    
    <button 
      @click="fetchNews"
      :disabled="loading"
      class="w-full mt-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-xs flex items-center justify-center"
    >
      <ArrowPathIcon class="w-4 h-4 mr-2" :class="{ 'animate-spin': loading }" />
      {{ loading ? 'Loading...' : 'Refresh News' }}
    </button>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '../services/api.js'
import { NewspaperIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'NewsWidget',
  components: {
    NewspaperIcon,
    ArrowPathIcon
  },
  setup() {
    const news = ref([])
    const loading = ref(false)
    const error = ref(null)

    const fetchNews = async () => {
      loading.value = true
      error.value = null
      try {
        const response = await api.quickAction('news-update')
        // Mock financial news data
        news.value = [
          {
            title: 'Nifty 50 Hits New All-Time High Above 22,000',
            source: 'Economic Times',
            published: '2 hours ago',
            url: '#'
          },
          {
            title: 'RBI Maintains Repo Rate at 6.5% in Policy Review',
            source: 'Business Standard', 
            published: '4 hours ago',
            url: '#'
          },
          {
            title: 'IT Stocks Rally: TCS, Infosys Gain 3% Each',
            source: 'Moneycontrol',
            published: '6 hours ago', 
            url: '#'
          },
          {
            title: 'FII Inflows Cross ₹5,000 Crore This Week',
            source: 'Mint',
            published: '8 hours ago',
            url: '#'
          },
          {
            title: 'Banking Stocks Outperform Broader Market',
            source: 'CNBC TV18',
            published: '10 hours ago',
            url: '#'
          }
        ]
      } catch (err) {
        error.value = 'Failed to load news'
      } finally {
        loading.value = false
      }
    }

    const openNews = (url) => {
      if (url && url !== '#') {
        window.open(url, '_blank')
      }
    }

    const formatDate = (dateString) => {
      // Handle relative time strings like "2 hours ago"
      if (typeof dateString === 'string' && dateString.includes('ago')) {
        return dateString
      }
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }

    onMounted(() => {
      fetchNews()
    })

    return {
      news,
      loading,
      error,
      fetchNews,
      openNews,
      formatDate
    }
  }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 2px; }

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.dot-typing-dark { 
  position: relative; 
  width: 8px; 
  height: 8px; 
  border-radius: 50%; 
  background-color: #a0a0a0; 
  animation: 900ms ease-in-out infinite both dot-typing-wave; 
}
.dot-typing-dark::before, .dot-typing-dark::after { 
  content: ''; 
  display: inline-block; 
  position: absolute; 
  top: 0; 
  width: 8px; 
  height: 8px; 
  border-radius: 50%; 
  background-color: #a0a0a0; 
  animation: 900ms ease-in-out infinite both dot-typing-wave; 
}
.dot-typing-dark::before { left: -12px; animation-delay: -200ms; }
.dot-typing-dark::after { left: 12px; animation-delay: 200ms; }
@keyframes dot-typing-wave {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(0.75); }
}

@keyframes pulse-fast {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
}
.animate-pulse-fast { animation: pulse-fast 1.5s ease-in-out infinite; }
</style>