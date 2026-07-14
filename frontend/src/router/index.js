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

router.beforeEach(async (to, from, next) => {
  if (to.name !== 'login') {
    try {
      const res = await fetch('/api/check_auth')
      const data = await res.json()
      if (!data.logged_in) {
        next({ name: 'login' })
        return
      }
    } catch (e) {
      next({ name: 'login' })
      return
    }
  }
  next()
})

export default router
