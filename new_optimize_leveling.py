import math
import heapq
import argparse
import time
from weapon_db import WEAPON_DB

# --- Constants & Data ---

def get_xp_for_level(level):
    total = 0
    for l in range(1, level):
        diff = math.floor(l + 300 * (2 ** (l / 7.0)))
        total += diff
    return math.floor(total / 4)

XP_TABLE = {l: get_xp_for_level(l) for l in range(1, 125)}

MONSTER_DEF_LVL = 1
MONSTER_DEF_BONUS = 0

def parse_time(time_str):
    if not time_str: return 0.0
    total_seconds = 0
    try: return float(time_str)
    except ValueError: pass
    multipliers = {'s': 1, 'm': 60, 'h': 3600}
    import re
    parts = re.findall(r'(\d+)([smh])', time_str)
    for val, unit in parts: total_seconds += int(val) * multipliers[unit]
    return float(total_seconds)

def calculate_max_hit(str_lvl, equip_str_bonus, style_bonus):
    effective_str = str_lvl + style_bonus + 8
    return math.floor(0.5 + (effective_str * (equip_str_bonus + 64)) / 640.0)

def calculate_hit_chance(atk_lvl, equip_atk_bonus, style_bonus):
    effective_atk = atk_lvl + style_bonus + 8
    atk_roll = effective_atk * (equip_atk_bonus + 64)
    eff_def = MONSTER_DEF_LVL + 9
    def_roll = eff_def * (MONSTER_DEF_BONUS + 64)
    if atk_roll > def_roll: return 1.0 - (def_roll + 2.0) / (2.0 * (atk_roll + 1.0))
    else: return atk_roll / (2.0 * (def_roll + 1.0))

def get_dps_raw(name, data, atk_lvl, str_lvl, style, amulet_stats):
    if "mace" in name:
        attack_bonus = data['bonus']['stab'] if style == 'accurate' else data['bonus']['crush']
    else:
        attack_bonus = max(data['bonus'].values())
    if style == 'accurate': 
        mh = calculate_max_hit(str_lvl, data['str'] + amulet_stats['str'], 0) 
        hc = calculate_hit_chance(atk_lvl, attack_bonus + amulet_stats['acc'], 3) 
    else: 
        mh = calculate_max_hit(str_lvl, data['str'] + amulet_stats['str'], 3) 
        hc = calculate_hit_chance(atk_lvl, attack_bonus + amulet_stats['acc'], 0) 
    return (0.5 * mh * hc) / data['speed']

