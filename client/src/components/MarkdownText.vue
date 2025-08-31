<template>
  <div class="text-white/90 whitespace-pre-wrap" v-html="formattedText"></div>
</template>

<script>
export default {
  name: 'MarkdownText',
  props: {
    text: {
      type: String,
      required: true
    }
  },
  computed: {
    formattedText() {
      return this.text
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-bold">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="text-white/80 italic">$1</em>')
        .replace(/`(.*?)`/g, '<code class="bg-white/10 px-1 rounded text-blue-200">$1</code>')
        .replace(/\n/g, '<br>')
    }
  }
}
</script>