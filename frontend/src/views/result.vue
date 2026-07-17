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
                      <div style="white-space: pre-wrap;" 
                           v-html="feedback.marked_html"
                           @click="handleMarkClick"></div>
                  </div>
              </div>
          </div>

          <div class="col-lg-4">
              <div class="card sticky-top shadow-sm" 
                   style="top: 2rem; max-height: 85vh; overflow-y: auto; border-left: 4px solid var(--accent-color);">
                  <div class="card-header text-danger bg-white">Correction Details</div>
                  <div class="card-body p-4">
                      <!-- Selected correction details -->
                      <div v-if="selectedCorrection" class="w-100 text-start animation-fade-in">
                          <div class="mb-4 p-3 rounded-3" style="background: rgba(255,255,255,0.5);">
                              <h6 class="text-uppercase text-muted small mb-2 fw-bold" style="letter-spacing: 1px;">Original</h6>
                              <span class="diff-del fs-5" style="text-decoration: none; background-color: transparent; border-bottom: 2px solid var(--diff-del-text); padding: 2px 0;">
                                  {{ selectedCorrection.original }}
                              </span>
                          </div>
                          
                          <div class="text-center my-3">
                              <i class="display-6 text-muted" style="opacity: 0.5;">↓</i>
                          </div>

                          <div class="mb-4 p-3 rounded-3" style="background: rgba(196, 232, 209, 0.3);">
                              <h6 class="text-uppercase text-success small mb-2 fw-bold" style="letter-spacing: 1px;">Correction</h6>
                              <span class="diff-add fs-4" style="background-color: transparent;">
                                  {{ selectedCorrection.correction }}
                              </span>
                          </div>

                          <div class="mt-4">
                              <h6 class="text-uppercase text-muted small mb-2 fw-bold" style="letter-spacing: 1px;">Reason</h6>
                              <p class="text-muted fst-italic" style="font-size: 1.05rem; line-height: 1.6;">
                                  {{ selectedCorrection.explanation }}
                              </p>
                          </div>
                      </div>

                      <!-- Default prompt -->
                      <div v-else class="d-flex align-items-center justify-content-center text-center" style="min-height: 120px;">
                          <p class="text-muted fst-italic mb-0">
                              <i style="font-size: 2rem; display: block; margin-bottom: 1rem;">👆</i>
                              Click on a highlighted area in your draft to see the correction and explanation here.
                          </p>
                      </div>
                  </div>
              </div>
          </div>
      </div>

      <div class="card mb-5" style="border-color: rgba(141, 110, 99, 0.3);">
          <div class="card-header d-flex justify-content-between align-items-center" style="color: var(--accent-color);">
              <span>Polished Version</span>
              <button class="btn btn-sm btn-link text-muted text-decoration-none" @click="copyPolished">
                  {{ copyLabel }}
              </button>
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
const selectedCorrection = ref(null)
const copyLabel = ref('Copy')

onMounted(async () => {
    try {
        const { data } = await api.get(`/api/diary/${route.params.timestamp}`)
        feedback.value = data.feedback
        entry.value = data.content
    } catch (e) {
        router.push('/history')
    }
})

// Event delegation: handle clicks on <mark> elements inside v-html
const handleMarkClick = (event) => {
    const mark = event.target.closest('mark.highlight')
    if (!mark || !feedback.value?.corrections) return

    // Remove active class from all marks
    const container = event.currentTarget
    container.querySelectorAll('mark.highlight').forEach(m => m.classList.remove('active'))
    mark.classList.add('active')

    const index = mark.getAttribute('data-index')
    if (index !== null && feedback.value.corrections[index]) {
        selectedCorrection.value = feedback.value.corrections[index]
    }
}

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

const copyPolished = () => {
    const el = document.createElement('div')
    el.innerHTML = feedback.value.polished_html
    navigator.clipboard.writeText(el.innerText).then(() => {
        copyLabel.value = 'Copied!'
        setTimeout(() => { copyLabel.value = 'Copy' }, 2000)
    })
}
</script>
