<template>
  <div class="backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 p-6 shadow-lg">
    <h3 class="text-xl font-bold text-white mb-6 flex items-center">
      <CurrencyDollarIcon class="w-6 h-6 mr-3 text-neon-green" />
      Usage Analytics
    </h3>

    <div v-if="loading" class="flex items-center justify-center h-32">
      <div class="dot-typing-dark"></div>
    </div>

    <div v-else-if="usageData" class="space-y-4">
      <!-- Summary Cards -->
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white/5 rounded-lg p-4 border border-white/10">
          <div class="text-white/60 text-xs mb-1">Tokens Used (30 days)</div>
          <div class="text-white font-bold text-lg">{{ usageData.total_tokens.toLocaleString() }}</div>
        </div>
        <div class="bg-white/5 rounded-lg p-4 border border-white/10">
          <div class="text-white/60 text-xs mb-1">API Calls</div>
          <div class="text-white font-bold text-lg">{{ usageData.total_api_calls }}</div>
        </div>
      </div>

      <!-- Service Breakdown -->
      <div class="bg-white/5 rounded-lg p-4 border border-white/10">
        <div class="text-white font-medium text-sm mb-3">Service Breakdown</div>
        <div class="space-y-2">
          <div v-for="service in usageData.breakdown" :key="service._id" class="flex justify-between items-center">
            <span class="text-white/70 text-xs capitalize">{{ service._id }}</span>
            <span class="text-white text-xs font-medium">{{ service.api_calls }} calls</span>
          </div>
        </div>
      </div>

      <!-- Usage Tips -->
      <div class="bg-gradient-to-r from-electric-blue/20 to-neon-green/20 rounded-lg p-4 border border-electric-blue/30">
        <div class="text-white font-medium text-xs mb-2">💡 Usage Tips</div>
        <div class="text-white/80 text-xs">
          • Keep conversations focused for better responses<br>
          • Use specific stock symbols for accurate data<br>
          • All services are free to use!
        </div>
      </div>
    </div>

    <div v-else class="text-center text-white/60 py-8">
      <CurrencyDollarIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
      <p class="text-sm">No usage data available</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '../services/api.js'
import { CurrencyDollarIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'CostDashboard',
  components: {
    CurrencyDollarIcon
  },
  setup() {
    const usageData = ref(null)
    const loading = ref(true)

    const fetchUsageData = async () => {
      try {
        const response = await api.getUserUsage(30) // 30 days
        usageData.value = response.data
      } catch (error) {
        console.error('Failed to fetch usage data:', error)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchUsageData()
    })

    return {
      usageData,
      loading
    }
  }
}
</script>

<style scoped>
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
.dot-typing-dark::before {
  left: -12px;
  animation-delay: -200ms;
}
.dot-typing-dark::after {
  left: 12px;
  animation-delay: 200ms;
}
@keyframes dot-typing-wave {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(0.75); }
}
</style>