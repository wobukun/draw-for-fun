<template>
  <div class="main-menu">
    <h1>欢迎使用，Let's start！</h1>
    <div class="menu-container">
      <button @click="goToCharacterGacha" class="menu-button start-button">角色活动祈愿</button>
      <button @click="goToWeaponGacha" class="menu-button weapon-button">武器活动祈愿</button>
      <button @click="goToGoalProbability" class="menu-button probability-button">抽取概率计算（Beta）</button>
      <button @click="goToHelpPage" class="menu-button help-button">查看帮助</button>
      <button @click="exitApp" class="menu-button exit-button">退出</button>
    </div>
    <div class="version-info">v{{ version }}</div>
  </div>
</template>

<script>
export default {
  name: 'MainMenu',
  data() {
    return {
      // 版本号，可在此处方便修改
      version: '0.3.1'
    }
  },
  methods: {
    goToCharacterGacha() {
      this.$router.push('/character')
    },
    goToWeaponGacha() {
      this.$router.push('/weapon')
    },
    goToGoalProbability() {
      this.$router.push('/goal-probability')
    },
    goToHelpPage() {
      this.$router.push('/help')
    },
    exitApp() {
      // 退出应用的逻辑
      console.log('开始执行退出操作...')
      
      // 1. 首先检查服务器是否已经被关闭
      if (window.serverShutdown) {
        console.log('服务器已经被关闭，不再发送shutdown请求')
        // 导航到ClosePrompt组件
        console.log('导航到ClosePrompt组件...')
        this.$router.push('/close-prompt')
        return
      }
      
      // 2. 标记服务器为已关闭
      window.serverShutdown = true
      
      // 3. 发送关闭服务器请求
      console.log('正在发送关闭服务器请求...')
      
      // 立即导航到ClosePrompt组件，不需要等待请求完成
      console.log('导航到ClosePrompt组件...')
      this.$router.push('/close-prompt')
      
      // 使用fetch发送关闭服务器请求到正确的端点（在后台执行）
      try {
        fetch('/api/shutdown', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ action: 'shutdown' }),
          keepalive: true
        }).then(response => {
          console.log('使用fetch发送关闭服务器请求:', response.ok ? '成功' : '失败')
        }).catch(error => {
          console.error('使用fetch发送关闭服务器请求时出错:', error)
        })
      } catch (error) {
        console.error('发送关闭服务器请求时出错:', error)
      }
    }
  }
}
</script>

<style scoped>
.main-menu {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: relative;
  overflow: hidden;
}

.main-menu::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 10% 20%, rgba(138, 216, 255, 0.1) 0%, rgba(187, 222, 251, 0.05) 90%);
  z-index: 0;
}

h1 {
  color: #2c3e50;
  margin-top: 60px;
  margin-bottom: 40px;
  font-size: 36px;
  text-align: center;
  font-weight: 700;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 1;
}

.version-info {
  color: #7f8c8d;
  margin-top: 60px;
  font-size: 14px;
  text-align: center;
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.menu-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
  max-width: 420px;
  position: relative;
  z-index: 1;
}

.menu-button {
  padding: 20px 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.menu-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.menu-button:hover::before {
  opacity: 1;
}

.menu-button:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-4px);
  box-shadow: 0 10px 24px rgba(102, 126, 234, 0.4);
}

.menu-button:active {
  transform: translateY(0);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
}

.start-button {
  background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%);
  box-shadow: 0 6px 16px rgba(255, 154, 158, 0.3);
}

.start-button:hover {
  background: linear-gradient(135deg, #fad0c4 0%, #ff9a9e 100%);
  box-shadow: 0 10px 24px rgba(255, 154, 158, 0.4);
}

.weapon-button {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
  box-shadow: 0 6px 16px rgba(132, 250, 176, 0.3);
}

.weapon-button:hover {
  background: linear-gradient(135deg, #8fd3f4 0%, #84fab0 100%);
  box-shadow: 0 10px 24px rgba(132, 250, 176, 0.4);
}

.probability-button {
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
  color: #2c3e50;
  box-shadow: 0 4px 12px rgba(191, 230, 255, 0.7);
  border: 1px solid #bae6fd;
}

.probability-button:hover {
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  box-shadow: 0 8px 20px rgba(191, 230, 255, 0.9);
}

.help-button {
  background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
  box-shadow: 0 6px 16px rgba(212, 252, 121, 0.3);
}

.help-button:hover {
  background: linear-gradient(135deg, #96e6a1 0%, #d4fc79 100%);
  box-shadow: 0 10px 24px rgba(212, 252, 121, 0.4);
}

.exit-button {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 6px 16px rgba(240, 147, 251, 0.3);
}

.exit-button:hover {
  background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
  box-shadow: 0 10px 24px rgba(240, 147, 251, 0.4);
}

@media (max-width: 768px) {
  h1 {
    font-size: 28px;
    margin-bottom: 40px;
  }
  
  .menu-button {
    padding: 16px 32px;
    font-size: 18px;
  }
  
  .menu-container {
    max-width: 320px;
  }
}
</style>