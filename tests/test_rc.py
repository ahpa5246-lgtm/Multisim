import math
import unittest
from scripts.verify_rc import validate

class RCTest(unittest.TestCase):
    def samples(self):
        return [(i/100000, 5*(1-math.exp(-(i/100000)/.001))) for i in range(501)]

    def test_analytic_waveform(self):
        self.assertLess(validate(self.samples())['max_error_v'], 1e-12)

    def test_wrong_waveform(self):
        with self.assertRaises(ValueError):
            validate([(t, v/2) for t,v in self.samples()])

    def test_nonfinite(self):
        for value in [math.nan, math.inf]:
            rows = self.samples()
            rows[10] = (rows[10][0], value)
            with self.assertRaises(ValueError):
                validate(rows)

    def test_short_capture(self):
        with self.assertRaises(ValueError):
            validate(self.samples()[:20])

    def test_empty_capture(self):
        with self.assertRaises(ValueError):
            validate([])

    def test_reverse_time(self):
        with self.assertRaises(ValueError):
            validate(list(reversed(self.samples())))
