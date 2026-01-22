import unittest
from unittest.mock import patch

from osrs_dps import cli as optimize_melee

# Mock Constants
MOCK_AMMY_DB = {
    "str": {"str": 10, "acc": 0, "cost": 0.0},
    "none": {"str": 0, "acc": 0, "cost": 0.0},
}

MOCK_WEAPON_DB = {
    "iron scimitar": {
        "atk_req": 1,
        "bonus": {"stab": 2, "slash": 10, "crush": -2},
        "str": 9,
        "speed": 2.4,
        "cost": 0.0,
    }
}


class TestAmuletStability(unittest.TestCase):
    def test_stability_str_vs_none(self) -> None:
        """
        Reproduce the issue where optimizer switches from 'str' to 'none'
        despite 'str' being owned and better.
        """
        # Patch data
        with (
            patch("osrs_dps.cli.AMULETS_DB", MOCK_AMMY_DB),
            patch("osrs_dps.cli.WEAPON_DB", MOCK_WEAPON_DB),
        ):
            # Use graph for costs (though 0 here)
            graph = optimize_melee.ReqGraph()
            # If we wanted to override cost, we'd add node here.

            # Run solve
            result = optimize_melee.solve(
                req_graph=graph,
                goal_atk=1,
                goal_str=5,
                start_atk=1,
                start_str=1,
                timeout=5,
                lookahead=100,
            )

            if not result:
                self.fail("Solver failed")

            time_val, path = result

            for step in path:
                ammy = step[4]
                # print(f"Step {step[0]}->{step[1]}: Ammy {ammy}")
                self.assertNotEqual(
                    ammy, "none", f"Optimizer switched to 'none' at step {step}"
                )


if __name__ == "__main__":
    unittest.main()
