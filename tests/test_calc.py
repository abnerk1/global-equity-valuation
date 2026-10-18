"""Tests with hypothetical cases: they check the math properties of each engine."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "global-equity-valuation"))
import calc  # noqa: E402


class EngineA(unittest.TestCase):
    def test_no_growth_full_payout_is_a_perpetuity(self):
        # g = 0 and 100% payout -> multiple = 1/r
        self.assertAlmostEqual(calc.two_stage_multiple(0.0, 1.0, 0.10), 10.0, places=9)

    def test_growth_raises_the_multiple(self):
        low = calc.two_stage_multiple(0.03, 0.90)
        high = calc.two_stage_multiple(0.08, 0.90)
        self.assertGreater(high, low)

    def test_reference_multiples(self):
        cases = [  # (g, payout, r, expected multiple)
            (0.03, 0.90, 0.10, 11.56),
            (0.08, 0.90, 0.10, 16.47),
            (0.07, 0.85, 0.08, 19.47),
            (0.15, 0.56, 0.10, 22.81),
        ]
        for g, p, r, expected in cases:
            self.assertAlmostEqual(calc.two_stage_multiple(g, p, r), expected, places=2)

    def test_engine_a_end_to_end(self):
        # Hypothetical company: earnings 10, ROIC 20%, reinvests 40% -> g 8%, payout 60%
        res = calc.engine_a(base=10, roic=0.20, reinvestment=0.40, shares=1.0)
        self.assertAlmostEqual(res["g"], 0.08)
        self.assertAlmostEqual(res["ceiling"], res["fair_per_share"] * 0.80)
        self.assertEqual(calc.finalize(res).rounded_ceiling, 110)

    def test_terminal_growth(self):
        flat = calc.two_stage_multiple(0.10, 0.5)
        growing = calc.two_stage_multiple(0.10, 0.5, g_terminal=0.025)
        self.assertGreater(growing, flat)
        with self.assertRaises(ValueError):
            calc.two_stage_multiple(0.1, 0.5, r=0.02, g_terminal=0.025)


class EngineB(unittest.TestCase):
    def test_gordon(self):
        res = calc.engine_b(fcf=3.0, g=0.04, shares=1.0)  # 3 / 6%
        self.assertAlmostEqual(res["ceiling"], 50.0)

    def test_return_at_the_ceiling_equals_r(self):
        res = calc.engine_b(fcf=2.0, g=0.03, shares=1.0)
        mc = res["ceiling"] * 1.0
        self.assertAlmostEqual(calc.engine_b(2.0, 0.03, 1.0, market_cap=mc)["expected_return"], 0.10)


class EngineC(unittest.TestCase):
    def test_default_and_high_cost_yield(self):
        self.assertAlmostEqual(calc.engine_c(1.0, 0.1)["ceiling"], 50.0)
        self.assertAlmostEqual(calc.engine_c(1.0, 0.1, low_cost=False)["ceiling"], 40.0)

    def test_sensitivity(self):
        s = calc.sensitivity_c({"low": 0.5, "normal": 1.0}, shares=0.1)
        self.assertLess(s["low"], s["normal"])


class EngineD(unittest.TestCase):
    def test_sum_of_the_parts_uses_the_lowest_method(self):
        res = calc.engine_d([5, 3, 2], net_debt=1.0, shares=0.1, haircut=0.10,
                            alternative_methods=[12.0])
        self.assertAlmostEqual(res["equity_used"], 9.0)
        self.assertAlmostEqual(res["ceiling"], 81.0)


class OutputRules(unittest.TestCase):
    def test_call(self):
        self.assertEqual(calc.call(99, 100), "Buy")
        self.assertEqual(calc.call(100, 100), "Buy")
        self.assertEqual(calc.call(101, 100), "Hold")

    def test_rounding(self):
        self.assertEqual(calc.round_ceiling(147.3), 140)
        self.assertEqual(calc.round_ceiling(1273), 1250)
        self.assertEqual(calc.round_ceiling(44.7), 44)
        self.assertEqual(calc.round_ceiling(10.93), 10.9)

    def test_dividend_yield_and_return(self):
        self.assertEqual(calc.expected_dividend_yield(0.5, 4, 50), "4.0%")
        self.assertEqual(calc.expected_dividend_yield(None, 4, 50), "-")
        self.assertAlmostEqual(calc.total_return(150, 100), 0.5)


if __name__ == "__main__":
    unittest.main()
