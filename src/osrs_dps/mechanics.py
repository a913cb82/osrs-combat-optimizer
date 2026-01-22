"""
OSRS Mechanics and Formulas.

This module contains the core mathematical formulas for Old School RuneScape,
including Max Hit, Hit Chance, and Experience calculations.
"""

import math
import re

# --- Constants ---
GAME_TICK_SECONDS = 0.6
XP_PER_DAMAGE = 4.0

# Formula Constants
EFFECTIVE_LEVEL_OFFSET = 8
EQUIPMENT_BONUS_OFFSET = 64
MAX_HIT_DIVISOR = 640.0
DEFENSE_ROLL_OFFSET = 9
HIT_CHANCE_ROLL_OFFSET = 64

# --- XP Calculations ---


def get_xp_for_level(level: int) -> int:


    """


    Calculates the total XP required to reach a specific level.


    Uses the OSRS formula: Points = floor(L + 300 * 2^(L/7)).


    """


    total_points = 0


    for level_index in range(1, level):


        diff = math.floor(level_index + 300 * (2 ** (level_index / 7.0)))


        total_points += diff


    return math.floor(total_points / 4)





def generate_xp_table(max_level: int = 126) -> dict[int, int]:


    """Generates a dictionary mapping level to required XP."""


    return {


        level_index: get_xp_for_level(level_index)


        for level_index in range(1, max_level + 1)


    }


# --- Combat Formulas ---


def calculate_max_hit(str_lvl: int, equip_str_bonus: int, style_bonus: int) -> int:
    """
    Calculates the maximum melee hit.

    Args:
        str_lvl: Visible Strength level (including potions/prayers,
                 though we assume base).
        equip_str_bonus: Total Strength bonus from equipment.
        style_bonus: +3 for Aggressive, +1 for Controlled, +0 otherwise.
    """
    effective_str = str_lvl + style_bonus + EFFECTIVE_LEVEL_OFFSET
    base_damage = (
        0.5
        + (effective_str * (equip_str_bonus + EQUIPMENT_BONUS_OFFSET)) / MAX_HIT_DIVISOR
    )
    return math.floor(base_damage)


def calculate_hit_chance(
    atk_lvl: int,
    equip_atk_bonus: int,
    style_bonus: int,
    monster_def_lvl: int = 1,
    monster_def_bonus: int = 0,
) -> float:
    """
    Calculates the probability of a successful hit (0.0 to 1.0).

    Args:
        atk_lvl: Visible Attack level.
        equip_atk_bonus: Attack bonus for the specific style (Stab/Slash/Crush).
        style_bonus: +3 for Accurate, +1 for Controlled, +0 otherwise.
        monster_def_lvl: Defender's Defense level (default 1 for low-level training).
        monster_def_bonus: Defender's specific defense bonus (default 0).
    """
    # Calculate Attack Roll
    effective_atk = atk_lvl + style_bonus + EFFECTIVE_LEVEL_OFFSET
    atk_roll = effective_atk * (equip_atk_bonus + HIT_CHANCE_ROLL_OFFSET)

    # Calculate Defense Roll
    effective_def = monster_def_lvl + DEFENSE_ROLL_OFFSET
    def_roll = effective_def * (monster_def_bonus + HIT_CHANCE_ROLL_OFFSET)

    if atk_roll > def_roll:
        return 1.0 - (def_roll + 2.0) / (2.0 * (atk_roll + 1.0))
    else:
        return atk_roll / (2.0 * (def_roll + 1.0))


def calculate_dps(max_hit: int, hit_chance: float, attack_speed: float) -> float:
    """Calculates Damage Per Second."""
    # Average damage per successful hit is roughly MaxHit / 2
    avg_damage_per_hit = 0.5 * max_hit * hit_chance
    return avg_damage_per_hit / attack_speed


# --- Utilities ---


def parse_time(time_str: str) -> float:
    """
    Parses a time string (e.g., '1h30m', '30s') into total seconds.
    Returns 0.0 if input is invalid or empty.
    """
    if not time_str:
        return 0.0

    # Check if direct float
    try:
        return float(time_str)
    except ValueError:
        pass

    total_seconds = 0
    multipliers = {"s": 1, "m": 60, "h": 3600}

    # Regex to find pairs of digits and units
    matches = re.findall(r"(\d+)([smh])", time_str.lower())

    for val, unit in matches:
        total_seconds += int(val) * multipliers[unit]

    return float(total_seconds)
