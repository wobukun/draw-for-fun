<template>
  <div class="help-page">
    <div class="action-buttons">
      <button @click="goBack" class="action-button">返回</button>
    </div>
    
    <h1>帮助中心</h1>
    
    <div class="help-content">
      <!-- 帮助内容将在这里添加 -->
      <div class="help-section">
        <h2>使用指南</h2>
        <p>这里将添加使用指南的详细内容...</p>
      </div>
      
      <div class="help-section">
        <h2>抽卡规则</h2>
        <p>这里将添加抽卡规则的详细说明...</p>
      </div>
      
      <div class="help-section">
        <h2>常见问题</h2>
        <p>这里将添加常见问题的解答...</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HelpPage',
  methods: {
    goBack() {
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.help-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: relative;
  overflow: hidden;
}

.help-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 10% 20%, rgba(138, 216, 255, 0.1) 0%, rgba(187, 222, 251, 0.05) 90%);
  z-index: 0;
}

.action-buttons {
  position: absolute;
  top: 40px;
  right: 40px;
  z-index: 1;
}

.action-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  color: #2c3e50;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 16px rgba(255, 255, 255, 0.3);
}

.action-button:hover {
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  box-shadow: 0 10px 24px rgba(255, 255, 255, 0.4);
  transform: translateY(-2px);
}

h1 {
  color: #2c3e50;
  margin-top: 80px;
  margin-bottom: 40px;
  font-size: 32px;
  text-align: center;
  font-weight: 700;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 1;
}

.help-content {
  width: 100%;
  max-width: 800px;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
}

.help-section {
  margin-bottom: 30px;
}

.help-section h2 {
  color: #34495e;
  margin-bottom: 15px;
  font-size: 22px;
  font-weight: 600;
}

.help-section p {
  color: #7f8c8d;
  font-size: 16px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  h1 {
    font-size: 24px;
    margin-top: 60px;
    margin-bottom: 30px;
  }
  
  .help-content {
    padding: 20px;
    max-width: 90%;
  }
  
  .help-section h2 {
    font-size: 18px;
  }
  
  .help-section p {
    font-size: 14px;
  }
}
</style>