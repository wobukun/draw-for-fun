"""
Weapon Gacha Simulator — 武器抽卡模拟器

模块功能说明：
- 支持单抽、十连与自动批量模拟（`auto` 模式）。
- 基础 5★ 武器概率由 `BASE_RATE` 控制（默认 0.7%），在达到 `PITY_THRESHOLD` 后
    每抽增加 `PITY_INCREASE` 的概率直至 100%。
- 小保底：第80抽必定获得5星物品
- 增加 UP 机制：当抽到 5★ 时有 75% 的概率为 UP；若该次为常驻（非 UP），
    则下一次获得的 5★ 必定为 UP（由 `guarantee_up` 跟踪）。
- 增加定轨系统：当抽到 UP 武器时，有 50% 的概率为定轨武器；
    无论是否抽到 UP 武器，只要不是定轨武器，命定值都加 1（命定值最高为 1）；
    当命定值为 1 时，下次抽取的 5★ 武器必定为定轨武器；
    抽到定轨武器后，命定值和大保底都清零。
- `simulate_pulls` 已实现向量化并行试验：可用于多次独立试验，返回每次
    "抽到 UP 5★ 所需抽数" 的样本列表，方便计算期望（样本均值）。

主要接口：
- `draw_once()` / `draw_n(n)`：进行一次或连续多次抽卡，返回命中、UP 信息和定轨信息。
- `pull_one()` / `pull_ten()`：便捷单抽 / 十连接口并包含统计信息。
- `simulate_pulls(total_pulls)`：并行模拟多次试验，返回抽卡结果统计。
"""

import numpy as np
import sys
import os

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)




BASE_RATE = 0.007
PITY_THRESHOLD = 63
PITY_INCREASE = 0.07


