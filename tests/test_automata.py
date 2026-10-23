"""Language equivalence and boundary checks, independent of implementation."""

import itertools
import unittest

from bank_workbench.automata import balance_tm, credit_nfa, normalize, risk_nfa, suffix_dfa, vowel_dfa


class MachineTests(unittest.TestCase):
    def test_suffix_language_exhaustively(self):
        for length in range(6):
            for letters in itertools.product("پیورx", repeat=length):
                word = "".join(letters)
                self.assertEqual(suffix_dfa(word), word.endswith(("ی", "پور")), word)

    def test_vowel_language_exhaustively(self):
        for length in range(5):
            for letters in itertools.product("اوژx", repeat=length):
                word = "".join(letters)
                expected = (
                    bool(word)
                    and word[-1] in "زژوه"
                    and any(c in "اآوی" for c in word[:-1])
                )
                self.assertEqual(vowel_dfa(word), expected, word)

    def test_risk_truth_table(self):
        for a, b, c in itertools.product((False, True), repeat=3):
            self.assertEqual(
                risk_nfa(
                    "ناز" if c else "علی",
                    "اصغری" if a else "دیگر",
                    1370,
                    "هرمزگان" if b else "تهران",
                ),
                sum((a, b, c)) >= 2,
            )

    def test_unicode_and_credit_boundaries(self):
        self.assertEqual(normalize("  كيان\u200c۱۲٣  "), "کیان 123")
        self.assertTrue(credit_nfa("رضایی\u200cنژاد", 1400))
        self.assertFalse(credit_nfa("محمدیپور دیگر", 1400))
        for year, decision in [
            (1369, "review"),
            (1370, "reject"),
            (1404, "reject"),
            (1405, "review"),
        ]:
            self.assertEqual(
                credit_nfa("احمدي", year, trace=True)["decision"], decision
            )

    def test_tm_boundary_and_trace(self):
        for value in (0, 100_000_000_000, 100_000_000_001, 10**30):
            result = balance_tm(value, trace=True)
            self.assertEqual(result["blocked"], value > 100_000_000_000)
            self.assertEqual(result["value"], "مسدود" if result["blocked"] else value)
            self.assertEqual(
                sum(s["state"] == "q_read" for s in result["steps"]), len(str(value))
            )
        for invalid in (-1, True, 1.2, "100"):
            with self.assertRaises(ValueError):
                balance_tm(invalid)


if __name__ == "__main__":
    unittest.main()
