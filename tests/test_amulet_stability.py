import unittest
from unittest.mock import patch
import optimize_melee

# Mock Constants
MOCK_AMMY_DB = {
    "str":      {"str": 10, "acc": 0, "cost": 30.0},
    "none":     {"str": 0,  "acc": 0, "cost": 0.0},
}

MOCK_WEAPON_DB = {
    "iron scimitar": {
        "atk_req": 1, 
        "bonus": {"stab": 2, "slash": 10, "crush": -2}, 
        "str": 9, 
        "speed": 2.4, 
        "cost": 0.0
    }
}

class TestAmuletStability(unittest.TestCase):
    def test_stability_str_vs_none(self):
        """
        Reproduce the issue where optimizer switches from 'str' to 'none' 
        despite 'str' being owned and better.
        """
        # Patch data
        with patch('optimize_melee.AMULETS_DB', MOCK_AMMY_DB), \
             patch('optimize_melee.WEAPON_DB', MOCK_WEAPON_DB):
            
            # Start at Atk 1, Str 3.
            # Goal: Atk 1, Str 4.
            # Scenario: We own 'str' ammy (simulated by passing costs_override=0 for str? 
            # No, we simulate the step where it decides).
            
            # We run solve for a short range (1/1 to 1/5)
            # We expect it to buy 'str' (cost 30s) if it helps enough?
            # Or assume we override cost to 0 (already owned).
            
            costs = {"str": 0.0, "none": 0.0} # Simulate owned
            
            # Run solve
            result = optimize_melee.solve(
                costs_override=costs,
                shared_costs_map={},
                goal_lvl=5,
                start_atk=1,
                start_str=1,
                timeout=5,
                lookahead=100
            )
            
            if not result:
                self.fail("Solver failed")
                
            time, path = result
            
            # Check path for any usage of "none"
            # Format: (skill, lvl, time, weapon, ammy)
            for step in path:
                ammy = step[4]
                print(f"Step {step[0]}->{step[1]}: Ammy {ammy}")
                self.assertNotEqual(ammy, "none", f"Optimizer switched to 'none' at step {step}")

if __name__ == '__main__':
    unittest.main()
