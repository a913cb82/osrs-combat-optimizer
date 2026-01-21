import unittest
from new_optimize_leveling import get_dps_raw

# Mock Data
MOCK_RUNE_SCIM = {"bonus": {"stab": 7, "slash": 45, "crush": -2}, "max_bonus": 45, "str": 44, "speed": 2.4}
MOCK_BRONZE_SCIM = {"bonus": {"stab": 1, "slash": 7, "crush": -2}, "max_bonus": 7, "str": 6, "speed": 2.4}

class TestDPS(unittest.TestCase):
    def test_dps_comparison(self):
        # Scenario: Level 40/40. 
        # Rune Scimitar should have higher DPS than Bronze.
        
        atk = 40
        str_lvl = 40
        ammy = {"str": 0, "acc": 0}
        
        dps_rune = get_dps_raw("rune scimitar", MOCK_RUNE_SCIM, atk, str_lvl, 'aggressive', ammy)
        dps_bronze = get_dps_raw("bronze scimitar", MOCK_BRONZE_SCIM, atk, str_lvl, 'aggressive', ammy)
        
        self.assertGreater(dps_rune, dps_bronze)
        self.assertGreater(dps_rune, 0)

if __name__ == '__main__':
    unittest.main()
