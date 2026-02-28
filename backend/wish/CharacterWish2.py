"""
角色活动祈愿-2抽卡模拟器 — 规则说明

规则概览：
- 5星物品规则：
  - 5星物品基础概率为 `BASE_RATE`（默认 0.6%）
  - 当连续73抽未抽到5星或以上物品时，抽取到5星物品的概率每抽上升6%，直到最高100%。
    即第74抽抽取5星以上概率为6.6%（0.6% + 6%）。
  - 当祈愿获取到5星物品时，有50.000%的概率为本期5星UP角色-2。
  - 如果本次祈愿获取的5星物品非本期5星UP角色-2，下次祈愿获取的5星物品必定为本期5星UP角色-2。

- 4星物品规则：
  - 4星物品基础概率为 `FOUR_STAR_BASE_RATE`（默认 5.100%）
  - 当连续8抽未抽到4星或以上物品时，抽取到4星物品的概率每抽上升51%，直到最高100%。
    即第9抽抽取4星以上概率为56.1%（5.1% + 51%）。
  - 当祈愿获取到4星物品时，有50.000%的概率为本期4星UP角色中的一个。
  - 如果本次祈愿获取的4星物品非本期4星UP角色，下次祈愿获取的4星物品必定为本期4星UP角色。
  - 当祈愿获取到4星UP物品时，每个本期4星UP角色的获取概率均等。

- 捕获明光机制：
  - 当获取到5星角色时，若并非必定获取5星UP的情况，可能触发捕获明光机制
  - 触发捕获明光的基础概率为 `CAPTURE_MINGUANG_BASE_RATE`（默认 0.018%）
  - 若连续3次在第二次获取5星角色时才获取本期up5星角色，则下次祈愿获取5星角色时，必定触发捕获明光机制

- 其他规则：
  - 若当次祈愿未获取4,5星物品，则随机获取1个3星物品。
  - 程序会维护累计抽数 `total_pulls`，并在输出页显示"当前总抽数"。
"""

import numpy as np
import sys
import os

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)



# 5星物品概率设置
BASE_RATE = 0.006  # 5星物品基础概率 0.6%
PITY_THRESHOLD = 73  # 5星保底阈值
PITY_INCREASE = 0.06  # 每超过保底阈值一次，5星概率额外提升 6%
FIVE_STAR_PITY_MAX = 89  # 5星必定出保底（第90抽）
FIVE_STAR_UP_RATE = 0.5  # 小保底：50%概率为UP角色
CAPTURE_MINGUANG_BASE_RATE = 0.00018  # 捕获明光机制的基础概率 0.018%
CAPTURE_MINGUANG_MAX_COUNTER = 3  # 捕获明光计数器最大值

# 4星物品概率设置
FOUR_STAR_BASE_RATE = 0.051  # 4星物品基础概率 5.100%
FOUR_STAR_CHARACTER_RATE = 0.0255  # 4星角色基础概率 2.550%
FOUR_STAR_WEAPON_RATE = 0.0255  # 4星武器基础概率 2.550%
FOUR_STAR_PITY_THRESHOLD = 8  # 4星概率开始提升的阈值（连续8抽未出4星，第9抽开始提升）
FOUR_STAR_PITY_INCREASE = 0.51  # 超过保底阈值前每抽一次4星概率提升 51%
FOUR_STAR_UP_RATE = 0.5  # 4星UP概率 50%

# 5星UP角色
FIVE_STAR_UP_CHARACTER = '5星UP角色-2'  # 本期5星UP角色-2

# 4星UP角色列表
FOUR_STAR_UP_CHARACTERS = ['4星UP角色-1', '4星UP角色-2', '4星UP角色-3']  # 本期4星UP角色


