<template>
  <div class="container py-5">
      <div class="d-flex justify-content-between align-items-center mb-5">
          <h2 class="mb-0">History</h2>
          <router-link to="/" class="btn btn-primary btn-sm">New</router-link>
      </div>
      
      <div class="row justify-content-center mb-5">
          <div class="col-lg-8">
              <form @submit.prevent="fetchHistory" class="search-box-container">
                  <div class="input-group">
                      <input type="text" v-model="searchQuery" class="form-control search-input" 
                             placeholder="Search memories...">
                      <button class="btn btn-primary" type="submit">Search</button>
                  </div>
              </form>
          </div>
      </div>
      
      <div class="timeline">
          <div v-if="loading" class="py-5 text-muted text-center card bg-transparent border-0">
              <p class="fs-5">Loading...</p>
          </div>
          <div v-else-if="records.length === 0" class="py-5 text-muted text-center card bg-transparent border-0">
              <p class="fs-5">No entries found.</p>
              <button v-if="searchQuery" @click="clearSearch" class="btn btn-link text-muted">Clear Search</button>
          </div>

          <div v-for="row in records" :key="row.Timestamp" class="position-relative mb-4">
              <div class="timeline-dot"></div>
              
              <router-link :to="'/entry/' + row.Timestamp" class="text-decoration-none text-reset">
                  <div class="card card-hover-effect border-0 shadow-sm" style="transition: transform 0.2s;">
                      <div class="card-body p-4">
                          
                          <div class="d-flex justify-content-between align-items-center mb-2">
                              <span class="text-muted small" style="font-family: var(--font-hand);">
                                  {{ row.Timestamp }}
                              </span>
                              <span v-if="row.Mood && row.Mood.label" class="badge rounded-pill" 
                                    :style="{ backgroundColor: row.Mood.color, fontWeight: 'normal', opacity: 0.9 }">
                                  {{ row.Mood.label }}
                              </span>
                          </div>

                          <h5 class="fw-bold mb-2 text-dark" style="font-family: var(--font-hand); font-size: 1.4rem;">
                              {{ row.Title }}
                          </h5>

                          <p class="text-muted mb-0 text-truncate" style="font-family: var(--font-reading);">
                              {{ row.Original && row.Original.length > 80 ? row.Original.substring(0, 80) + '...' : row.Original }}
                          </p>
                      </div>
                  </div>
              </router-link>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const records = ref([])
const searchQuery = ref('')
const loading = ref(true)

const fetchHistory = async () => {
    loading.value = true
    try {
        const { data } = await api.get('/api/history', { params: { q: searchQuery.value } })
        records.value = data.records
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const clearSearch = () => {
    searchQuery.value = ''
    fetchHistory()
}

onMounted(() => {
    fetchHistory()
    setTimeout(() => {
        if (window.initOrganicFlow) window.initOrganicFlow()
    }, 100)
})
</script>

<style>
.card-hover-effect:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
    cursor: pointer;
}
</style>
