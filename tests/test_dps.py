import unittest

from osrs_dps.mechanics import calculate_dps


class TestDPS(unittest.TestCase):
    def test_dps_calculation(self) -> None:
        # Scenario: Max Hit 10, Hit Chance 0.5, Speed 2.4s
        # Avg Dmg = 0.5 * 10 * 0.5 = 2.5
        # DPS = 2.5 / 2.4 = 1.0416...

        dps = calculate_dps(10, 0.5, 2.4)
        self.assertAlmostEqual(dps, 1.0416666, places=5)

    def test_higher_stats_yield_higher_dps(self) -> None:
        # Compare "Weak" vs "Strong" inputs
        dps_weak = calculate_dps(10, 0.5, 2.4)
        dps_strong = calculate_dps(20, 0.5, 2.4)
        self.assertGreater(dps_strong, dps_weak)

        dps_fast = calculate_dps(10, 0.5, 2.4)
        dps_slow = calculate_dps(10, 0.5, 3.6)
        self.assertGreater(dps_fast, dps_slow)


if __name__ == "__main__":
    unittest.main()
