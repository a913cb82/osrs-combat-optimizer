"""
OSRS F2P Melee Optimizer.

This module implements an A* search algorithm to find the optimal leveling path
for Attack and Strength skills, considering weapon stats, acquisition costs,
and long-term time investments.
"""

import math
import heapq
import argparse
import time
from typing import Dict, List, Set, Tuple, Optional, FrozenSet
from dataclasses import dataclass, field

from weapon_db import WEAPON_DB
from mechanics import (
    generate_xp_table,
    calculate_max_hit,
    calculate_hit_chance,
    calculate_dps,
    parse_time,
    XP_PER_DAMAGE
)

# --- Constants ---
MAX_LEVEL_CAP = 125  # Extended buffer for lookahead calculations
XP_TABLE = generate_xp_table(MAX_LEVEL_CAP)

@dataclass(frozen=True)
class WeaponData:
    """Immutable weapon configuration data."""
    name: str
    attack_bonus: int
    strength_bonus: int
    speed: float
    attack_req: int
    base_cost: float

    def get_dps(self, atk_lvl: int, str_lvl: int, style: str, amulet_stats: Dict[str, int]) -> float:
        """Calculates DPS for this weapon at a given state."""
        # Determine style bonuses
        if style == 'accurate':
            style_bonus_acc = 3
            style_bonus_str = 0
        else: # aggressive
            style_bonus_acc = 0
            style_bonus_str = 3
            
        # Calculate raw stats
        max_hit = calculate_max_hit(str_lvl, self.strength_bonus + amulet_stats['str'], style_bonus_str)
        hit_chance = calculate_hit_chance(atk_lvl, self.attack_bonus + amulet_stats['acc'], style_bonus_acc)
        
        return calculate_dps(max_hit, hit_chance, self.speed)

@dataclass
class OptimizerConfig:
    """Configuration for the optimization run."""
    allowed_weapons: List[str]
    costs_override: Dict[str, float]
    amulet_stats: Dict[str, int]
    goal_level: int
    timeout: int
    lookahead_depth: int

def load_weapons(config: OptimizerConfig) -> Dict[str, WeaponData]:
    """Loads and filters weapons based on configuration."""
    loaded_weapons = {}
    for name, data in WEAPON_DB.items():
        # Check if allowed
        if not any(allowed.lower() in name.lower() for allowed in config.allowed_weapons):
            continue
            
        # Determine effective attack bonus (Mace logic)
        # Note: We simplify 'max_bonus' logic here for general pre-calc, 
        # but the WeaponData.get_dps method could be more specific if we passed raw bonuses.
        # For now, we stick to the optimized logic: 
        # If Mace -> Acc=Stab, Agg=Crush.
        # To handle this cleanly in WeaponData, we might need to store raw bonuses.
        # For performance, we pre-calculate the 'effective' bonus for the intended styles.
        
        # Actually, let's just stick to the robust logic used in previous version:
        # Maces use specific bonuses. Others use max.
        
        # We'll instantiate WeaponData with the RAW bonuses dictionary if possible?
        # No, WeaponData expects an int. 
        # Let's just create two virtual weapon profiles per weapon? 
        # Or make WeaponData smarter. 
        
        # Let's keep it simple: We used 'get_dps_raw' previously.
        # We'll just define helper functions instead of complex objects to keep it fast.
        pass
    return {} # Placeholder, we'll use dictionaries for speed in the critical path

# --- Optimization Engine ---

