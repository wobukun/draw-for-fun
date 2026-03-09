<template>
  <div class="goal-probability">
    <div class="content-container">
      <div class="header">
        <h1>抽取概率计算（角色/武器活动祈愿）（Beta）</h1>
        <div class="header-actions">
          <button class="header-button" @click="goBackToPrevious">返回</button>
          <button class="header-button" @click="goBack">返回主菜单</button>
        </div>
      </div>

      <div class="card">
        <h2>输入您的资源与目标</h2>
        <div class="form-grid">
          <div class="form-group">
            <label for="resources">拥有的<span class="gradient-text-fate">纠缠之缘</span>数量</label>
            <input
              id="resources"
              type="number"
              min="0"
              max="9999999"
              v-model.number="form.resources"
            />
            <p class="helper-text">1 纠缠之缘 = 1 抽，可在角色池或武器池中自由分配。</p>
          </div>

          <div class="form-group">
            <label for="primogems">拥有的<span class="light-blue-text">原石</span>数量</label>
            <input
              id="primogems"
              type="number"
              min="0"
              max="9999999"
              v-model.number="form.primogems"
            />
            <p class="helper-text">160 原石 = 1 纠缠之缘</p>
          </div>

          <div class="form-group">
            <label for="crystals">拥有的<span class="light-blue-text">创世结晶</span>数量</label>
            <input
              id="crystals"
              type="number"
              min="0"
              max="9999999"
              v-model.number="form.crystals"
            />
            <p class="helper-text">1 创世结晶 = 1 原石</p>
          </div>

          <div class="form-group">
            <div class="toggle-row">
              <label class="toggle-label">
                <input
                  type="checkbox"
                  v-model="form.includeCharacter1"
                  @change="onCharacter1Toggle"
                />
                <span>本次抽取<span class="gold-text">5⭐UP角色-1</span><span class="type-icon character-icon">👤</span></span>
              </label>
            </div>
            <label for="character1-target">
              目标<span style="color: #e8b4b8;">命之座层数</span>（UP角色-1）
            </label>
            <input
              id="character1-target"
              type="number"
              min="0"
              max="6"
              :disabled="!form.includeCharacter1"
              v-model.number="form.targetCharacterConstellation1"
            />
            <p class="helper-text">
              0命=1个角色，6命=7个角色。
            </p>
          </div>

          <div class="form-group">
            <div class="toggle-row">
              <label class="toggle-label">
                <input
                  type="checkbox"
                  v-model="form.includeCharacter2"
                  @change="onCharacter2Toggle"
                />
                <span>本次抽取<span class="gold-text">5⭐UP角色-2</span><span class="type-icon character-icon">👤</span></span>
              </label>
            </div>
            <label for="character2-target">
              目标<span style="color: #e8b4b8;">命之座层数</span>（UP角色-2）
            </label>
            <input
              id="character2-target"
              type="number"
              min="0"
              max="6"
              :disabled="!form.includeCharacter2"
              v-model.number="form.targetCharacterConstellation2"
            />
            <p class="helper-text">
              0命=1个角色，6命=7个角色。
            </p>
          </div>

          <div class="form-group">
            <div class="toggle-row">
              <label class="toggle-label">
                <input
                  type="checkbox"
                  v-model="form.includeWeapon1"
                  @change="onWeapon1Toggle"
                />
                <span>本次抽取<span class="gold-text">5⭐UP武器-1</span><span class="type-icon weapon-icon">⚔️</span></span>
              </label>
            </div>
            <label for="weapon1-target">
              目标<span style="color: #e8b4b8;">精炼等级</span>（UP武器-1）
            </label>
            <input
              id="weapon1-target"
              type="number"
              min="1"
              max="5"
              :disabled="!form.includeWeapon1"
              v-model.number="form.targetWeaponRefinement1"
            />
            <p class="helper-text">
              1精=1把武器，5精=5把武器。
            </p>
          </div>

          <div class="form-group">
            <div class="toggle-row">
              <label class="toggle-label">
                <input
                  type="checkbox"
                  v-model="form.includeWeapon2"
                  @change="onWeapon2Toggle"
                />
                <span>本次抽取<span class="gold-text">5⭐UP武器-2</span><span class="type-icon weapon-icon">⚔️</span></span>
              </label>
            </div>
            <label for="weapon2-target">
              目标<span style="color: #e8b4b8;">精炼等级</span>（UP武器-2）
            </label>
            <input
              id="weapon2-target"
              type="number"
              min="1"
              max="5"
              :disabled="!form.includeWeapon2"
              v-model.number="form.targetWeaponRefinement2"
            />
            <p class="helper-text">
              1精=1把武器，5精=5把武器。
            </p>
          </div>

        </div>

        <div class="extra-options-section">
          <div class="extra-options-title">额外计算选项</div>
          <div class="extra-options-grid">
            <div class="checkbox-item">
              <input
                type="checkbox"
                id="calculateExpectedPulls"
                v-model="form.calculateExpectedPulls"
              >
              <label for="calculateExpectedPulls">计算达成目标所需总抽数（期望）</label>
            </div>
            <div class="checkbox-item">
              <input
                type="checkbox"
                id="calculateRequiredPulls"
                v-model="form.calculateRequiredPulls"
              >
              <label for="calculateRequiredPulls">计算达成目标所需总抽数（保底）</label>
            </div>
          </div>
        </div>

        <div class="actions">
          <button
            class="calculate-button"
            :disabled="isLoading"
            @click="calculate"
          >
            <span v-if="!isLoading">
              <span v-if="form.calculateRequiredPulls || form.calculateExpectedPulls">开始计算（包含额外抽数计算，时间较长）</span>
              <span v-else>开始计算</span>
            </span>
            <span v-else>计算中，请稍候...</span>
          </button>
        </div>
      </div>

      <div v-if="errorMessage" class="card error-card">
        <h2>提示</h2>
        <p class="error-message">{{ errorMessage }}</p>
      </div>

      <div v-if="result" class="card result-card results-section">
        <h2>计算结果</h2>

        <div class="result-summary">
          <div class="summary-item">
            <div class="summary-label">资源</div>
            <div class="summary-value">{{ result.resources }} 抽</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">5星UP角色-1</div>
            <div class="summary-value">
              <span v-if="result.targets.five_star_up_character_1 > 0">
                {{ result.targets.five_star_up_character_1 - 1 }} 命（{{ result.targets.five_star_up_character_1 }} 个）
              </span>
              <span v-else>无目标</span>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-label">5星UP角色-2</div>
            <div class="summary-value">
              <span v-if="result.targets.five_star_up_character_2 > 0">
                {{ result.targets.five_star_up_character_2 - 1 }} 命（{{ result.targets.five_star_up_character_2 }} 个）
              </span>
              <span v-else>无目标</span>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-label">5星UP武器-1</div>
            <div class="summary-value">
              <span v-if="result.targets.five_star_up_weapon_1 > 0">
                {{ result.targets.five_star_up_weapon_1 }} 精（{{ result.targets.five_star_up_weapon_1 }} 把）
              </span>
              <span v-else>无目标</span>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-label">5星UP武器-2</div>
            <div class="summary-value">
              <span v-if="result.targets.five_star_up_weapon_2 > 0">
                {{ result.targets.five_star_up_weapon_2 }} 精（{{ result.targets.five_star_up_weapon_2 }} 把）
              </span>
              <span v-else>无目标</span>
            </div>
          </div>
        </div>

        <div class="probability-section probability-top">
          <h3>达成目标概率（先角色，后武器策略）</h3>
          <div class="probability-main">
            <div class="probability-value">
              {{ result.best.probability * 100 < 0.01 ? '<0.01%' : (result.best.probability * 100).toFixed(2) + '%' }}
            </div>
            <div class="probability-detail">
              95% 置信区间：
              {{ (result.best.ci95_wilson[0] * 100).toFixed(2) }}%
              ~
              {{ (result.best.ci95_wilson[1] * 100).toFixed(2) }}%
            </div>
            <div class="probability-detail secondary">
              模拟次数（实际使用）：{{ result.best.trials_used }} 次
            </div>
          </div>
        </div>

        <div v-if="requiredPullsFor50Percent" class="probability-section section-with-separator">
          <div class="section-divider"></div>
          <h3>达成目标所需总抽数（期望，按50%概率分位计算）：</h3>
          <div class="probability-main">
            <div class="probability-value">
              {{ requiredPullsFor50Percent.required_pulls }}
            </div>
            <div class="probability-detail">
              达成目标概率达到50%时所需总抽数
            </div>

          </div>
        </div>
        
        <div v-if="requiredPullsFor50Percent" class="probability-section">
          <h3>期望仍需抽数</h3>
          <div class="probability-main">
            <div class="probability-value">
              {{ requiredPullsFor50Percent.remaining_pulls }}
            </div>
            <div class="probability-detail">
              期望仍需金额（粗略估计）：¥{{ requiredPullsFor50Percent.remaining_amount_min.toFixed(2) }} ~ ¥{{ requiredPullsFor50Percent.remaining_amount_max.toFixed(2) }}
            </div>
          </div>
        </div>
        
        <div v-if="requiredPullsFor95Percent" class="probability-section section-with-separator">
          <div class="section-divider"></div>
          <h3>达成目标所需总抽数（保底，按95%概率分位计算）：</h3>
          <div class="probability-main">
            <div class="probability-value">
              {{ requiredPullsFor95Percent.required_pulls }}
            </div>
            <div class="probability-detail">
              达成目标概率达到95%时所需总抽数
            </div>

          </div>
        </div>
        
        <div v-if="requiredPullsFor95Percent" class="probability-section">
          <h3>保底仍需抽数</h3>
          <div class="probability-main">
            <div class="probability-value">
              {{ requiredPullsFor95Percent.remaining_pulls }}
            </div>
            <div class="probability-detail">
              保底仍需金额（粗略估计）：¥{{ requiredPullsFor95Percent.remaining_amount_min.toFixed(2) }} ~ ¥{{ requiredPullsFor95Percent.remaining_amount_max.toFixed(2) }}
            </div>
          </div>
        </div>

        <!-- 返回顶部按钮 -->
        <button class="back-to-top" @click="scrollToTop" v-show="showBackToTop">
          TOP
        </button>

        <p class="beta-note">
          本功能为 Beta 版，仅通过蒙特卡洛模拟做近似估计，结果存在随机波动，仅供娱乐与参考。
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'GoalProbability',
  data() {
    return {
      form: {
        resources: 0,
        primogems: 0,
        crystals: 0,
        targetCharacterConstellation1: 0,
        targetCharacterConstellation2: 0,
        targetWeaponRefinement1: 1,
        targetWeaponRefinement2: 1,
        trials: 5000,
        includeCharacter1: true,
        includeCharacter2: false,
        includeWeapon1: true,
        includeWeapon2: false,
        calculateRequiredPulls: false,
        calculateExpectedPulls: false
      },
      isLoading: false,
      errorMessage: '',
      result: null,
      requiredPullsFor95Percent: null,
      requiredPullsFor50Percent: null,
      showBackToTop: false,
      cancelToken: null,
      isMounted: true
    }
  },
  methods: {
    goBack() {
      this.$router.push('/')
    },
    goBackToPrevious() {
      this.$router.back()
    },
    validateForm() {
      // 验证纠缠之缘数范围
      if (this.form.resources === null || this.form.resources < 0 || this.form.resources > 9999999) {
        return '纠缠之缘数量必须在 0 - 9999999 之间。'
      }
      
      // 验证原石数范围
      if (this.form.primogems === null || this.form.primogems < 0 || this.form.primogems > 9999999) {
        return '原石数量必须在 0 - 9999999 之间。'
      }
      
      // 验证创世结晶数范围
      if (this.form.crystals === null || this.form.crystals < 0 || this.form.crystals > 9999999) {
        return '创世结晶数量必须在 0 - 9999999 之间。'
      }
      
      // 5星UP角色-1：仅在勾选时校验，命之座范围 0-6
      if (this.form.includeCharacter1) {
        if (
          this.form.targetCharacterConstellation1 === null ||
          this.form.targetCharacterConstellation1 < 0 ||
          this.form.targetCharacterConstellation1 > 6
        ) {
          return '命之座层数必须在 0 - 6 之间。'
        }
      }
      
      // 5星UP角色-2：仅在勾选时校验，命之座范围 0-6
      if (this.form.includeCharacter2) {
        if (
          this.form.targetCharacterConstellation2 === null ||
          this.form.targetCharacterConstellation2 < 0 ||
          this.form.targetCharacterConstellation2 > 6
        ) {
          return '命之座层数必须在 0 - 6 之间。'
        }
      }
      
      // 5星UP武器-1：仅在勾选时校验，精炼范围 1-5
      if (this.form.includeWeapon1) {
        if (
          this.form.targetWeaponRefinement1 === null ||
          this.form.targetWeaponRefinement1 < 1 ||
          this.form.targetWeaponRefinement1 > 5
        ) {
          return '精炼等级必须在 1 - 5 之间。'
        }
      }
      
      // 5星UP武器-2：仅在勾选时校验，精炼范围 1-5
      if (this.form.includeWeapon2) {
        if (
          this.form.targetWeaponRefinement2 === null ||
          this.form.targetWeaponRefinement2 < 1 ||
          this.form.targetWeaponRefinement2 > 5
        ) {
          return '精炼等级必须在 1 - 5 之间。'
        }
      }
      
      // 至少选择一个目标
      if (!this.form.includeCharacter1 && !this.form.includeCharacter2 && 
          !this.form.includeWeapon1 && !this.form.includeWeapon2) {
        return '请至少选择一个目标（角色或武器）。'
      }
      
      return ''
    },
    onCharacter1Toggle() {
      if (this.form.includeCharacter1 && this.form.targetCharacterConstellation1 === null) {
        this.form.targetCharacterConstellation1 = 0
      }
    },
    onCharacter2Toggle() {
      if (this.form.includeCharacter2 && this.form.targetCharacterConstellation2 === null) {
        this.form.targetCharacterConstellation2 = 0
      }
    },
    onWeapon1Toggle() {
      if (this.form.includeWeapon1 && this.form.targetWeaponRefinement1 === null) {
        this.form.targetWeaponRefinement1 = 1
      }
    },
    onWeapon2Toggle() {
      if (this.form.includeWeapon2 && this.form.targetWeaponRefinement2 === null) {
        this.form.targetWeaponRefinement2 = 1
      }
    },
    calculate() {
      // 取消之前的请求
      if (this.cancelToken) {
        this.cancelToken.cancel('Operation canceled by user')
      }
      
      // 创建新的取消令牌
      this.cancelToken = axios.CancelToken.source()
      
      this.errorMessage = ''
      const msg = this.validateForm()
      if (msg) {
        this.errorMessage = msg
        return
      }
      this.isLoading = true
      this.result = null

      const payload = {
        resources: this.form.resources || 0,
        primogems: this.form.primogems || 0,
        crystals: this.form.crystals || 0,
        strategy: "character_then_weapon",
        trials: this.form.trials,
        // 命之座层数和精炼等级
        target_character_constellation_1: this.form.targetCharacterConstellation1 || 0,
        target_character_constellation_2: this.form.targetCharacterConstellation2 || 0,
        target_weapon_refinement_1: this.form.targetWeaponRefinement1 || 1,
        target_weapon_refinement_2: this.form.targetWeaponRefinement2 || 1,
        // 是否包含该目标
        include_character_1: this.form.includeCharacter1,
        include_character_2: this.form.includeCharacter2,
        include_weapon_1: this.form.includeWeapon1,
        include_weapon_2: this.form.includeWeapon2
      }

      // 准备API调用
      const apiCalls = [
        // 计算达成目标概率
        axios.post('/api/goal_probability', payload, {
          cancelToken: this.cancelToken.token
        })
      ]
      
      // 根据用户选择决定是否添加50%概率所需抽数（期望）的计算
      if (this.form.calculateExpectedPulls) {
        const expectedPullsPayload = {
          resources: this.form.resources || 0,
          primogems: this.form.primogems || 0,
          crystals: this.form.crystals || 0,
          target_character_constellation_1: this.form.targetCharacterConstellation1 || 0,
          target_character_constellation_2: this.form.targetCharacterConstellation2 || 0,
          target_weapon_refinement_1: this.form.targetWeaponRefinement1 || 1,
          target_weapon_refinement_2: this.form.targetWeaponRefinement2 || 1,
          include_character_1: this.form.includeCharacter1,
          include_character_2: this.form.includeCharacter2,
          include_weapon_1: this.form.includeWeapon1,
          include_weapon_2: this.form.includeWeapon2,
          strategy: "character_then_weapon"
        }
        apiCalls.push(axios.post('/api/required_pulls_for_50_percent', expectedPullsPayload, {
          cancelToken: this.cancelToken.token
        }))
      }
      
      // 根据用户选择决定是否添加95%概率所需抽数的计算
      if (this.form.calculateRequiredPulls) {
        const requiredPullsPayload = {
          resources: this.form.resources || 0,
          primogems: this.form.primogems || 0,
          crystals: this.form.crystals || 0,
          target_character_constellation_1: this.form.targetCharacterConstellation1 || 0,
          target_character_constellation_2: this.form.targetCharacterConstellation2 || 0,
          target_weapon_refinement_1: this.form.targetWeaponRefinement1 || 1,
          target_weapon_refinement_2: this.form.targetWeaponRefinement2 || 1,
          include_character_1: this.form.includeCharacter1,
          include_character_2: this.form.includeCharacter2,
          include_weapon_1: this.form.includeWeapon1,
          include_weapon_2: this.form.includeWeapon2,
          strategy: "character_then_weapon"
        }
        apiCalls.push(axios.post('/api/required_pulls_for_95_percent', requiredPullsPayload, {
          cancelToken: this.cancelToken.token
        }))
      }
      
      // 并行执行所有API调用
      Promise.all(apiCalls)
        .then((responses) => {
          // 检查组件是否仍然挂载
          if (!this.isMounted) return
          
          // 处理第一个响应（达成目标概率）
          if (responses[0]) {
            this.result = responses[0].data
          }
          
          // 处理后续响应
          let responseIndex = 1
          
          // 处理50%概率所需抽数（期望）
          if (this.form.calculateExpectedPulls && responses[responseIndex]) {
            this.requiredPullsFor50Percent = responses[responseIndex].data
            responseIndex++
          } else {
            // 如果用户不选择计算，则清空之前的结果
            this.requiredPullsFor50Percent = null
          }
          
          // 处理95%概率所需抽数
          if (this.form.calculateRequiredPulls && responses[responseIndex]) {
            this.requiredPullsFor95Percent = responses[responseIndex].data
          } else {
            // 如果用户不选择计算，则清空之前的结果
            this.requiredPullsFor95Percent = null
          }
          
          this.isLoading = false
          
          // 计算完成后滑动到结果
          // 使用$nextTick确保DOM更新完成后再滚动
          this.$nextTick(() => {
            this.scrollToResults()
          })
        })
        .catch((error) => {
          // 忽略取消请求的错误
          if (axios.isCancel(error)) {
            console.log('请求已取消:', error.message)
            return
          }
          // 检查组件是否仍然挂载
          if (!this.isMounted) return
          
          console.error('计算失败:', error)
          this.errorMessage =
            (error.response && error.response.data && error.response.data.error) ||
            '计算失败，请检查输入参数是否正确'
        })
        .finally(() => {
          // 检查组件是否仍然挂载
          if (!this.isMounted) return
          
          this.isLoading = false
        })
    },
    formatStrategy(s) {
      if (s === 'character_then_weapon') {
        return '先角色后武器'
      }
      if (s === 'weapon_then_character') {
        return '先武器后角色'
      }
      return s
    },
    scrollToTop() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      })
    },
    scrollToResults() {
      // 找到结果部分的元素并滚动到那里
      const resultsSection = document.querySelector('.results-section')
      if (resultsSection) {
        resultsSection.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }
    },
    handleScroll() {
      // 简化判断，只要滚动了就显示按钮
      this.showBackToTop = window.scrollY > 10
    }
  },
  mounted() {
    this.isMounted = true
    window.addEventListener('scroll', this.handleScroll)
  },
  beforeUnmount() {
    this.isMounted = false
    window.removeEventListener('scroll', this.handleScroll)
    // 取消未完成的API请求
    if (this.cancelToken) {
      this.cancelToken.cancel('Component unmounted')
    }
  }
}
</script>

