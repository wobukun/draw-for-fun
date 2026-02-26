"""
角色活动祈愿抽卡模拟器 — 简要规则说明

规则概览：
- 基础五星概率为 `BASE_RATE`（默认 0.6%）；若 pity 达到 `PITY_THRESHOLD`（默认 73）
    则每超过一次额外提升 `PITY_INCREASE`（默认 6%），概率上限为 100%。
- 每次抽卡会更新普通 `pity`（距离上次五星的抽数）和 `up_pity`（距离上次 UP 五星的抽数）。
- 五星命中时：有 50% 概率为 UP（`is_up=True`），若为常驻则下一次五星必为 UP（`guarantee_up`）。
- 捕获明光机制：
  - 当获取到5星角色时，若并非必定获取5星UP的情况，可能触发捕获明光机制
  - 触发捕获明光的基础概率为 `CAPTURE_MINGUANG_BASE_RATE`（默认 0.018%）
  - 若连续3次在第二次获取5星角色时才获取本期up5星角色，则下次祈愿获取5星角色时，必定触发捕获明光机制
- 程序会维护累计抽数 `total_pulls`，并在输出页显示“当前总抽数”。
"""

import numpy as np
import sys
import os

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)




BASE_RATE = 0.006
PITY_THRESHOLD = 73
PITY_INCREASE = 0.06
CAPTURE_MINGUANG_BASE_RATE = 0.00018


