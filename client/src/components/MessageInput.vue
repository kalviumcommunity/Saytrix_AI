<template>
  <div class="w-full relative">
    <form @submit.prevent="sendMessage" class="flex items-center space-x-4 bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-2 shadow-lg transition-all duration-300">
      <input
        v-model="message"
        type="text"
        placeholder="Ask about stocks, portfolio, or market analysis..."
        class="flex-1 px-4 py-2 bg-transparent text-white placeholder-gray-400 focus:outline-none focus:ring-0"
        :disabled="disabled"
      />
      <button
        type="submit"
        :disabled="disabled || !message.trim()"
        class="flex items-center justify-center w-12 h-12 bg-blue-600 text-white rounded-lg shadow-md transition-all duration-200 
               hover:bg-blue-700 disabled:bg-white/10 disabled:text-gray-400 disabled:cursor-not-allowed
               active:scale-95 transform"
      >
        <svg
          v-if="disabled"
          class="animate-spin h-6 w-6 text-white/80"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>

        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </form>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'MessageInput',
  props: {
    disabled: Boolean
  },
  emits: ['send'],
  setup(props, { emit }) {
    const message = ref('')

    const sendMessage = () => {
      if (message.value.trim() && !props.disabled) {
        emit('send', message.value.trim())
        message.value = ''
      }
    }

    return {
      message,
      sendMessage
    }
  }
}
</script>