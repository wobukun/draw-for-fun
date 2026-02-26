<template>
  <div class="goal-probability-intro">
    <div class="content-container">
      <h1>抽取概率计算（Beta）</h1>
      <div class="description">
        <p>本功能通过蒙特卡洛模拟方法估算在指定资源下达成抽卡目标的概率。</p>
        <p>选择您想要抽取的祈愿类型，开始计算吧！</p>
      </div>
      <div class="actions">
        <button @click="goToGoalProbability" class="action-button primary-button">
          <span class="button-icon">🎯</span>
          通过角色/武器活动祈愿抽取
        </button>
        <button @click="goBack" class="action-button secondary-button">
          <span class="button-icon">🔙</span>
          返回
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GoalProbabilityIntro',
  methods: {
    goToGoalProbability() {
      this.$router.push('/goal-probability')
    },
    goBack() {
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.goal-probability-intro {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.content-container {
  width: 100%;
  max-width: 800px;
  text-align: center;
  animation: fadeIn 0.8s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

h1 {
  color: #2c3e50;
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 32px;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.1);
  letter-spacing: 1px;
}

.description {
  background: white;
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 48px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

.description p {
  color: #4a5568;
  font-size: 16px;
  line-height: 1.6;
  margin: 0 0 16px;
}

.description p:last-child {
  margin-bottom: 0;
  font-weight: 500;
  color: #2d3748;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
}

.action-button {
  padding: 16px 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  min-width: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.button-icon {
  font-size: 20px;
}

.primary-button {
  background: linear-gradient(135deg, #4299e1 0%, #63b3ed 100%);
  color: white;
}

.primary-button:hover {
  background: linear-gradient(135deg, #3182ce 0%, #4299e1 100%);
  box-shadow: 0 8px 24px rgba(66, 153, 225, 0.4);
  transform: translateY(-3px);
}

.secondary-button {
  background: white;
  color: #4a5568;
  border: 1px solid #e2e8f0;
}

.secondary-button:hover {
  background: #f8f9fa;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transform: translateY(-3px);
  border-color: #cbd5e0;
}

.action-button:active {
  transform: translateY(0);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .content-container {
    padding: 0 16px;
  }
  
  h1 {
    font-size: 24px;
    margin-bottom: 24px;
  }
  
  .description {
    padding: 24px;
    margin-bottom: 32px;
  }
  
  .actions {
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }
  
  .action-button {
    width: 100%;
    max-width: 300px;
  }
}
</style>
