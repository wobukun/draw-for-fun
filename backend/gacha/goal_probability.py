"""
目标达成概率计算（后端）- 抽卡资源 -> 达成目标概率

说明：
- 纠缠之缘 = 抽数（1:1）
- 角色目标用“命之座层数”表示：0命=1个UP角色，1命=2个UP角色，... => copies = constellation + 1
- 武器目标用“精炼层数”表示：1精=1把目标武器，2精=2把目标武器，... => copies = refinement

实现策略：
- 使用蒙特卡洛模拟估算概率（可设置 trials）
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
    # 角色池
    character_pity: int = 0
    character_guarantee_up: bool = False
    # 武器池
    weapon_pity: int = 0
    weapon_guarantee_up: bool = False
    weapon_fate_point: int = 0
    weapon_is_fate_guaranteed: bool = False


def constellation_to_copies(constellation: int) -> int:
    c = int(constellation)
    if c < 0:
        raise ValueError("target_character_constellation must be >= 0")
    return c + 1


def refinement_to_copies(refinement: int) -> int:
    r = int(refinement)
    if r < 0:
        raise ValueError("target_weapon_refinement must be >= 0")
    return r


def _wilson_ci95(successes: int, n: int) -> tuple[float, float]:
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


def _simulate_one_trial(
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
        nonlocal remaining, got_char
        while remaining > 0 and got_char < need_char:
            success, _, _, is_up = char_sim.draw_once()
            remaining -= 1
            if success and is_up:
                got_char += 1

    def pull_weapon_until_done() -> None:
        nonlocal remaining, got_weap
        while remaining > 0 and got_weap < need_weap:
            success, _, _, _, is_fate = weap_sim.draw_once()
            remaining -= 1
            # refinement 目标按“定轨武器”计数（更贴近“目标武器”）
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
    pulls = int(pulls)
    trials = int(trials)
    if pulls < 0:
        raise ValueError("pulls/resources must be >= 0")
    if trials <= 0:
        raise ValueError("trials must be > 0")

    # 保护：避免 requests 过大导致卡死
    if pulls > 0:
        cap = max(1, max_total_draws // pulls)
        effective_trials = min(trials, cap)
    else:
        effective_trials = trials

    base_seed = 123456789 if seed is None else int(seed)
    ss = np.random.SeedSequence(base_seed)
    child_seeds = ss.spawn(effective_trials)

    successes = 0
    for i in range(effective_trials):
        trial_seed = int(child_seeds[i].generate_state(1, dtype=np.uint32)[0])
        ok = _simulate_one_trial(
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

    p = successes / effective_trials if effective_trials else 0.0
    ci_lo, ci_hi = _wilson_ci95(successes, effective_trials)
    return {
        "strategy": strategy,
        "pulls": pulls,
        "trials_requested": trials,
        "trials_used": effective_trials,
        "successes": successes,
        "probability": float(p),
        "ci95_wilson": [ci_lo, ci_hi],
    }

