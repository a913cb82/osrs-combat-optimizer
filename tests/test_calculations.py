import unittest

from osrs_dps.mechanics import calculate_hit_chance, calculate_max_hit


class TestCalculations(unittest.TestCase):
    def test_max_hit_rune_scimitar(self) -> None:
        # Scenario: 99 Str, Str Amulet, Aggressive Style, Rune Scimitar
        str_lvl = 99
        equip_str = 44 + 10  # Scim + Ammy
        style_bonus = 3  # Aggressive

        # Expected: 20 (Calculated: floor(0.5 + (110 * 118)/640) = 20)
        max_hit = calculate_max_hit(str_lvl, equip_str, style_bonus)
        self.assertEqual(max_hit, 20)

    def test_max_hit_bronze_scimitar_lvl_1(self) -> None:
        # Scenario: 1 Str, No Ammy, Aggressive, Bronze Scim (+6)
        str_lvl = 1
        equip_str = 6
        style_bonus = 3

        # EffStr = 1 + 3 + 8 = 12
        # Equip = 6 + 64 = 70
        # (12 * 70) / 640 = 840 / 640 = 1.3125
        # floor(0.5 + 1.3125) = floor(1.8125) = 1
        max_hit = calculate_max_hit(str_lvl, equip_str, style_bonus)
        self.assertEqual(max_hit, 1)

    def test_hit_chance_basic(self) -> None:
        # Scenario: 1 Atk, Bronze Scim (+7 Slash), Accurate (+3), vs Def 1 (Bonus 0)
        atk_lvl = 1
        equip_atk = 7
        style_bonus = 3

        # EffAtk = 1 + 3 + 8 = 12
        # AtkRoll = 12 * (7 + 64) = 12 * 71 = 852

        # EffDef = 1 + 9 = 10
        # DefRoll = 10 * (0 + 64) = 640

        # AtkRoll > DefRoll
        # Chance = 1 - (640 + 2) / (2 * (852 + 1))
        # Chance = 1 - 642 / 1706
        # Chance = 1 - 0.3763 = 0.6237

        chance = calculate_hit_chance(atk_lvl, equip_atk, style_bonus)
        self.assertAlmostEqual(chance, 1.0 - (642.0 / 1706.0), places=4)


if __name__ == "__main__":
    unittest.main()
