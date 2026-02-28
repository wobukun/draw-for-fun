<template>
  <div class="character-gacha">
    <div class="content-container">
      <h1>角色活动祈愿-2</h1>
      <div class="gacha-buttons">
        <button @click="startGacha" class="gacha-button start-button">开始</button>
        <button @click="showAutoSimulation" class="gacha-button auto-button">自动模拟</button>
        <button @click="goBack" class="gacha-button back-button">返回</button>
      </div>
      

    </div>
    
    <!-- 自动模拟设置 -->
    <div v-if="showAutoSim" class="auto-simulation">
      <div class="modal-overlay" @click="hideAutoSimulation"></div>
      <div class="modal-content">
        <h2>自动模拟设置</h2>
        <div class="form-group">
          <label for="sim-count">模拟抽取次数：</label>
          <input type="number" id="sim-count" v-model.number="simCount" min="0" max="10000000" value="1000" title="">
        </div>
        <div class="modal-buttons">
          <button @click="performAutoSimulation" class="modal-button">开始模拟</button>
          <button @click="hideAutoSimulation" class="modal-button cancel-button">取消</button>
        </div>
      </div>
    </div>
    
    <!-- 加载提示 -->
    <div v-if="isLoading" class="loading-indicator">
      <div class="loading-content">
        <div class="loading-text">正在进行模拟，请稍候...</div>
        <div class="loading-bar-container">
          <div class="loading-bar" :style="{ width: loadingProgress + '%' }"></div>
        </div>
        <div class="loading-status">处理中...</div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'CharacterWish2',
  data() {
    return {
      showAutoSim: false,
      simCount: 1000,
      isLoading: false,
      loadingProgress: 0,
      loadingInterval: null
    }
  },
  methods: {
    startGacha() {
      // 直接跳转到结果页面
      this.$router.push('/character-result-2')
    },
    showAutoSimulation() {
      this.showAutoSim = true
    },
    hideAutoSimulation() {
      this.showAutoSim = false
    },
    performAutoSimulation() {
      // 验证模拟次数是否在有效范围内
      if (this.simCount < 0 || this.simCount > 10000000) {
        alert('模拟次数必须在0-10000000之间，请重新输入');
        return;
      }
      
      
      this.isLoading = true
      this.loadingProgress = 0
      
      // 模拟进度条动画
      this.loadingInterval = setInterval(() => {
        this.loadingProgress += 5
        if (this.loadingProgress > 90) {
          this.loadingProgress = 90
        }
      }, 300)
      
      // 提交自动模拟请求
      axios.post('/api/wish', {
        mode: 'character2',
        action: 'auto',
        count: this.simCount,
        start_pity: 0
      })
      .then(response => {
        clearInterval(this.loadingInterval)
        this.loadingProgress = 100
        
        // 跳转到结果页面
        setTimeout(() => {
          this.isLoading = false
          this.$router.push({
            path: '/character-simulation-result-2',
            query: { result: JSON.stringify(response.data) }
          })
        }, 500)
      })
      .catch(error => {
        clearInterval(this.loadingInterval)
        this.isLoading = false
        console.error('自动模拟失败:', error)
      })
    },
    goBack() {
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.character-gacha {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: relative;
  justify-content: flex-start;
}

.content-container {
  width: 100%;
  max-width: 1000px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

h1 {
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 28px;
  text-align: center;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
  font-weight: 700;
  width: 100%;
}

.gacha-buttons {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin: 0 auto;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 60vh;
}

.gacha-button {
  padding: 20px 60px;
  background: linear-gradient(135deg, #9f7aea 0%, #b794f4 100%);
  color: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 16px rgba(159, 122, 234, 0.3);
  position: relative;
  overflow: hidden;
  min-width: 280px;
}

.gacha-button::before {
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

.gacha-button:hover::before {
  opacity: 1;
}

.gacha-button:hover {
  background: linear-gradient(135deg, #b794f4 0%, #9f7aea 100%);
  box-shadow: 0 10px 24px rgba(159, 122, 234, 0.4);
  transform: translateY(-4px);
}

.start-button {
  background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%);
  color: #2c3e50;
  font-size: 20px;
  padding: 20px 60px;
  box-shadow: 0 6px 16px rgba(255, 154, 158, 0.3);
  min-width: 280px;
  border: none;
}

.start-button:hover {
  background: linear-gradient(135deg, #fad0c4 0%, #ff9a9e 100%);
  box-shadow: 0 10px 24px rgba(255, 154, 158, 0.4);
}

.auto-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
  border: none;
}

.auto-button:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  box-shadow: 0 10px 24px rgba(102, 126, 234, 0.4);
}

.back-button {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  color: #2c3e50;
  box-shadow: 0 6px 16px rgba(255, 255, 255, 0.3);
  border: 2px solid #e2e8f0;
}

.back-button:hover {
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  box-shadow: 0 10px 24px rgba(255, 255, 255, 0.4);
}



.auto-simulation {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(245, 247, 250, 0.9) 100%);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 12px;
  padding: 30px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
  z-index: 1001;
  border: 1px solid #e8eaf6;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.modal-content:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2);
}

.modal-content h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 22px;
  text-align: center;
  font-weight: 600;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #6c757d;
  font-size: 14px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
  background: white;
}

.form-group input:hover::-webkit-inner-spin-button,
.form-group input:hover::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.modal-buttons {
  display: flex;
  gap: 30px;
  margin-top: 20px;
  justify-content: center;
}

.modal-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
  position: relative;
  overflow: hidden;
}

.modal-button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.modal-button:hover::before {
  width: 300px;
  height: 300px;
}

.modal-button:hover {
  background: linear-gradient(135deg, #2980b9 0%, #1f618d 100%);
  box-shadow: 0 6px 16px rgba(52, 152, 219, 0.4);
  transform: translateY(-2px);
}

.cancel-button {
  background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
  box-shadow: 0 4px 12px rgba(149, 165, 166, 0.3);
}

.cancel-button:hover {
  background: linear-gradient(135deg, #7f8c8d 0%, #6c757d 100%);
  box-shadow: 0 6px 16px rgba(149, 165, 166, 0.4);
}

.loading-indicator {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.7) 0%, rgba(0, 0, 0, 0.8) 100%);
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-text {
  font-size: 24px;
  margin-bottom: 30px;
  font-weight: 600;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.loading-bar-container {
  width: 300px;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
  margin: 0 auto 10px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.loading-bar {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #9b59b6);
  border-radius: 10px;
  transition: width 0.3s ease-in-out;
  box-shadow: 0 0 10px rgba(52, 152, 219, 0.5);
}

.loading-status {
  font-size: 16px;
  margin-top: 10px;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}

@media (max-width: 768px) {
  .gacha-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .gacha-button {
    width: 200px;
  }
}
</style>
