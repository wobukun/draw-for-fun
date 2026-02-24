"""
目标达成概率计算（后端）- 抽卡资源 -> 达成目标概率

说明：
- 纠缠之缘 = 抽数（1:1）
- 角色目标用“命之座层数”表示：0命=1个UP角色，1命=2个UP角色，... => copies = constellation + 1
- 武器目标用“精炼层数”表示：1精=1把目标武器，2精=2把目标武器，... => copies = refinement

实现策略：
- 使用蒙特卡洛模拟估算概率（固定 trials）
- 提供两种“先抽谁”的简单策略，并在 auto 模式下返回更高者：
  - character_then_weapon：先抽角色直到达成（或抽数用尽），剩余抽数用于武器
  - weapon_then_character：先抽武器直到达成（或抽数用尽），剩余抽数用于角色
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
    weapon_is_fate_guaranteed: bool = False  # 下次5星是否必定为定轨武器


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
        character_target_copies: int,
        weapon_target_copies: int,
        strategy: Strategy,
        seed: int,
        start: StartState,
        draw_character_module,
        draw_weapon_module,
    ) -> bool:
        """模拟单次试验

        Args:
            pulls: 总抽数
            character_target_copies: 目标角色拷贝数
            weapon_target_copies: 目标武器拷贝数
            strategy: 抽取策略
            seed: 随机种子
            start: 起始状态
            draw_character_module: 角色抽卡模块
            draw_weapon_module: 武器抽卡模块

        Returns:
            bool: 是否达成目标
        """
        CharacterGachaSimulator = draw_character_module.CharacterGachaSimulator
        WeaponGachaSimulator = draw_weapon_module.WeaponGachaSimulator

        # 分离 seed，避免角色/武器强相关
        rng = np.random.default_rng(seed)
        seed_char = int(rng.integers(0, 2**31 - 1))
        seed_weap = int(rng.integers(0, 2**31 - 1))

        char_sim = CharacterGachaSimulator(pity=start.character_pity, seed=seed_char)
        char_sim.guarantee_up = bool(start.character_guarantee_up)

        weap_sim = WeaponGachaSimulator(pity=start.weapon_pity, seed=seed_weap)
        weap_sim.guarantee_up = bool(start.weapon_guarantee_up)
        weap_sim.fate_point = int(start.weapon_fate_point)
        weap_sim.is_fate_guaranteed = bool(start.weapon_is_fate_guaranteed)

        need_char = max(0, int(character_target_copies))
        need_weap = max(0, int(weapon_target_copies))
        got_char = 0
        got_weap = 0

        remaining = int(pulls)
        if remaining <= 0:
            return need_char == 0 and need_weap == 0

        def pull_character_until_done() -> None:
            """抽角色直到达成目标或抽数用尽"""
            nonlocal remaining, got_char
            while remaining > 0 and got_char < need_char:
                success, _, _, is_up = char_sim.draw_once()
                remaining -= 1
                if success and is_up:
                    got_char += 1

        def pull_weapon_until_done() -> None:
            """抽武器直到达成目标或抽数用尽"""
            nonlocal remaining, got_weap
            while remaining > 0 and got_weap < need_weap:
                success, _, _, _, is_fate = weap_sim.draw_once()
                remaining -= 1
                # refinement 目标按"定轨武器"计数（更贴近"目标武器"）
                if success and is_fate:
                    got_weap += 1

        if strategy == "character_then_weapon":
            pull_character_until_done()
            pull_weapon_until_done()
        elif strategy == "weapon_then_character":
            pull_weapon_until_done()
            pull_character_until_done()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        return got_char >= need_char and got_weap >= need_weap

    def estimate_goal_probability(
        self,
        *,
        pulls: int,
        character_target_copies: int,
        weapon_target_copies: int,
        trials: int,
        strategy: Strategy,
        seed: int | None,
        start: StartState,
        draw_character_module,
        draw_weapon_module,
    ) -> dict:
        """估算目标达成概率

        Args:
            pulls: 总抽数
            character_target_copies: 目标角色拷贝数
            weapon_target_copies: 目标武器拷贝数
            trials: 试验次数
            strategy: 抽取策略
            seed: 随机种子
            start: 起始状态
            draw_character_module: 角色抽卡模块
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

        # 保护：避免 requests 过大导致卡死
        if pulls > 0:
            cap = max(1, self.max_total_draws // pulls)
            effective_trials = min(trials, cap)
        else:
            effective_trials = trials

        base_seed = 123456789 if seed is None else int(seed)
        ss = np.random.SeedSequence(base_seed)
        child_seeds = ss.spawn(effective_trials)

        successes = 0
        for i in range(effective_trials):
            trial_seed = int(child_seeds[i].generate_state(1, dtype=np.uint32)[0])
            ok = self._simulate_one_trial(
                pulls=pulls,
                character_target_copies=character_target_copies,
                weapon_target_copies=weapon_target_copies,
                strategy=strategy,
                seed=trial_seed,
                start=start,
                draw_character_module=draw_character_module,
                draw_weapon_module=draw_weapon_module,
            )
            if ok:
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


# ===== 向后兼容的模块级封装函数 =====

def constellation_to_copies(constellation: int) -> int:
    """兼容旧接口，内部委托给 GoalProbabilityCalculator

    Args:
        constellation: 命之座层数

    Returns:
        int: 需要的UP角色数量
    """
    return GoalProbabilityCalculator.constellation_to_copies(constellation)


def refinement_to_copies(refinement: int) -> int:
    """兼容旧接口，内部委托给 GoalProbabilityCalculator

    Args:
        refinement: 精炼层数

    Returns:
        int: 需要的定轨武器数量
    """
    return GoalProbabilityCalculator.refinement_to_copies(refinement)


def estimate_goal_probability(
    *,
    pulls: int,
    character_target_copies: int,
    weapon_target_copies: int,
    trials: int,
    strategy: Strategy,
    seed: int | None,
    start: StartState,
    draw_character_module,
    draw_weapon_module,
    max_total_draws: int = 3_000_000,
) -> dict:
    """兼容旧接口的函数形式入口，实际由 GoalProbabilityCalculator 实例完成计算。

    Args:
        pulls: 总抽数
        character_target_copies: 目标角色拷贝数
        weapon_target_copies: 目标武器拷贝数
        trials: 试验次数
        strategy: 抽取策略
        seed: 随机种子
        start: 起始状态
        draw_character_module: 角色抽卡模块
        draw_weapon_module: 武器抽卡模块
        max_total_draws: 最大总抽数限制

    Returns:
        dict: 包含概率估算结果的字典
    """
    calculator = GoalProbabilityCalculator(max_total_draws=max_total_draws)
    return calculator.estimate_goal_probability(
        pulls=pulls,
        character_target_copies=character_target_copies,
        weapon_target_copies=weapon_target_copies,
        trials=trials,
        strategy=strategy,
        seed=seed,
        start=start,
        draw_character_module=draw_character_module,
        draw_weapon_module=draw_weapon_module,
    )