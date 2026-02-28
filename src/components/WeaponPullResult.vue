<template>
  <div class="pull-result">
    <div class="content-container">
      <!-- 右上角按钮 -->
      <div class="action-buttons">
        <button @click="goBack" class="action-button small-action-button">返回</button>
        <button @click="goToMainMenu" class="action-button">主菜单</button>
      </div>
      
      <h1>武器活动祈愿结果</h1>
      
      <div class="main-content">
        <!-- 左侧：历史记录 -->
        <div class="pull-history">
          <h2>历史记录</h2>
          <div class="history-container">
            <div v-for="(item, index) in pullHistory" :key="index" class="history-item" :class="[`star-${item.star}`, { 'history-item-5star': item.star === 5 }]">
              <div class="history-pull-number">{{ result.total_pulls - index }}</div>
              <div class="history-star">{{ item.star }}★</div>
              <div class="history-name" v-if="item.star !== 3">{{ getDisplayName(item) }}</div>
            </div>
          </div>
        </div>
        
        <!-- 右侧：抽卡结果和按钮 -->
        <div class="pull-results-wrapper">
          <!-- 抽卡结果 -->
          <div class="pull-results">
            <h2 class="text-2xl font-bold text-gray-800 mb-5 text-center">本次抽卡结果（点击卡片查看详情）</h2>
            <div class="results-container">
              <div class="results-left">
                <div v-for="(item, index) in displayResults" :key="index" class="result-wrapper">
                  <div class="result-item"
                       :class="[
                         item.star === 3 ? 'star-3' : 
                         item.star === 4 ? 'star-4' : 
                         'star-5',
                         { 'appear-animation': showRefreshAnimation }
                       ]"
                       @click="showItemDetail(item)">
                    <div class="result-name" v-if="item.star !== 3">{{ getResultDisplayName(item) }}</div>
                    <div class="result-star">{{ item.star }}★</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 物品详情模态框 -->
            <div v-if="selectedItem" class="item-detail-modal" @click="closeItemDetail">
              <div class="item-detail-content" @click.stop>
                <div class="item-detail-close" @click="closeItemDetail">×</div>
                <div class="item-detail-card" :class="`star-${selectedItem.star}`">
                  <div class="item-detail-star">{{ selectedItem.star }}★</div>
                  <div class="item-detail-name" :class="`star-${selectedItem.star}`">{{ getResultDisplayName(selectedItem) }}</div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 数学统计信息 -->
          <div class="stats-card">
            <h2>数学统计</h2>
            <div class="stats-compact">
              <div class="stat-row">
                <div class="stat-item-compact">
                  <span class="stat-label-compact">总抽数:</span>
                  <span class="stat-value-compact">{{ result.total_pulls }}</span>
                </div>
                <div class="stat-item-compact">
                  <span class="stat-label-compact">5★UP武器-1数:</span>
                  <span class="stat-value-compact success">{{ result.five_star_up_counts?.['5星UP武器-1'] || 0 }}</span>
                </div>
                <div class="stat-item-compact">
                  <span class="stat-label-compact">5★UP武器-2数:</span>
                  <span class="stat-value-compact success">{{ result.five_star_up_counts?.['5星UP武器-2'] || 0 }}</span>
                </div>
              </div>
              <div class="stat-row">
                <div class="stat-item-compact">
                  <span class="stat-label-compact">5★常驻武器数:</span>
                  <span class="stat-value-compact">{{ result.avg_count }}</span>
                </div>
                <div class="stat-item-compact">
                  <span class="stat-label-compact">4★UP武器数:</span>
                  <span class="stat-value-compact four-star-up">{{ result.four_star_up_count || 0 }}</span>
                </div>
                <div class="stat-item-compact">
                  <span class="stat-label-compact">4★常驻武器数:</span>
                  <span class="stat-value-compact">{{ result.four_star_avg_count || 0 }}</span>
                </div>
              </div>
              <div class="stat-row">
                <div class="stat-item-compact">
                  <span class="stat-label-compact">已连续</span>
                  <span class="stat-value-compact">{{ result.current_pity }}</span>
                  <span class="stat-label-compact">抽未出5★</span>
                </div>
                <div class="stat-item-compact">
                  <span class="stat-label-compact">上一个5★花费:</span>
                  <span class="stat-value-compact">{{ result.last_five_star_cost || 0 }}</span>
                  <span class="stat-label-compact">抽</span>
                </div>
                <div class="stat-item-compact">
                  <span class="stat-label-compact">下次5★必UP:</span>
                  <span class="stat-value-compact">{{ result.guarantee_up ? '是' : '否' }}</span>
                </div>
              </div>
              <div class="stat-row">
                <div class="stat-item-compact">
                  <span class="stat-label-compact">命定值:</span>
                  <span class="stat-value-compact" :class="{ 'blue-text': (result.fate_point || 0) === 1 }">{{ result.fate_point || 0 }}</span>
                </div>
                <div class="stat-item-compact">
                  <span class="stat-label-compact">定轨武器:</span>
                  <span class="stat-value-compact" :class="{ 'fate-weapon-selected': result.selected_fate_weapon }">{{ result.selected_fate_weapon || '未选择' }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 继续抽卡按钮 -->
          <div class="continue-buttons">
            <div class="reset-button-container">
              <button @click="resetGacha" class="action-button small-action-button">重置</button>
            </div>
            <div class="button-group">
              <button @click="showFateWeaponModal" class="action-button fate-button" :disabled="isLoading">{{ isLoading ? '抽卡中...' : '选择定轨武器' }}</button>
              <button @click="setMiguCounterTo3" class="action-button set-migu-button" :disabled="isLoading" style="display: none;">设置捕获明光计数器为3</button>
              <button @click="performSinglePull" class="action-button single-pull" :disabled="isLoading">{{ isLoading ? '抽卡中...' : '单抽' }}</button>
              <button @click="performTenPulls" class="action-button ten-pull" :disabled="isLoading">{{ isLoading ? '抽卡中...' : '十连' }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 定轨武器选择模态框 -->
    <div v-if="showFateModal" class="fate-modal" @click="closeFateModal">
      <div class="fate-modal-content" @click.stop>
        <div class="fate-modal-close" @click="closeFateModal">×</div>
        <h2 class="fate-modal-title">选择定轨武器</h2>
        <div class="fate-point-display" :class="{ 'max': (result.fate_point || 0) >= 1 }">
          命定值：<span class="current-value">{{ result.fate_point || 0 }}</span>/<span class="max-value">1</span>
        </div>
        <div class="fate-options">
          <div 
            v-for="weapon in fateWeaponOptions" 
            :key="weapon.value"
            class="fate-option"
            :class="{ 'selected': tempSelectedFateWeapon === weapon.value }"
            @click="selectFateWeaponAndConfirm(weapon.value)">
            <div class="fate-option-icon">{{ weapon.icon }}</div>
            <div class="fate-option-name">{{ weapon.label }}</div>
            <div v-if="tempSelectedFateWeapon === weapon.value" class="fate-option-check">✓</div>
          </div>
        </div>
        <div class="fate-modal-info">
          <p>选择定轨武器后，当获得非定轨武器时，命定值将增加。命定值达到满值后，下一次获得的5星武器必定为定轨武器。</p>
          <p>更换或取消定轨武器将重置命定值为0。</p>
        </div>
        <button @click="closeFateModal" class="action-button fate-confirm-button">关闭</button>
      </div>
    </div>
    
    <!-- 更换定轨武器确认对话框 -->
    <div v-if="showFateConfirmDialog" class="fate-modal" @click="closeFateConfirmDialog">
      <div class="fate-confirm-dialog" @click.stop>
        <div class="fate-confirm-content">
          <template v-if="confirmMode === 'change'">
            <p class="fate-confirm-question">您确定要更换定轨武器？</p>
            <div class="fate-weapon-row">
              <p class="fate-confirm-weapon">{{ result.selected_fate_weapon }}</p>
              <div class="fate-arrow-wrapper">
                <div class="fate-arrow">➜</div>
              </div>
              <p class="fate-confirm-weapon new">{{ tempSelectedFateWeapon }}</p>
            </div>
            <p class="fate-confirm-warning">⚠️ 更换定轨武器将重置命定值为0</p>
          </template>
          <template v-else-if="confirmMode === 'cancel'">
            <p class="fate-confirm-question">您确定要取消定轨武器？</p>
            <p class="fate-confirm-weapon">{{ result.selected_fate_weapon }}</p>
            <p class="fate-confirm-warning">⚠️ 取消定轨将重置命定值为0</p>
          </template>
          <template v-else>
            <p class="fate-confirm-question">您确定要定轨武器？</p>
            <p class="fate-confirm-weapon new">{{ tempSelectedFateWeapon }}</p>
            <p class="fate-confirm-warning">⚠️ 定轨后，当获得非定轨武器时命定值将增加</p>
          </template>
        </div>
        <div class="fate-confirm-buttons">
          <button @click="confirmFateWeaponChange" class="action-button fate-confirm-button">{{ confirmButtonText }}</button>
          <button @click="cancelFateWeaponChange" class="action-button fate-cancel-button">取消</button>
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
        four_star_pity: 0,
        avg_count: 0,
        five_star_up_counts: {
          '5星UP武器-1': 0,
          '5星UP武器-2': 0
        },
        four_star_up_count: 0,
        four_star_avg_count: 0,
        guarantee_up: false,
        guarantee_four_star_up: false,
        fate_point: 0,
        selected_fate_weapon: null,
        last_five_star_cost: 0
      },
      isLoading: false,
      showRefreshAnimation: false,
      pullHistory: [],
      selectedItem: null,
      showFateModal: false,
      showFateConfirmDialog: false,
      tempSelectedFateWeapon: null,
      fateWeaponOptions: [
        { value: '5星UP武器-1', label: '5星UP武器-1', icon: '⚔️' },
        { value: '5星UP武器-2', label: '5星UP武器-2', icon: '🗡️' },
        { value: null, label: '不定轨', icon: '❌' }
      ]
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
      } else if (this.result.results && this.result.weapon_names) {
        // 十连结果：将多个数组合并为对象数组
        return this.result.results.map((isFiveStar, index) => ({
          star: isFiveStar ? 5 : (this.result.four_star_results[index] ? 4 : 3),
          name: this.result.weapon_names[index],
          is_up: this.result.is_up[index],
          is_four_star_up: this.result.is_four_star_up[index],
          is_fate: this.result.is_fate[index]
        }))
      } else {
        // 单抽新格式：将单个结果转换为对象格式
        return [{
          star: this.result.star,
          name: this.result.name,
          is_up: this.result.is_up,
          is_four_star_up: this.result.is_four_star_up,
          is_fate: this.result.is_fate
        }]
      }
    },
    confirmMode() {
      if (this.result.selected_fate_weapon && this.tempSelectedFateWeapon === null) {
        return 'cancel'
      } else if (this.result.selected_fate_weapon && this.tempSelectedFateWeapon !== null) {
        return 'change'
      } else {
        return 'set'
      }
    },
    confirmDialogTitle() {
      if (this.confirmMode === 'cancel') {
        return '确认取消定轨'
      } else if (this.confirmMode === 'change') {
        return '确认更换定轨武器'
      } else {
        return '确认定轨武器'
      }
    },
    confirmButtonText() {
      return '确认'
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
          axios.post('/api/wish', {
            mode: 'weapon',
            action: 'one',
            current_pity: this.result.current_pity || 0,
            four_star_pity: this.result.four_star_pity || 0,
            avg_count: this.result.avg_count || 0,
            five_star_up_counts: this.result.five_star_up_counts || { '5星UP武器-1': 0, '5星UP武器-2': 0 },
            four_star_up_count: this.result.four_star_up_count || 0,
            four_star_avg_count: this.result.four_star_avg_count || 0,
            guarantee_up: this.result.guarantee_up || false,
            guarantee_four_star_up: this.result.guarantee_four_star_up || false,
            fate_point: this.result.fate_point || 0,
            selected_fate_weapon: this.result.selected_fate_weapon || null,
            total_pulls: this.result.total_pulls || 0,
            last_five_star_cost: this.result.last_five_star_cost || 0
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
          axios.post('/api/wish', {
            mode: 'weapon',
            action: 'ten',
            current_pity: this.result.current_pity || 0,
            four_star_pity: this.result.four_star_pity || 0,
            avg_count: this.result.avg_count || 0,
            five_star_up_counts: this.result.five_star_up_counts || { '5星UP武器-1': 0, '5星UP武器-2': 0 },
            four_star_up_count: this.result.four_star_up_count || 0,
            four_star_avg_count: this.result.four_star_avg_count || 0,
            guarantee_up: this.result.guarantee_up || false,
            guarantee_four_star_up: this.result.guarantee_four_star_up || false,
            fate_point: this.result.fate_point || 0,
            selected_fate_weapon: this.result.selected_fate_weapon || null,
            total_pulls: this.result.total_pulls || 0,
            last_five_star_cost: this.result.last_five_star_cost || 0
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
        four_star_pity: 0,
        avg_count: 0,
        five_star_up_counts: {
          '5星UP武器-1': 0,
          '5星UP武器-2': 0
        },
        four_star_up_count: 0,
        four_star_avg_count: 0,
        guarantee_up: false,
        guarantee_four_star_up: false,
        fate_point: 0,
        selected_fate_weapon: null,
        last_five_star_cost: 0
      }
      // 清空抽卡历史
      this.pullHistory = []
      // 重置动画状态
      this.showRefreshAnimation = false
    },
    updatePullHistory(data) {
      // 处理单抽和十连的不同数据结构
      if (data.results && data.weapon_names) {
        // 十连结果
        data.results.forEach((isFiveStar, index) => {
          const star = isFiveStar ? 5 : (data.four_star_results[index] ? 4 : 3)
          this.pullHistory.unshift({
            star: star,
            name: data.weapon_names[index],
            is_fate: data.is_fate[index]
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
    },
    setMiguCounterTo3() {
      // 武器池不需要捕获明光功能，此方法保留以保持结构一致
    },
    showItemDetail(item) {
      this.selectedItem = item
    },
    closeItemDetail() {
      this.selectedItem = null
    },
    getDisplayName(item) {
      if (item.star === 4) {
        const name = item.name
        if (name.includes('4星UP武器')) {
          return '4星UP'
        } else if (name.includes('4星常驻武器')) {
          return '4星常驻'
        }
        return name
      } else if (item.star === 5) {
        const name = item.name
        if (name.includes('5星UP武器-1')) {
          return 'UP-1'
        } else if (name.includes('5星UP武器-2')) {
          return 'UP-2'
        } else if (name.includes('5星常驻武器')) {
          return '常驻'
        }
        return name
      }
      return item.name
    },
    getResultDisplayName(item) {
      if (item.star === 4) {
        const name = item.name
        if (name.includes('4星UP武器')) {
          return '4星UP'
        } else if (name.includes('4星常驻武器')) {
          return '4星常驻'
        }
        return name
      } else if (item.star === 5) {
        const name = item.name
        if (name.includes('5星UP武器-1')) {
          return 'UP-1'
        } else if (name.includes('5星UP武器-2')) {
          return 'UP-2'
        } else if (name.includes('5星常驻武器')) {
          return '常驻'
        }
        return name
      }
      return item.name
    },
    showFateWeaponModal() {
      this.tempSelectedFateWeapon = this.result.selected_fate_weapon
      this.showFateModal = true
    },
    closeFateModal() {
      this.showFateModal = false
      this.tempSelectedFateWeapon = null
    },
    selectFateWeaponTemp(weaponValue) {
      this.tempSelectedFateWeapon = weaponValue
    },
    selectFateWeaponAndConfirm(weaponValue) {
      this.tempSelectedFateWeapon = weaponValue
      if (weaponValue !== this.result.selected_fate_weapon) {
        this.showFateConfirmDialog = true
      }
    },
    confirmFateWeapon() {
      if (this.result.selected_fate_weapon === null) {
        this.result.selected_fate_weapon = this.tempSelectedFateWeapon
        this.closeFateModal()
      } else if (this.tempSelectedFateWeapon !== this.result.selected_fate_weapon) {
        this.showFateConfirmDialog = true
      } else {
        this.closeFateModal()
      }
    },
    closeFateConfirmDialog() {
      this.showFateConfirmDialog = false
    },
    cancelFateWeaponChange() {
      this.tempSelectedFateWeapon = this.result.selected_fate_weapon
      this.showFateConfirmDialog = false
    },
    confirmFateWeaponChange() {
      if (this.result.selected_fate_weapon !== null) {
        this.result.fate_point = 0
      }
      this.result.selected_fate_weapon = this.tempSelectedFateWeapon
      this.showFateConfirmDialog = false
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




@keyframes glow {
  from {
    box-shadow: 0 0 5px #ff6b81, 0 0 10px #ff6b81;
  }
  to {
    box-shadow: 0 0 10px #ff6b81, 0 0 20px #ff6b81, 0 0 30px #ff6b81;
  }
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
  display: flex;
  align-items: center;
  z-index: 10;
  margin-right: auto;
  margin-left: -20px;
}

.small-action-button {
  padding: 14px 24px !important;
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

/* 3星记录的特殊样式 */
.history-item.star-3 {
  background: linear-gradient(135deg, #f0f9ff 0%, #e2e8f0 100%);
  border: 1px solid #93c5fd;
  box-shadow: 0 2px 8px rgba(147, 197, 253, 0.2);
}

/* 4星记录的特殊样式 */
.history-item.star-4 {
  background: linear-gradient(135deg, #f5f3ff 0%, #e2e8f0 100%);
  border: 1px solid #8b5cf6;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.2);
}

/* 5星记录的特殊样式 */
.history-item.star-5 {
  background: linear-gradient(135deg, #fffbeb 0%, #ffeb3b 100%);
  border: 1px solid #ffd700;
  box-shadow: 0 4px 16px rgba(255, 215, 0, 0.3);
}

/* 抽数显示 */
.history-pull-number {
  font-size: 11px;
  font-weight: bold;
  width: 45px;
  text-align: center;
  color: #475569;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  padding: 2px 4px;
  border: 1px solid #e2e8f0;
  box-sizing: border-box;
}

.history-star {
  font-size: 12px;
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
  color: #60a5fa;
  background: rgba(239, 246, 255, 0.9);
  border: 1px solid #bfdbfe;
}

.history-name {
  font-size: 13px;
  color: #2d3748;
  font-weight: 600;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  position: relative;
  z-index: 1;
  text-align: right;
}

.history-item.star-5 .history-name {
  color: #92400e;
  font-weight: 700;
}

.history-item.star-4 .history-name {
  color: #5b21b6;
  font-weight: 600;
}

.history-item.star-3 .history-name {
  color: #1e40af;
  font-weight: 600;
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
  background: rgba(255,255, 255, 0.98);
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.pull-results h2 {
  text-align: center;
  margin: 0 auto 20px;
  width: 100%;
  font-size: 20px;
}

.results-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 320px;
  width: 100%;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 249, 250, 0.8) 100%);
  border-radius: 16px;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  box-sizing: border-box;
  overflow: visible;
}

.results-left {
  flex: 1;
  display: flex;
  flex-direction: row;
  gap: 5px;
  align-items: center;
  padding: 5px;
  width: 100%;
  height: 100%;
  justify-content: flex-start;
  overflow-x: auto;
}

/* 结果卡片样式 */
.result-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 70px;
  height: 260px;
  overflow: visible;
}

.result-item {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 240, 240, 0.9) 100%);
  border-radius: 8px;
  padding: 12px 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 0 20px rgba(255, 255, 255, 0.3);
  text-align: center;
  width: 100%;
  height: 260px;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: stretch;
  backdrop-filter: blur(10px);
  cursor: pointer;
  box-sizing: border-box;
}

.result-item:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2), 0 0 30px rgba(255, 255, 255, 0.4);
  z-index: 10;
}

/* 3星结果样式 */
.result-item.star-3 {
  border-color: #93c5fd;
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
  box-shadow: 0 4px 15px rgba(147, 197, 253, 0.2), 0 0 20px rgba(147, 197, 253, 0.1);
}

.result-item.star-3::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #93c5fd, #bfdbfe, #93c5fd);
}

/* 4星结果样式 */
.result-item.star-4 {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #f5f3ff 0%, #ffffff 100%);
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.2), 0 0 20px rgba(139, 92, 246, 0.1);
}

.result-item.star-4::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #8b5cf6, #a78bfa, #8b5cf6);
}

/* 5星结果样式 */
.result-item.star-5 {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.3), 0 0 30px rgba(245, 158, 11, 0.2);
  position: relative;
}

.result-item.star-5::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b);
  animation: shine 3s ease-in-out infinite;
}