<style scoped>
.goal-probability {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.content-container {
  width: 100%;
  max-width: 1100px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

h1 {
  color: #2c3e50;
  font-size: 26px;
  font-weight: 700;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-button {
  padding: 14px 24px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.header-button:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.card {
  background: white;
  border-radius: 14px;
  padding: 24px 24px 20px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  margin-bottom: 20px;
}

.card h2 {
  font-size: 20px;
  margin-bottom: 18px;
  color: #2c3e50;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 6px;
}

.form-group input {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
  background: #f8fafc;
}

.form-group input:focus {
  border-color: #4299e1;
  box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.25);
  background: #ffffff;
}

.form-group input:disabled {
  background: #e2e8f0;
  border-color: #cbd5e0;
  color: #718096;
  cursor: not-allowed;
  opacity: 0.6;
  box-shadow: none;
}

.form-group input:disabled:hover {
  border-color: #cbd5e0;
  background: #e2e8f0;
  transform: none;
}

.helper-text {
  font-size: 12px;
  color: #718096;
  margin-top: 4px;
}

.checkbox-group {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: nowrap;
  width: 100%;
}

.checkbox-group input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
  flex-shrink: 0;
  margin: 0;
}

.checkbox-group label {
  font-size: 14px;
  color: #4a5568;
  cursor: pointer;
  margin: 0;
  flex-shrink: 1;
  white-space: normal;
  word-wrap: break-word;
  line-height: 1.3;
  flex: 1;
}

.toggle-row {
  margin: 12px 0 6px;
}

.toggle-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #4a5568;
}

.strategy-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.strategy-option {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: #4a5568;
}

.strategy-option input {
  margin-top: 3px;
}

.actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.calculate-button {
  padding: 12px 32px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #4299e1 0%, #667eea 100%);
  color: white;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(66, 153, 225, 0.35);
  transition: all 0.25s ease;
}

.calculate-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(66, 153, 225, 0.45);
}

