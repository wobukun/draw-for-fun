<template>
  <div class="goal-probability">
    <div class="content-container">
      <div class="header">
        <h1>抽取概率计算（Beta）</h1>
        <div class="header-actions">
          <button class="header-button" @click="goBack">返回主菜单</button>
        </div>
      </div>

      <div class="card">
        <h2>输入您的资源与目标</h2>
        <div class="form-grid">
          <div class="form-group">
            <label for="resources">拥有的纠缠之缘数量</label>
            <input
              id="resources"
              type="number"
              min="0"
              max="9999999"
              v-model.number="form.resources"
              placeholder="例如：180"
            />
            <p class="helper-text">1 纠缠之缘 = 1 抽，可在角色池或武器池中自由分配。</p>
          </div>

          <div class="form-group">
            <label for="primogems">拥有的原石数量</label>
            <input
              id="primogems"
              type="number"
              min="0"
              max="9999999"
              v-model.number="form.primogems"
              placeholder="例如：1600"
              @input="calculateTotalResources"
            />
            <p class="helper-text">160 原石 = 1 纠缠之缘</p>
          </div>

          <div class="form-group">
            <label for="crystals">拥有的创世结晶数量</label>
            <input
              id="crystals"
              type="number"
              min="0"
              max="9999999"
              v-model.number="form.crystals"
              placeholder="例如：1600"
              @input="calculateTotalResources"
            />
            <p class="helper-text">1 创世结晶 = 1 原石</p>
          </div>

          <div class="form-group">
            <label for="character-constellation">
              目标角色命之座层数（UP 角色）
            </label>
            <div class="toggle-row">
              <label class="toggle-label">
                <input
                  type="checkbox"
                  v-model="form.includeCharacter"
                />
                <span>本次抽取角色</span>
              </label>
            </div>
            <input
              id="character-constellation"
              type="number"
              min="0"
              max="6"
              :disabled="!form.includeCharacter"
              v-model.number="form.targetCharacterConstellation"
              placeholder="0 = 0命（1个UP），1 = 1命（2个UP）..."
            />
            <p class="helper-text">
              0 命 = 需要 1 个 UP 角色，1 命 = 2 个 UP 角色，以此类推。
            </p>
          </div>

          <div class="form-group">
            <label for="weapon-refinement">
              目标武器精炼等级（定轨武器）
            </label>
            <div class="toggle-row">
              <label class="toggle-label">
                <input
                  type="checkbox"
                  v-model="form.includeWeapon"
                />
                <span>本次抽取武器</span>
              </label>
            </div>
            <input
              id="weapon-refinement"
              type="number"
              min="1"
              max="5"
              :disabled="!form.includeWeapon"
              v-model.number="form.targetWeaponRefinement"
              placeholder="1 = 1 精（1把定轨），2 = 2 精（2把定轨）..."
            />
            <p class="helper-text">
              1 精 = 需要 1 把定轨武器，2 精 = 2 把定轨武器，以此类推。
            </p>
          </div>
        </div>

        <div class="actions">
          <button
            class="calculate-button"
            :disabled="isLoading"
            @click="calculate"
          >
            <span v-if="!isLoading">开始计算</span>
            <span v-else>计算中，请稍候...</span>
          </button>
        </div>
      </div>

      <div v-if="errorMessage" class="card error-card">
        <h2>提示</h2>
        <p class="error-message">{{ errorMessage }}</p>
      </div>

      <div v-if="result" class="card result-card">
        <h2>计算结果</h2>

        <div class="result-summary">
          <div class="summary-item">
            <div class="summary-label">资源</div>
            <div class="summary-value">{{ result.resources }} 抽</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">角色目标</div>
            <div class="summary-value">
              <span v-if="result.targets.character_target_copies > 0">
                需要 {{ result.targets.character_target_copies }} 个 UP 角色
              </span>
              <span v-else>无目标</span>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-label">武器目标</div>
            <div class="summary-value">
              <span v-if="result.targets.weapon_target_copies > 0">
                需要 {{ result.targets.weapon_target_copies }} 把定轨武器
              </span>
              <span v-else>无目标</span>
            </div>
          </div>
        </div>

        <div class="probability-section">
          <h3>计算结果（先角色，后武器策略）</h3>
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
        targetCharacterConstellation: 0,
        targetWeaponRefinement: 1,
        trials: 5000,
        includeCharacter: true,
        includeWeapon: true
      },
      isLoading: false,
      errorMessage: '',
      result: null
    }
  },
  computed: {
    totalResources() {
      // 计算总抽数：纠缠之缘 + (原石 + 创世结晶兑换的原石) / 160
      const totalPrimogems = (this.form.primogems || 0) + (this.form.crystals || 0)
      const primogemsToFate = Math.floor(totalPrimogems / 160)
      return (this.form.resources || 0) + primogemsToFate
    }
  },
  methods: {
    goBack() {
      this.$router.push('/')
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
      
      // 验证总抽数
      if (this.totalResources <= 0) {
        return '总抽数必须 > 0。'
      }
      
      // 角色：仅在勾选时校验，范围 0-6
      if (this.form.includeCharacter) {
        if (
          this.form.targetCharacterConstellation === null ||
          this.form.targetCharacterConstellation < 0 ||
          this.form.targetCharacterConstellation > 6
        ) {
          return '角色命之座层数必须在 0 - 6 之间。'
        }
      }
      
      // 武器：仅在勾选时校验，范围 1-5
      if (this.form.includeWeapon) {
        if (
          this.form.targetWeaponRefinement === null ||
          this.form.targetWeaponRefinement < 1 ||
          this.form.targetWeaponRefinement > 5
        ) {
          return '武器精炼等级必须在 1 - 5 之间。'
        }
      }
      
      // 至少选择一个目标（角色或武器）
      if (!this.form.includeCharacter && !this.form.includeWeapon) {
        return '请至少选择一个目标（角色命之座或武器精炼）。'
      }
      
      return ''
    },
    calculateTotalResources() {
      // 此方法用于触发计算属性更新
      // 实际计算逻辑在 computed.totalResources 中
    },
    calculate() {
      this.errorMessage = ''
      const msg = this.validateForm()
      if (msg) {
        this.errorMessage = msg
        return
      }
      this.isLoading = true
      this.result = null

      const payload = {
        resources: this.totalResources,
        strategy: "character_first",
        trials: this.form.trials
      }

      if (this.form.includeCharacter) {
        payload.target_character_constellation = this.form.targetCharacterConstellation
      }

      if (this.form.includeWeapon) {
        payload.target_weapon_refinement = this.form.targetWeaponRefinement
      }

      axios
        .post('/api/goal_probability', payload)
        .then((response) => {
          this.result = response.data
        })
        .catch((error) => {
          console.error('计算失败:', error)
          this.errorMessage =
            (error.response && error.response.data && error.response.data.error) ||
            '计算失败，请稍后重试。'
        })
        .finally(() => {
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

.toggle-row {
  margin: 4px 0 6px;
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
</style>