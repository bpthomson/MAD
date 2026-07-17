<template>
  <div class="container py-5 d-flex justify-content-center align-items-center" style="min-height: 100vh;">
      <div class="card p-4 shadow-sm border-0" style="width: 100%; max-width: 400px; background: var(--card-bg); backdrop-filter: blur(8px);">
          <h3 class="text-center mb-4 text-dark" style="font-family: var(--font-hand); letter-spacing: 1px;">Private Diary</h3>
          
          <div v-if="error" class="alert alert-danger py-2 text-center border-0 shadow-sm">{{ error }}</div>
          
          <form @submit.prevent="handleLogin">
              <div class="mb-4">
                  <input type="password" v-model="password" class="form-control text-center shadow-sm" placeholder="Enter Password" required autofocus>
              </div>
              <button type="submit" class="btn btn-primary w-100 shadow-sm">Unlock</button>
          </form>
      </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const password = ref('')
const error = ref('')


const handleLogin = async () => {
    try {
        const { data } = await api.post('/api/login', { password: password.value })
        if (data.success) {
            router.push('/')
        } else {
            error.value = data.error || 'Login failed'
        }
    } catch (e) {
        if (e.response) {
            error.value = e.response.data.error || 'Login failed'
        } else {
            error.value = 'Network error'
        }
    }
}
</script>
