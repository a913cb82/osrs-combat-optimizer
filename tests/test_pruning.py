import unittest
from new_optimize_leveling import prune_owned_weapons

# Mock Data
MOCK_DATA = {
    "iron scimitar": {"bonus": {"stab": 2, "slash": 10, "crush": -2, "stab": 2}, "max_bonus": 10, "str": 9, "speed": 2.4, "base_cost": 30.0},
    "rune scimitar": {"bonus": {"stab": 7, "slash": 45, "crush": -2, "stab": 7}, "max_bonus": 45, "str": 44, "speed": 2.4, "base_cost": 30.0},
    "rune sword":    {"bonus": {"stab": 38, "slash": 26, "crush": -2, "stab": 38}, "max_bonus": 38, "str": 39, "speed": 2.4, "base_cost": 30.0},
    "rune mace":     {"bonus": {"stab": 20, "slash": -2, "crush": 39, "stab": 20}, "max_bonus": 39, "str": 36, "speed": 2.4, "base_cost": 30.0},
}

class TestPruning(unittest.TestCase):
    def test_prune_dominated_weapons(self):
        # Scenario: Own Iron Scimitar and Rune Scimitar.
        # Rune Scimitar dominates Iron Scimitar in all stats.
        owned = {"iron scimitar", "rune scimitar"}
        atk_lvl = 40
        str_lvl = 40
        ammy = {"str": 0, "acc": 0}
        
        pruned = prune_owned_weapons(owned, atk_lvl, str_lvl, ammy, MOCK_DATA)
        self.assertIn("rune scimitar", pruned)
        self.assertNotIn("iron scimitar", pruned)
        self.assertEqual(len(pruned), 1)

    def test_prune_mixed_dominance(self):
        # Scenario: Own Rune Sword and Rune Mace.
        owned = {"rune sword", "rune mace"}
        atk_lvl = 40
        str_lvl = 40
        ammy = {"str": 0, "acc": 0}
        
        pruned = prune_owned_weapons(owned, atk_lvl, str_lvl, ammy, MOCK_DATA)
        self.assertIn("rune sword", pruned)
        self.assertIn("rune mace", pruned)
        self.assertEqual(len(pruned), 2)
        
    def test_prune_equal_stats(self):
        pass

if __name__ == '__main__':
    unittest.main()
