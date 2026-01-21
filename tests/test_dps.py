import unittest
from new_optimize_leveling import get_best_dps

class TestDPS(unittest.TestCase):
    def test_best_dps_selection(self):
        # Scenario: Level 40/40. 
        # Allowed: Bronze Scimitar, Rune Scimitar.
        # Expected: Rune Scimitar selected.
        
        atk = 40
        str_lvl = 40
        allowed = ["bronze scimitar", "rune scimitar"]
        excluded = []
        ammy = {"str": 0, "acc": 0}
        
        (dps_atk, name_atk), (dps_str, name_str) = get_best_dps(atk, str_lvl, allowed, excluded, ammy)
        
        self.assertEqual(name_atk, "rune scimitar")
        self.assertEqual(name_str, "rune scimitar")
        self.assertGreater(dps_atk, 0)

    def test_exclusion_logic(self):
        # Scenario: Level 40/40.
        # Allowed: Rune Scimitar, Adamant Scimitar.
        # Exclude: Rune Scimitar.
        # Expected: Adamant Scimitar.
        
        atk = 40
        str_lvl = 40
        allowed = ["rune scimitar", "adamant scimitar"]
        excluded = ["rune scimitar"]
        ammy = {"str": 0, "acc": 0}
        
        (dps_atk, name_atk), (dps_str, name_str) = get_best_dps(atk, str_lvl, allowed, excluded, ammy)
        
        self.assertEqual(name_atk, "adamant scimitar")

if __name__ == '__main__':
    unittest.main()
