<template>
  <div class="container-xxl py-5" v-if="feedback">
      
      <div class="d-flex justify-content-between align-items-center mb-4">
          <div class="d-flex align-items-center gap-3">
              <h2 class="mb-0">Insight</h2>
              <span v-if="feedback.mood" class="badge rounded-pill px-3 py-2 shadow-sm" 
                    :style="{ backgroundColor: feedback.mood.color, color: '#fff', fontFamily: 'var(--font-hand)', fontWeight: 'normal', fontSize: '1rem', border: '1px solid rgba(255,255,255,0.3)' }">
                  {{ feedback.mood.label }}
              </span>
          </div>
          
          <div class="d-flex gap-2">
              <router-link v-if="feedback.timestamp" :to="'/edit/' + feedback.timestamp" class="btn btn-outline-primary btn-sm">Edit</router-link>
              <button v-if="feedback.timestamp" @click="deleteEntry" class="btn btn-outline-danger btn-sm">Delete</button>
              <router-link to="/history" class="btn btn-outline-secondary btn-sm">Back</router-link>
          </div>
      </div>
      
      <div class="card mb-4 border-0 bg-transparent">
          <div class="card-body p-0">
              <p style="font-family: var(--font-hand); color: var(--accent-color); font-size: 1.3rem; line-height: 1.6;">
                  "{{ feedback.comment }}"
              </p>
          </div>
      </div>

      <div class="row g-4 mb-5">
          <div class="col-lg-8">
              <div class="card h-100">
                  <div class="card-header text-muted">Interactive Draft (Click highlights)</div>
                  <div class="card-body">
                      <div id="marked-original-text" style="white-space: pre-wrap;" v-html="feedback.marked_html"></div>
                  </div>
              </div>
          </div>

          <div class="col-lg-4">
              <div class="card sticky-top shadow-sm" 
                   style="top: 2rem; max-height: 85vh; overflow-y: auto; border-left: 4px solid var(--accent-color);">
                  <div class="card-header text-danger bg-white">Correction Details</div>
                  <div class="card-body d-flex align-items-center justify-content-center text-center p-4" id="correction-details-panel">
                      <p class="text-muted fst-italic mb-0">
                          <i style="font-size: 2rem; display: block; margin-bottom: 1rem;">👆</i>
                          Click on a highlighted area in your draft to see the correction and explanation here.
                      </p>
                  </div>
              </div>
          </div>
      </div>

      <div class="card mb-5" style="border-color: rgba(141, 110, 99, 0.3);">
          <div class="card-header d-flex justify-content-between align-items-center" style="color: var(--accent-color);">
              <span>Polished Version</span>
              <button class="btn btn-sm btn-link text-muted text-decoration-none" @click="copyToClipboard">Copy</button>
          </div>
          <div class="card-body">
              <div class="native-polish-text fs-5" v-html="feedback.polished_html"></div>
          </div>
      </div>

      <div>
          <h5 class="text-muted mb-3 border-bottom pb-2">Vocabulary Bank</h5>
          <div class="row g-3">
              <div v-for="v in feedback.vocabulary" :key="v.word" class="col-md-6 col-lg-4">
                  <div class="card h-100">
                      <div class="card-body">
                          <div class="d-flex justify-content-between align-items-baseline mb-2">
                              <span class="fw-bold fs-5" style="font-family: var(--font-reading); color: var(--text-main);">{{ v.word }}</span>
                              <span class="badge bg-light text-dark border">{{ v.meaning }}</span>
                          </div>
                          <small class="text-muted fst-italic">"{{ v.example }}"</small>
                      </div>
                  </div>
              </div>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const route = useRoute()
const router = useRouter()
const feedback = ref(null)
const entry = ref('')

onMounted(async () => {
    try {
        const { data } = await api.get(`/api/diary/${route.params.timestamp}`)
        feedback.value = data.feedback
        entry.value = data.content
        
        window.correctionsData = data.feedback.corrections
        setTimeout(() => {
            if (window.initInteractiveCorrections) window.initInteractiveCorrections()
            if (window.initOrganicFlow) window.initOrganicFlow()
        }, 100)
    } catch (e) {
        router.push('/history')
    }
})

const deleteEntry = async () => {
    if (confirm("Are you sure you want to delete this entry?")) {
        try {
            await api.delete(`/api/diary/${route.params.timestamp}`)
            router.push('/history')
        } catch (e) {
            console.error(e)
        }
    }
}

const copyToClipboard = () => {
    const el = document.createElement('div')
    el.innerHTML = feedback.value.polished_html
    navigator.clipboard.writeText(el.innerText)
}
</script>
