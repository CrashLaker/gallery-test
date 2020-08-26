import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'

Vue.use(VueRouter)

  const routes = [
  {
    path: '/:query(.*)',
    name: 'Home',
    props: true,
    component: Home,
    beforeEnter: (to, from, next) => {
      if (to.params.query == ''){
        to.params.query = 'all'
      }
      next()
    }
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
