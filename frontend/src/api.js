import axios from 'axios'
import router from './router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  withCredentials: true,
})

// Unified 401 handler — redirect to login for any unauthorized response
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't redirect if we're already on the login page or calling the login/check_auth API
      const url = error.config.url || ''
      if (!url.includes('/api/login') && !url.includes('/api/check_auth')) {
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default api
