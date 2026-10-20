"""The fallback core in SKILL.md (section 7) must give the same numbers as calc.py."""
import os
import re
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "skills", "global-equity-valuation")
sys.path.insert(0, ROOT)
import calc  # noqa: E402


def load_core():
    text = open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
    block = re.search(r"## 7\. Calculation core.*?```python\n(.*?)```", text, re.S).group(1)
    ns = {}
    exec(block, ns)
    return ns


class CoreMatchesCalc(unittest.TestCase):
    core = load_core()

    def test_engine_a(self):
        self.assertAlmostEqual(self.core["engine_a"](10, 0.20, 0.40, 1.0),
                               calc.engine_a(10, 0.20, 0.40, 1.0)["ceiling"])
        self.assertAlmostEqual(self.core["engine_a"](101, 0.21, 0.70, 10.7, g_terminal=0.025),
                               calc.engine_a(101, 0.21, 0.70, 10.7, g_terminal=0.025)["ceiling"])

    def test_engines_b_c_d(self):
        self.assertAlmostEqual(self.core["engine_b"](3, 0.04, 1), calc.engine_b(3, 0.04, 1)["ceiling"])
        self.assertAlmostEqual(self.core["engine_c"](1, 0.05, False), calc.engine_c(1, 0.05, False)["ceiling"])
        self.assertAlmostEqual(self.core["engine_d"]([5, 3, 2], 1, 0.1, 0.1, [12]),
                               calc.engine_d([5, 3, 2], 1, 0.1, 0.1, [12])["ceiling"])

    def test_output_rules(self):
        for c in (0.873, 7.31, 44.7, 147.3, 1273):
            self.assertEqual(self.core["round_ceiling"](c), calc.round_ceiling(c))
        self.assertEqual(self.core["call"](101, 100), calc.call(101, 100))

    def test_dividend_trap_and_status(self):
        for args in ((12, 10, None), (9, 10, 8), (9, 10, 11), (1, -2, None)):
            self.assertEqual(self.core["dividend_trap"](*args), calc.dividend_trap(*args))
        for crit, mon in (([], []), (["x"], ["y"]), ([], ["y", "z"])):
            self.assertEqual(self.core["thesis_status"](crit, mon), calc.thesis_status(crit, mon))


if __name__ == "__main__":
    unittest.main()