class WeaponGachaSimulator:
    """封装抽武器逻辑的类。

    属性:
    - `pity`: 当前已连续未抽中 5★ 武器 的次数（整数）
    - `base_rate`, `pity_threshold`, `pity_increase`：概率参数
    - `rng`: numpy 随机数生成器

    方法:
    - `current_rate(pity=None)`: 返回给定（或当前）pity 的命中概率
    - `draw_once()`, `draw_n(n)`: 在内部使用并更新 `pity`
    - `pull_one()` / `pull_ten()`: 便捷接口，返回与之前相同的 dict 结构
    """

    def __init__(self, pity: int = 0, *, base_rate: float = BASE_RATE, pity_threshold: int = PITY_THRESHOLD,
                 pity_increase: float = PITY_INCREASE, seed: int | None = None):
        self.pity = int(pity)
        self.up_pity = int(pity)
        self.guarantee_up = False  # 下次5★是否必定为UP
        self.avg_count = 0  # 常驻武器数
        self.up_count = 0   # UP武器数
        self.total_pulls = 0  # 累计总抽数
        self.base_rate = float(base_rate)
        self.pity_threshold = int(pity_threshold)
        self.pity_increase = float(pity_increase)
        self.rng = np.random.default_rng(seed)
        self.fate_point = 0  # 命定值，最高为1
        self.is_fate_guaranteed = False  # 下次5★是否必定为定轨武器
        self.fate_count = 0  # 定轨武器数量
        self.fate_pity = 0  # 已连续未出定轨5星抽数

    def current_rate(self, pity: int | None = None) -> float:
        """返回给定或当前 `pity` 下的 5★ 武器命中概率。

        参数:
        - `pity`: 可选，若不提供使用实例当前的 `self.pity`。
        返回值为 0.0-1.0 的浮点数。函数保证返回值不会超过 1.0（100%）。
        """
        p = self.pity if pity is None else int(pity)
        # 小保底：第80抽必定获得5星物品
        if p >= 79:
            return 1.0
        if p < self.pity_threshold:
            return self.base_rate
        extra_steps = p - (self.pity_threshold - 1)
        return min(1.0, self.base_rate + extra_steps * self.pity_increase)

    def draw_once(self) -> tuple[bool, int, float, bool, bool]:
        """进行一次抽卡：使用当前 `pity` 计算命中率并进行随机判定。

        副作用：若未命中，`self.pity` 增加 1；若命中，`self.pity` 重置为 0。
        返回值为 `(is_5star, new_pity, used_probability, is_up, is_fate)`。
        其中 `is_up` 表示若获得 5★，是否为 UP 武器，`is_fate` 表示是否为定轨武器。
        """
        prob = self.current_rate(self.pity)
        # 显式将概率上限限制为 1.0（防止任何计算误差导致 >1）
        prob = min(1.0, prob)
        success = self.rng.random() < prob
        is_up = False
        is_fate = False

        if success:
            # 先判断命定值是否为1
            if self.is_fate_guaranteed:
                # 命定值为1，必定获得定轨武器
                is_fate = True
                is_up = True  # 定轨武器一定是UP武器
                self.is_fate_guaranteed = False
                self.fate_point = 0
                self.fate_count += 1
                self.up_count += 1
                # 抽到定轨武器后，大保底也清零
                self.guarantee_up = False
            else:
                # 判定是否为 UP 武器
                if self.guarantee_up:
                    is_up = True
                    self.guarantee_up = False
                    self.up_count += 1
                else:
                    is_up = self.rng.random() < 0.75
                    if is_up:
                        self.up_count += 1
                    else:
                        self.avg_count += 1
                        self.guarantee_up = True

                # 判定是否为定轨武器
                if is_up:
                    # 是UP武器，50%概率为定轨武器
                    is_fate = self.rng.random() < 0.5
                    if not is_fate:
                        self.fate_point = min(1, self.fate_point + 1)
                        if self.fate_point == 1:
                            self.is_fate_guaranteed = True
                    else:
                        self.fate_point = 0
                        self.fate_count += 1
                        # 抽到定轨武器后，大保底也清零
                        self.guarantee_up = False
                else:
                    # 非UP武器，不是定轨武器，增加命定值
                    is_fate = False
                    self.fate_point = min(1, self.fate_point + 1)
                    if self.fate_point == 1:
                        self.is_fate_guaranteed = True

            # 命中后重置 pity
            self.pity = 0
            if is_up:
                self.up_pity = 0
            else:
                self.up_pity += 1
            
            # 重置或增加定轨 pity
            if is_fate:
                self.fate_pity = 0
            else:
                self.fate_pity += 1
        else:
            self.pity += 1
            self.up_pity += 1
            self.fate_pity += 1
        # 计入累计抽数
        self.total_pulls += 1
        return success, self.pity, prob, is_up, is_fate

    def draw_n(self, n: int) -> tuple[list[bool], int, list[float], list[bool], list[bool]]:
        """连续抽 `n` 次并返回每次结果与使用概率。

        返回 `(results_list, new_pity, probs_list, is_up_list, is_fate_list)`，其中 `results_list` 为 bool 列表，
        `probs_list` 为对应每次抽卡使用的概率，`is_up_list` 为对应每次是否为 UP(仅在命中时有效)，
        `is_fate_list` 为对应每次是否为定轨武器(仅在命中时有效)。
        """
        results: list[bool] = []
        probs: list[float] = []
        is_up_list: list[bool] = []
        is_fate_list: list[bool] = []
        for _ in range(int(n)):
            ok, _, p, is_up, is_fate = self.draw_once()
            results.append(ok)
            probs.append(p)
            is_up_list.append(is_up)
            is_fate_list.append(is_fate)
        return results, self.pity, probs, is_up_list, is_fate_list

    def pull_one(self) -> dict:
        """便捷接口：进行一次单抽并返回字典结果。

        返回结构：{"results": [bool], "new_pity": int, "used_probs": [float], "start_pity": int}。
        """
        start_pity = self.pity
        start_up_pity = self.up_pity
        ok, new_pity, prob, is_up, is_fate = self.draw_once()
        return {"results": [ok], "new_pity": new_pity, "used_probs": [prob], "is_up": [is_up], "is_fate": [is_fate],
            "avg_count": self.avg_count, "up_count": self.up_count, "fate_count": self.fate_count,
            "up_pity": self.up_pity, "start_up_pity": start_up_pity,
            "start_pity": start_pity, "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up, "fate_point": self.fate_point, "is_fate_guaranteed": self.is_fate_guaranteed,
            "fate_pity": self.fate_pity}

    def pull_ten(self) -> dict:
        """便捷接口：进行一次十连并返回字典结果。

        返回结构同 `pull_one`，但 `results` 与 `used_probs` 长度为 10。
        """
        start_pity = self.pity
        start_up_pity = self.up_pity
        results, new_pity, probs, is_up_list, is_fate_list = self.draw_n(10)
        return {"results": results, "new_pity": new_pity, "used_probs": probs, "is_up": is_up_list, "is_fate": is_fate_list,
            "avg_count": self.avg_count, "up_count": self.up_count, "fate_count": self.fate_count,
            "fate_pity": self.fate_pity,
            "up_pity": self.up_pity, "start_up_pity": start_up_pity,
            "start_pity": start_pity, "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up, "fate_point": self.fate_point, "is_fate_guaranteed": self.is_fate_guaranteed}

    @classmethod
    def quick_pull_one(cls, pity: int = 0, seed: int | None = None) -> dict:
        """类方法：无需显式创建实例即可进行一次单抽（返回结果，不保留状态）。"""
        sim = cls(pity, seed=seed)
        return sim.pull_one()

    @classmethod
    def quick_pull_ten(cls, pity: int = 0, seed: int | None = None) -> dict:
        """类方法：无需显式创建实例即可进行一次十连（返回结果，不保留状态）。"""
        sim = cls(pity, seed=seed)
        return sim.pull_ten()

    def simulate_pulls(self, total_pulls: int) -> dict:
        """
        模拟实际抽卡 `total_pulls` 次，返回抽卡结果统计。

        返回字典：包含抽卡结果的统计信息，包括：
        - up_count: UP武器数量
        - avg_count: 常驻武器数量
        - total_hits: 总命中数量
        - pity_history: 每次抽卡后的pity值
        - hit_positions: 命中位置列表
        - up_positions: UP命中位置列表
        - avg_positions: 常驻命中位置列表
        - fate_positions: 定轨武器命中位置列表
        - stats: 数学统计信息，包括期望抽数、中位数抽数、标准差、最小抽数、最大抽数
        """
        total_pulls = int(total_pulls)
        if total_pulls <= 0:
            return {
                'up_count': 0,
                'avg_count': 0,
                'fate_count': 0,
                'total_hits': 0,
                'pity_history': [],
                'hit_positions': [],
                'up_positions': [],
                'avg_positions': [],
                'fate_positions': [],
                'stats': {
                    'expected_pulls': 0,
                    'median_pulls': 0,
                    'std_pulls': 0,
                    'min_pulls': 0,
                    'max_pulls': 0
                }
            }

        # 起始状态（不修改 self）
        current_pity = int(self.pity)
        current_guarantee = bool(self.guarantee_up)
        current_fate_point = 0
        current_is_fate_guaranteed = False
        current_up_count = 0
        current_avg_count = 0
        current_fate_count = 0
        total_hits = 0
        
        # 记录抽卡过程
        pity_history = []
        hit_positions = []
        up_positions = []
        avg_positions = []
        fate_positions = []
        # 记录每次5星所花费的抽数
        five_star_costs = []
        last_hit_position = 0

        rs = self.rng

        # 执行指定次数的抽卡
        for pull_num in range(1, total_pulls + 1):
            # 计算当前抽卡概率
            if current_pity < self.pity_threshold:
                prob = self.base_rate
            else:
                prob = self.base_rate + (current_pity - (self.pity_threshold - 1)) * self.pity_increase
            prob = min(prob, 1.0)

            # 随机判断是否命中 5★
            success = rs.random() < prob

            if success:
                # 命中5★，记录位置
                total_hits += 1
                hit_positions.append(pull_num)
                
                # 计算本次5星所花费的抽数
                if last_hit_position == 0:
                    cost = pull_num
                else:
                    cost = pull_num - last_hit_position
                last_hit_position = pull_num
                
                # 先判断命定值是否为1
                is_fate = False
                if current_is_fate_guaranteed:
                    # 命定值为1，必定获得定轨武器
                    is_fate = True
                    is_up = True  # 定轨武器一定是UP武器
                    current_is_fate_guaranteed = False
                    current_fate_point = 0
                    current_fate_count += 1
                    current_up_count += 1
                    up_positions.append(pull_num)
                    fate_positions.append(pull_num)
                    # 抽到定轨武器后，大保底也清零
                    current_guarantee = False
                else:
                    # 判定是否为 UP：若 guarantee 为 True 则必为 UP，否则 75% 概率为 UP
                    if current_guarantee:
                        is_up = True
                        current_up_count += 1
                        up_positions.append(pull_num)
                        current_guarantee = False  # 重置guarantee
                    else:
                        is_up = rs.random() < 0.75
                        if is_up:
                            current_up_count += 1
                            up_positions.append(pull_num)
                            current_guarantee = False  # 重置guarantee
                        else:
                            current_avg_count += 1
                            avg_positions.append(pull_num)
                            current_guarantee = True  # 下次必UP
                    
                    # 判定是否为定轨武器
                    if is_up:
                        # 是UP武器，50%概率为定轨武器
                        is_fate = rs.random() < 0.5
                        if not is_fate:
                            current_fate_point = min(1, current_fate_point + 1)
                            if current_fate_point == 1:
                                current_is_fate_guaranteed = True
                        else:
                            current_fate_point = 0
                            current_fate_count += 1
                            fate_positions.append(pull_num)
                            # 抽到定轨武器后，大保底也清零
                            current_guarantee = False
                    else:
                        # 非UP武器，不是定轨武器，增加命定值
                        is_fate = False
                        current_fate_point = min(1, current_fate_point + 1)
                        if current_fate_point == 1:
                            current_is_fate_guaranteed = True
                
                # 记录本次5星的信息
                five_star_costs.append({
                    'cost': cost,
                    'is_up': is_up,
                    'is_fate': is_fate
                })
                
                # 重置pity
                current_pity = 0
            else:
                # 未命中，增加pity
                current_pity += 1
            
            # 记录本次抽卡后的pity值
            pity_history.append(current_pity)

        # 计算数学统计信息
        stats = {
            'fate_avg_count': 0,
            'fate_median_count': 0,
            'fate_std_count': 0,
            'fate_min_count': 0,
            'fate_max_count': 0
        }


        # 计算定轨武器的统计信息
        if len(fate_positions) > 1:
            import numpy as np
            # 计算相邻定轨武器之间的抽数间隔
            fate_intervals = []
            for i in range(1, len(fate_positions)):
                fate_intervals.append(fate_positions[i] - fate_positions[i-1])
            
            if fate_intervals:
                stats['fate_avg_count'] = float(np.mean(fate_intervals))
                stats['fate_median_count'] = float(np.median(fate_intervals))
                stats['fate_std_count'] = float(np.std(fate_intervals))
                stats['fate_min_count'] = int(np.min(fate_intervals))
                stats['fate_max_count'] = int(np.max(fate_intervals))

        return {
            'up_count': current_up_count,
            'avg_count': current_avg_count,
            'fate_count': current_fate_count,
            'total_hits': total_hits,
            'five_star_costs': five_star_costs,
            'stats': stats
        }