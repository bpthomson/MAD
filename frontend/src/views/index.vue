<template>
  <div class="container py-5">
      <div class="d-flex justify-content-between align-items-baseline mb-4">
          <div>
              <h2 class="mb-0">{{ is_edit ? 'Edit Entry' : 'My Diary' }}</h2>
              <div class="text-muted small mt-1" style="font-family: var(--font-hand);">
                  {{ currentDate }}
              </div>
          </div>
          <router-link to="/history" class="btn btn-outline-secondary btn-sm">History</router-link>
      </div>
      
      <div v-if="error" class="alert alert-danger shadow-sm border-0 rounded-2 mb-3">
          {{ error }}
      </div>

      <div class="row g-4">
          <div class="col-lg-8">
              <form @submit.prevent="submitForm">
                  <div class="d-flex align-items-center gap-4 mb-2">
                      <div class="d-flex align-items-center gap-2">
                          <label for="dateInput" class="text-muted small" style="font-family: var(--font-hand);">Date:</label>
                          <input type="date" v-model="form.date" id="dateInput" class="custom-date-input py-1 px-2" style="font-size: 1rem;" required>
                      </div>
                      <div class="d-flex align-items-center gap-2">
                          <label for="modelSelect" class="text-muted small" style="font-family: var(--font-hand);">Model:</label>
                          <select v-model="form.model" id="modelSelect" class="custom-model-select shadow-sm" style="max-width: 200px;">
                              <option v-if="availableModels.length === 0" value="">Loading models...</option>
                              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
                          </select>
                      </div>
                  </div>

                  <div class="mb-3">
                      <textarea class="form-control shadow-sm" v-model="form.content" rows="9" 
                                placeholder="Write freely..." required></textarea>
                  </div>
                  
                  <div class="d-flex gap-2">
                      <button type="submit" v-if="!loading" class="btn btn-primary px-5 shadow-sm">
                          {{ is_edit ? 'Update & Polish' : 'Polish Entry' }}
                      </button>
                      <router-link v-if="is_edit && !loading" to="/history" class="btn btn-outline-secondary">Cancel</router-link>
                      <button class="btn btn-primary px-5 shadow-sm" v-if="loading" type="button" disabled>Analyzing...</button>
                  </div>
              </form>
          </div>

          <div class="col-lg-4">
              <CalendarWidget v-model="form.date" />
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'
import CalendarWidget from '../components/CalendarWidget.vue'

const router = useRouter()
const route = useRoute()

const currentDate = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
const is_edit = ref(false)
const error = ref('')
const loading = ref(false)
const availableModels = ref([])

const form = reactive({
    date: new Date().toISOString().split('T')[0],
    content: '',
    old_timestamp: '',
    model: ''
})

onMounted(async () => {
    // Fetch models
    try {
        const { data: mData } = await api.get('/api/models')
        availableModels.value = mData.models || []
        if (mData.default) {
            form.model = mData.default
        } else if (availableModels.value.length > 0) {
            form.model = availableModels.value[0]
        }
    } catch (e) {
        console.error("Failed to load models", e)
    }

    if (route.name === 'edit' && route.params.timestamp) {
        is_edit.value = true
        form.old_timestamp = route.params.timestamp
        try {
            const { data } = await api.get(`/api/diary/${route.params.timestamp}`)
            form.content = data.content
            if (data.date_value) form.date = data.date_value
        } catch (e) {
            error.value = 'Failed to load entry for editing'
        }
    }
})

const submitForm = async () => {
    loading.value = true
    error.value = ''
    try {
        const { data } = await api.post('/api/diary', form)
        if (data.success) {
            if (data.feedback && data.feedback.timestamp) {
                router.push(`/entry/${data.feedback.timestamp}`)
            } else {
                router.push('/history')
            }
        } else {
            error.value = data.error || 'Failed to polish entry'
        }
    } catch (e) {
        if (e.response) {
            error.value = e.response.data.error || 'Failed to polish entry'
        } else {
            error.value = 'Network error'
        }
    } finally {
        loading.value = false
    }
}
</script>
