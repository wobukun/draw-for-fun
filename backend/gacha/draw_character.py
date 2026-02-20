"""
角色抽卡模拟器 — 简要规则说明

规则概览：
- 基础五星概率为 `BASE_RATE`（默认 0.6%）；若 pity 达到 `PITY_THRESHOLD`（默认 73）
    则每超过一次额外提升 `PITY_INCREASE`（默认 6%），概率上限为 100%。
- 每次抽卡会更新普通 `pity`（距离上次五星的抽数）和 `up_pity`（距离上次 UP 五星的抽数）。
- 五星命中时：有 50% 概率为 UP（`is_up=True`），若为常驻则下一次五星必为 UP（`guarantee_up`）。
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
                 pity_increase: float = PITY_INCREASE, seed: int | None = None):
        self.pity = int(pity)
        self.up_pity = int(pity)
        self.guarantee_up = False  # 下次5★是否必定为UP
        self.avg_count = 0  # 常驻角色数
        self.up_count = 0   # UP角色数
        self.total_pulls = 0  # 累计总抽数
        self.base_rate = float(base_rate)
        self.pity_threshold = int(pity_threshold)
        self.pity_increase = float(pity_increase)
        self.rng = np.random.default_rng(seed)

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

    def draw_once(self) -> tuple[bool, int, float, bool]:
        """进行一次抽卡：使用当前 `pity` 计算命中率并进行随机判定。

        副作用：若未命中，`self.pity` 增加 1；若命中，`self.pity` 重置为 0。
        返回值为 `(is_5star, new_pity, used_probability, is_up)`。
        其中 `is_up` 表示若获得 5★，是否为 UP 角色。
        """
        prob = self.current_rate(self.pity)
        # 为保证设计约束，显式将概率上限限制为 1.0（防止任何计算误差导致 >1）
        prob = min(1.0, prob)
        success = self.rng.random() < prob
        is_up = False
        
        if success:
            # 判定是否为 UP 角色
            if self.guarantee_up:
                # 上次获得常驻角色，本次必定 UP
                is_up = True
                self.guarantee_up = False
                self.up_count += 1
            else:
                # 50% 概率 UP，50% 概率常驻
                is_up = self.rng.random() < 0.5
                if is_up:
                    self.up_count += 1
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
        
        return success, self.pity, prob, is_up

    def draw_n(self, n: int) -> tuple[list[bool], int, list[float], list[bool]]:
        """连续抽 `n` 次并返回每次结果与使用概率。

        返回 `(results_list, new_pity, probs_list, is_up_list)`，其中 `results_list` 为 bool 列表，
        `probs_list` 为对应每次抽卡使用的概率，`is_up_list` 为对应每次是否为 UP(仅在命中时有效)。
        """
        results: list[bool] = []
        probs: list[float] = []
        is_up_list: list[bool] = []
        for _ in range(int(n)):
            ok, _, p, is_up = self.draw_once()
            results.append(ok)
            probs.append(p)
            is_up_list.append(is_up)
        return results, self.pity, probs, is_up_list

    def pull_one(self) -> dict:
        """便捷接口：进行一次单抽并返回字典结果。

        返回结构：{"results": [bool], "new_pity": int, "used_probs": [float], "is_up": [bool], 
                  "avg_count": int, "up_count": int, "up_pity": int, "start_up_pity": int, "guarantee_up": bool}。
        """
        start_up_pity = self.up_pity
        ok, new_pity, prob, is_up = self.draw_once()
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
            "guarantee_up": self.guarantee_up
        }

    def pull_ten(self) -> dict:
        """便捷接口：进行一次十连并返回字典结果。

        返回结构同 `pull_one`，但 `results`、`used_probs` 与 `is_up` 长度为 10。
        """
        start_up_pity = self.up_pity
        results, new_pity, probs, is_up_list = self.draw_n(10)
        return {
            "results": results,
            "new_pity": new_pity,
            "used_probs": probs,
            "is_up": is_up_list,
            "avg_count": self.avg_count,
            "up_count": self.up_count,
            "up_pity": self.up_pity,
            "start_up_pity": start_up_pity,
            "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up
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
                
                # 判定是否为 UP：若 guarantee 为 True 则必为 UP，否则 50% 概率为 UP
                if current_guarantee:
                    is_up = True
                    current_up_count += 1
                    up_positions.append(pull_num)
                    current_guarantee = False  # 重置guarantee
                else:
                    is_up = rs.random() < 0.5
                    if is_up:
                        current_up_count += 1
                        up_positions.append(pull_num)
                        current_guarantee = False  # 重置guarantee
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
            'five_star_costs': five_star_costs,
            'stats': stats
        }