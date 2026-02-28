<template>
  <div class="simulation-result">
    <div class="content-container">
      <!-- 右上角按钮 -->
      <div class="action-buttons">
        <button @click="goBack" class="action-button small-action-button">返回</button>
        <button @click="goToMainMenu" class="action-button small-action-button">主菜单</button>
      </div>
      
      <h1>武器活动祈愿结果（自动模拟）</h1>
      
      <div class="result-container">
        <!-- 基本统计信息 -->
        <div class="stats-card">
          <h2>基本统计</h2>
          <div class="stats-grid basic-stats">
            <div class="stat-item">
              <div class="stat-label">总抽取次数</div>
              <div class="stat-value">{{ result.total_pulls }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★总数</div>
              <div class="stat-value">{{ result.total_hits }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★UP武器-1数</div>
              <div class="stat-value warning">{{ result.five_star_up_counts?.['5星UP武器-1'] || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★UP武器-2数</div>
              <div class="stat-value warning">{{ result.five_star_up_counts?.['5星UP武器-2'] || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★常驻武器数</div>
              <div class="stat-value">{{ result.avg_count }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★概率</div>
              <div class="stat-value probability">{{ result.total_pulls > 0 ? ((result.total_hits / result.total_pulls) * 100).toFixed(3) : '0.000' }}%</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★UP概率</div>
              <div class="stat-value probability">{{ result.total_pulls > 0 ? (((result.up_count || 0) / result.total_pulls) * 100).toFixed(3) : '0.000' }}%</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">4★UP武器数</div>
              <div class="stat-value four-star-up">{{ result.four_star_up_count || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">4★常驻武器数</div>
              <div class="stat-value">{{ result.four_star_avg_count || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">4★概率</div>
              <div class="stat-value probability">{{ result.total_pulls > 0 ? (((result.four_star_up_count + result.four_star_avg_count) / result.total_pulls) * 100).toFixed(3) : '0.000' }}%</div>
            </div>
          </div>
        </div>
        
        <!-- 数学统计信息 -->
        <div class="stats-card">
          <h2>数学统计</h2>
          <div class="stats-grid math-stats">
            <div class="stat-item">
              <div class="stat-label">5★UP武器的平均抽数</div>
              <div class="stat-value">{{ (result.stats?.avg_count || 0).toFixed(2) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★UP武器的中位数抽数</div>
              <div class="stat-value">{{ (result.stats?.median_count || 0).toFixed(2) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★UP武器标准差</div>
              <div class="stat-value">{{ (result.stats?.std_count || 0).toFixed(2) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★UP武器最小抽数</div>
              <div class="stat-value">{{ result.stats?.min_count || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">5★UP武器最大抽数</div>
              <div class="stat-value">{{ result.stats?.max_count || 0 }}</div>
            </div>
          </div>
        </div>
        
        <!-- 前10次抽到5星的情况 -->
        <div class="stats-card">
          <h2>前10次抽到5星武器的情况</h2>
          <div class="five-star-list">
            <div v-for="(item, index) in result.five_star_costs.slice(0, 10)" :key="index" class="five-star-item">
              <span class="cost">{{ item.cost }}抽</span>
              <div class="cost-bar" :style="{ width: getBarWidth(item.cost), backgroundColor: getBarColor(item.cost) }"></div>
              <span v-if="!item.is_up" class="is-avg">常驻（歪）</span>
              <span v-else class="is-up">{{ simplifyWeaponName(item.weapon_name) || 'UP' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WeaponSimulationResult',
  data() {
    return {
      result: {
        total_pulls: 0,
        total_hits: 0,
        up_count: 0,
        avg_count: 0,
        five_star_up_counts: {
          '5星UP武器-1': 0,
          '5星UP武器-2': 0
        },
        four_star_up_count: 0,
        four_star_avg_count: 0,
        stats: {
          avg_count: 0,
          median_count: 0,
          std_count: 0,
          min_count: 0,
          max_count: 0
        },
        five_star_costs: []
      }
    }
  },
  mounted() {
    // 从路由参数获取结果
    const resultStr = this.$route.query.result
    
    if (resultStr) {
      try {
        const parsedResult = JSON.parse(resultStr)
        // 限制 five_star_costs 数组长度，优化性能
        const limitedFiveStarCosts = (parsedResult.five_star_costs || []).slice(0, 50)
        
        // 计算 up_count
        const upCount = (parsedResult.five_star_up_counts?.['5星UP武器-1'] || 0) + 
                       (parsedResult.five_star_up_counts?.['5星UP武器-2'] || 0)
        
        // 合并解析结果和默认值，确保所有必要的属性都存在
        this.result = {
          ...this.result,
          ...parsedResult,
          up_count: upCount,
          stats: {
            ...this.result.stats,
            ...(parsedResult.stats || {})
          },
          five_star_costs: limitedFiveStarCosts
        }
      } catch (error) {
        console.error('解析结果失败:', error)
      }
    }
  },
  methods: {
    getBarWidth(cost) {
      // 计算条的宽度，基于抽数比例
      const maxCost = 80
      const minWidth = 15
      const maxWidth = 850
      const widthRatio = Math.min(cost / maxCost, 1)
      return `${minWidth + widthRatio * (maxWidth - minWidth)}px`
    },
    getBarColor(cost) {
      // 根据抽数大小确定颜色
      if (cost <= 30) {
        return '#2ecc71' // 绿色
      } else if (cost <= 63) {
        return '#f9ca24' // 亮色浅橙色
      } else {
        return '#e74c3c' // 红色
      }
    },
    simplifyWeaponName(weaponName) {
      if (!weaponName) return 'UP'
      if (weaponName.includes('5星UP武器-1')) return 'UP-1'
      if (weaponName.includes('5星UP武器-2')) return 'UP-2'
      return weaponName
    },
    goBack() {
      this.$router.push('/weapon')
    },
    goToMainMenu() {
      // 直接跳转，不需要清理数据
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.simulation-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.content-container {
  width: 100%;
  max-width: 1200px;
  padding: 0 20px;
  box-sizing: border-box;
  position: relative;
}

h1 {
  color: #4a4a4a;
  margin-bottom: 30px;
  font-size: 24px;
  text-align: center;
}

.result-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-card {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  width: 100%;
}

.stats-card h2 {
  color: #4a4a4a;
  margin-bottom: 15px;
  font-size: 18px;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
  width: 100%;
}

/* 基本统计的10个数据项 */
.stats-grid.basic-stats {
  grid-template-rows: auto auto auto;
}

.stats-grid.basic-stats .stat-item:nth-child(-n+7) {
  grid-row: 1;
  grid-column: span 1;
}

.stats-grid.basic-stats .stat-item:nth-child(n+8) {
  grid-row: 2;
  grid-column: span 1;
}

/* 数学统计的5个数据项 */
.stats-grid.math-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}

.stats-grid.math-stats .stat-item {
  grid-column: span 1;
  min-width: 150px;
}

.stats-grid .stat-item {
  min-width: 120px;
  max-width: none;
  width: 100%;
}

.stat-item {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  padding: 12px;
  border-radius: 6px;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  font-weight: normal;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
}

.probability {
  color: #e67e22;
}

.success {
  color: #27ae60;
}

.warning {
  color: #ffc107;
}

.four-star-up {
  color: #8b5cf6;
  text-shadow: 0 1px 2px rgba(139, 92, 246, 0.3);
}

.failure {
  color: #e74c3c;
}

.five-star-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.five-star-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cost {
  width: 60px;
  font-weight: bold;
  font-size: 14px;
}

.cost-bar {
  height: 20px;
  border-radius: 10px;
}

.is-avg {
  color: #000000;
  font-weight: bold;
  font-size: 14px;
}

.is-up {
  color: #ffc107;
  font-weight: bold;
  font-size: 14px;
}

.action-buttons {
  position: absolute;
  top: 0;
  right: 20px;
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  z-index: 10;
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

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  border-color: #cbd5e0;
}

.action-button:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-button.small-action-button {
  padding: 10px 24px;
  font-size: 14px;
  min-width: 120px;
  text-transform: none;
  letter-spacing: 0.5px;
}

.action-button.small-action-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}

.action-button.small-action-button:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.exit-button {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  color: #718096;
}

.exit-button:hover {
  border-color: #cbd5e0;
  color: #4a5568;
}

.exit-button:active {
  border-color: #a0aec0;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-button {
    width: 200px;
  }
}
</style>