.result-item.star-5:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2), 0 0 30px rgba(255, 255, 255, 0.4);
  z-index: 10;
}

.result-name {
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  line-height: 1.2;
  word-wrap: break-word;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: break-word;
  padding: 0 2px;
  min-height: 40px;
  overflow: visible;
  display: block;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
  box-sizing: border-box;
  align-self: center;
  width: 98%;
  margin-bottom: 13px;
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  color: #2d3748;
  margin-top: 4px;
  line-height: 1.2;
  max-width: 100%;
}

.result-star {
  font-size: 18px;
  font-weight: bold;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
  padding: 0;
  transition: all 0.3s ease;
  text-align: center;
  align-self: center;
  margin-bottom: 10px;
  margin-top: auto;
}

.star-3 .result-name {
  color: #60a5fa;
  text-shadow: 0 0 5px rgba(96, 165, 250, 0.3);
}

.star-4 .result-name {
  color: #8b5cf6;
  text-shadow: 0 0 5px rgba(139, 92, 246, 0.3);
}

.star-5 .result-name {
  color: #f59e0b;
  text-shadow: 0 0 5px rgba(245, 158, 11, 0.3);
}

.star-3 .result-star {
  color: #60a5fa;
  font-size: 18px;
  text-shadow: 0 0 10px rgba(96, 165, 250, 0.4);
}

