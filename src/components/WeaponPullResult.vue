<template>
  <div class="pull-result">
    <div class="content-container">
      <!-- 右上角按钮 -->
      <div class="action-buttons">
        <button @click="goBack" class="action-button small-action-button">返回</button>
        <button @click="goToMainMenu" class="action-button">主菜单</button>
      </div>
      
      <!-- 左下角重置按钮 -->
      <div class="reset-button-container">
        <button @click="resetGacha" class="action-button small-action-button">重置</button>
      </div>
      
      <h1>武器活动祈愿结果</h1>
      
      <div class="main-content">
        <!-- 左侧：历史记录 -->
        <div class="pull-history">
          <h2>历史记录</h2>
          <div class="history-container">
            <div v-for="(item, index) in pullHistory" :key="index" class="history-item" :class="[`star-${item.star}`, { 'history-item-5star': item.star === 5 }]">
              <div class="history-pull-number">{{ result.total_pulls - index }}</div>
              <div class="history-star">{{ item.star === 5 ? item.star : '3/4' }}★</div>
              <div class="history-name"></div>
              <div class="history-type" v-if="item.star === 5">
                {{ item.is_fate ? '定轨武器' : (item.name.includes('常驻') ? '常驻武器' : 'UP武器（非定轨）') }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- 右侧：抽卡结果和按钮 -->
        <div class="pull-results-wrapper">
          <!-- 抽卡结果 -->
          <div class="pull-results">
            <h2>本次抽卡结果</h2>
            <div class="results-container">
              <div v-for="(item, index) in displayResults" :key="index" class="result-item" :class="[`star-${item.star}`, { 'appear-animation': showRefreshAnimation }]">
                <div class="result-star">{{ item.star === 5 ? item.star : '3/4' }}★</div>
                <div class="result-name" v-if="item.star === 5" v-html="item.is_fate ? '定轨' : (item.name.includes('常驻') ? '常驻' : 'UP<br>非定轨')"></div>
                <div class="result-name" v-else></div>
              </div>
            </div>
          </div>
          
          <!-- 数学统计信息 -->
          <div class="stats-card">
            <h2>数学统计</h2>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-label">总抽数</div>
                <div class="stat-value">{{ result.total_pulls }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">已连续未出5星抽数</div>
                <div class="stat-value">{{ result.current_pity }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">已连续未出UP5星抽数</div>
                <div class="stat-value">{{ result.up_pity }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">已连续未出定轨5星抽数</div>
                <div class="stat-value">{{ result.fate_pity || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">常驻武器数</div>
                <div class="stat-value">{{ result.avg_count }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">UP（非定轨）武器数</div>
                <div class="stat-value">{{ result.up_count - result.fate_count }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">定轨武器数</div>
                <div class="stat-value success">{{ result.fate_count || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">下次必UP</div>
                <div class="stat-value">{{ result.guarantee_up ? '是' : '否' }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">命定值</div>
                <div class="stat-value" :class="{ 'blue-text': (result.fate_point || 0) === 1 }">{{ result.fate_point || 0 }}</div>
              </div>
            </div>
          </div>
          
          <!-- 继续抽卡按钮 -->
          <div class="continue-buttons">
            <div class="button-group">
              <button @click="performSinglePull" class="action-button single-pull" :disabled="isLoading">
                {{ isLoading ? '抽卡中...' : '单抽' }}
              </button>
              <button @click="performTenPulls" class="action-button ten-pull" :disabled="isLoading">
                {{ isLoading ? '抽卡中...' : '十连' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'WeaponPullResult',
  data() {
    return {
      result: {
        total_pulls: 0,
        current_pity: 0,
        up_pity: 0,
        fate_pity: 0,
        avg_count: 0,
        up_count: 0,
        fate_count: 0,
        guarantee_up: false,
        fate_point: 0,
        is_fate_guaranteed: false
      },
      isLoading: false,
      showRefreshAnimation: false,
      pullHistory: []
    }
  },
  computed: {
    displayResults() {
      // 当已抽0抽时，不显示任何结果
      if (this.result.total_pulls === 0) {
        return []
      }
      
      // 处理单抽和十连的不同数据结构
      if (Array.isArray(this.result)) {
        // 旧格式（单抽）
        return this.result
      } else if (this.result.results) {
        // 新格式（十连）
        return this.result.results.map((item, index) => ({
          star: item.star,
          name: item.name,
          is_fate: item.is_fate
        }))
      } else {
        // 单抽新格式
        return [{
          star: this.result.star,
          name: this.result.name,
          is_fate: this.result.is_fate
        }]
      }
    }
  },
  mounted() {
    // 从路由参数获取结果
    const resultStr = this.$route.query.result
    
    if (resultStr) {
      this.result = JSON.parse(resultStr)
    }
  },
  methods: {
    async performSinglePull() {
      try {
        this.isLoading = true
        
        // 设置固定的延迟时间
        const delay = 500 // 0.5秒
        
        // 同时处理网络请求和固定延迟
        const [response] = await Promise.all([
          axios.post('/api/gacha', {
            mode: 'weapon',
            action: 'one',
            current_pity: this.result.current_pity || 0,
            up_pity: this.result.up_pity || 0,
            fate_pity: this.result.fate_pity || 0,
            avg_count: this.result.avg_count || 0,
            up_count: this.result.up_count || 0,
            fate_count: this.result.fate_count || 0,
            guarantee_up: this.result.guarantee_up || false,
            fate_point: this.result.fate_point || 0,
            is_fate_guaranteed: this.result.is_fate_guaranteed || false,
            total_pulls: this.result.total_pulls || 0
          }),
          new Promise(resolve => setTimeout(resolve, delay))
        ])
        
        this.isLoading = false
        // 直接更新当前页面的结果
        this.result = response.data
        // 更新抽卡记录
        this.updatePullHistory(response.data)
        // 重置动画状态
        this.showRefreshAnimation = false
        // 强制 Vue 更新 DOM
        this.$nextTick(() => {
          // 触发刷新动画
          this.showRefreshAnimation = true
          // 0.6秒后重置动画状态
          setTimeout(() => {
            this.showRefreshAnimation = false
          }, 600)
        })
      } catch (error) {
        this.isLoading = false
        console.error('单抽失败:', error)
      }
    },
    async performTenPulls() {
      try {
        this.isLoading = true
        
        // 设置固定的延迟时间
        const delay = 500 // 0.5秒
        
        // 同时处理网络请求和固定延迟
        const [response] = await Promise.all([
          axios.post('/api/gacha', {
            mode: 'weapon',
            action: 'ten',
            current_pity: this.result.current_pity || 0,
            up_pity: this.result.up_pity || 0,
            fate_pity: this.result.fate_pity || 0,
            avg_count: this.result.avg_count || 0,
            up_count: this.result.up_count || 0,
            fate_count: this.result.fate_count || 0,
            guarantee_up: this.result.guarantee_up || false,
            fate_point: this.result.fate_point || 0,
            is_fate_guaranteed: this.result.is_fate_guaranteed || false,
            total_pulls: this.result.total_pulls || 0
          }),
          new Promise(resolve => setTimeout(resolve, delay))
        ])
        
        this.isLoading = false
        // 直接更新当前页面的结果
        this.result = response.data
        // 更新抽卡记录
        this.updatePullHistory(response.data)
        // 重置动画状态
        this.showRefreshAnimation = false
        // 强制 Vue 更新 DOM
        this.$nextTick(() => {
          // 触发刷新动画
          this.showRefreshAnimation = true
          // 0.6秒后重置动画状态
          setTimeout(() => {
            this.showRefreshAnimation = false
          }, 600)
        })
      } catch (error) {
        this.isLoading = false
        console.error('十连失败:', error)
      }
    },
    goBack() {
      this.$router.push('/weapon')
    },
    goToMainMenu() {
      this.$router.push('/')
    },
    resetGacha() {
      // 重置所有统计数据
      this.result = {
        total_pulls: 0,
        current_pity: 0,
        up_pity: 0,
        fate_pity: 0,
        avg_count: 0,
        up_count: 0,
        fate_count: 0,
        guarantee_up: false,
        fate_point: 0,
        is_fate_guaranteed: false
      }
      // 清空抽卡历史
      this.pullHistory = []
      // 重置动画状态
      this.showRefreshAnimation = false
    },
    updatePullHistory(data) {
      // 处理单抽和十连的不同数据结构
      if (data.results) {
        // 十连结果
        data.results.forEach(item => {
          this.pullHistory.unshift({
            star: item.star,
            name: item.name,
            is_fate: item.is_fate
          })
        })
      } else {
        // 单抽结果
        this.pullHistory.unshift({
          star: data.star,
          name: data.name,
          is_fate: data.is_fate
        })
      }
      // 保持最近100次抽卡记录
      if (this.pullHistory.length > 100) {
        this.pullHistory = this.pullHistory.slice(0, 100)
      }
    }
  }
}
</script>

<style scoped>
.pull-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  position: relative;
  justify-content: flex-start;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.content-container {
  width: 100%;
  max-width: 1800px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  padding: 20px;
  box-sizing: border-box;
  min-height: calc(100vh - 40px);
  justify-content: space-between;
}

/* 右上角按钮 */
.action-buttons {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 20px;
  z-index: 10;
}

/* 左下角重置按钮 */
.reset-button-container {
  position: absolute;
  bottom: 20px;
  left: 20px;
  z-index: 10;
}

.small-action-button {
  padding: 12px 24px !important;
  min-width: 120px !important;
  font-size: 16px !important;
  letter-spacing: 0.8px !important;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
  border-color: #cbd5e1 !important;
}

/* 主内容区域 - 左右布局 */
.main-content {
  width: 100%;
  display: flex;
  gap: 20px;
  margin-top: 20px;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: nowrap;
  box-sizing: border-box;
  flex-grow: 1;
  height: 680px;
}

/* 左侧：历史记录 */
.pull-history {
  flex: 0 0 320px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border: 1px solid #e2e8f0;
  height: 630px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  box-sizing: border-box;
}



.pull-history h2 {
  margin-bottom: 15px;
  color: #2d3748;
  font-size: 18px;
  text-align: center;
  font-weight: 700;
  position: relative;
}

.pull-history h2::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 2px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 2px;
}

.history-container {
  max-height: calc(100% - 60px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 20px 15px 0;
  box-sizing: border-box;
  width: 100%;
}

/* 自定义滚动条 */
.history-container::-webkit-scrollbar {
  width: 6px;
}

.history-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.history-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.history-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 确保没有记录时也显示占位内容 */
.history-container:empty::before {
  content: '暂无抽卡记录';
  text-align: center;
  color: #94a3b8;
  padding: 30px 15px;
  font-style: italic;
  margin-top: 30px;
  font-size: 14px;
}

.history-item {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 8px;
  padding: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #e2e8f0;
  position: relative;
  overflow: hidden;
  height: 40px;
  box-sizing: border-box;
  width: 100%;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.history-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  border-color: #cbd5e0;
}

/* 5星记录的特殊样式 */
.history-item.history-item-5star {
  background: linear-gradient(135deg, #fff9c4 0%, #ffeb3b 100%);
  border: 2px solid #ffd700;
  box-shadow: 0 4px 16px rgba(255, 215, 0, 0.3);
}

/* 抽数显示 */
.history-pull-number {
  font-size: 10px;
  font-weight: bold;
  width: 30px;
  text-align: center;
  color: #475569;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 2px 4px;
  border: 1px solid #e2e8f0;
  box-sizing: border-box;
}

.history-star {
  font-size: 11px;
  font-weight: bold;
  width: 45px;
  text-align: center;
  border-radius: 4px;
  padding: 2px 4px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid #e2e8f0;
  box-sizing: border-box;
}

.history-star.star-5 {
  color: #f59e0b;
  background: rgba(255, 249, 196, 0.9);
  border: 1px solid #fcd34d;
}

.history-star.star-4 {
  color: #8b5cf6;
  background: rgba(243, 232, 255, 0.9);
  border: 1px solid #ddd6fe;
}

.history-star.star-3 {
  color: #6b7280;
  background: rgba(249, 250, 251, 0.9);
  border: 1px solid #e5e7eb;
}

.history-name {
  font-size: 10px;
  color: #2d3748;
  font-weight: 600;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

.history-type {
  font-size: 9px;
  color: #64748b;
  font-weight: 500;
  text-align: right;
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

.history-item.history-item-5star .history-type {
  color: #f59e0b;
  font-weight: 700;
  font-size: 11px;
}

.history-item.history-item-5star .history-name {
  color: #92400e;
  font-weight: 700;
}

/* 右侧：抽卡结果和按钮 */
.pull-results-wrapper {
  flex: 1;
  min-width: 600px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  box-sizing: border-box;
  height: 100%;
}

/* 标题样式 */
h1 {
  color: #2d3748;
  margin-bottom: 10px;
  font-size: 24px;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-weight: 800;
  width: 100%;
  position: relative;
  padding: 5px 0;
}



/* 抽卡结果部分 */
.pull-results {
  width: 100%;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border: 1px solid #e2e8f0;
  position: relative;
  backdrop-filter: blur(10px);
  box-sizing: border-box;
  flex-grow: 2;
}

.pull-results h2 {
  color: #2d3748;
  margin-bottom: 20px;
  font-size: 20px;
  text-align: center;
  font-weight: 700;
  position: relative;
}

.pull-results h2::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 70px;
  height: 2px;
  background: linear-gradient(90deg, #4facfe, #00f2fe);
  border-radius: 2px;
}

.results-container {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 16px;
  justify-items: center;
  align-items: center;
  min-height: 300px;
  width: 100%;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 249, 250, 0.8) 100%);
  border-radius: 16px;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  box-sizing: border-box;
  overflow: hidden;
}

.results-container::before {
  content: '';
  position: absolute;
  top: -3px;
  left: -3px;
  right: -3px;
  bottom: -3px;
  background: linear-gradient(45deg, #4299e1, #805ad5, #f6ad55, #fc8181, #4fd1c5, #63b3ed);
  border-radius: 16px;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.5s ease;
  animation: gradient-shift 8s ease infinite;
  background-size: 400% 400%;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.results-container:hover::before {
  opacity: 0.1;
}

/* 卡片渐进出现动画效果 */
@keyframes appearAnimation {
  0% {
    transform: scale(0.8) rotateY(-15deg);
    opacity: 0;
  }
  100% {
    transform: scale(1) rotateY(0);
    opacity: 1;
  }
}

.result-item.appear-animation {
  animation: appearAnimation 0.8s cubic-bezier(0.23, 1, 0.32, 1);
}

/* 确保5星卡片也能正确应用动画 */
.result-item.star-5.appear-animation {
  animation: appearAnimation 0.8s cubic-bezier(0.23, 1, 0.32, 1), glow-pulse 2s ease-in-out infinite 0.8s;
}

/* 结果卡片样式 */
.result-item {
  background: white;
  border-radius: 12px;
  padding: 20px 12px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  text-align: center;
  width: 100%;
  max-width: 100px;
  height: 180px;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(10px);
  cursor: pointer;
  box-sizing: border-box;
}

.result-item:hover {
  transform: translateY(-10px) scale(1.05) rotateY(5deg);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
}

.result-item::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(66, 153, 225, 0.1) 0%, rgba(128, 90, 213, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.result-item:hover::after {
  opacity: 1;
}

/* 3星结果样式 */
.result-item.star-3 {
  border-color: #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  box-shadow: 0 4px 15px rgba(107, 114, 128, 0.1);
}

.result-item.star-3::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #a0aec0, #cbd5e0);
}

/* 4星结果样式 */
.result-item.star-4 {
  border-color: #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  box-shadow: 0 4px 15px rgba(107, 114, 128, 0.1);
}

.result-item.star-4::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #a0aec0, #cbd5e0);
}

/* 5星结果样式 */
.result-item.star-5 {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
  box-shadow: 0 8px 25px rgba(245, 158, 11, 0.3);
  position: relative;
}

.result-item.star-5::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b);
  animation: shine 3s ease-in-out infinite;
}

.result-item.star-5:hover {
  transform: translateY(-12px) scale(1.08) rotateY(5deg);
  box-shadow: 0 25px 50px rgba(245, 158, 11, 0.4);
}

/* 卡片内容样式 */
.result-star {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 16px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
  padding: 0;
  transition: all 0.3s ease;
}

.star-3 .result-star {
  color: #94a3b8;
  font-size: 24px;
}

.star-4 .result-star {
  color: #94a3b8;
  font-size: 24px;
}

.star-5 .result-star {
  color: #f59e0b;
  font-size: 32px;
  text-shadow: 0 0 15px rgba(245, 158, 11, 0.6);
  animation: star-glow 2s ease-in-out infinite alternate;
}

.result-name {
  font-size: 16px;
  color: #2d3748;
  margin-bottom: 8px;
  font-weight: 600;
  position: relative;
  z-index: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  padding: 0 8px;
  line-height: 1.3;
}

.star-5 .result-name {
  color: #92400e;
  font-weight: 700;
  font-size: 18px;
  text-shadow: 0 1px 2px rgba(245, 158, 11, 0.3);
  animation: text-glow 2s ease-in-out infinite alternate;
}

@keyframes text-glow {
  from {
    text-shadow: 0 0 5px rgba(245, 158, 11, 0.5);
  }
  to {
    text-shadow: 0 0 15px rgba(245, 158, 11, 0.8);
  }
}

/* 数学统计部分 */
.stats-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  width: 100%;
  border: 1px solid #e2e8f0;
  position: relative;
  backdrop-filter: blur(10px);
  box-sizing: border-box;
  transition: all 0.3s ease;
  flex-grow: 1;
}

.stats-card h2 {
  color: #2d3748;
  margin-bottom: 15px;
  font-size: 20px;
  padding-bottom: 10px;
  font-weight: 700;
  text-align: center;
}

.stats-grid {
  display: flex;
  flex-wrap: nowrap;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
  justify-content: space-between;
  width: 100%;
}

/* 自定义滚动条 */
.stats-grid::-webkit-scrollbar {
  height: 6px;
}

.stats-grid::-webkit-scrollbar-track {
  background: rgba(241, 245, 249, 0.8);
  border-radius: 3px;
}

.stats-grid::-webkit-scrollbar-thumb {
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 3px;
}

.stat-item {
  flex: 1;
  min-width: 120px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  padding: 15px 10px;
  border-radius: 8px;
  text-align: center;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(5px);
  box-sizing: border-box;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.2px;
  line-height: 1.2;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #2d3748;
  line-height: 1.1;
}

.stat-value.blue-text {
  color: #60a5fa;
}

.success {
  color: #fcd34d;
  text-shadow: 0 2px 4px rgba(252, 211, 77, 0.3);
}

/* 按钮部分 */
.continue-buttons {
  width: 100%;
  padding: 20px;
  box-sizing: border-box;
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.button-group {
  display: flex;
  gap: 40px;
  position: relative;
  flex-wrap: wrap;
  margin-right: 0;
  justify-content: flex-end;
}



.action-button {
  padding: 14px 44px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  color: #2d3748;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
  min-width: 220px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.action-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.1), transparent);
  transition: left 0.6s ease;
}

.action-button:hover::before {
  left: 100%;
}

.action-button:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  transform: translateY(-4px);
  border-color: #cbd5e0;
}

.action-button:active {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.action-button.single-pull {
  background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
  color: #2d3748;
  border-color: #93c5fd;
  box-shadow: 0 4px 12px rgba(147, 197, 253, 0.2);
}

.action-button.single-pull:hover {
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
  box-shadow: 0 8px 20px rgba(147, 197, 253, 0.3);
  border-color: #60a5fa;
}

.action-button.ten-pull {
  background: linear-gradient(135deg, #ffffff 0%, #fef3c7 100%);
  color: #2d3748;
  border-color: #fcd34d;
  box-shadow: 0 4px 12px rgba(252, 211, 77, 0.2);
}

.action-button.ten-pull:hover {
  background: linear-gradient(135deg, #fef3c7 0%, #ffffff 100%);
  box-shadow: 0 8px 20px rgba(252, 211, 77, 0.3);
  border-color: #fbbf24;
}

.action-button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.action-button:disabled:hover {
  background: #94a3b8;
  transform: none;
}

.action-button:disabled::before {
  display: none;
}

/* 动画效果 */
@keyframes star-glow {
  from {
    text-shadow: 0 0 10px #f59e0b, 0 0 20px #f59e0b;
  }
  to {
    text-shadow: 0 0 20px #f59e0b, 0 0 30px #f59e0b, 0 0 40px #f59e0b;
  }
}

@keyframes glow-pulse {
  0%, 100% {
    box-shadow: 0 0 25px rgba(245, 158, 11, 0.3);
  }
  50% {
    box-shadow: 0 0 40px rgba(245, 158, 11, 0.6), 0 0 60px rgba(245, 158, 11, 0.3);
  }
}

@keyframes shine {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
    align-items: center;
  }
  
  .pull-history {
    flex: 1;
    width: 100%;
    max-width: 800px;
    height: 300px;
    order: 2;
  }
  
  .pull-results-wrapper {
    flex: 1;
    min-width: 100%;
    order: 1;
  }
  
  .history-container {
    height: 240px;
  }
  
  .results-container {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .pull-result {
    padding: 10px;
  }
  
  .content-container {
    padding: 0 10px;
  }
  
  h1 {
    font-size: 28px;
    margin-bottom: 20px;
  }
  
  .pull-results,
  .stats-card,
  .continue-buttons {
    padding: 15px;
  }
  
  .results-container {
    grid-template-columns: repeat(3, 1fr);
    padding: 15px;
    min-height: 240px;
  }
  
  .result-item {
    max-width: 120px;
    height: 110px;
    padding: 15px;
  }
  
  .result-star {
    font-size: 20px;
    padding: 6px 12px;
  }
  
  .star-5 .result-star {
    font-size: 24px;
  }
  
  .result-name {
    font-size: 12px;
  }
  
  .star-5 .result-name {
    font-size: 14px;
  }
  
  .button-group,
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-button {
    width: 100%;
    max-width: 300px;
  }
  
  .stats-grid {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .stat-item {
    min-width: 100px;
    padding: 12px 8px;
  }
  
  .stat-value {
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  h1 {
    font-size: 24px;
  }
  
  .pull-results h2,
  .stats-card h2,
  .pull-history h2 {
    font-size: 16px;
  }
  
  .results-container {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .result-item {
    max-width: 100px;
    height: 100px;
  }
  
  .result-star {
    font-size: 18px;
  }
  
  .star-5 .result-star {
    font-size: 22px;
  }
  
  .result-name {
    font-size: 11px;
  }
  
  .star-5 .result-name {
    font-size: 12px;
  }
  
  .action-button {
    padding: 12px 24px;
    font-size: 14px;
  }
}
</style>