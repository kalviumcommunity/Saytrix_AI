<template>
  <div class="backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 p-4 shadow-lg">
    <h3 class="text-lg font-bold text-white mb-4 flex items-center">
      <ChartBarIcon class="w-6 h-6 mr-3 animate-pulse-fast text-electric-blue" />
      Chat Stats
    </h3>
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-white/70">Messages</span>
        <span ref="messageCountRef" class="text-white text-xl font-bold animate-pop-in">
          {{ messageCount }}
        </span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-white/70">AI Responses</span>
        <span ref="aiResponsesRef" class="text-white text-xl font-bold animate-pop-in">
          {{ aiResponses }}
        </span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-white/70">Session Time</span>
        <span class="text-white font-bold text-lg">{{ sessionTime }}</span>
      </div>

      <div class="p-3 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/30">
        <div class="text-white/90 text-xs">
          <div class="font-bold mb-1 flex items-center">
            <LightBulbIcon class="w-4 h-4 mr-1 text-neon-green" />
            Pro Tip
          </div>
          <div class="text-white/70">
            Ask about specific stocks using their symbols (e.g., "RELIANCE.NS").
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import { ChartBarIcon, LightBulbIcon } from '@heroicons/vue/24/outline';

export default {
  name: 'StatsWidget',
  components: {
    ChartBarIcon,
    LightBulbIcon
  },
  props: {
    messages: Array
  },
  setup(props) {
    const startTime = ref(Date.now());
    const sessionTime = ref('0m 0s');
    let timerId = null;

    const messageCount = computed(() => props.messages.length);
    const aiResponses = computed(() => props.messages.filter(m => m.type === 'ai').length);

    const updateSessionTime = () => {
      const elapsed = Math.floor((Date.now() - startTime.value) / 1000);
      const minutes = Math.floor(elapsed / 60);
      const seconds = elapsed % 60;
      sessionTime.value = `${minutes}m ${seconds}s`;
    };

    onMounted(() => {
      timerId = setInterval(updateSessionTime, 1000);
    });

    onUnmounted(() => {
      clearInterval(timerId);
    });

    const messageCountRef = ref(null);
    const aiResponsesRef = ref(null);

    watch(messageCount, (newValue, oldValue) => {
      if (newValue > oldValue && messageCountRef.value) {
        messageCountRef.value.classList.add('animate-pop-in');
        messageCountRef.value.addEventListener('animationend', () => {
          messageCountRef.value.classList.remove('animate-pop-in');
        });
      }
    });

    watch(aiResponses, (newValue, oldValue) => {
      if (newValue > oldValue && aiResponsesRef.value) {
        aiResponsesRef.value.classList.add('animate-pop-in');
        aiResponsesRef.value.addEventListener('animationend', () => {
          aiResponsesRef.value.classList.remove('animate-pop-in');
        });
      }
    });

    return {
      messageCount,
      aiResponses,
      sessionTime,
      messageCountRef,
      aiResponsesRef
    };
  }
}
</script>

<style scoped>
@keyframes pop-in {
  0% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(1); }
}
.animate-pop-in { animation: pop-in 0.3s ease-out; }

@keyframes pulse-fast {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
}
.animate-pulse-fast { animation: pulse-fast 1.5s ease-in-out infinite; }
</style>