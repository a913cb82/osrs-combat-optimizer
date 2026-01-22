import unittest
from unittest.mock import patch

from osrs_dps import cli as optimize_melee

# Mock Data
MOCK_AMMY_DB = {
    "none": {"str": 0, "acc": 0, "cost": 0.0},
}

MOCK_WEAPON_DB = {
    "super weapon": {
        "atk_req": 1,
        "str": 100,
        "speed": 2.4,
        "cost": 10.0,
        "bonus": {"stab": 100, "slash": 100, "crush": 100},
    },
    "okay weapon": {
        "atk_req": 1,
        "str": 50,
        "speed": 2.4,
        "cost": 10.0,
        "bonus": {"stab": 50, "slash": 50, "crush": 50},
    },
}


class TestGraphPruningBug(unittest.TestCase):
    def test_pruning_ignores_graph_costs(self) -> None:
        """
        Verify that static pruning incorrectly drops 'okay weapon' because it only sees
        base costs (10.0 vs 10.0), ignoring the massive graph cost of 'super weapon'.
        """
        # Graph: Super Weapon requires "expensive_node" (1,000,000s)
        # Okay Weapon has no requirements.
        graph = optimize_melee.ReqGraph()
        graph.add_node("expensive_node", 1000000.0)
        graph.add_node("super weapon", 0.0, ["expensive_node"])

        # Base costs are equal (10.0)
        # costs = {"super weapon": 10.0, "okay weapon": 10.0}

        with (
            patch("osrs_dps.cli.AMULETS_DB", MOCK_AMMY_DB),
            patch("osrs_dps.cli.WEAPON_DB", MOCK_WEAPON_DB),
        ):
            # Goal 10 (Short training)
            # Training time with Super (DPS ~10) -> ~1000s?
            # Training time with Okay (DPS ~5) -> ~2000s.
            # Super Total = 1,000,000 + 1000.
            # Okay Total = 2000 + 10.
            # Okay Weapon SHOULD win.

            result = optimize_melee.solve(
                req_graph=graph,
                goal_atk=10,
                goal_str=10,
                start_atk=1,
                start_str=1,
                timeout=5,
                lookahead=100,
            )

            self.assertIsNotNone(result)
            assert result is not None
            total_time, path = result

            # Check if Super Weapon was used (Bug) or Okay Weapon (Correct)
            # used_super = any(step[3] == "super weapon" for step in path)

            # If the bug exists, Super Weapon will be used because Okay was pruned.
            # We ASSERT that Okay Weapon is used (to fail if bug exists).
            # Or better, check total time.

            # print(f"Total Time: {total_time}")
            self.assertLess(
                total_time,
                50000,
                "Optimizer picked the expensive path! Pruning bug confirmed.",
            )


if __name__ == "__main__":
    unittest.main()
