<template>
  <div class="fixed right-0 top-0 h-full w-80 backdrop-blur-md bg-white/5 border-l border-white/10 z-20 transform transition-transform duration-300"
       :class="{ 'translate-x-full': !isOpen, 'translate-x-0': isOpen }">
    
    <!-- Toggle Button -->
    <button 
      @click="toggleSidebar"
      class="absolute -left-12 top-1/2 transform -translate-y-1/2 w-10 h-16 bg-white/10 backdrop-blur-sm border border-white/20 rounded-l-xl flex items-center justify-center text-white hover:bg-white/20 transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
    >
      <span class="text-lg">{{ isOpen ? '→' : '←' }}</span>
    </button>

    <!-- Sidebar Content -->
    <div class="h-full overflow-y-auto overflow-x-hidden p-4 space-y-4 custom-scrollbar">
      <div class="text-white font-bold text-lg mb-4 flex items-center">
        <ChartBarIcon class="w-5 h-5 mr-2 text-stock-green" />
        Financial Dashboard
      </div>
      
      <MarketWidget />
      <NewsWidget />
      <PortfolioWidget />
      <StatsWidget :messages="messages" />
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import MarketWidget from './MarketWidget.vue'
import PortfolioWidget from './PortfolioWidget.vue'
import StatsWidget from './StatsWidget.vue'
import NewsWidget from './NewsWidget.vue'
import { ChartBarIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'Sidebar',
  components: {
    MarketWidget,
    PortfolioWidget,
    StatsWidget,
    NewsWidget,
    ChartBarIcon
  },
  props: {
    messages: Array
  },
  setup() {
    const isOpen = ref(false)

    const toggleSidebar = () => {
      isOpen.value = !isOpen.value
    }

    return {
      isOpen,
      toggleSidebar
    }
  }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 2px; }
</style>