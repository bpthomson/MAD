import { createRouter, createWebHistory } from 'vue-router'
import Index from '../views/index.vue'
import Login from '../views/login.vue'
import History from '../views/history.vue'
import Result from '../views/result.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Index
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/history',
      name: 'history',
      component: History
    },
    {
      path: '/entry/:timestamp',
      name: 'entry',
      component: Result
    },
    {
      path: '/edit/:timestamp',
      name: 'edit',
      component: Index
    }
  ]
})

// Deduplicate concurrent auth checks — if one is in-flight, reuse it
let authCheckPromise = null

router.beforeEach(async (to, from, next) => {
  if (to.name !== 'login') {
    try {
      // Reuse in-flight auth check to avoid duplicate requests
      if (!authCheckPromise) {
        authCheckPromise = import('../api').then(({ default: api }) =>
          api.get('/api/check_auth')
        )
      }
      const { data } = await authCheckPromise
      authCheckPromise = null

      if (!data.logged_in) {
        next({ name: 'login' })
        return
      }
    } catch (e) {
      authCheckPromise = null
      next({ name: 'login' })
      return
    }
  }
  next()
})

export default router
