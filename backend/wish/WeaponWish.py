"""
武器活动祈愿抽卡模拟器 — 规则说明

规则概览：
- 5星物品规则：
  - 5星武器基础概率为 0.700%
  - 当连续63抽未抽到5星物品时，抽取到5星以上物品的概率每抽增加7%，（即第64抽7.7%）直到最高100%。
  - 最多80次祈愿必定能通过保底获取5星武器。
  - 当祈愿获取到5星武器时，有75.000%的概率为本期5星UP武器 5星UP武器-1， 5星UP武器-2中的一个。
  - 如果本次祈愿获取的5星武器非本期5星UP武器，下次祈愿获取的5星武器必定为本期5星UP武器。
  - 在未通过命定值达到满值获取定轨武器的情况下，当祈愿获取到5星UP物品时，每把本期5星UP武器的获取概率均等。

- 4星物品规则：
  - 4星物品基础概率为 6.000%，4星角色祈愿的基础概率为3.000%，4星武器祈愿的基础概率为3.000%。
  - 当连续7抽未抽到4星以上物品时，抽取到4星以上物品的概率每抽增加60%，（即第8抽66%）直到最高100%。
  - 当祈愿获取到4星物品时，有75.000%的概率为本期4星UP武器：4星UP武器-1、4星UP武器-2、4星UP武器-3、4星UP武器-4、4星UP武器-5中的一个。
  - 如果本次祈愿获取的4星物品非本期4星UP武器，下次祈愿获取的4星物品必定为本期4星UP武器。
  - 当祈愿获取到4星UP物品时，每把本期4星UP武器的获取概率均等。

- 神铸定轨机制：
  - 可使用「神铸定轨」对本期5星UP武器进行定轨，定轨武器的选择仅在本期活动祈愿中生效。
  - 使用「神铸定轨」定轨武器后，当获取到的5星武器为非当前定轨武器时，获得1点命定值，命定值达到满值后，在本祈愿中获得的下一把5星武器必定为当前定轨武器。
  - 获取到当前定轨武器时，无论当前命定值是否达到满值，都将会重置为0，重新累计。
  - 未使用「神铸定轨」定轨武器时，将不会累积命定值。
  - 定轨武器可进行更换或取消。更换或取消当前定轨武器时，命定值将会重置为0，重新累计。

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
BASE_RATE = 0.007  # 5星武器基础概率 0.700%
PITY_THRESHOLD = 63  # 5星保底阈值（连续63抽未出5星）
PITY_INCREASE = 0.07  # 每超过保底阈值一次，5星概率额外提升 7%
FIVE_STAR_PITY_MAX = 79  # 5星必定出保底（第80抽）
FIVE_STAR_UP_RATE = 0.75  # 小保底：75%概率为UP武器

# 4星物品概率设置
FOUR_STAR_BASE_RATE = 0.06  # 4星物品基础概率 6.000%
FOUR_STAR_CHARACTER_RATE = 0.03  # 4星角色基础概率 3.000%
FOUR_STAR_WEAPON_RATE = 0.03  # 4星武器基础概率 3.000%
FOUR_STAR_PITY_THRESHOLD = 7  # 4星概率开始提升的阈值（连续7抽未出4星，第8抽开始提升）
FOUR_STAR_PITY_INCREASE = 0.6  # 超过保底阈值前每抽一次4星概率提升 60%
FOUR_STAR_UP_RATE = 0.75  # 4星UP概率 75%

# 命定值设置
FATE_POINT_MAX = 1  # 命定值满值（达到后必定获得定轨武器）

# 5星UP武器列表
FIVE_STAR_UP_WEAPONS = ['5星UP武器-1', '5星UP武器-2']  # 本期5星UP武器

# 4星UP武器列表
FOUR_STAR_UP_WEAPONS = ['4星UP武器-1', '4星UP武器-2', '4星UP武器-3', '4星UP武器-4', '4星UP武器-5']  # 本期4星UP武器


class WeaponWishSimulator:
    """封装抽卡逻辑的类。

    属性:
    - `pity`: 当前已连续未抽中 5★ 武器 的次数（整数）
    - `four_star_pity`: 当前已连续未抽中 4★ 物品 的次数（整数）
    - `guarantee_up`: 下次 5★ 是否必定为 UP 武器（常驻武器后自动设为 True）
    - `guarantee_four_star_up`: 下次 4★ 是否必定为 UP 物品（非UP4星后自动设为 True）
    - `fate_point`: 当前命定值（达到最大值时必定获得定轨武器）
    - `avg_count`: 当前已获取的常驻5星武器数
    - `five_star_up_counts`: 当前已获取的各5星UP武器的数量（字典）
    - `four_star_up_count`: 当前已获取的 UP4星物品数
    - `four_star_avg_count`: 当前已获取的常驻4星物品数
    - `selected_fate_weapon`: 当前选择的定轨武器（None表示不定轨）
    - `base_rate`, `pity_threshold`, `pity_increase`：概率参数
    - `rng`: numpy 随机数生成器

    方法:
    - `current_five_star_rate(pity=None)`: 返回给定（或当前）pity 的5星命中概率
    - `current_four_star_rate(four_star_pity=None)`: 返回给定（或当前）four_star_pity 的4星命中概率
    - `set_fate_weapon(weapon_name)`: 设置定轨武器
    - `draw_once()`: 进行一次抽卡，返回抽卡结果和状态更新
    - `draw_n(n)`: 连续抽 n 次，返回每次的抽卡结果和状态更新
    - `pull_one()`: 便捷接口，进行一次单抽并返回字典结果
    - `pull_ten()`: 便捷接口，进行一次十连并返回字典结果
    """

    def __init__(self, pity: int = 0, fate_point: int = 0, guarantee_up: bool = False,
                 guarantee_four_star_up: bool = False, selected_fate_weapon: str | None = None,
                 base_rate: float = BASE_RATE, pity_threshold: int = PITY_THRESHOLD,
                 pity_increase: float = PITY_INCREASE, five_star_pity_max: int = FIVE_STAR_PITY_MAX,
                 five_star_up_rate: float = FIVE_STAR_UP_RATE, seed: int | None = None,
                 four_star_base_rate: float = FOUR_STAR_BASE_RATE, four_star_pity_threshold: int = FOUR_STAR_PITY_THRESHOLD,
                 four_star_pity_increase: float = FOUR_STAR_PITY_INCREASE, four_star_up_rate: float = FOUR_STAR_UP_RATE,
                 fate_point_max: int = FATE_POINT_MAX,
                 five_star_up_weapons: list = FIVE_STAR_UP_WEAPONS, four_star_up_weapons: list = FOUR_STAR_UP_WEAPONS):
        self.total_pulls = 0  # 累计总抽数
        self.pity = int(pity)  # 当前已连续未抽中 5★ 武器的抽数
        self.four_star_pity = 0  # 当前已连续未抽中 4★ 物品的抽数
        self.guarantee_up = bool(guarantee_up)  # 下次 5★ 是否必定为 UP 武器（抽到常驻5星武器后自动设为 True）
        self.guarantee_four_star_up = bool(guarantee_four_star_up)  # 下次 4★ 是否必定为 UP 物品（抽到常驻4星物品后自动设为 True）
        self.fate_point = int(fate_point)  # 当前命定值
        self.fate_point_max = int(fate_point_max)  # 命定值最大值
        self.avg_count = 0  # 当前已获取的常驻5星武器数
        self.five_star_up_counts = {weapon: 0 for weapon in five_star_up_weapons}  # 当前已获取的各5星UP武器的数量
        self.four_star_up_count = 0  # 当前已获取的 4★ UP 物品总数
        self.four_star_avg_count = 0  # 当前已获取的常驻4星物品数
        self.last_five_star_cost = 0  # 上一个5星花费的抽数
        self.selected_fate_weapon = selected_fate_weapon  # 当前选择的定轨武器（None表示不定轨）
        self.base_rate = float(base_rate)  # 5★ 基础概率
        self.pity_threshold = int(pity_threshold)  # 5★ 概率开始提升的阈值
        self.pity_increase = float(pity_increase)  # 超过阈值后每抽一次5★概率提升的值
        self.five_star_pity_max = int(five_star_pity_max)  # 5★ 必定出保底（小保底）
        self.five_star_up_rate = float(five_star_up_rate)  # 小保底：UP武器概率
        self.four_star_base_rate = float(four_star_base_rate)  # 4★ 基础概率
        self.four_star_pity_threshold = int(four_star_pity_threshold)  # 4★ 概率开始提升的阈值
        self.four_star_pity_increase = float(four_star_pity_increase)  # 超过阈值后每抽一次4★概率提升的值
        self.four_star_up_rate = float(four_star_up_rate)  # 4★ UP概率
        self.rng = np.random.default_rng(seed)  # 随机数生成器
        self.five_star_up_weapons = five_star_up_weapons  # 5星UP武器列表
        self.four_star_up_weapons = four_star_up_weapons  # 4星UP武器列表

    def set_fate_weapon(self, weapon_name: str | None) -> None:
        """设置定轨武器。
        
        参数:
        - `weapon_name`: 定轨武器名称，必须在 five_star_up_weapons 列表中，或者为 None 表示取消定轨。
        """
        if weapon_name is None or weapon_name in self.five_star_up_weapons:
            self.selected_fate_weapon = weapon_name
            self.fate_point = 0  # 重置命定值

    def current_five_star_rate(self, pity: int | None = None) -> float:
        """返回给定或当前 `pity` 下的 5★ 武器命中概率。

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

    def draw_once(self) -> tuple[bool, bool, int, int, float, bool, bool, bool, str, bool, int, str | None]:
        """进行一次抽卡：使用当前 `pity` 计算命中率并进行随机判定。

        若未命中，`self.pity` 增加 1；若命中，`self.pity` 重置为 0。
        返回值为 `(is_5star, is_4star, new_pity, new_four_star_pity, used_probability, is_up, is_four_star_up, is_fate, weapon_name, is_fate_guaranteed, new_fate_point, selected_fate_weapon)`。
        其中 `is_up` 表示若获得 5★，是否为 UP 武器，`is_four_star_up` 表示若获得 4★，是否为 UP 物品，
        `is_fate` 表示若获得 5★，是否为定轨武器，`weapon_name` 表示武器名称，
        `new_fate_point` 表示新的命定值，
        `selected_fate_weapon` 表示当前选择的定轨武器。
        """
        # 计算5星概率
        five_star_prob = self.current_five_star_rate(self.pity)
        five_star_prob = min(1.0, five_star_prob)
        
        # 先判断是否命中5星
        is_5star = self.rng.random() < five_star_prob
        is_4star = False
        is_up = False
        is_four_star_up = False
        is_fate = False
        weapon_name = '3星武器'
        
        if is_5star:
            # 命中5星
            # 优先判断是否定轨
            if self.selected_fate_weapon is not None:
                # 已定轨情况
                # 检查是否触发命定值保底
                if self.fate_point >= self.fate_point_max:
                    # 命定值满值，必定获得定轨武器
                    is_fate = True
                    is_up = True
                    weapon_name = self.selected_fate_weapon
                    self.five_star_up_counts[weapon_name] += 1
                    self.fate_point = 0  # 重置命定值
                    self.guarantee_up = False
                else:
                    # 命定值未满，检查是否触发大保底
                    if self.guarantee_up:
                        # 大保底：上次获得常驻武器，本次必定 UP，随机获取一把UP武器
                        is_up = True
                        self.guarantee_up = False
                        # 随机选择一个5星UP武器
                        weapon_name = self.rng.choice(self.five_star_up_weapons)
                        self.five_star_up_counts[weapon_name] += 1
                        # 检查是否为定轨武器
                        if weapon_name == self.selected_fate_weapon:
                            is_fate = True
                            self.fate_point = 0  # 重置命定值
                        else:
                            # 非定轨武器，增加命定值并确保不超过最大值
                            self.fate_point = min(self.fate_point + 1, self.fate_point_max)
                    else:
                        # 命定值未满，小保底：UP 概率为 self.five_star_up_rate
                        is_up = self.rng.random() < self.five_star_up_rate
                        if is_up:
                            # 命中UP，随机选择一个UP武器
                            weapon_name = self.rng.choice(self.five_star_up_weapons)
                            self.five_star_up_counts[weapon_name] += 1
                            # 检查是否为定轨武器
                            if weapon_name == self.selected_fate_weapon:
                                is_fate = True
                                self.fate_point = 0  # 重置命定值
                            else:
                                # 非定轨武器，增加命定值并确保不超过最大值
                                self.fate_point = min(self.fate_point + 1, self.fate_point_max)
                        else:
                            # 未命中UP，获得常驻武器
                            weapon_name = '5星常驻武器'
                            self.avg_count += 1
                            self.guarantee_up = True  # 下次必定 UP
                            # 非UP武器，增加命定值并确保不超过最大值
                            self.fate_point = min(self.fate_point + 1, self.fate_point_max)
            else:
                # 未定轨情况
                # 检查是否触发大保底
                if self.guarantee_up:
                    # 大保底：上次获得常驻武器，本次必定 UP
                    is_up = True
                    self.guarantee_up = False
                    # 随机选择一个5星UP武器
                    weapon_name = self.rng.choice(self.five_star_up_weapons)
                    self.five_star_up_counts[weapon_name] += 1
                else:
                    # 小保底：UP 概率为 self.five_star_up_rate，其余概率为常驻
                    is_up = self.rng.random() < self.five_star_up_rate
                    if is_up:
                        # 随机选择一个5星UP武器
                        weapon_name = self.rng.choice(self.five_star_up_weapons)
                        self.five_star_up_counts[weapon_name] += 1
                    else:
                        # 常驻5星武器
                        weapon_name = '5星常驻武器'
                        self.avg_count += 1
                        self.guarantee_up = True  # 下次必定 UP
            
            # 重置pity
            self.last_five_star_cost = self.pity + 1  # 记录上一个5星花费的抽数
            self.pity = 0
            self.four_star_pity += 1  # 命中5星时，4星pity仍加1
        else:
            # 未命中5星，判断是否命中4星
            # 计算4星概率
            four_star_prob = self.current_four_star_rate(self.four_star_pity)
            is_4star = self.rng.random() < four_star_prob
            
            if is_4star:
                # 命中4星
                is_four_star_up = False
                
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
                    # 从UP武器列表中随机选择一个
                    weapon_name = self.rng.choice(self.four_star_up_weapons)
                else:
                    # 生成一个4星常驻物品
                    weapon_name = '4星常驻武器'
                
                # 重置4星pity
                self.four_star_pity = 0
            else:
                # 未命中4星，增加4星pity
                self.four_star_pity += 1
                # 3星武器不区分任何类型
            
            # 未命中5星，增加5星pity
            self.pity += 1

        # 增加累计抽数（在本次抽卡完成后计入）
        self.total_pulls += 1
        
        return is_5star, is_4star, self.pity, self.four_star_pity, five_star_prob, is_up, is_four_star_up, is_fate, weapon_name, self.fate_point, self.selected_fate_weapon

    def draw_n(self, n: int) -> tuple[list[bool], list[bool], int, int, list[float], list[bool], list[bool], list[bool], list[str], list[int], list[str | None]]:
        """连续抽 `n` 次并返回每次结果与使用概率。

        返回 `(five_star_results, four_star_results, new_pity, new_four_star_pity, probs_list, is_up_list, is_four_star_up_list, is_fate_list, weapon_names_list, fate_point_list, selected_fate_weapon_list)`，
        其中 `five_star_results` 为5星命中结果列表，`four_star_results` 为4星命中结果列表，
        `probs_list` 为对应每次抽卡使用的概率，`is_up_list` 为对应每次是否为 UP(仅在5星命中时有效)，
        `is_four_star_up_list` 为对应每次是否为4星 UP(仅在4星命中时有效)，
        `is_fate_list` 为对应每次是否为定轨武器(仅在5星命中时有效)，`weapon_names_list` 为对应每次武器的具体信息，
        `fate_point_list` 为对应每次的命定值，
        `selected_fate_weapon_list` 为对应每次选择的定轨武器。
        """
        five_star_results: list[bool] = []
        four_star_results: list[bool] = []
        probs: list[float] = []
        is_up_list: list[bool] = []
        is_four_star_up_list: list[bool] = []
        is_fate_list: list[bool] = []
        weapon_names_list: list[str] = []
        fate_point_list: list[int] = []
        selected_fate_weapon_list: list[str | None] = []
        for _ in range(int(n)):
            is_5star, is_4star, _, _, p, is_up, is_four_star_up, is_fate, weapon_name, fate_point, selected_fate_weapon = self.draw_once()
            five_star_results.append(is_5star)
            four_star_results.append(is_4star)
            probs.append(p)
            is_up_list.append(is_up)
            is_four_star_up_list.append(is_four_star_up)
            is_fate_list.append(is_fate)
            weapon_names_list.append(weapon_name)
            fate_point_list.append(fate_point)
            selected_fate_weapon_list.append(selected_fate_weapon)
        return five_star_results, four_star_results, self.pity, self.four_star_pity, probs, is_up_list, is_four_star_up_list, is_fate_list, weapon_names_list, fate_point_list, selected_fate_weapon_list

    def pull_one(self) -> dict:
        """便捷接口：进行一次单抽并返回字典结果。

        返回结构：{"results": [bool], "four_star_results": [bool], "new_pity": int, "new_four_star_pity": int, "used_probs": [float], "is_up": [bool], "is_four_star_up": [bool], "is_fate": [bool], "weapon_names": [str],
                  "avg_count": int, "five_star_up_counts": dict, "four_star_up_count": int, "four_star_avg_count": int, "guarantee_up": bool, "guarantee_four_star_up": bool, "fate_point": int, "selected_fate_weapon": str | None}
        """
        is_5star, is_4star, new_pity, new_four_star_pity, prob, is_up, is_four_star_up, is_fate, weapon_name, fate_point, selected_fate_weapon = self.draw_once()
        return {
            "results": [is_5star],
            "four_star_results": [is_4star],
            "new_pity": new_pity,
            "new_four_star_pity": new_four_star_pity,
            "used_probs": [prob],
            "is_up": [is_up],
            "is_four_star_up": [is_four_star_up],
            "is_fate": [is_fate],
            "weapon_names": [weapon_name],
            "avg_count": self.avg_count,
            "five_star_up_counts": self.five_star_up_counts,
            "four_star_up_count": self.four_star_up_count,
            "four_star_avg_count": self.four_star_avg_count,
            "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up,
            "guarantee_four_star_up": self.guarantee_four_star_up,
            "fate_point": fate_point,
            "selected_fate_weapon": selected_fate_weapon,
            "last_five_star_cost": self.last_five_star_cost
        }

    def pull_ten(self) -> dict:
        """便捷接口：进行一次十连并返回字典结果。

        返回结构同 `pull_one`，但 `results`、`four_star_results`、`used_probs`、`is_up`、`is_four_star_up`、`is_fate` 与 `weapon_names` 长度为 10。
        """
        five_star_results, four_star_results, new_pity, new_four_star_pity, probs, is_up_list, is_four_star_up_list, is_fate_list, weapon_names_list, fate_point_list, selected_fate_weapon_list = self.draw_n(10)
        return {
            "results": five_star_results,
            "four_star_results": four_star_results,
            "new_pity": new_pity,
            "new_four_star_pity": new_four_star_pity,
            "used_probs": probs,
            "is_up": is_up_list,
            "is_four_star_up": is_four_star_up_list,
            "is_fate": is_fate_list,
            "weapon_names": weapon_names_list,
            "avg_count": self.avg_count,
            "five_star_up_counts": self.five_star_up_counts,
            "four_star_up_count": self.four_star_up_count,
            "four_star_avg_count": self.four_star_avg_count,
            "total_pulls": self.total_pulls,
            "guarantee_up": self.guarantee_up,
            "guarantee_four_star_up": self.guarantee_four_star_up,
            "fate_point": self.fate_point,
            "selected_fate_weapon": selected_fate_weapon_list[-1] if selected_fate_weapon_list else None,
            "last_five_star_cost": self.last_five_star_cost
        }

    @classmethod
    def quick_pull_one(cls, pity: int = 0, fate_point: int = 0,
                      guarantee_up: bool = False, guarantee_four_star_up: bool = False,
                      selected_fate_weapon: str | None = None, fate_point_max: int = FATE_POINT_MAX, seed: int | None = None) -> dict:
        """类方法：无需显式创建实例即可进行一次单抽（返回结果，不保留状态）。"""
        sim = cls(pity, fate_point, guarantee_up, guarantee_four_star_up, selected_fate_weapon,
                 fate_point_max=fate_point_max, seed=seed)
        return sim.pull_one()

    @classmethod
    def quick_pull_ten(cls, pity: int = 0, fate_point: int = 0,
                      guarantee_up: bool = False, guarantee_four_star_up: bool = False,
                      selected_fate_weapon: str | None = None, fate_point_max: int = FATE_POINT_MAX, seed: int | None = None) -> dict:
        """类方法：无需显式创建实例即可进行一次十连（返回结果，不保留状态）。"""
        sim = cls(pity, fate_point, guarantee_up, guarantee_four_star_up, selected_fate_weapon,
                 fate_point_max=fate_point_max, seed=seed)
        return sim.pull_ten()

    def simulate_pulls(self, total_pulls: int) -> dict:
        """
        模拟实际抽卡 `total_pulls` 次，返回抽卡结果统计。

        返回字典：包含抽卡结果的统计信息，包括：
        - up_count: UP武器数量
        - avg_count: 常驻武器数量
        - five_star_up_counts: 各5星UP武器的数量（字典）
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
                'five_star_up_counts': {weapon: 0 for weapon in self.five_star_up_weapons},
                'avg_count': 0,
                'four_star_up_count': 0,
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
        current_pity = int(self.pity)  # 当前5星保底计数
        current_four_star_pity = int(self.four_star_pity)  # 当前4星保底计数
        current_guarantee = bool(self.guarantee_up)  # 下次是否必定UP
        current_guarantee_four_star_up = bool(self.guarantee_four_star_up)  # 下次是否必定4星UP
        current_fate_point = int(self.fate_point)  # 当前命定值
        current_fate_point_max = self.fate_point_max  # 命定值最大值
        current_selected_fate_weapon = self.selected_fate_weapon  # 当前选择的定轨武器
        current_five_star_up_counts = {weapon: 0 for weapon in self.five_star_up_weapons}  # 各5星UP武器的获取数量
        current_avg_count = 0  # 常驻5星武器获取数量
        current_four_star_up_count = 0  # 4星UP物品获取数量
        current_four_star_avg_count = 0  # 常驻4星物品获取数量
        total_hits = 0  # 5星命中总次数
        total_four_star_hits = 0  # 4星命中总次数
        current_last_five_star_cost = 0  # 上一个5星花费的抽数
        
        # 记录抽卡过程
        pity_history = []  # 每次抽卡后的5星保底计数
        four_star_pity_history = []  # 每次抽卡后的4星保底计数
        hit_positions = []  # 5星命中位置列表
        up_positions = []  # UP武器命中位置列表
        avg_positions = []  # 常驻武器命中位置列表

        four_star_positions = []  # 4星物品命中位置列表
        four_star_up_positions = []  # 4星UP物品命中位置列表
        # 记录每次5星所花费的抽数
        five_star_costs = []  # 每次5星的抽数花费记录
        last_hit_position = 0  # 上次5星命中的位置

        rs = self.rng  # 随机数生成器

        # 执行指定次数的抽卡
        for pull_num in range(1, total_pulls + 1):
            # 计算当前5星抽卡概率
            five_star_prob = self.current_five_star_rate(current_pity)

            # 先判断是否命中5星
            is_5star = rs.random() < five_star_prob
            is_4star = False
            is_up = False
            is_four_star_up = False
            is_fate = False

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
                
                # 优先判断是否定轨
                if current_selected_fate_weapon is not None:
                    # 已定轨情况
                    # 检查是否触发命定值保底
                    if current_fate_point >= current_fate_point_max:
                        # 命定值满值，必定获得定轨武器
                        is_fate = True
                        is_up = True
                        current_fate_point = 0  # 重置命定值
                        weapon_name = current_selected_fate_weapon
                        current_five_star_up_counts[weapon_name] += 1
                        current_guarantee = False
                    else:
                        # 命定值未满，检查是否触发大保底
                        if current_guarantee:
                            # 大保底：上次获得常驻武器，本次必定 UP，随机获取一把UP武器
                            is_up = True
                            current_guarantee = False
                            # 随机选择一个5星UP武器
                            weapon_name = rs.choice(self.five_star_up_weapons)
                            current_five_star_up_counts[weapon_name] += 1
                            up_positions.append(pull_num)
                            # 检查是否为定轨武器
                            if weapon_name == current_selected_fate_weapon:
                                is_fate = True
                                current_fate_point = 0  # 重置命定值
                            else:
                                # 非定轨武器，增加命定值并确保不超过最大值
                                current_fate_point = min(current_fate_point + 1, current_fate_point_max)
                        else:
                            # 小保底：UP 概率为 self.five_star_up_rate，其余概率为常驻
                            is_up = rs.random() < self.five_star_up_rate
                            if is_up:
                                # 随机选择一个UP武器
                                weapon_name = rs.choice(self.five_star_up_weapons)
                                current_five_star_up_counts[weapon_name] += 1
                                up_positions.append(pull_num)
                                # 检查是否为定轨武器
                                if weapon_name == current_selected_fate_weapon:
                                    is_fate = True
                                    current_fate_point = 0  # 重置命定值
                                else:
                                    # 非定轨武器，增加命定值并确保不超过最大值
                                    current_fate_point = min(current_fate_point + 1, current_fate_point_max)
                            else:
                                # 常驻5星武器
                                weapon_name = '5星常驻武器'
                                current_avg_count += 1
                                avg_positions.append(pull_num)
                                current_guarantee = True  # 下次必UP
                                # 非UP武器，增加命定值并确保不超过最大值
                                current_fate_point = min(current_fate_point + 1, current_fate_point_max)
                else:
                    # 未定轨情况
                    # 检查是否触发大保底
                    if current_guarantee:
                        # 大保底：上次获得常驻武器，本次必定 UP
                        is_up = True
                        current_guarantee = False
                        # 随机选择一个5星UP武器
                        weapon_name = rs.choice(self.five_star_up_weapons)
                        current_five_star_up_counts[weapon_name] += 1
                        up_positions.append(pull_num)
                    else:
                        # 小保底：UP 概率为 self.five_star_up_rate，其余概率为常驻
                        is_up = rs.random() < self.five_star_up_rate
                        if is_up:
                            # 随机选择一个5星UP武器
                            weapon_name = rs.choice(self.five_star_up_weapons)
                            current_five_star_up_counts[weapon_name] += 1
                            up_positions.append(pull_num)
                        else:
                            # 常驻5星武器
                            weapon_name = '5星常驻武器'
                            current_avg_count += 1
                            avg_positions.append(pull_num)
                            current_guarantee = True  # 下次必UP
                
                # 记录本次5星的信息
                five_star_costs.append({
                    'cost': cost,
                    'is_up': is_up,
                    'is_fate': is_fate,
                    'weapon_name': weapon_name
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
                        # 从UP武器列表中随机选择一个
                        weapon_name = rs.choice(self.four_star_up_weapons)
                    else:
                        # 生成一个4星常驻物品
                        weapon_name = '4星常驻武器'
                    
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
            'five_star_up_counts': current_five_star_up_counts,
            'avg_count': current_avg_count,
            'four_star_up_count': current_four_star_up_count,
            'four_star_avg_count': current_four_star_avg_count,
            'total_hits': total_hits,
            'total_four_star_hits': total_four_star_hits,
            'five_star_costs': five_star_costs,
            'pity_history': pity_history,
            'four_star_pity_history': four_star_pity_history,
            'hit_positions': hit_positions,
            'up_positions': up_positions,
            'avg_positions': avg_positions,
            'four_star_positions': four_star_positions,
            'four_star_up_positions': four_star_up_positions,
            'stats': stats,
            'last_five_star_cost': current_last_five_star_cost,
            'selected_fate_weapon': current_selected_fate_weapon
        }
