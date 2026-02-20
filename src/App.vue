<template>
  <div class="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  mounted() {
    // 初始化全局变量
    if (typeof window.serverShutdown === 'undefined') {
      window.serverShutdown = false
    }
    
    // 添加多个事件监听器，确保在各种关闭场景下都能触发
    window.addEventListener('beforeunload', this.handleUnloadEvent)
    window.addEventListener('unload', this.handleUnloadEvent)
    window.addEventListener('pagehide', this.handleUnloadEvent)
  },
  beforeUnmount() {
    // 移除事件监听器
    window.removeEventListener('beforeunload', this.handleUnloadEvent)
    window.removeEventListener('unload', this.handleUnloadEvent)
    window.removeEventListener('pagehide', this.handleUnloadEvent)
  },
  methods: {
    handleUnloadEvent() {
      // 当用户关闭浏览器或标签页时，向后端发送shutdown请求
      this.sendShutdownRequest()
    },
    sendShutdownRequest() {
      // 如果服务器已经被关闭，不再发送请求
      if (window.serverShutdown) {
        console.log('服务器已经被关闭，不再发送shutdown请求')
        return
      }
      
      try {
        // 标记服务器为已关闭
        window.serverShutdown = true
        
        // 尝试使用fetch请求发送关闭服务器请求到正确的端点
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
          // 忽略连接被拒绝的错误，因为此时服务器可能已经关闭
          console.log('忽略连接被拒绝的错误，服务器可能已经关闭')
        })
        
        // 尝试使用XMLHttpRequest作为备用
        try {
          const xhr = new XMLHttpRequest()
          xhr.open('POST', '/api/shutdown', true)
          xhr.setRequestHeader('Content-Type', 'application/json')
          xhr.send(JSON.stringify({ action: 'shutdown' }))
          console.log('使用XMLHttpRequest发送关闭服务器请求: 已发送')
        } catch (xhrError) {
          // 忽略连接被拒绝的错误，因为此时服务器可能已经关闭
          console.log('忽略连接被拒绝的错误，服务器可能已经关闭')
        }
      } catch (error) {
        console.log('忽略连接被拒绝的错误，服务器可能已经关闭')
      }
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  color: #333;
  line-height: 1.6;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>