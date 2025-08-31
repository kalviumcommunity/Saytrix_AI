<template>
  <div class="backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 p-4 shadow-lg">
    <h3 class="text-lg font-bold text-white mb-4 flex items-center">
      <BriefcaseIcon class="w-6 h-6 mr-3 animate-pulse-fast text-electric-blue" />
      Portfolio Calculator
    </h3>
    
    <div class="space-y-3">
      <!-- Symbol Input -->
      <input
        v-model="newHolding.symbol"
        placeholder="Symbol (e.g., RELIANCE.NS)"
        class="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 text-xs"
      />
      
      <!-- Quantity and Price Row -->
      <div class="flex space-x-1">
        <input
          v-model.number="newHolding.quantity"
          type="number"
          placeholder="Qty"
          class="flex-1 px-2 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 text-xs min-w-0"
        />
        <input
          v-model.number="newHolding.avg_price"
          type="number"
          placeholder="Price"
          class="flex-1 px-2 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 text-xs min-w-0"
        />
      </div>
      
      <!-- Add Button -->
      <button
        @click="addHolding"
        class="w-full py-2.5 bg-gradient-to-r from-electric-blue to-neon-green text-white rounded-lg hover:from-neon-green hover:to-electric-blue text-xs font-medium transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl flex items-center justify-center"
      >
        <PlusIcon class="w-4 h-4 mr-1.5" /> Add Holding
      </button>
      
      <div v-if="holdings.length > 0" class="space-y-2">
        <!-- Holdings List -->
        <div class="max-h-32 overflow-y-auto space-y-1 custom-scrollbar">
          <div v-for="(holding, index) in holdings" :key="index" 
               class="flex flex-col p-2 bg-white/5 rounded-lg text-xs border border-white/10">
            <div class="flex justify-between items-center">
              <span class="text-white font-medium">{{ holding.symbol }}</span>
              <button @click="removeHolding(index)" class="text-red-400 hover:text-red-300 text-sm">×</button>
            </div>
            <div class="text-white/70 text-xs mt-1">
              {{ holding.quantity }} shares @ ₹{{ holding.avg_price }}
            </div>
          </div>
        </div>
        
        <!-- Calculate Button -->
        <button
          @click="calculatePortfolio"
          :disabled="calculating"
          class="w-full py-3 bg-gradient-to-r from-neon-green to-electric-blue text-white rounded-lg hover:from-electric-blue hover:to-neon-green disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg flex items-center justify-center"
        >
          <template v-if="calculating">
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
            Calculating...
          </template>
          <template v-else>
            <CalculatorIcon class="w-4 h-4 mr-2" /> 
            Calculate P&L
          </template>
        </button>
        
        <!-- Portfolio Summary -->
        <div v-if="portfolioResult" class="mt-4 space-y-3">
          <!-- Summary Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <CurrencyDollarIcon class="w-5 h-5 text-neon-green" />
              <span class="text-white font-semibold text-sm">Portfolio Summary</span>
            </div>
          </div>
          
          <!-- Investment Overview -->
          <div class="grid grid-cols-2 gap-2">
            <div class="bg-white/5 rounded-lg p-3 border border-white/10 text-center">
              <div class="text-white/60 text-xs mb-1">Invested</div>
              <div class="text-white font-bold text-sm">₹{{ portfolioResult.portfolio_summary.total_invested.toLocaleString() }}</div>
            </div>
            <div class="bg-white/5 rounded-lg p-3 border border-white/10 text-center">
              <div class="text-white/60 text-xs mb-1">Current Value</div>
              <div class="text-white font-bold text-sm">₹{{ portfolioResult.portfolio_summary.total_current_value.toLocaleString() }}</div>
            </div>
          </div>
          
          <!-- P&L Display -->
          <div class="p-4 rounded-xl border-2 transition-all duration-200" :class="portfolioResult.portfolio_summary.total_pnl >= 0 ? 'bg-stock-green/10 border-stock-green/30' : 'bg-stock-red/10 border-stock-red/30'">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-white/70 text-xs mb-1">Total P&L</div>
                <div class="flex items-baseline space-x-2">
                  <span :class="portfolioResult.portfolio_summary.total_pnl >= 0 ? 'text-stock-green' : 'text-stock-red'" class="font-bold text-lg">
                    {{ portfolioResult.portfolio_summary.total_pnl >= 0 ? '+' : '' }}₹{{ Math.abs(portfolioResult.portfolio_summary.total_pnl).toLocaleString() }}
                  </span>
                  <span :class="portfolioResult.portfolio_summary.total_pnl >= 0 ? 'text-stock-green' : 'text-stock-red'" class="text-sm font-medium">
                    ({{ portfolioResult.portfolio_summary.total_pnl_percent >= 0 ? '+' : '' }}{{ portfolioResult.portfolio_summary.total_pnl_percent.toFixed(2) }}%)
                  </span>
                </div>
              </div>
              <div class="text-3xl">
                {{ portfolioResult.portfolio_summary.total_pnl >= 0 ? '📈' : '📉' }}
              </div>
            </div>
          </div>
          
          <!-- Holdings Count -->
          <div class="text-center">
            <span class="text-white/60 text-xs">{{ portfolioResult.portfolio_summary.number_of_holdings }} Holdings</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { api } from '../services/api.js'
import { BriefcaseIcon, PlusIcon, CalculatorIcon, CurrencyDollarIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'PortfolioWidget',
  components: {
    BriefcaseIcon,
    PlusIcon,
    CalculatorIcon,
    CurrencyDollarIcon
  },
  setup() {
    const holdings = ref([])
    const newHolding = ref({ symbol: '', quantity: 0, avg_price: 0 })
    const calculating = ref(false)
    const portfolioResult = ref(null)

    const addHolding = () => {
      if (newHolding.value.symbol && newHolding.value.quantity > 0 && newHolding.value.avg_price > 0) {
        holdings.value.push({ ...newHolding.value })
        newHolding.value = { symbol: '', quantity: 0, avg_price: 0 }
      }
    }

    const removeHolding = (index) => {
      holdings.value.splice(index, 1)
      portfolioResult.value = null
    }

    const calculatePortfolio = async () => {
      calculating.value = true
      try {
        const response = await api.calculatePortfolio(holdings.value)
        portfolioResult.value = response.data
      } catch (error) {
        console.error('Portfolio calculation failed:', error)
      } finally {
        calculating.value = false
      }
    }

    return {
      holdings,
      newHolding,
      calculating,
      portfolioResult,
      addHolding,
      removeHolding,
      calculatePortfolio
    }
  }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 2px; }
</style>