.star-4 .result-star {
  color: #8b5cf6;
  font-size: 18px;
  text-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
}

.star-5 .result-star {
  color: #f59e0b;
  font-size: 22px;
  text-shadow: 0 0 15px rgba(245, 158, 11, 0.6);
  animation: star-glow 2s ease-in-out infinite alternate;
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

.stats-compact {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
}

.stat-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.stat-item-compact {
  display: flex;
  align-items: center;
  gap: 3px;
  width: calc(33.333% - 6.666px);
  min-width: 160px;
}

.stat-label-compact {
  font-size: 15px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

.stat-value-compact {
  font-size: 15px;
  font-weight: 700;
  color: #2d3748;
}

.stat-value-compact.success {
  color: #f59e0b;
  text-shadow: 0 1px 2px rgba(252, 211, 77, 0.3);
}

.stat-value-compact.four-star-up {
  color: #8b5cf6;
  text-shadow: 0 1px 2px rgba(139, 92, 246, 0.3);
}

.stat-value-compact.blue-text {
  color: #60a5fa;
  text-shadow: 0 1px 2px rgba(59, 130, 246, 0.3);
}

.stat-value-compact.fate-weapon-selected {
  color: #f59e0b;
  text-shadow: 0 1px 2px rgba(245, 158, 11, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stat-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .stat-item-compact {
    min-width: 100%;
  }
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
  gap: 50px;
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

.action-button.set-migu-button {
  background: linear-gradient(135deg, #ffffff 0%, #fef3c7 100%);
  color: #2d3748;
  border-color: #fcd34d;
  box-shadow: 0 4px 12px rgba(252, 211, 77, 0.2);
}

.action-button.set-migu-button:hover {
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

/* 物品详情模态框样式 */
.item-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.item-detail-content {
  position: relative;
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: scaleIn 0.3s ease;
  max-width: 400px;
  width: 90%;
}

@keyframes scaleIn {
  from {
    transform: scale(0.8);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.item-detail-close {
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 30px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.3s ease;
  line-height: 1;
}

.item-detail-close:hover {
  color: #f59e0b;
  transform: rotate(90deg);
}

.item-detail-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.item-detail-card.star-3 {
  border-color: #93c5fd;
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
  box-shadow: 0 8px 24px rgba(147, 197, 253, 0.3);
}

.item-detail-card.star-4 {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #f5f3ff 0%, #ffffff 100%);
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.3);
}

.item-detail-card.star-5 {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.3);
}

.item-detail-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 6px;
}

.item-detail-card.star-3::before {
  background: linear-gradient(90deg, #93c5fd, #bfdbfe);
}

.item-detail-card.star-4::before {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.item-detail-card.star-5::before {
  background: linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b);
  animation: shine 3s ease-in-out infinite;
}

.item-detail-star {
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 20px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.item-detail-card.star-3 .item-detail-star {
  color: #60a5fa;
  text-shadow: 0 0 20px rgba(96, 165, 250, 0.6);
}

.item-detail-card.star-4 .item-detail-star {
  color: #8b5cf6;
  text-shadow: 0 0 20px rgba(139, 92, 246, 0.6);
}

.item-detail-card.star-5 .item-detail-star {
  color: #f59e0b;
  text-shadow: 0 0 20px rgba(245, 158, 11, 0.6);
  animation: star-glow 2s ease-in-out infinite alternate;
}

.item-detail-name {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 16px;
  text-align: center;
}

.item-detail-card.star-3 .item-detail-name {
  color: #60a5fa;
}

.item-detail-card.star-4 .item-detail-name {
  color: #8b5cf6;
}

.item-detail-card.star-5 .item-detail-name {
  color: #f59e0b;
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

/* 定轨武器选择模态框样式 */
.fate-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

.fate-modal-content {
  position: relative;
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: scaleIn 0.3s ease;
  max-width: 500px;
  width: 90%;
}

.fate-modal-close {
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 30px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.3s ease;
  line-height: 1;
}

.fate-modal-close:hover {
  color: #f59e0b;
  transform: rotate(90deg);
}

.fate-modal-title {
  color: #2d3748;
  margin-bottom: 15px;
  font-size: 24px;
  text-align: center;
  font-weight: 700;
}

.fate-point-display {
  text-align: center;
  font-size: 16px;
  font-weight: 700;
  color: #4a5568;
  margin-bottom: 20px;
  padding: 8px 16px;
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  display: inline-block;
}

.fate-point-display .current-value {
  color: #4a5568;
}

.fate-point-display .max-value {
  color: #60a5fa;
}

.fate-point-display.max {
  background: #ffffff;
  border: 2px solid #60a5fa;
  animation: glow-pulse 1.5s ease-in-out infinite;
}

.fate-point-display.max .current-value,
.fate-point-display.max .max-value {
  color: #60a5fa;
}

@keyframes glow-pulse {
  0%, 100% {
    box-shadow: 0 0 8px rgba(96, 165, 250, 0.4);
  }
  50% {
    box-shadow: 0 0 20px rgba(96, 165, 250, 0.8);
  }
}

.fate-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 25px;
}

.fate-option {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
}

.fate-option:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  border-color: #cbd5e0;
}

.fate-option.selected {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.fate-option-icon {
  font-size: 32px;
  width: 50px;
  text-align: center;
}

.fate-option-name {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
}

.fate-option-check {
  font-size: 24px;
  color: #3b82f6;
  font-weight: bold;
}

.fate-modal-info {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  padding: 15px 20px;
  border-radius: 12px;
  margin-bottom: 25px;
  border: 1px solid #93c5fd;
}

.fate-modal-info p {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #1e40af;
  line-height: 1.6;
}

.fate-modal-info p:last-child {
  margin-bottom: 0;
}

.fate-button {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #1e40af;
  border-color: #93c5fd;
  box-shadow: 0 4px 12px rgba(147, 197, 253, 0.2);
}

.fate-button:hover {
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  box-shadow: 0 8px 20px rgba(147, 197, 253, 0.3);
  border-color: #60a5fa;
}

.fate-confirm-button {
  width: 100%;
  padding: 14px 44px;
  font-size: 16px;
  font-weight: bold;
}

.fate-confirm-dialog {
  position: relative;
  background: white;
  border-radius: 20px;
  padding: 35px 50px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: scaleIn 0.3s ease;
  max-width: 500px;
  width: 90%;
  text-align: center;
}

.fate-confirm-title {
  color: #2d3748;
  margin-bottom: 20px;
  font-size: 22px;
  font-weight: 700;
}

.fate-confirm-content {
  margin-bottom: 25px;
}

.fate-confirm-content p {
  margin: 8px 0;
  font-size: 15px;
  color: #4a5568;
}

.fate-confirm-weapon {
  font-size: 18px;
  font-weight: 700;
  color: #f59e0b !important;
  padding: 8px 16px;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-radius: 8px;
  display: inline-block;
  margin: 5px 0;
}

.fate-confirm-weapon.new {
  color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.fate-confirm-content .fate-confirm-question {
  font-weight: 700;
  font-size: 20px;
}

.fate-confirm-warning {
  color: #dc2626;
  font-weight: 600;
  margin-top: 15px;
  font-size: 14px;
}

.fate-weapon-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin: 10px 0;
}

.fate-arrow-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.fate-arrow {
  font-size: 20px;
  color: #f59e0b;
  font-weight: bold;
  line-height: 1;
}

.fate-confirm-buttons {
  display: flex;
  gap: 50px;
  justify-content: center;
}

.fate-cancel-button {
  padding: 12px 32px;
  font-size: 15px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-color: #cbd5e1;
  color: #475569;
  min-width: auto;
}

.fate-cancel-button:hover {
  background: linear-gradient(135deg, #e2e8f0 0%, #f1f5f9 100%);
}

.fate-confirm-buttons .fate-confirm-button {
  padding: 12px 32px;
  font-size: 15px;
  min-width: auto;
  width: auto;
  background: linear-gradient(135deg, #fef9c3 0%, #fde68a 100%);
  border-color: #fde68a;
  color: #92400e;
}

.fate-confirm-buttons .fate-confirm-button:hover {
  background: linear-gradient(135deg, #fef9c3 0%, #fde68a 100%);
}
</style>