<template>
  <div class="backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 p-6 shadow-lg">
    <h3 class="text-xl font-bold text-white mb-6 flex items-center">
      <BoltIcon class="w-6 h-6 mr-3 text-neon-green" />
      Quick Actions
    </h3>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <button
        v-for="action in actions"
        :key="action.id"
        @click="$emit('action', action.id)"
        class="group relative overflow-hidden backdrop-blur-sm bg-gradient-to-br from-white/20 to-white/10 hover:from-white/30 hover:to-white/20 border border-white/20 rounded-xl p-4 transition-all duration-300 transform hover:scale-[1.03] hover:shadow-xl active:scale-[0.97]
               opacity-0 translate-y-4 animate-fade-in-up cursor-pointer"
        :style="{ 'animation-delay': action.delay }"
      >
        <div class="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-20 transition-opacity duration-300" :class="action.gradient"></div>
        
        <div class="absolute inset-0 rounded-xl bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

        <div class="relative z-10 text-center flex flex-col items-center justify-center">
          <component :is="action.icon" class="w-8 h-8 mb-2 transform group-hover:scale-110 transition-transform duration-300 text-white" />
          <div class="text-white font-medium text-sm">{{ action.label }}</div>
        </div>
      </button>
    </div>
  </div>
</template>

<script>
import { BoltIcon, ChartBarIcon, BriefcaseIcon, MagnifyingGlassIcon, NewspaperIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'QuickActions',
  components: {
    BoltIcon,
    ChartBarIcon,
    BriefcaseIcon,
    MagnifyingGlassIcon,
    NewspaperIcon
  },
  emits: ['action'],
  data() {
    return {
      actions: [
        { id: 'market-analysis', label: 'Market Analysis', icon: 'ChartBarIcon', gradient: 'from-electric-blue to-neon-green', delay: '0.1s' },
        { id: 'portfolio-review', label: 'Portfolio Review', icon: 'BriefcaseIcon', gradient: 'from-fuchsia to-electric-blue', delay: '0.2s' },
        { id: 'stock-search', label: 'Stock Search', icon: 'MagnifyingGlassIcon', gradient: 'from-neon-green to-electric-blue', delay: '0.3s' },
        { id: 'news-update', label: 'Market News', icon: 'NewspaperIcon', gradient: 'from-fuchsia to-neon-green', delay: '0.4s' }
      ]
    }
  }
}
</script>

<style scoped>
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fade-in-up 0.5s ease-out forwards; }

@keyframes spin-fast {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin-fast { animation: spin-fast 1s linear infinite; }
</style>