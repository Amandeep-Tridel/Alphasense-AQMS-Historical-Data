"""Worked-example checks for the factory formulas (Python and JavaScript give the same answers).

    python -m unittest test_factory_formulas -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import factory_formulas as ff  # noqa: E402


class FactoryFormulas(unittest.TestCase):
    def test_h2s_worked_example(self):
        # ((300 - 250) - (280 - 260)) / 0.4 = 75 ppb
        self.assertAlmostEqual(ff.h2s_ppb(300, 250, 280, 260, 0.4), 75.0)

    def test_nh3_worked_example(self):
        self.assertAlmostEqual(ff.nh3_ppm(320, 270, 5), 10.0)

    def test_nh3_factory_sheet_77840031_on_live_reading(self):
        self.assertAlmostEqual(ff.nh3_ppm(349.69, 328, 58.624), (349.69 - 328) / 58.624)

    def test_voc_worked_example(self):
        self.assertAlmostEqual(ff.voc_ppm(150, 40, 55), 2.0)
        self.assertTrue(ff.voc_sensor_fault(30, 40))

    def test_negative_result_counts_as_zero(self):
        self.assertEqual(ff.no_negative(ff.nh3_ppm(300, 328, 58.624)), 0.0)
        self.assertEqual(ff.no_negative(1.5), 1.5)
        self.assertIsNone(ff.no_negative(None))

    def test_counts_to_mv_matches_station_volts(self):
        self.assertAlmostEqual(ff.counts_to_mv(6246), 487.97, places=2)


if __name__ == "__main__":
    unittest.main()
