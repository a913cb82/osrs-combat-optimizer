import unittest
from unittest.mock import patch
import optimize_melee

# Mock Data
MOCK_AMMY_DB = {
    "str":      {"str": 10, "acc": 0, "cost": 30.0},
    "power":    {"str": 6,  "acc": 6, "cost": 30.0},
    "none":     {"str": 0,  "acc": 0, "cost": 0.0},
}

MOCK_WEAPON_DB = {
    "rune sword": {"atk_req": 40, "str": 39, "speed": 2.4, "cost": 30.0, "bonus": {"stab": 38, "slash": 26, "crush": -2}},
    "rune mace":  {"atk_req": 40, "str": 36, "speed": 2.4, "cost": 30.0, "bonus": {"stab": 20, "slash": -2, "crush": 39}},
}

class TestSharedCosts(unittest.TestCase):
    
    def test_simple_shared_cost(self):
        """
        Verify that buying one item in a shared group makes the other cheaper.
        Scenario: Rune Sword & Mace share a 5h unlock cost.
        """
        # Build Graph
        graph = optimize_melee.ReqGraph()
        graph.add_node("guild", 18000.0)
        graph.add_node("rune sword", 0.0, ["guild"])
        graph.add_node("rune mace", 0.0, ["guild"])
        
        with patch('optimize_melee.AMULETS_DB', {"none": MOCK_AMMY_DB["none"]}), \
             patch('optimize_melee.WEAPON_DB', MOCK_WEAPON_DB):
            
            result = optimize_melee.solve(
                req_graph=graph,
                goal_atk=41, goal_str=41,
                start_atk=40, start_str=40,
                timeout=5, lookahead=5
            )
            
            self.assertIsNotNone(result)
            total_time, path = result
            self.assertGreater(total_time, 18000)

    def test_nested_shared_costs(self):
        """
        Verify additive shared costs (e.g. Str Ammy -> Power Ammy).
        """
        graph = optimize_melee.ReqGraph()
        graph.add_node("crafting_50", 1000.0)
        graph.add_node("str", 0.0, ["crafting_50"])
        
        graph.add_node("crafting_70", 2000.0, ["crafting_50"])
        graph.add_node("power", 0.0, ["crafting_70"])
        
        mock_ammys = {
            "str":   {"str": 10, "acc": 0, "cost": 30.0},
            "power": {"str": 100, "acc": 100, "cost": 30.0}, 
            "none":  {"str": 0,  "acc": 0, "cost": 0.0}
        }
        
        with patch('optimize_melee.AMULETS_DB', mock_ammys), \
             patch('optimize_melee.WEAPON_DB', MOCK_WEAPON_DB):
            
            result = optimize_melee.solve(
                req_graph=graph,
                goal_atk=50, goal_str=50,
                start_atk=40, start_str=40,
                timeout=5, lookahead=5
            )
            
            total_time, path = result
            
            used_power = False
            for step in path:
                if 'power' in step[4]:
                    used_power = True
                    break
            
            self.assertGreater(total_time, 1000, "Should pay at least base cost")
            self.assertLess(total_time, 20000)

    def test_independent_costs(self):
        """
        Verify that unrelated items do not share costs.
        """
        graph = optimize_melee.ReqGraph()
        graph.add_node("cost_a", 5000.0)
        graph.add_node("cost_b", 5000.0)
        graph.add_node("rune sword", 0.0, ["cost_a"])
        graph.add_node("rune mace", 0.0, ["cost_b"])
        
        with patch('optimize_melee.AMULETS_DB', {"none": MOCK_AMMY_DB["none"]}), \
             patch('optimize_melee.WEAPON_DB', MOCK_WEAPON_DB):
            
            result = optimize_melee.solve(
                req_graph=graph,
                goal_atk=41, goal_str=41,
                start_atk=40, start_str=40,
                timeout=5, lookahead=5
            )
            
            total_time, path = result
            self.assertGreater(total_time, 5000)

if __name__ == '__main__':
    unittest.main()