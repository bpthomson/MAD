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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const password = ref('')
const error = ref('')

onMounted(() => {
    setTimeout(() => {
        if (window.initOrganicFlow) window.initOrganicFlow()
    }, 100)
})

const handleLogin = async () => {
    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: password.value })
        })
        const data = await res.json()
        if (data.success) {
            router.push('/')
        } else {
            error.value = data.error || 'Login failed'
        }
    } catch (e) {
        error.value = 'Network error'
    }
}
</script>