class LevelingOptimizer:
    def __init__(self, config: OptimizerConfig):
        self.config = config
        self.amulet_stats = config.amulet_stats
        self.goal = config.goal_level
        self.allowed_data = self._prepare_weapon_data()
        
        # Tables
        self.dps_table = {}
        self.heuristic_table = {}
        self.window_table = {}
        
    def _prepare_weapon_data(self) -> Dict[str, dict]:
        data_map = {}
        for name, entry in WEAPON_DB.items():
            if any(a.lower() in name.lower() for a in self.config.allowed_weapons):
                d = entry.copy()
                d['base_cost'] = self.config.costs_override.get(name, entry['cost'])
                
                # Pre-calculate style-specific bonuses
                if "mace" in name:
                    d['bonus_acc'] = entry['bonus']['stab']
                    d['bonus_agg'] = entry['bonus']['crush']
                else:
                    best = max(entry['bonus'].values())
                    d['bonus_acc'] = best
                    d['bonus_agg'] = best
                
                data_map[name] = d
        return data_map

    def _calculate_dps(self, name: str, atk: int, stri: int, style: str) -> float:
        data = self.allowed_data[name]
        
        if style == 'accurate':
            bonus_atk = data['bonus_acc'] + self.amulet_stats['acc']
            bonus_str = data['str'] + self.amulet_stats['str']
            s_str = 0
            s_acc = 3
        else: # aggressive
            bonus_atk = data['bonus_agg'] + self.amulet_stats['acc']
            bonus_str = data['str'] + self.amulet_stats['str']
            s_str = 3
            s_acc = 0
            
        mh = calculate_max_hit(stri, bonus_str, s_str)
        hc = calculate_hit_chance(atk, bonus_atk, s_acc)
        return calculate_dps(mh, hc, data['speed'])

    def precalculate_tables(self):
        """Generates DPS, Heuristic, and Lookahead tables."""
        print("Pre-calculating DPS tables...")
        for name in self.allowed_data:
            self.dps_table[name] = {'accurate': {}, 'aggressive': {}}
            for style in ['accurate', 'aggressive']:
                for a in range(1, 101):
                    self.dps_table[name][style][a] = {}
                    for s in range(1, 101):
                        self.dps_table[name][style][a][s] = self._calculate_dps(name, a, s, style)

        print("Pre-calculating A* heuristic...")
        # Best possible DPS at any level (ignoring cost)
        best_dps_grid = {'accurate': {}, 'aggressive': {}}
        for style in ['accurate', 'aggressive']:
            for a in range(1, 101):
                best_dps_grid[style][a] = {}
                for s in range(1, 101):
                    best_val = 0.0
                    for n, d in self.allowed_data.items():
                        if a >= d['atk_req']:
                            best_val = max(best_val, self.dps_table[n][style][a][s])
                    best_dps_grid[style][a][s] = best_val

        # Dynamic Programming for Heuristic (Remaining Time)
        self.heuristic_table = {}
        for a in range(self.goal, 0, -1):
            self.heuristic_table[a] = {}
            for s in range(self.goal, 0, -1):
                if a == self.goal and s == self.goal:
                    self.heuristic_table[a][s] = 0.0
                    continue
                
                time_atk = float('inf')
                time_str = float('inf')
                
                if a < self.goal:
                    d = best_dps_grid['accurate'][a][s]
                    if d > 0:
                        xp_req = XP_TABLE[a+1] - XP_TABLE[a]
                        time_atk = (xp_req / XP_PER_DAMAGE) / d + self.heuristic_table.get(a+1, {}).get(s, float('inf'))
                
                if s < self.goal:
                    d = best_dps_grid['aggressive'][a][s]
                    if d > 0:
                        xp_req = XP_TABLE[s+1] - XP_TABLE[s]
                        time_str = (xp_req / XP_PER_DAMAGE) / d + self.heuristic_table.get(a, {}).get(s+1, float('inf'))
                        
                self.heuristic_table[a][s] = min(time_atk, time_str)

        print("Pre-calculating Lookahead windows...")
        for name in self.allowed_data:
            self.window_table[name] = {'accurate': {}, 'aggressive': {}}
            for style in ['accurate', 'aggressive']:
                for a in range(1, 101):
                    self.window_table[name][style][a] = {}
                    for s in range(1, 101):
                        score = 0.0
                        for i in range(max(1, self.config.lookahead_depth)):
                            ca = min(self.goal, a + i) if style == 'accurate' else a
                            cs = min(self.goal, s + i) if style == 'aggressive' else s
                            
                            # Current training level
                            cl = ca if style == 'accurate' else cs
                            if cl >= self.goal: break
                            
                            d = self.dps_table[name][style][ca][cs]
                            if d <= 0:
                                score = float('inf')
                                break
                            
                            xp_req = XP_TABLE[cl+1] - XP_TABLE[cl]
                            score += (xp_req / XP_PER_DAMAGE) / d
                        self.window_table[name][style][a][s] = score

    def run(self):
        """Executes the A* search."""
        self.precalculate_tables()
        
        start_time = time.time()
        
        # Static availability map
        avail_by_atk = {
            lvl: [n for n, d in self.allowed_data.items() if lvl >= d['atk_req']] 
            for lvl in range(1, 101)
        }
        
        # Initial State
        # PQ: (f_score, g_score, atk, str, owned_set, path)
        start_h = self.heuristic_table[1][1]
        pq = [(start_h, 0.0, 1, 1, frozenset(), [])]
        visited = {}
        
        print("Searching for optimal path...")
        
        while pq:
            if time.time() - start_time > self.config.timeout:
                print(f"Timeout reached ({self.config.timeout}s)!")
                return None
                
            f, g, atk, stri, owned, path = heapq.heappop(pq)
            
            # Visited check (using g_score for optimality)
            state_key = (atk, stri, owned)
            if state_key in visited and visited[state_key] <= g:
                continue
            visited[state_key] = g
            
            if atk == self.goal and stri == self.goal:
                return (g, path)
            
            # Generate Successors
            for skill_train in ['Atk', 'Str']:
                if (skill_train == 'Atk' and atk >= self.goal) or \
                   (skill_train == 'Str' and stri >= self.goal):
                    continue
                
                style = 'accurate' if skill_train == 'Atk' else 'aggressive'
                
                # Candidate Selection (Best Owned + Best Unowned)
                best_owned = None # (dps, name)
                best_unowned = None # (window_score, name)
                
                for name in avail_by_atk[atk]:
                    dps = self.dps_table[name][style][atk][stri]
                    if dps <= 0: continue
                    
                    if name in owned:
                        if best_owned is None or dps > best_owned[0]:
                            best_owned = (dps, name)
                    else:
                        score = self.window_table[name][style][atk][stri] + self.allowed_data[name]['base_cost']
                        if best_unowned is None or score < best_unowned[0]:
                            best_unowned = (score, name)
                
                candidates = []
                if best_owned: candidates.append(best_owned[1])
                if best_unowned: candidates.append(best_unowned[1])
                
                # Expand Candidates
                for name in set(candidates):
                    dps = self.dps_table[name][style][atk][stri]
                    cost = 0.0 if name in owned else self.allowed_data[name]['base_cost']
                    
                    next_lvl = (atk + 1) if skill_train == 'Atk' else (stri + 1)
                    curr_level_val = atk if skill_train == 'Atk' else stri
                    xp_req = XP_TABLE[next_lvl] - XP_TABLE[curr_level_val]
                    
                    train_time = (xp_req / XP_PER_DAMAGE) / dps
                    new_g = g + train_time + cost
                    
                    # Update Owned Set (with pruning)
                    new_raw_owned = set(owned)
                    new_raw_owned.add(name)
                    
                    # Inline Pruning
                    # Keep only the weapons that provide best DPS for EITHER style at next state
                    na = next_lvl if skill_train == 'Atk' else atk
                    ns = next_lvl if skill_train == 'Str' else stri
                    
                    kept = set()
                    best_a_dps, best_s_dps = -1.0, -1.0
                    best_a_name, best_s_name = None, None
                    
                    for o_name in new_raw_owned:
                        da = self.dps_table[o_name]['accurate'][na][ns]
                        ds = self.dps_table[o_name]['aggressive'][na][ns]
                        if da > best_a_dps: best_a_dps = da; best_a_name = o_name
                        if ds > best_s_dps: best_s_dps = ds; best_s_name = o_name
                    
                    if best_a_name: kept.add(best_a_name)
                    if best_s_name: kept.add(best_s_name)
                    new_owned = frozenset(kept)
                    
                    new_h = self.heuristic_table[na][ns]
                    new_f = new_g + new_h
                    
                    new_key = (na, ns, new_owned)
                    if new_key not in visited or new_g < visited[new_key]:
                        heapq.heappush(pq, (new_f, new_g, na, ns, new_owned, 
                                          path + [(skill_train, next_lvl, new_g, name)]))
        return None

