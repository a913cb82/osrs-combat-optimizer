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

AMULET_PRIORITY = {
    "str": 3,
    "power": 2,
    "accuracy": 1,
    "none": 0
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

# --- Requirement Graph Logic ---

class ReqGraph:
    def __init__(self):
        self.nodes = {}
        
    def add_node(self, name, cost, parents=None):
        self.nodes[name] = {'cost': cost, 'parents': parents or []}
        
    def get_unlock_cost(self, item_name, unlocked_set):
        if item_name in unlocked_set:
            return 0.0, []
        
        # If item is not in graph, it has 0 dependency cost
        if item_name not in self.nodes:
            return 0.0, []
            
        cost = 0.0
        to_unlock = set()
        queue = [item_name]
        visited = set()
        
        while queue:
            curr = queue.pop(0)
            if curr in visited: continue
            visited.add(curr)
            
            if curr not in unlocked_set:
                to_unlock.add(curr)
                node_data = self.nodes.get(curr)
                if node_data:
                    cost += node_data['cost']
                    for p in node_data['parents']:
                        queue.append(p)
                        
        return cost, sorted(list(to_unlock))

def solve(req_graph, goal_atk, goal_str, start_atk=1, start_str=1, timeout=300, lookahead=100):
    start_time_real = time.time()
    
    # We use base costs from DB (usually 30s)
    # Additional costs come from req_graph
    
    active_ammys = {}
    for name, data in AMULETS_DB.items():
        d = data.copy()
        d['base_cost'] = data['cost'] 
        active_ammys[name] = d
    if not active_ammys:
        active_ammys = {"none": {"str": 0, "acc": 0, "base_cost": 0.0}}

    allowed_data = {}
    for name, data in WEAPON_DB.items():
        d = data.copy(); d['base_cost'] = data['cost']; allowed_data[name] = d

    print("Pre-calculating tables...")
    combos = []
    for w_name in allowed_data:
        for a_name in active_ammys:
            combos.append((w_name, a_name))
            
    dps_cache = {c: {'accurate': {}, 'aggressive': {}} for c in combos}
    prefix_time = {c: {'accurate': {}, 'aggressive': {}} for c in combos}
    
    max_table_lvl = 100
    
    for w_name, a_name in combos:
        w_data = allowed_data[w_name]
        a_data = active_ammys[a_name]
        for style in ['accurate', 'aggressive']:
            grid = {}
            if style == 'accurate':
                for s in range(1, max_table_lvl + 1):
                    cum = 0.0
                    grid[s] = [0.0] * (max_table_lvl + 2)
                    for a in range(1, max_table_lvl + 1):
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
                for a in range(1, max_table_lvl + 1):
                    cum = 0.0
                    grid[a] = [0.0] * (max_table_lvl + 2)
                    if a not in dps_cache[(w_name, a_name)][style]:
                        dps_cache[(w_name, a_name)][style][a] = {}
                    for s in range(1, max_table_lvl + 1):
                        d = get_dps_raw(w_name, w_data, a, s, style, a_data)
                        dps_cache[(w_name, a_name)][style][a][s] = d
                        step_time = float('inf')
                        if d > 0: step_time = (XP_TABLE[s+1] - XP_TABLE[s]) / XP_PER_DAMAGE / d
                        cum += step_time
                        grid[a][s+1] = cum
                prefix_time[(w_name, a_name)]['aggressive'] = grid

    best_dps_at_level = {'accurate': {}, 'aggressive': {}}
    for style in ['accurate', 'aggressive']:
        for a in range(1, max_table_lvl + 1):
            best_dps_at_level[style][a] = {}
            for s in range(1, max_table_lvl + 1):
                best_val = 0.0
                for c in combos:
                    d = dps_cache[c][style][a][s]
                    if d > best_val: best_val = d
                best_dps_at_level[style][a][s] = best_val

    h_table = {}
    for a in range(goal_atk, 0, -1):
        h_table[a] = {}
        for s in range(goal_str, 0, -1):
            if a == goal_atk and s == goal_str:
                h_table[a][s] = 0.0
            else:
                opt_atk, opt_str = float('inf'), float('inf')
                if a < goal_atk:
                    d = best_dps_at_level['accurate'][a][s]
                    cost_step = (XP_TABLE[a+1] - XP_TABLE[a]) / XP_PER_DAMAGE / d if d > 0 else float('inf')
                    opt_atk = cost_step + h_table.get(a+1, {}).get(s, float('inf'))
                if s < goal_str:
                    d = best_dps_at_level['aggressive'][a][s]
                    cost_step = (XP_TABLE[s+1] - XP_TABLE[s]) / XP_PER_DAMAGE / d if d > 0 else float('inf')
                    opt_str = cost_step + h_table.get(a, {}).get(s+1, float('inf'))
                h_table[a][s] = min(opt_atk, opt_str)

    def get_window_score_fast(w_name, a_name, style, atk, stri):
        limit = max(1, lookahead)
        if style == 'accurate':
            end_lvl = min(goal_atk, atk + limit)
            p_arr = prefix_time[(w_name, a_name)]['accurate'][stri]
            return p_arr[end_lvl] - p_arr[atk]
        else:
            end_lvl = min(goal_str, stri + limit)
            p_arr = prefix_time[(w_name, a_name)]['aggressive'][atk]
            return p_arr[end_lvl] - p_arr[stri]

    avail_by_atk = {}
    for lvl in range(1, max_table_lvl + 1):
        raw_avail = [n for n, d in allowed_data.items() if lvl >= d['atk_req']]
        cands = []
        for name in raw_avail:
            max_d = 0.0
            for a_name in active_ammys:
                d1 = dps_cache[(name, a_name)]['accurate'][lvl][lvl]
                d2 = dps_cache[(name, a_name)]['aggressive'][lvl][lvl]
                max_d = max(max_d, d1, d2)
            
            # Use FULL cost (Base + Graph) for pruning to avoid dropping items 
            # that are cheap but have lower DPS than an expensive item.
            graph_cost, _ = req_graph.get_unlock_cost(name, frozenset())
            total_est_cost = allowed_data[name]['base_cost'] + graph_cost
            
            cands.append((max_d, total_est_cost, name))
        
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
    
    # State: (f, g, atk, str, owned_w, owned_a, tie_break, unlocked_groups, path)
    pq = [(start_h, 0.0, start_atk, start_str, frozenset(), frozenset(start_ammys), 0, frozenset(), [])] 
    visited = {} 
    final_state = None

    print(f"Searching from {start_atk}/{start_str} to {goal_atk}/{goal_str}...")
    while pq:
        if time.time() - start_time_real > timeout:
            print(f"Timeout reached ({timeout}s)!"); return None
        f, curr_time, atk, stri, owned_w, owned_a, _, unlocked_g, path = heapq.heappop(pq)
        
        state_key = (atk, stri, owned_w, owned_a, unlocked_g)
        if state_key in visited and visited[state_key] <= curr_time: continue
        visited[state_key] = curr_time
        if atk == goal_atk and stri == goal_str:
            final_state = (curr_time, path); break
            
        for skill_train in ['Atk', 'Str']:
            if (skill_train == 'Atk' and atk >= goal_atk) or (skill_train == 'Str' and stri >= goal_str): continue
            style = 'accurate' if skill_train == 'Atk' else 'aggressive'
            
            candidates = []
            
            for w_name in avail_by_atk[atk]:
                w_cost = 0.0
                pending_w_nodes = []
                
                if w_name not in owned_w:
                    w_cost = allowed_data[w_name]['base_cost']
                    req_cost, req_nodes = req_graph.get_unlock_cost(w_name, unlocked_g)
                    w_cost += req_cost
                    pending_w_nodes = req_nodes
                
                for a_name in active_ammys:
                    a_cost = 0.0
                    pending_a_nodes = []
                    
                    if a_name not in owned_a:
                        a_cost = active_ammys[a_name]['base_cost']
                        
                        eff_unlocked = set(unlocked_g)
                        eff_unlocked.update(pending_w_nodes)
                        
                        a_req_cost, a_req_nodes = req_graph.get_unlock_cost(a_name, eff_unlocked)
                        a_cost += a_req_cost
                        pending_a_nodes = a_req_nodes

                    score = get_window_score_fast(w_name, a_name, style, atk, stri) + w_cost + a_cost
                    curr_dps = dps_cache[(w_name, a_name)][style][atk][stri]
                    
                    prio = AMULET_PRIORITY.get(a_name, 0)
                    combined_pending = tuple(sorted(list(set(pending_w_nodes + pending_a_nodes))))
                    
                    candidates.append((score, -curr_dps, -prio, w_name, a_name, w_cost, a_cost, combined_pending))
            
            candidates.sort(key=lambda x: (round(x[0], 4), x[1], x[2]))
            selected = []
            if candidates: selected.append(candidates[0])
            
            for c in candidates:
                if len(selected) >= 2: break
                if c[5] == 0 and c[6] == 0 and c not in selected: selected.append(c)
            
            for score, neg_dps, neg_prio, w_name, a_name, w_cost, a_cost, pending_grps_tuple in selected:
                dps = -neg_dps
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
                
                new_unlocked_g = unlocked_g
                if pending_grps_tuple:
                    raw_g = set(unlocked_g)
                    raw_g.update(pending_grps_tuple)
                    new_unlocked_g = frozenset(raw_g)
                
                na, ns = (next_lvl if skill_train == 'Atk' else atk), (next_lvl if skill_train == 'Str' else stri)
                new_h = h_table[na][ns]
                new_f = new_g + new_h
                
                # Tie-breaker: Prefer higher priority items to avoid 'none' winning via string comparison
                tie_break_prio = -(AMULET_PRIORITY.get(a_name, 0))
                
                new_key = (na, ns, new_owned_w, new_owned_a, new_unlocked_g)
                if new_key not in visited or new_g < visited[new_key]:
                    heapq.heappush(pq, (new_f, new_g, na, ns, new_owned_w, new_owned_a, tie_break_prio, new_unlocked_g,
                                        path + [(skill_train, next_lvl, new_g, w_name, a_name)]))
    return final_state

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    return f"{h}h {m}m {s}s"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSRS F2P Melee Optimizer")
    parser.add_argument("--reqs", nargs='+', default=[], help="Dependency graph (node:cost:parent)")
    
    # Goals
    parser.add_argument("--goal", type=int, default=40, help="Default goal for both skills")
    parser.add_argument("--goal_atk", type=int, help="Target Attack level")
    parser.add_argument("--goal_str", type=int, help="Target Strength level")
    
    parser.add_argument("--start_atk", type=int, default=1, help="Starting Attack level")
    parser.add_argument("--start_str", type=int, default=1, help="Starting Strength level")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--lookahead", type=int, default=100, help="Levels to look ahead")
    args = parser.parse_args()
    
    # Build Graph
    graph = ReqGraph()
    for item in args.reqs:
        parts = item.split(':')
        name = parts[0].strip().lower()
        cost = parse_time(parts[1])
        parents = []
        if len(parts) > 2 and parts[2].strip():
            parents = [p.strip().lower() for p in parts[2].split(',')]
        graph.add_node(name, cost, parents)

    # Resolve Goals
    g_atk = args.goal_atk if args.goal_atk else args.goal
    g_str = args.goal_str if args.goal_str else args.goal

    print(f"Optimizing for Goal: {g_atk}/{g_str}, Start: {args.start_atk}/{args.start_str}, Lookahead: {args.lookahead}")
    result = solve(graph, g_atk, g_str, args.start_atk, args.start_str, args.timeout, args.lookahead)
    
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
