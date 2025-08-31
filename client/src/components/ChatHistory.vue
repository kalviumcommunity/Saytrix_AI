<template>
  <div class="backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 p-4 h-[400px] flex flex-col space-y-3 custom-scrollbar overflow-y-auto">
    <div v-if="messages.length === 0" class="flex-grow flex flex-col items-center justify-center text-white/60 text-center py-16">
      <div class="mb-4 animate-bounce-slow">
        <CpuChipIcon class="w-16 h-16 text-neon-green mx-auto" />
      </div>
      <p class="text-2xl font-semibold bg-gradient-to-r from-blue-200 to-purple-200 bg-clip-text text-transparent">
        Start your financial journey
      </p>
      <p class="text-sm mt-2 text-white/40">Ask about stocks, portfolios, or market insights</p>
    </div>
    
    <div v-for="(message, index) in messages" :key="index" :class="messageAlignmentClass(message.type)">
      <div :class="messageBubbleClass(message.type)" class="max-w-[80%] rounded-2xl p-4 transition-all duration-300 transform scale-95 opacity-0 animate-fade-in-up">
        <div class="flex items-start space-x-4">
          <div v-if="message.type === 'ai'" :class="avatarClass(message.type)">
            <CpuChipIcon class="w-6 h-6" />
          </div>
          <div class="flex-1 min-w-0">
            <TypewriterText 
              v-if="message.type === 'ai'"
              :text="message.content"
              :speed="15"
            />
            <div v-else class="text-white/90 whitespace-pre-wrap">
              {{ message.content }}
            </div>
            <div :class="messageTimeClass(message.type)">
              {{ formatTime(message.timestamp) }}
            </div>
          </div>
          <div v-if="message.type === 'user'" :class="avatarClass(message.type)">
            <UserIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="flex items-center space-x-3 text-white/70">
      <div class="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center">
        <div class="dot-typing-dark"></div>
      </div>
      <span class="text-sm">Saytrix AI is analyzing...</span>
    </div>
  </div>
</template>

<script>
import TypewriterText from './TypewriterText.vue'
import { CpuChipIcon, UserIcon } from '@heroicons/vue/24/solid'

export default {
  name: 'ChatHistory',
  components: {
    TypewriterText,
    CpuChipIcon,
    UserIcon
  },
  props: {
    messages: Array,
    loading: Boolean
  },
  methods: {
    messageBubbleClass(type) {
      const base = 'backdrop-blur-sm p-4 rounded-xl shadow-lg';
      const user = 'bg-cyan-500/20 border border-cyan-400/30';
      const ai = 'bg-green-500/20 border border-green-400/30';
      const error = 'bg-red-600/30 border border-red-400/30';
      return `${base} ${type === 'user' ? user : type === 'ai' ? ai : error}`;
    },
    messageAlignmentClass(type) {
      return {
        'user': 'flex justify-end',
        'ai': 'flex justify-start',
        'error': 'flex justify-start'
      }[type];
    },
    avatarClass(type) {
      const base = 'w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-md flex-shrink-0';
      const user = 'bg-gradient-to-r from-electric-blue to-neon-green';
      const ai = 'bg-gradient-to-r from-fuchsia to-electric-blue animate-pulse-slow';
      return `${base} ${type === 'user' ? user : ai}`;
    },
    messageTimeClass(type) {
      return `text-xs mt-2 ${type === 'user' ? 'text-right' : 'text-left'} text-white/40`;
    },
    formatTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
  },
  updated() {
    this.$nextTick(() => {
      const container = this.$el;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    });
  }
}
</script>

<style scoped>
/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }
.custom-scrollbar { scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, 0.2) rgba(255, 255, 255, 0.05); }

/* New, subtle animations for the refined design */
@keyframes bounce-slow {
  0%, 100% { transform: translateY(-5%); animation-timing-function: cubic-bezier(0.8, 0, 1, 1); }
  50% { transform: translateY(0); animation-timing-function: cubic-bezier(0, 0, 0.2, 1); }
}
.animate-bounce-slow { animation: bounce-slow 2s infinite; }

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.animate-fade-in-up { animation: fade-in-up 0.5s ease-out forwards; }

/* Typing Indicator from Pure CSS */
.dot-typing-dark { position: relative; width: 8px; height: 8px; border-radius: 50%; background-color: #a0a0a0; animation: 900ms ease-in-out infinite both dot-typing-wave; }
.dot-typing-dark::before, .dot-typing-dark::after { content: ''; display: inline-block; position: absolute; top: 0; width: 8px; height: 8px; border-radius: 50%; background-color: #a0a0a0; animation: 900ms ease-in-out infinite both dot-typing-wave; }
.dot-typing-dark::before { left: -12px; animation-delay: -200ms; }
.dot-typing-dark::after { left: 12px; animation-delay: 200ms; }
@keyframes dot-typing-wave {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(0.75); }
}
</style>