class CharacterWishSimulator2:
    """封装角色活动祈愿-2抽卡逻辑的类。

    属性:
    - `pity`: 当前已连续未抽中 5★ 角色 的次数（整数）
    - `four_star_pity`: 当前已连续未抽中 4★ 物品 的次数（整数）
    - `up_pity`: 距离上次 5★ UP 角色的抽数
    - `guarantee_up`: 下次 5★ 是否必定为 UP 角色（常驻角色后自动设为 True）
    - `guarantee_four_star_up`: 下次 4★ 是否必定为 UP 物品（非UP4星后自动设为 True）
    - `avg_count`: 当前已获取的常驻5星角色数
    - `up_count`: 当前已获取的 UP5星角色数
    - `four_star_up_count`: 当前已获取的 UP4星物品数
    - `four_star_avg_count`: 当前已获取的常驻4星物品数
    - `base_rate`, `pity_threshold`, `pity_increase`：概率参数
    - `rng`: numpy 随机数生成器

    方法:
    - `current_rate(pity=None)`: 返回给定（或当前）pity 的5星命中概率
    - `draw_once()`: 进行一次抽卡，返回抽卡结果和状态更新
    - `draw_n(n)`: 连续抽 n 次，返回每次的抽卡结果和状态更新
    - `pull_one()`: 便捷接口，进行一次单抽并返回字典结果
    - `pull_ten()`: 便捷接口，进行一次十连并返回字典结果
    """

    def __init__(self, pity: int = 0, *, base_rate: float = BASE_RATE, pity_threshold: int = PITY_THRESHOLD,
                 pity_increase: float = PITY_INCREASE, five_star_pity_max: int = FIVE_STAR_PITY_MAX, 
                 five_star_up_rate: float = FIVE_STAR_UP_RATE, seed: int | None = None, 
                 capture_minguang_base_rate: float = CAPTURE_MINGUANG_BASE_RATE,
                 capture_minguang_max_counter: int = CAPTURE_MINGUANG_MAX_COUNTER,
                 four_star_base_rate: float = FOUR_STAR_BASE_RATE, four_star_pity_threshold: int = FOUR_STAR_PITY_THRESHOLD,
                 four_star_pity_increase: float = FOUR_STAR_PITY_INCREASE, four_star_up_rate: float = FOUR_STAR_UP_RATE,
                 four_star_up_characters: list = FOUR_STAR_UP_CHARACTERS):
        self.total_pulls = 0  # 累计总抽数
        self.pity = int(pity)  # 当前已连续未抽中 5★ 角色的抽数
        self.up_pity = int(pity)  # 距离上次抽中 5★ UP 角色的抽数
        self.four_star_pity = 0  # 当前已连续未抽中 4★ 物品的抽数
        self.guarantee_up = False  # 下次 5★ 是否必定为 UP 角色（抽到常驻5星角色后自动设为 True）
        self.guarantee_four_star_up = False  # 下次 4★ 是否必定为 UP 物品（抽到常驻4星物品后自动设为 True）
        self.avg_count = 0  # 当前已获取的常驻5星角色数
        self.up_count = 0  # 当前已获取的 UP5星角色数
        self.four_star_up_count = 0  # 当前已获取的 4★ UP 物品总数
        self.four_star_avg_count = 0  # 当前已获取的常驻4星物品数
        self.four_star_up_1_count = 0  # 当前已获取的 4★ UP 角色「4星UP角色-1」的数量
        self.four_star_up_2_count = 0  # 当前已获取的 4★ UP 角色「4星UP角色-2」的数量
        self.four_star_up_3_count = 0  # 当前已获取的 4★ UP 角色「4星UP角色-3」的数量
        self.last_five_star_cost = 0  # 上一个5星花费的抽数
        self.base_rate = float(base_rate)  # 5★ 基础概率
        self.pity_threshold = int(pity_threshold)  # 5★ 概率开始提升的阈值
        self.pity_increase = float(pity_increase)  # 超过阈值后每抽一次5★概率提升的值
        self.five_star_pity_max = int(five_star_pity_max)  # 5★ 必定出保底（小保底）
        self.five_star_up_rate = float(five_star_up_rate)  # 小保底：UP角色概率
        self.four_star_base_rate = float(four_star_base_rate)  # 4★ 基础概率
        self.four_star_pity_threshold = int(four_star_pity_threshold)  # 4★ 概率开始提升的阈值
        self.four_star_pity_increase = float(four_star_pity_increase)  # 超过阈值后每抽一次4★概率提升的值
        self.four_star_up_rate = float(four_star_up_rate)  # 4★ UP概率
        self.rng = np.random.default_rng(seed)  # 随机数生成器
        self.capture_minguang_base_rate = float(capture_minguang_base_rate)  # 捕获明光基础触发概率
        self.capture_minguang_max_counter = int(capture_minguang_max_counter)  # 捕获明光计数器最大值
        self.migu_counter = 0  # 捕获明光计数器（记录连续通过大保底抽到UP5星角色的次数，达到最大值时必定触发捕获明光）
        self.guarantee_capture_minguang = False  # 下次抽中5星角色时是否必定触发捕获明光
        self.capture_minguang_count = 0  # 捕获明光触发总次数
        self.four_star_up_characters = four_star_up_characters  # 4星UP角色列表

    def current_five_star_rate(self, pity: int | None = None) -> float:
        """返回给定或当前 `pity` 下的 5★ 角色命中概率。

        参数:
        - `pity`: 可选，若不提供使用实例当前的 `self.pity`。
        返回值为 0.0-1.0 的浮点数。函数保证返回值不会超过 1.0（100%）。
        """
        p = self.pity if pity is None else int(pity)
        # 小保底
        if p >= self.five_star_pity_max:
            return 1.0
        if p < self.pity_threshold:
            return self.base_rate
        extra_steps = p - (self.pity_threshold - 1)
        return min(1.0, self.base_rate + extra_steps * self.pity_increase)

    def current_four_star_rate(self, four_star_pity: int | None = None) -> float:
        """返回给定或当前 `four_star_pity` 下的 4★ 物品命中概率。

        参数:
        - `four_star_pity`: 可选，若不提供使用实例当前的 `self.four_star_pity`。
        返回值为 0.0-1.0 的浮点数。函数保证返回值不会超过 1.0（100%）。
        """
        p = self.four_star_pity if four_star_pity is None else int(four_star_pity)
        # 小保底：连续未抽到4星时概率递增
        if p < self.four_star_pity_threshold:
            return self.four_star_base_rate
        extra_steps = p - (self.four_star_pity_threshold - 1)
        return min(1.0, self.four_star_base_rate + extra_steps * self.four_star_pity_increase)

    def draw_once(self) -> tuple[bool, bool, int, int, float, bool, bool, bool]:
        """进行一次抽卡：使用当前 `pity` 计算命中率并进行随机判定。

        若未命中，`self.pity` 增加 1；若命中，`self.pity` 重置为 0。
        返回值为 `(is_5star, is_4star, new_pity, new_four_star_pity, used_probability, is_up, is_four_star_up, capture_minguang_triggered)`。
        其中 `is_up` 表示若获得 5★，是否为 UP 角色，`is_four_star_up` 表示若获得 4★，是否为 UP 物品，
        `capture_minguang_triggered` 表示是否触发了捕获明光机制。
        """
        # 计算5星概率
        five_star_prob = self.current_five_star_rate(self.pity)
        five_star_prob = min(1.0, five_star_prob)
        
        # 先判断是否命中5星
        is_5star = self.rng.random() < five_star_prob
        is_4star = False
        is_up = False
        is_four_star_up = False
        capture_minguang_triggered = False
        four_star_item = '4星常驻物品'
        
        if is_5star:
            # 命中5星
            # 先判断捕获明光计数器是否为最大值，若是则必定触发捕获明光
            if self.migu_counter >= self.capture_minguang_max_counter:
                capture_minguang_triggered = True
                is_up = True
                self.up_count += 1
                self.capture_minguang_count += 1  # 增加捕获明光触发次数
                self.guarantee_capture_minguang = False
                self.migu_counter = 0
                self.guarantee_up = False
            else:
                # 检查是否触发大保底
                if self.guarantee_up:
                    # 大保底：上次获得常驻角色，本次必定 UP
                    is_up = True
                    self.guarantee_up = False
                    self.up_count += 1
                    # 捕获明光计数器+1（触发大保底时），最高为最大值
                    self.migu_counter = min(self.migu_counter + 1, self.capture_minguang_max_counter)
                else:
                    # 尝试触发捕获明光
                    capture_minguang_triggered = self.rng.random() < self.capture_minguang_base_rate
                    if capture_minguang_triggered:
                        is_up = True
                        self.up_count += 1
                        self.capture_minguang_count += 1  # 增加捕获明光触发次数
                        self.guarantee_capture_minguang = False
                        self.migu_counter = 0
                        self.guarantee_up = False
                    else:
                        # 小保底：UP 概率为 self.five_star_up_rate，其余概率为常驻
                        is_up = self.rng.random() < self.five_star_up_rate
                        if is_up:
                            self.up_count += 1
                            # 小保底时清零捕获明光计数器
                            self.migu_counter = 0
                        else:
                            self.avg_count += 1
                            self.guarantee_up = True  # 下次必定 UP
            
            # 重置pity
            self.last_five_star_cost = self.pity + 1  # 记录上一个5星花费的抽数
            self.pity = 0
            self.four_star_pity += 1  # 命中5星时，4星pity仍加1
            if is_up:
                self.up_pity = 0
            else:
                # 抽到常驻 5★ 时，距离上次 UP 的计数应加上本次抽数
                self.up_pity += 1
        else:
            # 未命中5星，判断是否命中4星
            # 计算4星概率
            four_star_prob = self.current_four_star_rate(self.four_star_pity)
            is_4star = self.rng.random() < four_star_prob
            
            if is_4star:
                # 命中4星
                is_four_star_up = False
                four_star_item = None
                
                if self.guarantee_four_star_up:
                    # 4星大保底：必定为UP物品
                    is_four_star_up = True
                    self.four_star_up_count += 1
                    self.guarantee_four_star_up = False
                else:
                    # UP概率为 self.four_star_up_rate
                    is_four_star_up = self.rng.random() < self.four_star_up_rate
                    if is_four_star_up:
                        self.four_star_up_count += 1
                    else:
                        self.four_star_avg_count += 1
                        self.guarantee_four_star_up = True  # 下次4星必定为UP
                
                # 选择4星物品
                if is_four_star_up:
                    # 从UP角色列表中随机选择一个
                    four_star_item = self.rng.choice(self.four_star_up_characters)
                    # 根据选择的4星UP角色更新对应的计数器
                    if four_star_item == '4星UP角色-1':
                        self.four_star_up_1_count += 1
                    elif four_star_item == '4星UP角色-2':
                        self.four_star_up_2_count += 1
                    elif four_star_item == '4星UP角色-3':
                        self.four_star_up_3_count += 1
                else:
                    # 生成一个4星常驻物品
                    # 这里简化处理，实际应该从常驻池里随机
                    four_star_item = '4星常驻物品'
                
                # 重置4星pity
                self.four_star_pity = 0
            else:
                # 未命中4星，增加4星pity
                self.four_star_pity += 1
                # 3星物品不区分任何类型
            
            # 未命中5星，增加5星pity
            self.pity += 1
            self.up_pity += 1

        # 增加累计抽数（在本次抽卡完成后计入）
        self.total_pulls += 1
        
        return is_5star, is_4star, self.pity, self.four_star_pity, five_star_prob, is_up, is_four_star_up, capture_minguang_triggered, four_star_item

    def draw_n(self, n: int) -> tuple[list[bool], list[bool], int, int, list[float], list[bool], list[bool], list[bool], list[str]]:
        """连续抽 `n` 次并返回每次结果与使用概率。

        返回 `(five_star_results, four_star_results, new_pity, new_four_star_pity, probs_list, is_up_list, is_four_star_up_list, capture_minguang_list, four_star_items_list)`，
        其中 `five_star_results` 为5星命中结果列表，`four_star_results` 为4星命中结果列表，
        `probs_list` 为对应每次抽卡使用的概率，`is_up_list` 为对应每次是否为 UP(仅在5星命中时有效)，
        `is_four_star_up_list` 为对应每次是否为4星 UP(仅在4星命中时有效)，
        `capture_minguang_list` 为对应每次是否触发捕获明光机制，`four_star_items_list` 为对应每次4星物品的具体信息。
        """
        five_star_results: list[bool] = []
        four_star_results: list[bool] = []
        probs: list[float] = []
        is_up_list: list[bool] = []
        is_four_star_up_list: list[bool] = []
        capture_minguang_list: list[bool] = []
        four_star_items_list: list[str] = []
        for _ in range(int(n)):
            is_5star, is_4star, _, _, p, is_up, is_four_star_up, capture_minguang, four_star_item = self.draw_once()
            five_star_results.append(is_5star)
            four_star_results.append(is_4star)
            probs.append(p)
            is_up_list.append(is_up)
            is_four_star_up_list.append(is_four_star_up)
            capture_minguang_list.append(capture_minguang)
            four_star_items_list.append(four_star_item)
        return five_star_results, four_star_results, self.pity, self.four_star_pity, probs, is_up_list, is_four_star_up_list, capture_minguang_list, four_star_items_list

    def pull_one(self) -> dict:
        """便捷接口：进行一次单抽并返回字典结果。

        返回结构：{"results": [bool], "four_star_results": [bool], "new_pity": int, "new_four_star_pity": int, "used_probs": [float], "is_up": [bool], "is_four_star_up": [bool], "four_star_items": [str],
                  "avg_count": int, "up_count": int, "four_star_up_count": int, "four_star_avg_count": int, "up_pity": int, "start_up_pity": int, "guarantee_up": bool, "guarantee_four_star_up": bool,
                  "capture_minguang": [bool], "migu_counter": int, "guarantee_capture_minguang": bool, "capture_minguang_count": int}。
        """
        start_up_pity = self.up_pity
        is_5star, is_4star, new_pity, new_four_star_pity, prob, is_up, is_four_star_up, capture_minguang, four_star_item = self.draw_once()
        return {
            "results": [is_5star],
            "four_star_results": [is_4star],
            "new_pity": new_pity,
            "new_four_star_pity": new_four_star_pity,
            "used_probs": [prob],
            "is_up": [is_up],
            "is_four_star_up": [is_four_star_up],
            "four_star_items": [four_star_item],
            "avg_count": self.avg_count,
            "up_count": self.up_count,
            "four_star_up_count": self.four_star_up_count,
            "four_star_avg_count": self.four_star_avg_count,
            "four_star_up_1_count": self.four_star_up_1_count,
            "four_star_up_2_count": self.four_star_up_2_count,
            "four_star_up_3_count": self.four_star_up_3_count,
            "up_pity": self.up_pity,
            "start_up_pity": start_up_pity,
            "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up,
            "guarantee_four_star_up": self.guarantee_four_star_up,
            "capture_minguang": [capture_minguang],
            "migu_counter": self.migu_counter,
            "guarantee_capture_minguang": self.guarantee_capture_minguang,
            "capture_minguang_count": self.capture_minguang_count,
            "last_five_star_cost": self.last_five_star_cost
        }

    def pull_ten(self) -> dict:
        """便捷接口：进行一次十连并返回字典结果。

        返回结构同 `pull_one`，但 `results`、`four_star_results`、`used_probs`、`is_up`、`is_four_star_up` 与 `four_star_items` 长度为 10。
        """
        start_up_pity = self.up_pity
        five_star_results, four_star_results, new_pity, new_four_star_pity, probs, is_up_list, is_four_star_up_list, capture_minguang_list, four_star_items_list = self.draw_n(10)
        return {
            "results": five_star_results,
            "four_star_results": four_star_results,
            "new_pity": new_pity,
            "new_four_star_pity": new_four_star_pity,
            "used_probs": probs,
            "is_up": is_up_list,
            "is_four_star_up": is_four_star_up_list,
            "four_star_items": four_star_items_list,
            "capture_minguang": capture_minguang_list,
            "avg_count": self.avg_count,
            "up_count": self.up_count,
            "four_star_up_count": self.four_star_up_count,
            "four_star_avg_count": self.four_star_avg_count,
            "four_star_up_1_count": self.four_star_up_1_count,
            "four_star_up_2_count": self.four_star_up_2_count,
            "four_star_up_3_count": self.four_star_up_3_count,
            "up_pity": self.up_pity,
            "start_up_pity": start_up_pity,
            "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up,
            "guarantee_four_star_up": self.guarantee_four_star_up,
            "migu_counter": self.migu_counter,
            "guarantee_capture_minguang": self.guarantee_capture_minguang,
            "capture_minguang_count": self.capture_minguang_count,
            "last_five_star_cost": self.last_five_star_cost
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
        - four_star_up_count: 4星UP物品数量
        - four_star_avg_count: 4星常驻物品数量
        - total_hits: 总命中数量（5星）
        - total_four_star_hits: 总4星命中数量
        - pity_history: 每次抽卡后的5星pity值
        - four_star_pity_history: 每次抽卡后的4星pity值
        - hit_positions: 5星命中位置列表
        - up_positions: UP命中位置列表
        - avg_positions: 常驻命中位置列表
        - four_star_positions: 4星命中位置列表
        - four_star_up_positions: 4星UP命中位置列表
        - stats: 数学统计信息，包括期望抽数、中位数抽数、标准差、最小抽数、最大抽数
        """
        total_pulls = int(total_pulls)
        if total_pulls <= 0:
            return {
                'up_count': 0,
                'avg_count': 0,
                'four_star_up_count': 0,
                'four_star_up_1_count': 0,
                'four_star_up_2_count': 0,
                'four_star_up_3_count': 0,
                'four_star_avg_count': 0,
                'total_hits': 0,
                'total_four_star_hits': 0,
                'pity_history': [],
                'four_star_pity_history': [],
                'hit_positions': [],
                'up_positions': [],
                'avg_positions': [],
                'four_star_positions': [],
                'four_star_up_positions': [],
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
        current_four_star_pity = int(self.four_star_pity)
        current_guarantee = bool(self.guarantee_up)
        current_guarantee_four_star_up = bool(self.guarantee_four_star_up)
        current_capture_minguang_guarantee = False
        current_migu_counter = 0
        current_capture_minguang_count = 0  # 捕获明光触发次数
        current_up_count = 0
        current_avg_count = 0
        current_four_star_up_count = 0
        current_four_star_avg_count = 0
        current_four_star_up_1_count = 0
        current_four_star_up_2_count = 0
        current_four_star_up_3_count = 0
        total_hits = 0
        total_four_star_hits = 0
        current_last_five_star_cost = 0  # 上一个5星花费的抽数
        
        # 记录抽卡过程
        pity_history = []
        four_star_pity_history = []
        hit_positions = []
        up_positions = []
        avg_positions = []
        four_star_positions = []
        four_star_up_positions = []
        # 记录每次5星所花费的抽数
        five_star_costs = []
        last_hit_position = 0

        rs = self.rng

        # 执行指定次数的抽卡
        for pull_num in range(1, total_pulls + 1):
            # 计算当前5星抽卡概率
            five_star_prob = self.current_five_star_rate(current_pity)

            # 先判断是否命中5星
            is_5star = rs.random() < five_star_prob
            is_4star = False

            if is_5star:
                # 命中5★，记录位置
                total_hits += 1
                hit_positions.append(pull_num)
                
                # 计算本次5星所花费的抽数
                if last_hit_position == 0:
                    cost = pull_num
                else:
                    cost = pull_num - last_hit_position
                last_hit_position = pull_num
                
                # 先判断捕获明光计数器是否为最大值，若是则必定触发捕获明光
                capture_minguang = False
                if current_migu_counter >= self.capture_minguang_max_counter:
                    capture_minguang = True
                    is_up = True
                    current_up_count += 1
                    current_capture_minguang_count += 1  # 增加捕获明光触发次数
                    up_positions.append(pull_num)
                    current_capture_minguang_guarantee = False
                    current_migu_counter = 0
                    current_guarantee = False
                else:
                    # 检查是否触发大保底
                    if current_guarantee:
                        # 大保底：上次获得常驻角色，本次必定 UP
                        is_up = True
                        current_up_count += 1
                        up_positions.append(pull_num)
                        current_guarantee = False
                        # 捕获明光计数器+1（触发大保底时），最高为最大值
                        current_migu_counter = min(current_migu_counter + 1, self.capture_minguang_max_counter)
                    else:
                        # 尝试触发捕获明光
                        capture_minguang = rs.random() < self.capture_minguang_base_rate
                        if capture_minguang:
                            is_up = True
                            current_up_count += 1
                            current_capture_minguang_count += 1  # 增加捕获明光触发次数
                            up_positions.append(pull_num)
                            current_capture_minguang_guarantee = False
                            current_migu_counter = 0
                            current_guarantee = False
                        else:
                            # 小保底：UP 概率为 self.five_star_up_rate，其余概率为常驻
                            is_up = rs.random() < self.five_star_up_rate
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
                    'is_up': is_up,
                    'capture_minguang': capture_minguang
                })
                
                # 重置pity
                current_last_five_star_cost = cost  # 记录上一个5星花费的抽数
                current_pity = 0
                current_four_star_pity += 1  # 命中5星时，4星pity仍加1
            else:
                # 未命中5星，判断是否命中4星
                # 计算4星概率
                four_star_prob = self.current_four_star_rate(current_four_star_pity)
                is_4star = rs.random() < four_star_prob
                
                if is_4star:
                    # 命中4星，记录位置
                    total_four_star_hits += 1
                    four_star_positions.append(pull_num)
                    
                    if current_guarantee_four_star_up:
                        # 4星大保底：必定为UP物品
                        is_four_star_up = True
                        current_four_star_up_count += 1
                        four_star_up_positions.append(pull_num)
                        current_guarantee_four_star_up = False
                    else:
                        # UP概率为 self.four_star_up_rate
                        is_four_star_up = rs.random() < self.four_star_up_rate
                        if is_four_star_up:
                            current_four_star_up_count += 1
                            four_star_up_positions.append(pull_num)
                        else:
                            current_four_star_avg_count += 1
                            current_guarantee_four_star_up = True  # 下次4星必定为UP
                    
                    # 选择4星物品
                    if is_four_star_up:
                        # 从UP角色列表中随机选择一个
                        four_star_item = rs.choice(self.four_star_up_characters)
                        # 根据选择的4星UP角色更新对应的计数器
                        if four_star_item == '4星UP角色-1':
                            current_four_star_up_1_count += 1
                        elif four_star_item == '4星UP角色-2':
                            current_four_star_up_2_count += 1
                        elif four_star_item == '4星UP角色-3':
                            current_four_star_up_3_count += 1
                    else:
                        # 生成一个4星常驻物品
                        # 这里简化处理，实际应该从常驻池里随机
                        four_star_item = '4星常驻物品'
                    
                    # 重置4星pity
                    current_four_star_pity = 0
                else:
                    # 未命中4星，增加4星pity
                    current_four_star_pity += 1
                
                # 未命中5星，增加5星pity
                current_pity += 1
            
            # 记录本次抽卡后的pity值
            pity_history.append(current_pity)
            four_star_pity_history.append(current_four_star_pity)

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
            'four_star_up_count': current_four_star_up_count,
            'four_star_up_1_count': current_four_star_up_1_count,
            'four_star_up_2_count': current_four_star_up_2_count,
            'four_star_up_3_count': current_four_star_up_3_count,
            'four_star_avg_count': current_four_star_avg_count,
            'total_hits': total_hits,
            'total_four_star_hits': total_four_star_hits,
            'capture_minguang_count': current_capture_minguang_count,
            'five_star_costs': five_star_costs,
            'pity_history': pity_history,
            'four_star_pity_history': four_star_pity_history,
            'hit_positions': hit_positions,
            'up_positions': up_positions,
            'avg_positions': avg_positions,
            'four_star_positions': four_star_positions,
            'four_star_up_positions': four_star_up_positions,
            'stats': stats,
            'last_five_star_cost': current_last_five_star_cost
        }
