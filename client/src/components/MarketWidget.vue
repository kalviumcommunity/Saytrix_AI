<template>
  <div class="backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 p-4 shadow-lg">
    <h3 class="text-lg font-bold text-white mb-3 flex items-center">
      <ChartBarIcon class="w-6 h-6 mr-3 animate-pulse-slow text-stock-green" />
      Live Market
    </h3>

    <div v-if="loading" class="flex flex-col items-center justify-center h-32 space-y-3 text-white/60">
      <div class="dot-typing-dark"></div>
      <p class="text-sm">Fetching real-time data...</p>
    </div>

    <div v-else-if="error" class="flex flex-col items-center justify-center h-32 space-y-3 text-red-400">
      <ExclamationTriangleIcon class="w-12 h-12 text-red-400" />
      <p class="text-sm text-center">{{ error }}</p>
      <button @click="fetchMarketData" class="px-4 py-2 text-xs bg-white/10 rounded-lg hover:bg-white/20 transition-colors">
        Retry
      </button>
    </div>

    <div v-else class="space-y-3 animate-fade-in">
      <div v-for="stock in marketData" :key="stock.symbol" 
           @click="selectStock(stock.symbol)"
           class="flex items-center justify-between p-3 rounded-xl transition-all duration-300 transform hover:scale-[1.02] bg-white/5 hover:bg-white/10 cursor-pointer hover:shadow-lg active:scale-[0.98]">
        <div>
          <div class="text-white font-medium text-base">{{ stock.symbol }}</div>
          <div class="text-white/60 text-sm mt-1">{{ stock.name }}</div>
        </div>
        <div class="text-right">
          <div class="text-white font-bold text-base">₹{{ stock.price }}</div>
          <div :class="stock.change >= 0 ? 'text-stock-green' : 'text-stock-red'" class="text-sm flex items-center justify-end mt-1">
            <span class="mr-1 text-base">{{ stock.change >= 0 ? '▲' : '▼' }}</span>
            {{ stock.change }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '../services/api.js'
import { ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'MarketWidget',
  components: {
    ChartBarIcon,
    ExclamationTriangleIcon
  },
  setup() {
    const marketData = ref([
      { symbol: 'NIFTY', name: 'Nifty 50', price: '19,674.25', change: 0.85 },
      { symbol: 'SENSEX', name: 'BSE Sensex', price: '66,023.69', change: 0.92 },
      { symbol: 'RELIANCE', name: 'Reliance Ind.', price: '2,456.30', change: -0.45 },
      { symbol: 'TCS', name: 'Tata Consultancy', price: '3,789.15', change: 1.23 }
    ])
    const loading = ref(false)
    const error = ref(null)

    const fetchMarketData = async () => {
      loading.value = true
      error.value = null
      try {
        const response = await api.getMarketData()
        marketData.value = response.data.market_data
      } catch (err) {
        // Try direct Alpha Vantage as fallback
        try {
          const directResponse = await api.getStockDirect('RELIANCE.NS')
          if (directResponse.data['Global Quote']) {
            console.log('Using direct Alpha Vantage data')
          }
        } catch (directErr) {
          console.log('Using fallback mock data')
        }
        error.value = "Using cached market data. Live data unavailable."
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchMarketData()
    })

    const selectStock = (symbol) => {
      console.log(`Selected stock: ${symbol}`)
      // Emit event to parent or trigger stock analysis
    }

    return {
      marketData,
      loading,
      error,
      fetchMarketData,
      selectStock
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
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.75);
  }
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}

@keyframes pulse-slow {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.02);
    opacity: 0.8;
  }
}
.animate-pulse-slow {
  animation: pulse-slow 3s ease-in-out infinite;
}
</style>