.calculate-button:disabled {
  opacity: 0.6;
  cursor: default;
  box-shadow: none;
}

.error-card {
  border-color: #feb2b2;
  background: #fff5f5;
}

.error-message {
  color: #c53030;
  font-size: 14px;
}

.result-card {
  margin-top: 6px;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.summary-item {
  background: #f7fafc;
  border-radius: 10px;
  padding: 10px 12px;
}

.summary-label {
  font-size: 12px;
  color: #718096;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}

.probability-section {
  margin-bottom: 18px;
  margin-top: 12px;
}

.probability-top {
  margin-bottom: 24px;
}

.probability-bottom {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

/* 带分隔线的区块样式 */
.section-with-separator {
  margin-top: 32px;
  padding-top: 8px;
}

.section-divider {
  height: 2px;
  background: linear-gradient(90deg, transparent, #cbd5e0, transparent);
  margin-bottom: 20px;
  margin-top: -8px;
}

.probability-section h3 {
  font-size: 16px;
  margin-bottom: 8px;
  color: #2c5282;
}

.probability-main {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.probability-value {
  font-size: 32px;
  font-weight: 800;
  color: #2b6cb0;
}

.probability-detail {
  font-size: 14px;
  color: #4a5568;
}

.probability-detail.secondary {
  font-size: 12px;
  color: #718096;
}

.strategy-compare h3 {
  font-size: 16px;
  margin-bottom: 8px;
  color: #2c5282;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.strategy-card {
  border-radius: 10px;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  background: #f7fafc;
}

.strategy-card.best-strategy {
  border-color: #63b3ed;
  background: #ebf8ff;
}

.strategy-title {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.tag-best {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 999px;
  background: #3182ce;
  color: white;
}

.strategy-prob {
  font-size: 20px;
  font-weight: 700;
  color: #2b6cb0;
  margin-bottom: 2px;
}

.strategy-meta {
  font-size: 12px;
  color: #718096;
}

.beta-note {
  margin-top: 10px;
  font-size: 12px;
  color: #718096;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .header-actions {
    align-self: stretch;
    justify-content: flex-end;
  }
}

/* 返回顶部按钮样式 */
.back-to-top {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #64748b;
  border: 1px solid #cbd5e1;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(148, 163, 184, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-to-top:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(148, 163, 184, 0.5);
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  color: #475569;
}

.back-to-top:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(148, 163, 184, 0.3);
}

/* 纠缠之缘 - 粉蓝色渐变色 */
.gradient-text-fate {
  background: linear-gradient(135deg, #ff6b9d 0%, #4facfe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
}

/* 原石、创世结晶 - 浅蓝色 */
.light-blue-text {
  color: #63b3ed;
  font-weight: 600;
}

/* 5星UP角色/武器 - 橙色 */
.gold-text {
  color: #ff8c00;
  font-weight: 600;
}

/* 类型图标 */
.type-icon {
  margin-left: 4px;
  font-size: 14px;
}

.character-icon {
  color: #4a90e2;
}

.weapon-icon {
  color: #e74c3c;
}

/* 额外计算选项区域 */
.extra-options-section {
  margin-top: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.extra-options-title {
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 12px;
}

.extra-options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-item label {
  font-size: 14px;
  color: #4a5568;
  cursor: pointer;
  user-select: none;
}
</style>