class CharacterGachaSimulator:
    """封装抽卡逻辑的类。

    属性:
    - `pity`: 当前已连续未抽中 5★ 角色 的次数（整数）
    - `up_pity`: 距离上次 5★ UP 角色的抽数
    - `guarantee_up`: 下次 5★ 是否必定为 UP 角色（常驻角色后自动设为 True）
    - `avg_count`: 当前已获取的常驻角色数
    - `up_count`: 当前已获取的 UP 角色数
    - `base_rate`, `pity_threshold`, `pity_increase`：概率参数
    - `rng`: numpy 随机数生成器

    方法:
    - `current_rate(pity=None)`: 返回给定（或当前）pity 的命中概率
    - `draw_once()`, `draw_n(n)`: 在内部使用并更新 `pity` 与 UP 机制
    - `pull_one()` / `pull_ten()`: 便捷接口，返回与之前相同的 dict 结构
    """

    def __init__(self, pity: int = 0, *, base_rate: float = BASE_RATE, pity_threshold: int = PITY_THRESHOLD,
                 pity_increase: float = PITY_INCREASE, seed: int | None = None, capture_minguang_base_rate: float = CAPTURE_MINGUANG_BASE_RATE):
        self.pity = int(pity)  # 当前已连续未抽中 5★ 角色的次数
        self.up_pity = int(pity)  # 距离上次 5★ UP 角色的抽数
        self.guarantee_up = False  # 下次 5★ 是否必定为 UP 角色（常驻角色后自动设为 True）
        self.avg_count = 0  # 当前已获取的常驻角色数
        self.up_count = 0  # 当前已获取的 UP 角色数
        self.total_pulls = 0  # 累计总抽数
        self.base_rate = float(base_rate)  # 基础 5★ 概率
        self.pity_threshold = int(pity_threshold)  # 概率提升阈值
        self.pity_increase = float(pity_increase)  # 每次概率提升值
        self.rng = np.random.default_rng(seed)  # 随机数生成器
        self.capture_minguang_base_rate = float(capture_minguang_base_rate)  # 捕获明光基础触发概率
        self.migu_counter = 0  # 捕获明光计数器（记录通过guarantee_up为true时抽到UP5星角色的次数）
        self.guarantee_capture_minguang = False  # 下次是否必定触发捕获明光
        self.capture_minguang_count = 0  # 捕获明光触发总次数

    def current_rate(self, pity: int | None = None) -> float:
        """返回给定或当前 `pity` 下的 5★ 角色命中概率。

        参数:
        - `pity`: 可选，若不提供使用实例当前的 `self.pity`。
        返回值为 0.0-1.0 的浮点数。函数保证返回值不会超过 1.0（100%）。
        """
        p = self.pity if pity is None else int(pity)
        # 小保底：第90抽必定获得5星物品
        if p >= 89:
            return 1.0
        if p < self.pity_threshold:
            return self.base_rate
        extra_steps = p - (self.pity_threshold - 1)
        return min(1.0, self.base_rate + extra_steps * self.pity_increase)

    def draw_once(self) -> tuple[bool, int, float, bool, bool]:
        """进行一次抽卡：使用当前 `pity` 计算命中率并进行随机判定。

        副作用：若未命中，`self.pity` 增加 1；若命中，`self.pity` 重置为 0。
        返回值为 `(is_5star, new_pity, used_probability, is_up, capture_minguang_triggered)`。
        其中 `is_up` 表示若获得 5★，是否为 UP 角色，`capture_minguang_triggered` 表示是否触发了捕获明光机制。
        """
        prob = self.current_rate(self.pity)
        # 为保证设计约束，显式将概率上限限制为 1.0（防止任何计算误差导致 >1）
        prob = min(1.0, prob)
        success = self.rng.random() < prob
        is_up = False
        capture_minguang_triggered = False
        
        if success:
            # 先判断捕获明光计数器是否为3，若是则必定触发捕获明光
            if self.migu_counter >= 3:
                capture_minguang_triggered = True
                is_up = True
                self.up_count += 1
                self.capture_minguang_count += 1  # 增加捕获明光触发次数
                self.guarantee_capture_minguang = False
                self.guarantee_up = False
                self.migu_counter = 0
            else:
                # 检查是否触发大保底
                if self.guarantee_up:
                    # 大保底：上次获得常驻角色，本次必定 UP
                    is_up = True
                    self.guarantee_up = False
                    self.up_count += 1
                    # 捕获明光计数器+1（触发大保底时），最高为3
                    self.migu_counter = min(self.migu_counter + 1, 3)
                else:
                    # 尝试触发捕获明光
                    capture_minguang_triggered = self.rng.random() < self.capture_minguang_base_rate
                    if capture_minguang_triggered:
                        is_up = True
                        self.up_count += 1
                        self.capture_minguang_count += 1  # 增加捕获明光触发次数
                        self.guarantee_up = False
                        self.migu_counter = 0
                    else:
                        # 小保底：50% 概率 UP，50% 概率常驻
                        is_up = self.rng.random() < 0.5
                        if is_up:
                            self.up_count += 1
                            # 小保底时清零捕获明光计数器
                            self.migu_counter = 0
                        else:
                            self.avg_count += 1
                            self.guarantee_up = True  # 下次必定 UP
            
            # 本次命中会重置普通 pity（distance since last 5★），
            # 但只有当命中为 UP 时才重置 up_pity（distance since last UP）。
            self.pity = 0
            if is_up:
                self.up_pity = 0
            else:
                # 抽到常驻 5★ 时，距离上次 UP 的计数应加上本次抽数
                self.up_pity += 1
        else:
            self.pity += 1
            self.up_pity += 1

        # 增加累计抽数（在本次抽卡完成后计入）
        self.total_pulls += 1
        
        return success, self.pity, prob, is_up, capture_minguang_triggered

    def draw_n(self, n: int) -> tuple[list[bool], int, list[float], list[bool], list[bool]]:
        """连续抽 `n` 次并返回每次结果与使用概率。

        返回 `(results_list, new_pity, probs_list, is_up_list, capture_minguang_list)`，其中 `results_list` 为 bool 列表，
        `probs_list` 为对应每次抽卡使用的概率，`is_up_list` 为对应每次是否为 UP(仅在命中时有效)，
        `capture_minguang_list` 为对应每次是否触发捕获明光机制。
        """
        results: list[bool] = []
        probs: list[float] = []
        is_up_list: list[bool] = []
        capture_minguang_list: list[bool] = []
        for _ in range(int(n)):
            ok, _, p, is_up, capture_minguang = self.draw_once()
            results.append(ok)
            probs.append(p)
            is_up_list.append(is_up)
            capture_minguang_list.append(capture_minguang)
        return results, self.pity, probs, is_up_list, capture_minguang_list

    def pull_one(self) -> dict:
        """便捷接口：进行一次单抽并返回字典结果。

        返回结构：{"results": [bool], "new_pity": int, "used_probs": [float], "is_up": [bool], 
                  "avg_count": int, "up_count": int, "up_pity": int, "start_up_pity": int, "guarantee_up": bool,
                  "capture_minguang": [bool], "migu_counter": int, "guarantee_capture_minguang": bool}。
        """
        start_up_pity = self.up_pity
        ok, new_pity, prob, is_up, capture_minguang = self.draw_once()
        return {
            "results": [ok],
            "new_pity": new_pity,
            "used_probs": [prob],
            "is_up": [is_up],
            "avg_count": self.avg_count,
            "up_count": self.up_count,
            "up_pity": self.up_pity,
            "start_up_pity": start_up_pity,
            "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up,
            "capture_minguang": [capture_minguang],
            "migu_counter": self.migu_counter,
            "guarantee_capture_minguang": self.guarantee_capture_minguang,
            "capture_minguang_count": self.capture_minguang_count
        }

    def pull_ten(self) -> dict:
        """便捷接口：进行一次十连并返回字典结果。

        返回结构同 `pull_one`，但 `results`、`used_probs` 与 `is_up` 长度为 10。
        """
        start_up_pity = self.up_pity
        results, new_pity, probs, is_up_list, capture_minguang_list = self.draw_n(10)
        return {
            "results": results,
            "new_pity": new_pity,
            "used_probs": probs,
            "is_up": is_up_list,
            "capture_minguang": capture_minguang_list,
            "avg_count": self.avg_count,
            "up_count": self.up_count,
            "up_pity": self.up_pity,
            "start_up_pity": start_up_pity,
            "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up,
            "migu_counter": self.migu_counter,
            "guarantee_capture_minguang": self.guarantee_capture_minguang,
            "capture_minguang_count": self.capture_minguang_count
        }

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
        - up_count: UP角色数量
        - avg_count: 常驻角色数量
        - total_hits: 总命中数量
        - pity_history: 每次抽卡后的pity值
        - hit_positions: 命中位置列表
        - up_positions: UP命中位置列表
        - avg_positions: 常驻命中位置列表
        - stats: 数学统计信息，包括期望抽数、中位数抽数、标准差、最小抽数、最大抽数
        """
        total_pulls = int(total_pulls)
        if total_pulls <= 0:
            return {
                'up_count': 0,
                'avg_count': 0,
                'total_hits': 0,
                'pity_history': [],
                'hit_positions': [],
                'up_positions': [],
                'avg_positions': [],
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
        current_capture_minguang_guarantee = False
        current_migu_counter = 0
        current_capture_minguang_count = 0  # 捕获明光触发次数
        current_up_count = 0
        current_avg_count = 0
        total_hits = 0
        
        # 记录抽卡过程
        pity_history = []
        hit_positions = []
        up_positions = []
        avg_positions = []
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
                
                # 先判断捕获明光计数器是否为3，若是则必定触发捕获明光
                if current_migu_counter >= 3:
                    is_up = True
                    current_up_count += 1
                    current_capture_minguang_count += 1  # 增加捕获明光触发次数
                    up_positions.append(pull_num)
                    current_capture_minguang_guarantee = False
                    current_guarantee = False
                    current_migu_counter = 0
                else:
                    # 检查是否触发大保底
                    if current_guarantee:
                        # 大保底：上次获得常驻角色，本次必定 UP
                        is_up = True
                        current_up_count += 1
                        up_positions.append(pull_num)
                        current_guarantee = False
                        # 捕获明光计数器+1（触发大保底时），最高为3
                        current_migu_counter = min(current_migu_counter + 1, 3)
                    else:
                        # 尝试触发捕获明光
                        capture_minguang = rs.random() < CAPTURE_MINGUANG_BASE_RATE
                        if capture_minguang:
                            is_up = True
                            current_up_count += 1
                            current_capture_minguang_count += 1  # 增加捕获明光触发次数
                            up_positions.append(pull_num)
                            current_guarantee = False
                            current_migu_counter = 0
                        else:
                            # 小保底：50% 概率 UP，50% 概率常驻
                            is_up = rs.random() < 0.5
                            if is_up:
                                current_up_count += 1
                                up_positions.append(pull_num)
                                # 小保底时清零捕获明光计数器
                                current_migu_counter = 0
                            else:
                                current_avg_count += 1
                                avg_positions.append(pull_num)
                                current_guarantee = True  # 下次必UP
                
                # 记录本次5星的信息
                five_star_costs.append({
                    'cost': cost,
                    'is_up': is_up
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
            'avg_count': 0,
            'median_count': 0,
            'std_count': 0,
            'min_count': 0,
            'max_count': 0
        }

        if len(up_positions) > 1:
            import numpy as np
            # 计算相邻UP之间的抽数间隔
            intervals = []
            for i in range(1, len(up_positions)):
                intervals.append(up_positions[i] - up_positions[i-1])
            
            if intervals:
                stats['avg_count'] = float(np.mean(intervals))
                stats['median_count'] = float(np.median(intervals))
                stats['std_count'] = float(np.std(intervals))
                stats['min_count'] = int(np.min(intervals))
                stats['max_count'] = int(np.max(intervals))

        return {
            'up_count': current_up_count,
            'avg_count': current_avg_count,
            'total_hits': total_hits,
            'capture_minguang_count': current_capture_minguang_count,
            'five_star_costs': five_star_costs,
            'stats': stats
        }