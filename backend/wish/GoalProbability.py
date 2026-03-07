"""
目标达成概率计算（后端）- 抽卡资源 -> 达成目标概率

说明：
- 纠缠之缘 = 抽数（1:1）
- 支持多个具体目标：5星UP角色-1，5星UP角色-2，5星UP武器-1，5星UP武器-2
- 5星UP角色-1：在角色活动祈愿中抽取
- 5星UP角色-2：在角色活动祈愿-2中抽取
  - 角色活动祈愿和角色活动祈愿-2共享保底（包括大保底和小保底）
  - 默认抽取顺序：角色活动祈愿 -> 角色活动祈愿-2 -> 武器活动祈愿
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

    # 类级别的默认模拟次数常量
    DEFAULT_TRIALS: int = 10000  # 默认模拟次数，用于概率估算
    
    def __init__(self, max_total_draws: int = 3_000_000, trials: int = None) -> None:
        """初始化概率计算器

        Args:
            max_total_draws: 单次请求的最大总抽数限制，避免服务器阻塞
            trials: 模拟试验次数，默认为 DEFAULT_TRIALS
        """
        # 单次请求的「抽数 * 试验次数」上限，避免阻塞
        self.max_total_draws = int(max_total_draws)
        # 实例级别的模拟次数，可通过参数覆盖默认值
        self.trials = trials if trials is not None else self.DEFAULT_TRIALS

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
        CharacterWish2Simulator = draw_character2_module.CharacterWishSimulator2
        WeaponWishSimulator = draw_weapon_module.WeaponWishSimulator

        # 分离 seed，避免角色/武器强相关
        rng = np.random.default_rng(seed)
        seed_char = int(rng.integers(0, 2**31 - 1))
        seed_weap = int(rng.integers(0, 2**31 - 1))

        # 创建角色模拟器实例（UP角色-1 和 UP角色-2 分别在不同的池子，但共享保底）
        # 使用相同的seed和初始状态，确保保底同步
        char1_sim = CharacterWishSimulator(pity=start.character_pity, seed=seed_char)
        char1_sim.guarantee_up = bool(start.character_guarantee_up)
        
        char2_sim = CharacterWish2Simulator(pity=start.character_pity, seed=seed_char)
        char2_sim.guarantee_up = bool(start.character_guarantee_up)

        # 创建武器模拟器实例
        weap_sim = WeaponWishSimulator(pity=start.weapon_pity, seed=seed_weap)
        weap_sim.guarantee_up = bool(start.weapon_guarantee_up)
        weap_sim.fate_point = int(start.weapon_fate_point)

        # 辅助函数：同步角色池状态（保底计数和UP保证状态）
        def sync_character_state(source_sim, target_sim):
            """将源模拟器的状态同步到目标模拟器"""
            target_sim.pity = source_sim.pity
            target_sim.guarantee_up = source_sim.guarantee_up
            # 同步捕获明光相关状态（如果存在）
            if hasattr(source_sim, 'migu_counter') and hasattr(target_sim, 'migu_counter'):
                target_sim.migu_counter = source_sim.migu_counter
            if hasattr(source_sim, 'guarantee_capture_minguang') and hasattr(target_sim, 'guarantee_capture_minguang'):
                target_sim.guarantee_capture_minguang = source_sim.guarantee_capture_minguang

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

        # 默认抽取顺序：角色活动祈愿 -> 角色活动祈愿-2 -> 武器活动祈愿
        # 角色池共享保底，需要同步状态
        
        # 抽取角色（两个池子共享保底）
        while remaining > 0 and (got_char1 < need_char1 or got_char2 < need_char2):
            # 优先抽取UP角色-1，如果还需要
            if got_char1 < need_char1:
                is_5star, _, _, _, _, is_up, _, _, _ = char1_sim.draw_once()
                remaining -= 1
                if is_5star:
                    if is_up:
                        got_char1 += 1
                    # 同步状态到角色池2
                    sync_character_state(char1_sim, char2_sim)
            # 然后抽取UP角色-2，如果还需要
            elif got_char2 < need_char2:
                is_5star, _, _, _, _, is_up, _, _, _ = char2_sim.draw_once()
                remaining -= 1
                if is_5star:
                    if is_up:
                        got_char2 += 1
                    # 同步状态到角色池1
                    sync_character_state(char2_sim, char1_sim)
            
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
            raise ValueError("pulls/resources must be >=0")
        if trials <= 0:
            raise ValueError("trials must be >0")

        # 计算总目标拷贝数
        total_needed = targets.total_target_copies()

        # 当总抽数小于总目标拷贝数时，概率应显示为0
        if pulls < total_needed:
            return {
                "strategy": strategy,
                "resources": pulls,
                "pulls": pulls,
                "trials_requested": trials,
                "trials_used": 0,
                "successes": 0,
                "probability": 0.0,
                "frequency_estimate": 0.0,
                "ci95_wilson": [0.0, 0.0],
                "targets": {
                    "five_star_up_character_1": targets.five_star_up_character_1,
                    "five_star_up_character_2": targets.five_star_up_character_2,
                    "five_star_up_weapon_1": targets.five_star_up_weapon_1,
                    "five_star_up_weapon_2": targets.five_star_up_weapon_2
                },
                "best": {
                    "probability": 0.0,
                    "ci95_wilson": [0.0, 0.0],
                    "trials_used": 0
                }
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
                "resources": pulls,
                "pulls": pulls,
                "trials_requested": trials,
                "trials_used": 0,
                "successes": 0,
                "probability": 1.0,
                "frequency_estimate": 1.0,
                "ci95_wilson": [1.0, 1.0],
                "targets": {
                    "five_star_up_character_1": targets.five_star_up_character_1,
                    "five_star_up_character_2": targets.five_star_up_character_2,
                    "five_star_up_weapon_1": targets.five_star_up_weapon_1,
                    "five_star_up_weapon_2": targets.five_star_up_weapon_2
                },
                "best": {
                    "probability": 1.0,
                    "ci95_wilson": [1.0, 1.0],
                    "trials_used": 0
                }
            }

        # 使用实例属性中的模拟次数
        effective_trials = self.trials

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
            "resources": pulls,
            "pulls": pulls,
            "trials_requested": trials,
            "trials_used": effective_trials,
            "successes": successes,
            # 对外使用平滑后的贝叶斯估计，降低小样本导致的 0 概率问题
            "probability": float(bayes_p),
            "frequency_estimate": float(freq_p),
            "ci95_wilson": [ci_lo, ci_hi],
            "targets": {
                "five_star_up_character_1": targets.five_star_up_character_1,
                "five_star_up_character_2": targets.five_star_up_character_2,
                "five_star_up_weapon_1": targets.five_star_up_weapon_1,
                "five_star_up_weapon_2": targets.five_star_up_weapon_2
            },
            "best": {
                "probability": float(bayes_p),
                "ci95_wilson": [ci_lo, ci_hi],
                "trials_used": effective_trials
            }
        }

    def _find_first_pulls_meeting_probability(
        self,
        *,
        targets: Targets,
        target_probability: float,
        strategy: Strategy,
        seed: int | None,
        start: StartState,
        draw_character_module,
        draw_character2_module,
        draw_weapon_module,
        quick_trials: int = 1000,
        medium_trials: int = 3000,
    ) -> tuple[int, dict]:
        """找到第一个满足目标概率的抽数（严格边界验证）

        使用二分查找找到最小的抽数 n，使得 P(成功|n抽) >= target_probability
        且 P(成功|n-1抽) < target_probability

        优化策略：
        - 前期搜索阶段使用适中的模拟次数（快速定位且保证准确）
        - 使用更激进的指数搜索步长，快速定位大致范围
        - 限制二分查找范围，聚焦于已找到的上界附近
        - 最后使用实例默认的模拟次数（self.trials，默认10000次）进行严格边界验证

        Args:
            targets: 抽卡目标
            target_probability: 目标概率（0.5或0.95）
            strategy: 抽取策略
            seed: 随机种子
            start: 起始状态
            draw_character_module: 角色抽卡模块
            draw_character2_module: 角色抽卡模块2
            draw_weapon_module: 武器抽卡模块
            quick_trials: 快速搜索阶段的模拟次数（默认1000）
            medium_trials: 精细搜索阶段的模拟次数（默认3000）

        Returns:
            tuple[int, dict]: (所需抽数, 最终结果字典)
        """
        # 计算边界
        total_needed = targets.total_target_copies()
        max_pulls = (
            (targets.five_star_up_character_1 * 180) +
            (targets.five_star_up_character_2 * 180) +
            (targets.five_star_up_weapon_1 * 160) +
            (targets.five_star_up_weapon_2 * 160)
        )

        # 快速路径
        if total_needed == 0:
            return 0, {"probability": 1.0}

        # 第一阶段：快速定位上界
        # 使用指数搜索 + 更激进的步长策略
        low = total_needed
        high = max_pulls
        found_upper_bound = False
        test_pulls = low
        step = 20  # 初始步长

        while test_pulls <= high and not found_upper_bound:
            result = self.estimate_goal_probability(
                pulls=test_pulls,
                targets=targets,
                trials=quick_trials,
                strategy=strategy,
                seed=seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module,
            )
            
            if result["probability"] >= target_probability:
                high = test_pulls
                found_upper_bound = True
            else:
                # 更激进的指数增长步长
                step = max(step, int(step * 1.5))
                test_pulls = min(test_pulls + step, high)
                low = test_pulls

        if not found_upper_bound:
            # 如果没找到上界，返回max_pulls
            final_result = self.estimate_goal_probability(
                pulls=max_pulls,
                targets=targets,
                trials=self.trials,
                strategy=strategy,
                seed=seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module,
            )
            return max_pulls, final_result

        # 第二阶段：精细二分查找（使用中等精度）
        # 限制搜索范围，避免在过大范围内进行无效的二分查找
        required_pulls = high
        low_bound = max(total_needed, high // 2)  # 从下界的一半开始，更聚焦
        
        while low_bound <= high:
            mid = (low_bound + high) // 2
            
            result = self.estimate_goal_probability(
                pulls=mid,
                targets=targets,
                trials=medium_trials,
                strategy=strategy,
                seed=seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module,
            )
            
            if result["probability"] >= target_probability:
                required_pulls = mid
                high = mid - 1
            else:
                low_bound = mid + 1

        # 第三阶段：严格边界验证（使用实例默认的模拟次数）
        # 确保 required_pulls 是第一个满足条件的抽数
        
        # 先验证当前抽数
        final_result = self.estimate_goal_probability(
            pulls=required_pulls,
            targets=targets,
            trials=self.trials,
            strategy=strategy,
            seed=seed,
            start=start,
            draw_character_module=draw_character_module,
            draw_character2_module=draw_character2_module,
            draw_weapon_module=draw_weapon_module,
        )
        
        # 如果当前抽数不满足，向后搜索
        while final_result["probability"] < target_probability and required_pulls < max_pulls:
            required_pulls += 1
            final_result = self.estimate_goal_probability(
                pulls=required_pulls,
                targets=targets,
                trials=self.trials,
                strategy=strategy,
                seed=seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module,
            )
        
        # 向前搜索，找到第一个满足条件的抽数
        while required_pulls > total_needed:
            prev_result = self.estimate_goal_probability(
                pulls=required_pulls - 1,
                targets=targets,
                trials=self.trials,
                strategy=strategy,
                seed=seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module,
            )
            if prev_result["probability"] < target_probability:
                # 找到了！required_pulls-1不满足，required_pulls满足
                break
            # 继续向前搜索
            required_pulls -= 1
            final_result = prev_result

        return required_pulls, final_result

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
        """计算达成目标概率达到95%时的所需抽数（高精度版本，严格边界验证）

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

        required_pulls, final_result = self._find_first_pulls_meeting_probability(
            targets=targets,
            target_probability=0.95,
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
        """计算达成目标概率达到50%时的所需抽数（高精度版本，严格边界验证）

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

        required_pulls, final_result = self._find_first_pulls_meeting_probability(
            targets=targets,
            target_probability=0.50,
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
        trials = request_data.get('trials', self.DEFAULT_TRIALS)
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

        # 导入模块
        import backend.wish.CharacterWish as draw_character_module
        import backend.wish.CharacterWish2 as draw_character2_module
        import backend.wish.WeaponWish as draw_weapon_module

        # 根据概率选择计算方法
        if probability == 0.95:
            result = self.calculate_required_pulls_for_95_percent_probability(
                targets=targets,
                strategy="character_then_weapon",
                seed=None,
                start=StartState(),
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module
            )
        elif probability == 0.5:
            result = self.calculate_required_pulls_for_50_percent_probability(
                targets=targets,
                strategy="character_then_weapon",
                seed=None,
                start=StartState(),
                draw_character_module=draw_character_module,
                draw_character2_module=draw_character2_module,
                draw_weapon_module=draw_weapon_module
            )
        else:
            raise ValueError(f"Invalid probability: {probability}. Must be 0.5 or 0.95")

        return result
