"""
目标达成概率计算（后端）- 抽卡资源 -> 达成目标概率

说明：
- 纠缠之缘 = 抽数（1:1）
- 支持多个具体目标：5星UP角色-1，5星UP角色-2，5星UP武器-1，5星UP武器-2
- 5星UP角色-1：在角色活动祈愿中抽取
- 5星UP角色-2：在角色活动祈愿-2中抽取
- 5星UP武器-1 和 5星UP武器-2：都在武器活动祈愿中抽取
  - 如果只想要其中一把，定轨那把武器
  - 如果两把都想要，定轨距离目标更远的那把（剩余需求更多的）
  - 定轨策略会在以下情况重新计算：
    1. 获得定轨武器时（命定值清零）
    2. 抽到常驻5星武器时（取消定轨后重新定轨）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


Strategy = Literal["character_then_weapon", "weapon_then_character"]


@dataclass(frozen=True)
class StartState:
    """抽卡起始状态数据类

    用于记录角色池和武器池的当前状态，包括保底计数、UP保证等信息。
    """
    # 角色池
    character_pity: int = 0  # 当前已连续未抽中5星角色的抽数
    character_guarantee_up: bool = False  # 下次5星是否必定为UP角色
    # 武器池
    weapon_pity: int = 0  # 当前已连续未抽中5星武器的抽数
    weapon_guarantee_up: bool = False  # 下次5星是否必定为UP武器
    weapon_fate_point: int = 0  # 命定值（0或1）


@dataclass(frozen=True)
class Targets:
    """抽卡目标数据类

    用于存储具体的抽卡目标，包括角色和武器的目标数量。
    """
    # 具体目标
    five_star_up_character_1: int = 0  # 5星UP角色-1的目标数量
    five_star_up_character_2: int = 0  # 5星UP角色-2的目标数量
    five_star_up_weapon_1: int = 0  # 5星UP武器-1的目标数量
    five_star_up_weapon_2: int = 0  # 5星UP武器-2的目标数量

    def total_target_copies(self) -> int:
        """计算总目标拷贝数"""
        return (
            self.five_star_up_character_1 +
            self.five_star_up_character_2 +
            self.five_star_up_weapon_1 +
            self.five_star_up_weapon_2
        )


class GoalProbabilityCalculator:
    """目标达成概率计算器

    使用蒙特卡洛模拟方法估算在指定资源下达成抽卡目标的概率。
    支持角色和武器两种抽卡类型，以及不同的抽取策略。
    """

    def __init__(self, max_total_draws: int = 3_000_000) -> None:
        """初始化概率计算器

        Args:
            max_total_draws: 单次请求的最大总抽数限制，避免服务器阻塞
        """
        # 单次请求的「抽数 * 试验次数」上限，避免阻塞
        self.max_total_draws = int(max_total_draws)

    # ===== 静态/类工具方法 =====

    @staticmethod
    def constellation_to_copies(constellation: int) -> int:
        """将命之座层数转换为目标拷贝数

        Args:
            constellation: 命之座层数（0-6）

        Returns:
            int: 需要的UP角色数量

        Raises:
            ValueError: 当命之座层数超出有效范围时
        """
        c = int(constellation)
        # 0-6 命：0 命 = 1 个 UP，6 命 = 7 个 UP
        if c < 0 or c > 6:
            raise ValueError("target_character_constellation must be between 0 and 6")
        return c + 1

    @staticmethod
    def refinement_to_copies(refinement: int) -> int:
        """将精炼层数转换为目标拷贝数

        Args:
            refinement: 精炼层数（0-5，0表示不抽武器）

        Returns:
            int: 需要的定轨武器数量

        Raises:
            ValueError: 当精炼层数超出有效范围时
        """
        r = int(refinement)
        # 0 表示本次不抽武器；1-5 精有效
        if r < 0:
            raise ValueError("target_weapon_refinement must be >= 0")
        if r == 0:
            return 0
        if r > 5:
            raise ValueError("target_weapon_refinement must be between 1 and 5")
        return r

    @staticmethod
    def _wilson_ci95(successes: int, n: int) -> tuple[float, float]:
        """计算95%置信区间的Wilson区间

        Args:
            successes: 成功次数
            n: 总试验次数

        Returns:
            tuple[float, float]: 置信区间的下界和上界
        """
        if n <= 0:
            return 0.0, 0.0
        z = 1.959963984540054  # 95%
        phat = successes / n
        denom = 1 + (z * z) / n
        center = (phat + (z * z) / (2 * n)) / denom
        half = (z / denom) * np.sqrt((phat * (1 - phat) + (z * z) / (4 * n)) / n)
        lo = max(0.0, center - half)
        hi = min(1.0, center + half)
        return float(lo), float(hi)

    # ===== 核心模拟方法 =====

    def _simulate_one_trial(
        self,
        *,
        pulls: int,
        targets: Targets,
        strategy: Strategy,
        seed: int,
        start: StartState,
        draw_character_module,
        draw_character2_module,
        draw_weapon_module,
    ) -> bool:
        """模拟单次试验

        Args:
            pulls: 总抽数
            targets: 抽卡目标
            strategy: 抽取策略
            seed: 随机种子
            start: 起始状态
            draw_character_module: 角色抽卡模块（UP角色-1）
            draw_character2_module: 角色抽卡模块2（UP角色-2）
            draw_weapon_module: 武器抽卡模块

        Returns:
            bool: 是否达成目标
        """
        # 预计算目标数量，减少重复计算
        need_char1 = max(0, int(targets.five_star_up_character_1))
        need_char2 = max(0, int(targets.five_star_up_character_2))
        need_weap1 = max(0, int(targets.five_star_up_weapon_1))
        need_weap2 = max(0, int(targets.five_star_up_weapon_2))
        
        remaining = int(pulls)

        # 快速路径：如果抽数不足，直接返回失败
        total_needed = need_char1 + need_char2 + need_weap1 + need_weap2
        if remaining < total_needed:
            return False

        # 快速路径：如果不需要抽任何东西，直接返回成功
        if total_needed == 0:
            return True

        # 减少模块属性访问开销
        CharacterWishSimulator = draw_character_module.CharacterWishSimulator
        CharacterWish2Simulator = draw_character2_module.CharacterWishSimulator
        WeaponWishSimulator = draw_weapon_module.WeaponWishSimulator

        # 分离 seed，避免角色/武器强相关
        rng = np.random.default_rng(seed)
        seed_char1 = int(rng.integers(0, 2**31 - 1))
        seed_char2 = int(rng.integers(0, 2**31 - 1))
        seed_weap = int(rng.integers(0, 2**31 - 1))

        # 创建角色模拟器实例（UP角色-1 和 UP角色-2 分别在不同的池子）
        char1_sim = CharacterWishSimulator(pity=start.character_pity, seed=seed_char1)
        char1_sim.guarantee_up = bool(start.character_guarantee_up)
        
        char2_sim = CharacterWish2Simulator(pity=start.character_pity, seed=seed_char2)
        char2_sim.guarantee_up = bool(start.character_guarantee_up)

        # 创建武器模拟器实例
        weap_sim = WeaponWishSimulator(pity=start.weapon_pity, seed=seed_weap)
        weap_sim.guarantee_up = bool(start.weapon_guarantee_up)
        weap_sim.fate_point = int(start.weapon_fate_point)
        # 注意：WeaponWishSimulator 没有 is_fate_guaranteed 属性

        # 辅助函数：根据当前剩余需求决定定轨武器
        def update_fate_weapon(current_got_weap1: int, current_got_weap2: int) -> None:
            """根据当前已获得数量更新定轨武器"""
            remaining_weap1 = need_weap1 - current_got_weap1
            remaining_weap2 = need_weap2 - current_got_weap2
            
            if remaining_weap1 > 0 and remaining_weap2 > 0:
                # 两个都还需要，定轨剩余需求更多的那把
                weap_sim.selected_fate_weapon = '5星UP武器-1' if remaining_weap1 >= remaining_weap2 else '5星UP武器-2'
            elif remaining_weap1 > 0:
                weap_sim.selected_fate_weapon = '5星UP武器-1'
            elif remaining_weap2 > 0:
                weap_sim.selected_fate_weapon = '5星UP武器-2'
            else:
                weap_sim.selected_fate_weapon = None
        
        # 初始化定轨武器
        update_fate_weapon(0, 0)

        got_char1 = 0
        got_char2 = 0
        got_weap1 = 0
        got_weap2 = 0

        # 执行抽取策略
        if strategy == "character_then_weapon":
            # 抽取UP角色-1（角色活动祈愿）
            while remaining > 0 and got_char1 < need_char1:
                # draw_once 返回: (is_5star, is_4star, new_pity, new_four_star_pity, used_probability, is_up, is_four_star_up, capture_minguang_triggered, four_star_item)
                is_5star, _, _, _, _, is_up, _, _, _ = char1_sim.draw_once()
                remaining -= 1
                if is_5star and is_up:
                    got_char1 += 1
                # 提前终止检查
                if (
                    got_char1 >= need_char1 and
                    got_char2 >= need_char2 and
                    got_weap1 >= need_weap1 and
                    got_weap2 >= need_weap2
                ):
                    return True
            
            # 抽取UP角色-2（角色活动祈愿-2）
            while remaining > 0 and got_char2 < need_char2:
                is_5star, _, _, _, _, is_up, _, _, _ = char2_sim.draw_once()
                remaining -= 1
                if is_5star and is_up:
                    got_char2 += 1
                # 提前终止检查
                if (
                    got_char1 >= need_char1 and
                    got_char2 >= need_char2 and
                    got_weap1 >= need_weap1 and
                    got_weap2 >= need_weap2
                ):
                    return True
            
            # 抽取武器（武器活动祈愿）
            while remaining > 0 and (got_weap1 < need_weap1 or got_weap2 < need_weap2):
                # draw_once 返回: (is_5star, is_4star, new_pity, new_four_star_pity, used_probability, is_up, is_four_star_up, is_fate, weapon_name, new_fate_point, selected_fate_weapon)
                is_5star, _, _, _, _, is_up, _, is_fate, weapon_name, _, _ = weap_sim.draw_once()
                remaining -= 1
                if is_5star and is_up:
                    # 根据武器名称判断是哪个UP武器
                    if weapon_name == '5星UP武器-1':
                        got_weap1 += 1
                    elif weapon_name == '5星UP武器-2':
                        got_weap2 += 1
                    # 如果获得了定轨武器（命定值清零），重新计算定轨策略
                    if is_fate:
                        update_fate_weapon(got_weap1, got_weap2)
                elif is_5star and not is_up:
                    # 抽到常驻5星武器，且两把武器都还需要
                    # 取消定轨并重新定轨离目标更远的那把
                    if got_weap1 < need_weap1 and got_weap2 < need_weap2:
                        # 取消定轨
                        weap_sim.selected_fate_weapon = None
                        # 重新定轨离目标更远的那把
                        update_fate_weapon(got_weap1, got_weap2)
                # 提前终止检查
                if (
                    got_char1 >= need_char1 and
                    got_char2 >= need_char2 and
                    got_weap1 >= need_weap1 and
                    got_weap2 >= need_weap2
                ):
                    return True
                    
        elif strategy == "weapon_then_character":
            # 抽取武器（武器活动祈愿）
            while remaining > 0 and (got_weap1 < need_weap1 or got_weap2 < need_weap2):
                is_5star, _, _, _, _, is_up, _, is_fate, weapon_name, _, _ = weap_sim.draw_once()
                remaining -= 1
                if is_5star and is_up:
                    if weapon_name == '5星UP武器-1':
                        got_weap1 += 1
                    elif weapon_name == '5星UP武器-2':
                        got_weap2 += 1
                    # 如果获得了定轨武器（命定值清零），重新计算定轨策略
                    if is_fate:
                        update_fate_weapon(got_weap1, got_weap2)
                elif is_5star and not is_up:
                    # 抽到常驻5星武器，且两把武器都还需要
                    # 取消定轨并重新定轨离目标更远的那把
                    if got_weap1 < need_weap1 and got_weap2 < need_weap2:
                        # 取消定轨
                        weap_sim.selected_fate_weapon = None
                        # 重新定轨离目标更远的那把
                        update_fate_weapon(got_weap1, got_weap2)
                # 提前终止检查
                if (
                    got_char1 >= need_char1 and
                    got_char2 >= need_char2 and
                    got_weap1 >= need_weap1 and
                    got_weap2 >= need_weap2
                ):
                    return True
            
            # 抽取UP角色-1（角色活动祈愿）
            while remaining > 0 and got_char1 < need_char1:
                is_5star, _, _, _, _, is_up, _, _, _ = char1_sim.draw_once()
                remaining -= 1
                if is_5star and is_up:
                    got_char1 += 1
                # 提前终止检查
                if (
                    got_char1 >= need_char1 and
                    got_char2 >= need_char2 and
                    got_weap1 >= need_weap1 and
                    got_weap2 >= need_weap2
                ):
                    return True
            
            # 抽取UP角色-2（角色活动祈愿-2）
            while remaining > 0 and got_char2 < need_char2:
                is_5star, _, _, _, _, is_up, _, _, _ = char2_sim.draw_once()
                remaining -= 1
                if is_5star and is_up:
                    got_char2 += 1
                # 提前终止检查
                if (
                    got_char1 >= need_char1 and
                    got_char2 >= need_char2 and
                    got_weap1 >= need_weap1 and
                    got_weap2 >= need_weap2
                ):
                    return True
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        return (
            got_char1 >= need_char1 and
            got_char2 >= need_char2 and
            got_weap1 >= need_weap1 and
            got_weap2 >= need_weap2
        )

    def estimate_goal_probability(
        self,
        *,
        pulls: int,
        targets: Targets,
        trials: int,
        strategy: Strategy,
        seed: int | None,
        start: StartState,
        draw_character_module,
        draw_character2_module,
        draw_weapon_module,
    ) -> dict:
        """估算目标达成概率

        Args:
            pulls: 总抽数
            targets: 抽卡目标
            trials: 试验次数
            strategy: 抽取策略
            seed: 随机种子
            start: 起始状态
            draw_character_module: 角色抽卡模块（UP角色-1）
            draw_character2_module: 角色抽卡模块2（UP角色-2）
            draw_weapon_module: 武器抽卡模块

        Returns:
            dict: 包含概率估算结果的字典
        """
        pulls = int(pulls)
        trials = int(trials)
        if pulls < 0:
            raise ValueError("pulls/resources must be >= 0")
        if trials <= 0:
            raise ValueError("trials must be > 0")

        # 计算总目标拷贝数
        total_needed = targets.total_target_copies()

        # 当总抽数小于总目标拷贝数时，概率应显示为0
        if pulls < total_needed:
            return {
                "strategy": strategy,
                "pulls": pulls,
                "trials_requested": trials,
                "trials_used": 0,
                "successes": 0,
                "probability": 0.0,
                "frequency_estimate": 0.0,
                "ci95_wilson": [0.0, 0.0],
            }

        # 当抽数足够大时，直接返回100%概率
        # 计算最大可能的抽数（100%概率）
        total_pulls_needed = (
            (targets.five_star_up_character_1 * 180) +
            (targets.five_star_up_character_2 * 180) +
            (targets.five_star_up_weapon_1 * 160) +
            (targets.five_star_up_weapon_2 * 160)
        )

        # 检查是否满足条件
        if pulls >= total_pulls_needed:
            return {
                "strategy": strategy,
                "pulls": pulls,
                "trials_requested": trials,
                "trials_used": 0,
                "successes": 0,
                "probability": 1.0,
                "frequency_estimate": 1.0,
                "ci95_wilson": [1.0, 1.0],
            }

        # 固定试验次数以提升性能
        # 设置为固定值 10000 次，平衡精度和性能
        fixed_trials = 10000

        # 固定试验次数为 10000 次，不受抽数影响
        effective_trials = fixed_trials

        base_seed = 123456789 if seed is None else int(seed)
        ss = np.random.SeedSequence(base_seed)
        child_seeds = ss.spawn(effective_trials)

        successes = 0

        # 定义模拟函数
        def simulate_trial(trial_seed):
            return self._simulate_one_trial(
                pulls=pulls,
                targets=targets,
                strategy=strategy,
                seed=trial_seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module,
            )

        # 尝试使用并行计算
        try:
            import concurrent.futures
            # 使用ThreadPoolExecutor，避免多进程无法访问局部函数的问题
            with concurrent.futures.ThreadPoolExecutor() as executor:
                trial_seeds = [int(child_seeds[i].generate_state(1, dtype=np.uint32)[0]) for i in range(effective_trials)]
                results = list(executor.map(simulate_trial, trial_seeds))
                successes = sum(results)
        except ImportError:
            # 回退到串行执行
            for i in range(effective_trials):
                trial_seed = int(child_seeds[i].generate_state(1, dtype=np.uint32)[0])
                if simulate_trial(trial_seed):
                    successes += 1

        # 频率估计：successes / n
        freq_p = successes / effective_trials if effective_trials else 0.0
        # 使用 Jeffreys 先验 Beta(0.5, 0.5) 的贝叶斯估计，避免小样本下直接为 0 或 1
        # posterior mean = (s + 0.5) / (n + 1)
        bayes_p = (successes + 0.5) / (effective_trials + 1) if effective_trials else 0.0

        ci_lo, ci_hi = self._wilson_ci95(successes, effective_trials)
        return {
            "strategy": strategy,
            "pulls": pulls,
            "trials_requested": trials,
            "trials_used": effective_trials,
            "successes": successes,
            # 对外使用平滑后的贝叶斯估计，降低小样本导致的 0 概率问题
            "probability": float(bayes_p),
            "frequency_estimate": float(freq_p),
            "ci95_wilson": [ci_lo, ci_hi],
        }

    def calculate_required_pulls_for_95_percent_probability(
        self,
        *,
        targets: Targets,
        strategy: Strategy,
        seed: int | None = None,
        start: StartState | None = None,
        draw_character_module = None,
        draw_character2_module = None,
        draw_weapon_module = None,
    ) -> dict:
        """计算达成目标概率达到95%时的所需抽数

        Args:
            targets: 抽卡目标
            strategy: 抽取策略
            seed: 随机种子
            start: 起始状态
            draw_character_module: 角色抽卡模块（UP角色-1）
            draw_character2_module: 角色抽卡模块2（UP角色-2）
            draw_weapon_module: 武器抽卡模块

        Returns:
            dict: 包含所需抽数和相关信息的字典
        """
        # 导入必要的模块
        if draw_character_module is None:
            import backend.wish.CharacterWish as draw_character_module
        if draw_character2_module is None:
            import backend.wish.CharacterWish2 as draw_character2_module
        if draw_weapon_module is None:
            import backend.wish.WeaponWish as draw_weapon_module
        if start is None:
            start = StartState()

        # 快速路径：如果不需要抽任何东西，直接返回0抽
        total_needed = targets.total_target_copies()
        if total_needed == 0:
            return {
                "strategy": strategy,
                "required_pulls": 0,
                "targets": {
                    "five_star_up_character_1": targets.five_star_up_character_1,
                    "five_star_up_character_2": targets.five_star_up_character_2,
                    "five_star_up_weapon_1": targets.five_star_up_weapon_1,
                    "five_star_up_weapon_2": targets.five_star_up_weapon_2
                }
            }

        # 计算最大可能的抽数（100%概率）
        max_pulls = (
            (targets.five_star_up_character_1 * 180) +
            (targets.five_star_up_character_2 * 180) +
            (targets.five_star_up_weapon_1 * 160) +
            (targets.five_star_up_weapon_2 * 160)
        )
        
        # 二分查找范围，根据用户要求缩小范围
        # 该抽数会接近最大可能的抽数（100%概率），且大于等于最大可能的抽数除以2
        low = max(total_needed, max_pulls // 2)  # 最小可能的抽数，且不小于最大抽数的一半
        high = max_pulls  # 最大可能的抽数（100%概率）

        # 初始化结果
        required_pulls = high

        # 二分查找
        while low <= high:
            mid = (low + high) // 2
            
            # 计算当前抽数下的概率
            # 早期迭代使用较少的模拟次数，加快搜索速度
            # 后期迭代使用更多的模拟次数，提高精度
            trials = 1000 if abs(mid - (low + high) // 2) > 50 else 5000
            
            result = self.estimate_goal_probability(
                pulls=mid,
                targets=targets,
                trials=trials,
                strategy=strategy,
                seed=seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module,
            )
            
            probability = result["probability"]
            
            if probability >= 0.95:
                # 找到一个可行的抽数，尝试找更小的
                required_pulls = mid
                high = mid - 1
            else:
                # 概率不够，需要更多抽数
                low = mid + 1

        # 验证最终结果，使用较多的模拟次数确保精度
        final_result = self.estimate_goal_probability(
            pulls=required_pulls,
            targets=targets,
            trials=5000,
            strategy=strategy,
            seed=seed,
            start=start,
            draw_character_module=draw_character_module,
            draw_character2_module=draw_character2_module,
            draw_weapon_module=draw_weapon_module,
        )

        return {
            "strategy": strategy,
            "required_pulls": required_pulls,
            "targets": {
                "five_star_up_character_1": targets.five_star_up_character_1,
                "five_star_up_character_2": targets.five_star_up_character_2,
                "five_star_up_weapon_1": targets.five_star_up_weapon_1,
                "five_star_up_weapon_2": targets.five_star_up_weapon_2
            },
            "final_probability": final_result["probability"],
        }
    
    def calculate_required_pulls_for_50_percent_probability(
        self,
        *,
        targets: Targets,
        strategy: Strategy,
        seed: int | None = None,
        start: StartState | None = None,
        draw_character_module = None,
        draw_character2_module = None,
        draw_weapon_module = None,
    ) -> dict:
        """计算达成目标概率达到50%时的所需抽数（期望）

        Args:
            targets: 抽卡目标
            strategy: 抽取策略
            seed: 随机种子
            start: 起始状态
            draw_character_module: 角色抽卡模块（UP角色-1）
            draw_character2_module: 角色抽卡模块2（UP角色-2）
            draw_weapon_module: 武器抽卡模块

        Returns:
            dict: 包含所需抽数和相关信息的字典
        """
        # 导入必要的模块
        if draw_character_module is None:
            import backend.wish.CharacterWish as draw_character_module
        if draw_character2_module is None:
            import backend.wish.CharacterWish2 as draw_character2_module
        if draw_weapon_module is None:
            import backend.wish.WeaponWish as draw_weapon_module
        if start is None:
            start = StartState()

        # 快速路径：如果不需要抽任何东西，直接返回0抽
        total_needed = targets.total_target_copies()
        if total_needed == 0:
            return {
                "strategy": strategy,
                "required_pulls": 0,
                "targets": {
                    "five_star_up_character_1": targets.five_star_up_character_1,
                    "five_star_up_character_2": targets.five_star_up_character_2,
                    "five_star_up_weapon_1": targets.five_star_up_weapon_1,
                    "five_star_up_weapon_2": targets.five_star_up_weapon_2
                }
            }

        # 计算最大可能的抽数（100%概率）
        max_pulls = (
            (targets.five_star_up_character_1 * 180) +
            (targets.five_star_up_character_2 * 180) +
            (targets.five_star_up_weapon_1 * 160) +
            (targets.five_star_up_weapon_2 * 160)
        )
        
        # 二分查找范围，确保覆盖所有可能的情况
        low = total_needed  # 最小可能的抽数
        high = max_pulls  # 最大可能的抽数，使用与100%概率相同的上限

        # 初始化结果
        required_pulls = high

        # 二分查找
        while low <= high:
            mid = (low + high) // 2
            
            # 计算当前抽数下的概率
            # 早期迭代使用较少的模拟次数，加快搜索速度
            # 后期迭代使用更多的模拟次数，提高精度
            trials = 1000 if abs(mid - (low + high) // 2) > 30 else 5000
            
            result = self.estimate_goal_probability(
                pulls=mid,
                targets=targets,
                trials=trials,
                strategy=strategy,
                seed=seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module,
            )
            
            probability = result["probability"]
            
            if probability >= 0.5:
                # 找到一个可行的抽数，尝试找更小的
                required_pulls = mid
                high = mid - 1
            else:
                # 概率不够，需要更多抽数
                low = mid + 1

        # 验证最终结果，使用较多的模拟次数确保精度
        final_result = self.estimate_goal_probability(
            pulls=required_pulls,
            targets=targets,
            trials=5000,
            strategy=strategy,
            seed=seed,
            start=start,
            draw_character_module=draw_character_module,
            draw_character2_module=draw_character2_module,
            draw_weapon_module=draw_weapon_module,
        )

        return {
            "strategy": strategy,
            "required_pulls": required_pulls,
            "targets": {
                "five_star_up_character_1": targets.five_star_up_character_1,
                "five_star_up_character_2": targets.five_star_up_character_2,
                "five_star_up_weapon_1": targets.five_star_up_weapon_1,
                "five_star_up_weapon_2": targets.five_star_up_weapon_2
            },
            "final_probability": final_result["probability"],
        }

    def process_api_request(self, request_data: dict) -> dict:
        """处理API请求

        Args:
            request_data: API请求数据

        Returns:
            dict: 包含计算结果的字典
        """
        # 解析请求参数
        pulls = request_data.get('resources', 0)
        trials = request_data.get('trials', 10000)
        strategy = request_data.get('strategy', 'character_then_weapon')
        seed = request_data.get('seed', None)

        # 构建目标对象
        targets = Targets(
            five_star_up_character_1=request_data.get('target_five_star_up_character_1', 0),
            five_star_up_character_2=request_data.get('target_five_star_up_character_2', 0),
            five_star_up_weapon_1=request_data.get('target_five_star_up_weapon_1', 0),
            five_star_up_weapon_2=request_data.get('target_five_star_up_weapon_2', 0)
        )

        # 导入模块
        import backend.wish.CharacterWish as draw_character_module
        import backend.wish.CharacterWish2 as draw_character2_module
        import backend.wish.WeaponWish as draw_weapon_module

        # 计算概率
        result = self.estimate_goal_probability(
            pulls=pulls,
            targets=targets,
            trials=trials,
            strategy=strategy,
            seed=seed,
            start=StartState(),
            draw_character_module=draw_character_module,
            draw_character2_module=draw_character2_module,
            draw_weapon_module=draw_weapon_module
        )

        return result

    def process_required_pulls_request(self, request_data: dict, probability: float) -> dict:
        """处理所需抽数请求

        Args:
            request_data: API请求数据
            probability: 目标概率（0.5或0.95）

        Returns:
            dict: 包含所需抽数的字典
        """
        # 构建目标对象
        targets = Targets(
            five_star_up_character_1=request_data.get('target_five_star_up_character_1', 0),
            five_star_up_character_2=request_data.get('target_five_star_up_character_2', 0),
            five_star_up_weapon_1=request_data.get('target_five_star_up_weapon_1', 0),
            five_star_up_weapon_2=request_data.get('target_five_star_up_weapon_2', 0)
        )

        strategy = request_data.get('strategy', 'character_then_weapon')
        seed = request_data.get('seed', None)

        # 导入模块
        import backend.wish.CharacterWish as draw_character_module
        import backend.wish.CharacterWish2 as draw_character2_module
        import backend.wish.WeaponWish as draw_weapon_module

        # 根据概率调用不同的方法
        if probability == 0.5:
            result = self.calculate_required_pulls_for_50_percent_probability(
                targets=targets,
                strategy=strategy,
                seed=seed,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module
            )
        else:  # 0.95
            result = self.calculate_required_pulls_for_95_percent_probability(
                targets=targets,
                strategy=strategy,
                seed=seed,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module
            )

        return result