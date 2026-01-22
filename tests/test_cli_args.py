import unittest

from osrs_dps import cli as optimize_melee


class TestCLIArgs(unittest.TestCase):
    def test_solve_signature_match(self) -> None:
        """
        Verify that solve() can be called with the arguments constructed in main().
        mimics the README example call structure.
        """
        # Mock graph
        graph = optimize_melee.ReqGraph()
        graph.add_node("rune scimitar", 1300 * 3600)

        # Goals
        g_atk = 99
        g_str = 99
        start_atk = 1
        start_str = 1
        timeout = 30
        lookahead = 100

        # The main block calls:
        # solve(None, graph, g_atk, g_str, args.start_atk, args.start_str,
        #       args.timeout, args.lookahead)
        # Note: The traceback showed 'None' being passed as first arg.
        # This implies 'costs_map' was passed as None?
        # But I removed costs_map from the call in my thought process?
        # Let's verify what the code actually does by running this test with
        # the suspected signature.

        try:
            # Attempt to call with correct arguments
            # solve(req_graph, goal_atk, goal_str, start_atk, start_str,
            #       timeout, lookahead)
            optimize_melee.solve(
                graph, g_atk, g_str, start_atk, start_str, timeout, lookahead
            )
        except TypeError as e:
            self.fail(f"solve() raised TypeError with correct arguments: {e}")
        except Exception:
            # We expect it might fail logic due to mock graph, but NOT TypeError
            # on signature
            pass


if __name__ == "__main__":
    unittest.main()
