import math
import heapq
import argparse
import time
from data import WEAPON_DB

# --- Constants & Data ---

AMULETS_DB = {
    "str":      {"str": 10, "acc": 0, "cost": 30.0},
    "power":    {"str": 6,  "acc": 6, "cost": 30.0},
    "accuracy": {"str": 0,  "acc": 4, "cost": 30.0},
    "none":     {"str": 0,  "acc": 0, "cost": 0.0},
}

def get_xp_for_level(level):
    total = 0
    for l in range(1, level):
        diff = math.floor(l + 300 * (2 ** (l / 7.0)))
        total += diff
    return math.floor(total / 4)

XP_TABLE = {l: get_xp_for_level(l) for l in range(1, 125)}

XP_PER_DAMAGE = 4.0

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

def solve(costs_override, shared_costs_map, goal_lvl, start_atk=1, start_str=1, timeout=300, lookahead=100):
    start_time_real = time.time()
    
    # Process Shared Costs
    # shared_costs_map: {'group_id': cost}
    # item_groups: {'item_name': 'group_id'}
    item_groups = {}
    group_costs = {}
    
    # Parse the input map (which is group_id -> (items, cost)) from args?
    # No, args are parsed before. We expect shared_costs_map structure:
    # We need to map Items to Groups.
    # The helper `parse_shared_costs` below handles this structure.
    # Input `shared_costs_map` here is just the raw dict from args?
    # Let's clarify the signature. `shared_costs_map` is {group_key: cost}.
    # We need a separate map for items.
    
    # Actually, let's process the raw args inside main and pass clean structures here.
    # Let's assume `item_groups` (item->group_id) and `group_costs` (group_id->cost) are passed or processed.
    # To keep signature clean, let's parse inside solve or main.
    # I'll update main to parse.
    pass 

    # Re-structure for solve:
    # args.shared_costs is list of strings "item,item:cost"
    # We parse this into:
    # item_to_group: {"rune sword": 0, "rune mace": 0}
    # group_costs: {0: 18000.0}
    
    item_to_group = {}
    group_costs_dict = {}
    
    # Use the passed map which we will assume is {frozenset(items): cost}
    # Actually, simpler to pass the raw list and parse here?
    # No, cleaner to pass parsed data.
    # Let's modify solve signature:
    # solve(..., item_to_group, group_costs, ...)
    
    # Placeholder for the updated signature logic down below
    
    active_ammys = {}
    for name, data in AMULETS_DB.items():
        d = data.copy()
        d['base_cost'] = costs_override.get(name, data['cost'])
        active_ammys[name] = d
    if not active_ammys:
        active_ammys = {"none": {"str": 0, "acc": 0, "base_cost": 0.0}}

    allowed_data = {}
    for name, data in WEAPON_DB.items():
        d = data.copy(); d['base_cost'] = costs_override.get(name, data['cost']); allowed_data[name] = d

    print("Pre-calculating tables...")
    combos = []
    for w_name in allowed_data:
        for a_name in active_ammys:
            combos.append((w_name, a_name))
            
    dps_cache = {c: {'accurate': {}, 'aggressive': {}} for c in combos}
    prefix_time = {c: {'accurate': {}, 'aggressive': {}} for c in combos}
    
    for w_name, a_name in combos:
        w_data = allowed_data[w_name]
        a_data = active_ammys[a_name]
        for style in ['accurate', 'aggressive']:
            grid = {}
            if style == 'accurate':
                for s in range(1, 101):
                    cum = 0.0
                    grid[s] = [0.0] * 102
                    for a in range(1, 101):
                        if a not in dps_cache[(w_name, a_name)][style]:
                            dps_cache[(w_name, a_name)][style][a] = {}
                        d = get_dps_raw(w_name, w_data, a, s, style, a_data)
                        dps_cache[(w_name, a_name)][style][a][s] = d
                        step_time = float('inf')
                        if d > 0: step_time = (XP_TABLE[a+1] - XP_TABLE[a]) / XP_PER_DAMAGE / d
                        cum += step_time
                        grid[s][a+1] = cum
                prefix_time[(w_name, a_name)]['accurate'] = grid
            else:
                for a in range(1, 101):
                    cum = 0.0
                    grid[a] = [0.0] * 102
                    if a not in dps_cache[(w_name, a_name)][style]:
                        dps_cache[(w_name, a_name)][style][a] = {}
                    for s in range(1, 101):
                        d = get_dps_raw(w_name, w_data, a, s, style, a_data)
                        dps_cache[(w_name, a_name)][style][a][s] = d
                        step_time = float('inf')
                        if d > 0: step_time = (XP_TABLE[s+1] - XP_TABLE[s]) / XP_PER_DAMAGE / d
                        cum += step_time
                        grid[a][s+1] = cum
                prefix_time[(w_name, a_name)]['aggressive'] = grid

    best_dps_at_level = {'accurate': {}, 'aggressive': {}}
    for style in ['accurate', 'aggressive']:
        for a in range(1, 101):
            best_dps_at_level[style][a] = {}
            for s in range(1, 101):
                best_val = 0.0
                for c in combos:
                    d = dps_cache[c][style][a][s]
                    if d > best_val: best_val = d
                best_dps_at_level[style][a][s] = best_val

    h_table = {}
    for a in range(goal_lvl, 0, -1):
        h_table[a] = {}
        for s in range(goal_lvl, 0, -1):
            if a == goal_lvl and s == goal_lvl:
                h_table[a][s] = 0.0
            else:
                opt_atk, opt_str = float('inf'), float('inf')
                if a < goal_lvl:
                    d = best_dps_at_level['accurate'][a][s]
                    cost_step = (XP_TABLE[a+1] - XP_TABLE[a]) / XP_PER_DAMAGE / d if d > 0 else float('inf')
                    opt_atk = cost_step + h_table[a+1][s]
                if s < goal_lvl:
                    d = best_dps_at_level['aggressive'][a][s]
                    cost_step = (XP_TABLE[s+1] - XP_TABLE[s]) / XP_PER_DAMAGE / d if d > 0 else float('inf')
                    opt_str = cost_step + h_table[a][s+1]
                h_table[a][s] = min(opt_atk, opt_str)

    def get_window_score_fast(w_name, a_name, style, atk, stri):
        limit = max(1, lookahead)
        if style == 'accurate':
            end_lvl = min(goal_lvl, atk + limit)
            p_arr = prefix_time[(w_name, a_name)]['accurate'][stri]
            return p_arr[end_lvl] - p_arr[atk]
        else:
            end_lvl = min(goal_lvl, stri + limit)
            p_arr = prefix_time[(w_name, a_name)]['aggressive'][atk]
            return p_arr[end_lvl] - p_arr[stri]

    avail_by_atk = {}
    for lvl in range(1, 101):
        raw_avail = [n for n, d in allowed_data.items() if lvl >= d['atk_req']]
        cands = []
        for name in raw_avail:
            max_d = 0.0
            for a_name in active_ammys:
                d1 = dps_cache[(name, a_name)]['accurate'][lvl][lvl]
                d2 = dps_cache[(name, a_name)]['aggressive'][lvl][lvl]
                max_d = max(max_d, d1, d2)
            cands.append((max_d, allowed_data[name]['base_cost'], name))
        cands.sort(key=lambda x: x[0], reverse=True)
        keep = []
        min_cost = float('inf')
        for d, c, n in cands:
            if c < min_cost:
                keep.append(n)
                min_cost = c
        avail_by_atk[lvl] = keep

    start_h = h_table[start_atk][start_str]
    start_ammys = set()
    if 'none' in active_ammys: start_ammys.add('none')
    
    # State: (atk, str, owned_w, owned_a, unlocked_groups)
    pq = [(start_h, 0.0, start_atk, start_str, frozenset(), frozenset(start_ammys), frozenset(), [])] 
    visited = {} 
    final_state = None

    print(f"Searching from {start_atk}/{start_str} to {goal_lvl}/{goal_lvl}...")
    while pq:
        if time.time() - start_time_real > timeout:
            print(f"Timeout reached ({timeout}s)!"); return None
        f, curr_time, atk, stri, owned_w, owned_a, unlocked_g, path = heapq.heappop(pq)
        
        state_key = (atk, stri, owned_w, owned_a, unlocked_g)
        if state_key in visited and visited[state_key] <= curr_time: continue
        visited[state_key] = curr_time
        if atk == goal_lvl and stri == goal_lvl:
            final_state = (curr_time, path); break
            
        for skill_train in ['Atk', 'Str']:
            if (skill_train == 'Atk' and atk >= goal_lvl) or (skill_train == 'Str' and stri >= goal_lvl): continue
            style = 'accurate' if skill_train == 'Atk' else 'aggressive'
            
            candidates = []
            
            for w_name in avail_by_atk[atk]:
                # Calculate Weapon Cost (Base + Shared)
                w_cost = 0.0
                pending_group = None
                
                if w_name not in owned_w:
                    w_cost = allowed_data[w_name]['base_cost']
                    # Add shared cost if applicable
                    grp = shared_costs_map.get(w_name)
                    if grp and grp['id'] not in unlocked_g:
                        w_cost += grp['cost']
                        pending_group = grp['id']
                
                for a_name in active_ammys:
                    a_cost = 0.0 if a_name in owned_a else active_ammys[a_name]['base_cost']
                    score = get_window_score_fast(w_name, a_name, style, atk, stri) + w_cost + a_cost
                    candidates.append((score, w_name, a_name, w_cost, a_cost, pending_group))
            
            candidates.sort(key=lambda x: x[0])
            selected = []
            if candidates: selected.append(candidates[0])
            
            for c in candidates:
                if len(selected) >= 2: break
                if c[3] == 0 and c[4] == 0 and c not in selected: selected.append(c)
            
            for score, w_name, a_name, w_cost, a_cost, pending_grp in selected:
                dps = dps_cache[(w_name, a_name)][style][atk][stri]
                if dps <= 0: continue
                
                next_lvl = (atk + 1) if skill_train == 'Atk' else (stri + 1)
                curr_xp_lvl = atk if skill_train == 'Atk' else stri
                xp_needed = XP_TABLE[next_lvl] - XP_TABLE[curr_xp_lvl]
                
                train_time = (xp_needed / XP_PER_DAMAGE) / dps
                new_g = curr_time + train_time + w_cost + a_cost
                
                new_raw_w = set(owned_w); new_raw_w.add(w_name)
                new_raw_a = set(owned_a); new_raw_a.add(a_name)
                new_owned_w = frozenset(new_raw_w)
                new_owned_a = frozenset(new_raw_a)
                
                # Update unlocked groups
                new_unlocked_g = unlocked_g
                if pending_grp is not None:
                    raw_g = set(unlocked_g)
                    raw_g.add(pending_grp)
                    new_unlocked_g = frozenset(raw_g)
                
                na, ns = (next_lvl if skill_train == 'Atk' else atk), (next_lvl if skill_train == 'Str' else stri)
                new_h = h_table[na][ns]
                new_f = new_g + new_h
                
                new_key = (na, ns, new_owned_w, new_owned_a, new_unlocked_g)
                if new_key not in visited or new_g < visited[new_key]:
                    heapq.heappush(pq, (new_f, new_g, na, ns, new_owned_w, new_owned_a, new_unlocked_g,
                                        path + [(skill_train, next_lvl, new_g, w_name, a_name)]))
    return final_state

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    return f"{h}h {m}m {s}s"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSRS F2P Melee Optimizer")
    parser.add_argument("--costs", nargs='+', default=[], help="List of costs (weapon:time or ammy:time)")
    parser.add_argument("--shared_costs", nargs='+', default=[], help="Shared costs (item1,item2:time)")
    parser.add_argument("--goal", type=int, default=40, help="Target level")
    parser.add_argument("--start_atk", type=int, default=1, help="Starting Attack level")
    parser.add_argument("--start_str", type=int, default=1, help="Starting Strength level")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--lookahead", type=int, default=100, help="Levels to look ahead")
    args = parser.parse_args()
    
    costs_map = {item.split(':')[0].strip().lower(): parse_time(item.split(':')[1]) for item in args.costs if ':' in item}
    
    # Parse Shared Costs
    # Structure: {'rune sword': {'id': 0, 'cost': 18000}, 'rune mace': {'id': 0, 'cost': 18000}}
    shared_map = {}
    for i, item in enumerate(args.shared_costs):
        if ':' in item:
            names_str, time_str = item.split(':')
            cost = parse_time(time_str)
            names = [n.strip().lower() for n in names_str.split(',')]
            for n in names:
                shared_map[n] = {'id': i, 'cost': cost}

    print(f"Optimizing for Goal: {args.goal}/{args.goal}, Start: {args.start_atk}/{args.start_str}, Lookahead: {args.lookahead}")
    result = solve(costs_map, shared_map, args.goal, args.start_atk, args.start_str, args.timeout, args.lookahead)
    
    if result:
        total_seconds, path = result
        print(f"Optimal Time: {format_time(total_seconds)}")
        print(f"{'Atk':<5} {'Str':<5} {'Action':<10} {'Range':<8} {'Time Elapsed':<15} {'Weapon (Ammy)'}")
        print("-" * 75)
        groups = []
        c_atk, c_str = args.start_atk, args.start_str
        
        first_w, first_a = (path[0][3], path[0][4]) if path else ("None", "None")
        current_group = {'start_atk': c_atk, 'start_str': c_str, 'action': None, 'weapon': first_w, 'ammy': first_a, 'end_atk': c_atk, 'end_str': c_str, 'end_time': 0.0}
        for step in path:
            skill, lvl, time_comp, weapon_used, ammy_used = step
            action = f"Train {skill}"
            if current_group['action'] is None: 
                current_group['action'] = action; current_group['weapon'] = weapon_used; current_group['ammy'] = ammy_used
            
            if (action != current_group['action']) or (weapon_used != current_group['weapon']) or (ammy_used != current_group['ammy']):
                groups.append(current_group)
                current_group = {'start_atk': c_atk, 'start_str': c_str, 'action': action, 'weapon': weapon_used, 'ammy': ammy_used, 'end_atk': c_atk, 'end_str': c_str, 'end_time': 0.0}
            if skill == 'Atk': c_atk = lvl
            else: c_str = lvl
            current_group['end_atk'] = c_atk; current_group['end_str'] = c_str; current_group['end_time'] = time_comp; current_group['weapon'] = weapon_used; current_group['ammy'] = ammy_used
        groups.append(current_group)
        current_time = 0.0
        for g in groups:
            range_s = f"{g['start_atk']}->{g['end_atk']}" if "Atk" in g['action'] else f"{g['start_str']}->{g['end_str']}"
            w_display = f"{g['weapon']} ({g['ammy']})"
            print(f"{g['start_atk']:<5} {g['start_str']:<5} {g['action']:<10} {range_s:<8} {format_time(current_time):<15} {w_display}")
            current_time = g['end_time']
        print(f"Goal Reached at {format_time(total_seconds)}")
    else: print("No solution found or timeout.")
