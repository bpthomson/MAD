import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import api from './api'

// Expose api instance globally for non-module scripts (e.g. script.js)
window.__api = api

const app = createApp(App)
app.use(router)
app.mount('#app')