# --- Main Entry Point ---

def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}h {m}m {s}s"

def main():
    parser = argparse.ArgumentParser(description="OSRS F2P Melee Optimizer")
    parser.add_argument("--weapons", nargs='+', default=["scimitar"], help="List of allowed weapons")
    parser.add_argument("--costs", nargs='+', default=[], help="List of weapon costs (e.g. 'rune scimitar:999h')")
    parser.add_argument("--amulet", choices=["none", "str", "power", "accuracy"], default="str", help="Amulet choice")
    parser.add_argument("--goal", type=int, default=40, help="Target level")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--lookahead", type=int, default=100, help="Levels to look ahead")
    
    args = parser.parse_args()
    
    # Parse Cost Map
    costs_map = {}
    for item in args.costs:
        if ':' in item:
            name, time_str = item.split(':')
            costs_map[name.strip().lower()] = parse_time(time_str)
            
    # Configure Amulet
    ammy_stats = {"str": 0, "acc": 0}
    if args.amulet == "str": ammy_stats["str"] = 10
    elif args.amulet == "power": ammy_stats.update({"str": 6, "acc": 6})
    elif args.amulet == "accuracy": ammy_stats["acc"] = 4
    
    config = OptimizerConfig(
        allowed_weapons=args.weapons,
        costs_override=costs_map,
        amulet_stats=ammy_stats,
        goal_level=args.goal,
        timeout=args.timeout,
        lookahead_depth=args.lookahead
    )
    
    print(f"Optimizing for Goal: {args.goal}/{args.goal}, Weapons: {args.weapons}, Amulet: {args.amulet}, Lookahead: {args.lookahead}")
    
    optimizer = LevelingOptimizer(config)
    result = optimizer.run()
    
    if result:
        total_seconds, path = result
        print(f"Optimal Time: {format_time(total_seconds)}")
        print(f"{ 'Atk':<5} { 'Str':<5} { 'Action':<10} { 'Range':<8} { 'Time Elapsed':<15} {'Weapon'}")
        print("-" * 75)
        
        # Reconstruct path for pretty printing
        groups = []
        c_atk, c_str = 1, 1
        first_step_weapon = path[0][3] if path else "None"
        current_group = {
            'start_atk': c_atk, 'start_str': c_str, 
            'action': None, 'weapon': first_step_weapon, 
            'end_atk': c_atk, 'end_str': c_str, 
            'end_time': 0.0
        }
        
        for step in path:
            skill, lvl, time_comp, weapon_used = step
            action = f"Train {skill}"
            
            if current_group['action'] is None:
                current_group['action'] = action
                current_group['weapon'] = weapon_used
            
            change = (action != current_group['action']) or (weapon_used != current_group['weapon'])
            
            if change:
                groups.append(current_group)
                current_group = {
                    'start_atk': c_atk, 'start_str': c_str, 
                    'action': action, 'weapon': weapon_used, 
                    'end_atk': c_atk, 'end_str': c_str, 
                    'end_time': 0.0
                }
            
            if skill == 'Atk': c_atk = lvl
            else: c_str = lvl
            
            current_group['end_atk'] = c_atk
            current_group['end_str'] = c_str
            current_group['end_time'] = time_comp
            current_group['weapon'] = weapon_used
            
        groups.append(current_group)
        
        current_time = 0.0
        for g in groups:
            range_s = f"{g['start_atk']}->{g['end_atk']}" if "Atk" in g['action'] else f"{g['start_str']}->{g['end_str']}"
            print(f"{g['start_atk']:<5} {g['start_str']:<5} {g['action']:<10} {range_s:<8} {format_time(current_time):<15} {g['weapon']}")
            current_time = g['end_time']
            
        print(f"Goal Reached at {format_time(total_seconds)}")
    else:
        print("No solution found or timeout.")

if __name__ == "__main__":
    main()
