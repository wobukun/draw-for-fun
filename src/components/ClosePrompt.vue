<template>
  <div class="close-prompt">
    <div class="container">
      <h1>已退出应用</h1>
      <p>您已成功退出抽卡模拟应用。</p>
      <p>请手动关闭此标签页。</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ClosePrompt'
}
</script>

<style scoped>
.close-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  margin: 0;
  padding: 20px;
  font-family: Arial, sans-serif;
  background-color: #f5f5f5;
}

.container {
  background-color: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 500px;
}

h1 {
  color: #333;
  margin-bottom: 20px;
}

p {
  color: #666;
  margin-bottom: 20px;
  line-height: 1.5;
}

p:last-child {
  margin-bottom: 0;
}
</style>