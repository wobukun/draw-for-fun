import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import MainMenu from './components/MainMenu.vue'
import CharacterGacha from './components/CharacterGacha.vue'
import CharacterGacha2 from './components/CharacterGacha2.vue'
import WeaponGacha from './components/WeaponGacha.vue'
import CharacterPullResult from './components/CharacterPullResult.vue'
import CharacterPullResult2 from './components/CharacterPullResult2.vue'
import WeaponPullResult from './components/WeaponPullResult.vue'
import ClosePrompt from './components/ClosePrompt.vue'
import CharacterSimulationResult from './components/CharacterSimulationResult.vue'
import CharacterSimulationResult2 from './components/CharacterSimulationResult2.vue'
import WeaponSimulationResult from './components/WeaponSimulationResult.vue'
import HelpPage from './components/HelpPage.vue'
import GoalProbability from './components/GoalProbability.vue'
import GoalProbabilityIntro from './components/GoalProbabilityIntro.vue'

const routes = [
  {
    path: '/',
    name: 'MainMenu',
    component: MainMenu
  },
  {
    path: '/character',
    name: 'CharacterGacha',
    component: CharacterGacha
  },
  {
    path: '/character-2',
    name: 'CharacterGacha2',
    component: CharacterGacha2
  },
  {
    path: '/weapon',
    name: 'WeaponGacha',
    component: WeaponGacha
  },
  {
    path: '/character-result',
    name: 'CharacterPullResult',
    component: CharacterPullResult
  },
  {
    path: '/character-result-2',
    name: 'CharacterPullResult2',
    component: CharacterPullResult2
  },
  {
    path: '/weapon-result',
    name: 'WeaponPullResult',
    component: WeaponPullResult
  },
  {
    path: '/character-simulation-result',
    name: 'CharacterSimulationResult',
    component: CharacterSimulationResult
  },
  {
    path: '/character-simulation-result-2',
    name: 'CharacterSimulationResult2',
    component: CharacterSimulationResult2
  },
  {
    path: '/weapon-simulation-result',
    name: 'WeaponSimulationResult',
    component: WeaponSimulationResult
  },
  {
    path: '/close-prompt',
    name: 'ClosePrompt',
    component: ClosePrompt
  },
  {
    path: '/help',
    name: 'HelpPage',
    component: HelpPage
  },
  {
    path: '/goal-probability-intro',
    name: 'GoalProbabilityIntro',
    component: GoalProbabilityIntro
  },
  {
    path: '/goal-probability',
    name: 'GoalProbability',
    component: GoalProbability
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')

// 应用加载完成后隐藏加载动画
const hideLoadingAnimation = () => {
  const loadingContainer = document.getElementById('loading-container')
  if (loadingContainer) {
    loadingContainer.classList.add('hidden')
    // 延迟后完全移除加载容器
    setTimeout(() => {
      loadingContainer.remove()
    }, 300)
  }
}

// 立即尝试隐藏加载动画，确保动画不会显示太久
hideLoadingAnimation()

// 作为后备，确保即使应用加载较慢，动画也会在2秒后隐藏
setTimeout(hideLoadingAnimation, 2000)