def solve(allowed_weapons, costs_override, amulet_name, goal_lvl, timeout=300, lookahead=100):
    start_time_real = time.time()
    ammy_stats = {"str": 10 if amulet_name == "str" else (6 if amulet_name == "power" else 0), 
                  "acc": 6 if amulet_name == "power" else (4 if amulet_name == "accuracy" else 0)}

    allowed_data = {}
    for name, data in WEAPON_DB.items():
        if any(a.lower() in name.lower() for a in allowed_weapons):
            d = data.copy(); d['base_cost'] = costs_override.get(name, data['cost']); allowed_data[name] = d

    # 1. Pre-calculate DPS tables
    dps_table = {n: {'accurate': {}, 'aggressive': {}} for n in allowed_data}
    print("Pre-calculating DPS tables...")
    for n, data in allowed_data.items():
        for style in ['accurate', 'aggressive']:
            for a in range(1, 101):
                dps_table[n][style][a] = {}
                for s in range(1, 101):
                    dps_table[n][style][a][s] = get_dps_raw(n, data, a, s, style, ammy_stats)

    # 2. Pre-calculate A* Heuristic (h_table)
    # Admissible heuristic: Time to reach goal using the best weapon available in game (ignoring costs)
    print("Pre-calculating A* heuristic...")
    best_dps_at_level = {'accurate': {}, 'aggressive': {}}
    for style in ['accurate', 'aggressive']:
        for a in range(1, 101):
            best_dps_at_level[style][a] = {}
            for s in range(1, 101):
                best_dps = 0.0
                for n, data in allowed_data.items():
                    if a >= data['atk_req']:
                        best_dps = max(best_dps, dps_table[n][style][a][s])
                best_dps_at_level[style][a][s] = best_dps

    # Compute h_table[atk][str] using Dynamic Programming (backwards from Goal)
    # h(a, s) = min( h(a+1, s) + cost(a->a+1), h(a, s+1) + cost(s->s+1) )
    h_table = {}
    for a in range(goal_lvl, 0, -1):
        h_table[a] = {}
        for s in range(goal_lvl, 0, -1):
            if a == goal_lvl and s == goal_lvl:
                h_table[a][s] = 0.0
            else:
                opt_atk = float('inf')
                opt_str = float('inf')
                if a < goal_lvl:
                    d = best_dps_at_level['accurate'][a][s]
                    cost_step = (XP_TABLE[a+1] - XP_TABLE[a]) / (4.0 * d) if d > 0 else float('inf')
                    opt_atk = cost_step + h_table[a+1][s]
                if s < goal_lvl:
                    d = best_dps_at_level['aggressive'][a][s]
                    cost_step = (XP_TABLE[s+1] - XP_TABLE[s]) / (4.0 * d) if d > 0 else float('inf')
                    opt_str = cost_step + h_table[a][s+1]
                h_table[a][s] = min(opt_atk, opt_str)

    # 3. Pre-calculate Lookahead Window Scores (for candidate selection)
    window_table = {n: {'accurate': {}, 'aggressive': {}} for n in allowed_data}
    print("Pre-calculating Lookahead windows...")
    for n, data in allowed_data.items():
        for style in ['accurate', 'aggressive']:
            for a in range(1, 101):
                window_table[n][style][a] = {}
                for s in range(1, 101):
                    total_win_time = 0.0
                    for i in range(max(1, lookahead)):
                        ca, cs = (min(goal_lvl, a + i) if style == 'accurate' else a), (min(goal_lvl, s + i) if style == 'aggressive' else s)
                        cl = ca if style == 'accurate' else cs
                        if cl >= goal_lvl: break
                        d = dps_table[n][style][ca][cs]
                        if d <= 0: total_win_time = float('inf'); break
                        total_win_time += (XP_TABLE[cl+1] - XP_TABLE[cl]) / (4.0 * d)
                    window_table[n][style][a][s] = total_win_time

    avail_by_atk = {lvl: [n for n, d in allowed_data.items() if lvl >= d['atk_req']] for lvl in range(1, 101)}
    
    # PQ: (f_score, g_score, atk, str, owned_set, path)
    # f_score = g_score + h_score
    start_h = h_table[1][1]
    pq = [(start_h, 0.0, 1, 1, frozenset(), [])] 
    visited = {} 
    final_state = None

    print("Searching...")
    while pq:
        if time.time() - start_time_real > timeout:
            print(f"Timeout reached ({timeout}s)!"); return None
        f_score, curr_time, atk, stri, owned, path = heapq.heappop(pq)
        
        state_key = (atk, stri, owned)
        if state_key in visited and visited[state_key] <= curr_time: continue
        visited[state_key] = curr_time
        
        if atk == goal_lvl and stri == goal_lvl:
            final_state = (curr_time, path); break
            
        for skill_train in ['Atk', 'Str']:
            if (skill_train == 'Atk' and atk >= goal_lvl) or (skill_train == 'Str' and stri >= goal_lvl): continue
            style = 'accurate' if skill_train == 'Atk' else 'aggressive'
            
            best_owned, best_unowned = None, None
            for n in avail_by_atk[atk]:
                dps = dps_table[n][style][atk][stri]
                if dps <= 0: continue
                if n in owned:
                    if best_owned is None or dps > best_owned[0]: best_owned = (dps, n)
                else:
                    score = window_table[n][style][atk][stri] + allowed_data[n]['base_cost']
                    if best_unowned is None or score < best_unowned[0]: best_unowned = (score, n)
            
            cands = []
            if best_owned: cands.append(best_owned[1])
            if best_unowned: cands.append(best_unowned[1])
            
            for name in set(cands):
                dps = dps_table[name][style][atk][stri]
                cost = 0.0 if name in owned else allowed_data[name]['base_cost']
                next_lvl = (atk + 1) if skill_train == 'Atk' else (stri + 1)
                xp_needed = XP_TABLE[next_lvl] - XP_TABLE[atk if skill_train == 'Atk' else stri]
                
                new_g = curr_time + (xp_needed / (4.0 * dps)) + cost
                
                # Inline pruning for owned set
                raw_owned = set(owned); raw_owned.add(name)
                na, ns = (next_lvl if skill_train == 'Atk' else atk), (next_lvl if skill_train == 'Str' else stri)
                
                kept = set()
                b_atk_d, b_str_d = -1.0, -1.0
                b_atk_n, b_str_n = None, None
                for o_name in raw_owned:
                    d_a = dps_table[o_name]['accurate'][na][ns]
                    d_s = dps_table[o_name]['aggressive'][na][ns]
                    if d_a > b_atk_d: b_atk_d = d_a; b_atk_n = o_name
                    if d_s > b_str_d: b_str_d = d_s; b_str_n = o_name
                if b_atk_n: kept.add(b_atk_n)
                if b_str_n: kept.add(b_str_n)
                new_owned = frozenset(kept)
                
                new_h = h_table[na][ns]
                new_f = new_g + new_h
                
                new_key = (na, ns, new_owned)
                if new_key not in visited or new_g < visited[new_key]:
                    # Using g_score for visited check is standard for A*
                    heapq.heappush(pq, (new_f, new_g, na, ns, new_owned, path + [(skill_train, next_lvl, new_g, name)]))
    return final_state

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    return f"{h}h {m}m {s}s"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSRS F2P Melee Optimizer")
    parser.add_argument("--weapons", nargs='+', default=["scimitar"], help="List of allowed weapons")
    parser.add_argument("--costs", nargs='+', default=[], help="List of weapon costs")
    parser.add_argument("--amulet", choices=["none", "str", "power", "accuracy"], default="str", help="Amulet choice")
    parser.add_argument("--goal", type=int, default=40, help="Target level")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--lookahead", type=int, default=100, help="Levels to look ahead")
    args = parser.parse_args()
    costs_map = {item.split(':')[0].strip().lower(): parse_time(item.split(':')[1]) for item in args.costs if ':' in item}
    print(f"Optimizing for Goal: {args.goal}/{args.goal}, Weapons: {args.weapons}, Amulet: {args.amulet}, Lookahead: {args.lookahead}")
    result = solve(args.weapons, costs_map, args.amulet, args.goal, args.timeout, args.lookahead)
    if result:
        total_seconds, path = result
        print(f"Optimal Time: {format_time(total_seconds)}")
        print(f"{'Atk':<5} {'Str':<5} {'Action':<10} {'Range':<8} {'Time Elapsed':<15} {'Weapon'}")
        print("-" * 75)
        groups = []; c_atk, c_str = 1, 1
        first_step_weapon = path[0][3] if path else "None"
        current_group = {'start_atk': c_atk, 'start_str': c_str, 'action': None, 'weapon': first_step_weapon, 'end_atk': c_atk, 'end_str': c_str, 'end_time': 0.0}
        for step in path:
            skill, lvl, time_comp, weapon_used = step
            action = f"Train {skill}"
            if current_group['action'] is None: current_group['action'] = action; current_group['weapon'] = weapon_used
            if (action != current_group['action']) or (weapon_used != current_group['weapon']):
                groups.append(current_group)
                current_group = {'start_atk': c_atk, 'start_str': c_str, 'action': action, 'weapon': weapon_used, 'end_atk': c_atk, 'end_str': c_str, 'end_time': 0.0}
            if skill == 'Atk': c_atk = lvl
            else: c_str = lvl
            current_group['end_atk'] = c_atk; current_group['end_str'] = c_str; current_group['end_time'] = time_comp; current_group['weapon'] = weapon_used
        groups.append(current_group)
        current_time = 0.0
        for g in groups:
            range_s = f"{g['start_atk']}->{g['end_atk']}" if "Atk" in g['action'] else f"{g['start_str']}->{g['end_str']}"
            print(f"{g['start_atk']:<5} {g['start_str']:<5} {g['action']:<10} {range_s:<8} {format_time(current_time):<15} {g['weapon']}")
            current_time = g['end_time']
        print(f"Goal Reached at {format_time(total_seconds)}")
    else: print("No solution found or timeout.")