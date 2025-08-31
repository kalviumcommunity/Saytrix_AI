<template>
  <MarkdownText :text="displayedText" />
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import MarkdownText from './MarkdownText.vue'

export default {
  name: 'TypewriterText',
  components: {
    MarkdownText
  },
  props: {
    text: {
      type: String,
      required: true
    },
    speed: {
      type: Number,
      default: 30
    }
  },
  setup(props) {
    const displayedText = ref('')
    let typewriterInterval = null

    const startTypewriter = () => {
      if (typewriterInterval) {
        clearInterval(typewriterInterval)
      }
      
      displayedText.value = ''
      let currentIndex = 0
      
      typewriterInterval = setInterval(() => {
        if (currentIndex < props.text.length) {
          displayedText.value = props.text.slice(0, currentIndex + 1)
          currentIndex++
        } else {
          clearInterval(typewriterInterval)
          typewriterInterval = null
        }
      }, props.speed)
    }

    watch(() => props.text, (newText) => {
      if (newText) {
        startTypewriter()
      }
    }, { immediate: true })

    onMounted(() => {
      startTypewriter()
    })

    return {
      displayedText
    }
  }
}
</script>