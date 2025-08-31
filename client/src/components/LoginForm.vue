<template>
  <div class="min-h-screen flex items-center justify-center" style="background: linear-gradient(135deg, #0D1117 0%, #1a1f2e 50%, #0D1117 100%);">
    <div class="backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 p-8 w-full max-w-md shadow-2xl">
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-gradient-to-r from-fuchsia to-electric-blue rounded-xl flex items-center justify-center mx-auto mb-4">
          <ChartBarIcon class="w-8 h-8 text-white" />
        </div>
        <h1 class="text-2xl font-bold text-white mb-2">Saytrix AI</h1>
        <p class="text-light-gray text-sm">Advanced Financial Intelligence</p>
      </div>

      <div class="flex mb-6 bg-white/5 rounded-lg p-1">
        <button 
          @click="isLogin = true"
          :class="isLogin ? 'bg-electric-blue text-white' : 'text-light-gray'"
          class="flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all"
        >
          Login
        </button>
        <button 
          @click="isLogin = false"
          :class="!isLogin ? 'bg-electric-blue text-white' : 'text-light-gray'"
          class="flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all"
        >
          Register
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div v-if="!isLogin">
          <input
            v-model="form.name"
            type="text"
            placeholder="Full Name"
            class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-light-gray focus:outline-none focus:border-electric-blue"
            required
          />
        </div>
        
        <div>
          <input
            v-model="form.email"
            type="email"
            placeholder="Email"
            class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-light-gray focus:outline-none focus:border-electric-blue"
            required
          />
        </div>
        
        <div>
          <input
            v-model="form.password"
            type="password"
            placeholder="Password"
            class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-light-gray focus:outline-none focus:border-electric-blue"
            required
          />
        </div>

        <div v-if="error" class="text-fuchsia text-sm text-center">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 bg-gradient-to-r from-electric-blue to-neon-green text-white rounded-lg font-medium hover:from-neon-green hover:to-electric-blue transition-all duration-200 disabled:opacity-50"
        >
          {{ loading ? 'Processing...' : (isLogin ? 'Login' : 'Create Account') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { authService } from '../services/auth.js'
import { ChartBarIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'LoginForm',
  components: {
    ChartBarIcon
  },
  emits: ['login-success'],
  setup(props, { emit }) {
    const isLogin = ref(true)
    const loading = ref(false)
    const error = ref('')
    
    const form = ref({
      name: '',
      email: '',
      password: ''
    })

    const handleSubmit = async () => {
      loading.value = true
      error.value = ''

      try {
        let result
        if (isLogin.value) {
          result = await authService.login(form.value.email, form.value.password)
        } else {
          result = await authService.register(form.value.email, form.value.password, form.value.name)
        }

        if (result.success) {
          emit('login-success', result.user)
        } else {
          error.value = result.error
        }
      } catch (err) {
        error.value = 'An error occurred. Please try again.'
      } finally {
        loading.value = false
      }
    }

    return {
      isLogin,
      loading,
      error,
      form,
      handleSubmit
    }
  }
}
</script>