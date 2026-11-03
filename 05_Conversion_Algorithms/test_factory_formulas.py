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

    def test_site_zero_reads_zero_in_clean_air(self):
        # Median 02:00-05:00 Dubai, 29 Oct - 3 Nov 2026: A0 420.08, A1 458.05, A2 359.06 mV
        self.assertLess(ff.no_negative(ff.nh3_ppm(420.08, 420, 58.624)), 0.01)
        self.assertLess(ff.no_negative(ff.h2s_ppb(458.05, 458, 359.06, 359, 1.727952)), 1)
        self.assertAlmostEqual(ff.nh3_ppm(420.08, 328, 58.624), 1.5707, places=3)   # factory zero in the same air

    def test_channel_stuck_at_rail(self):
        self.assertTrue(ff.channel_at_rail(2560.86))
        self.assertTrue(ff.channel_at_rail(2.19))
        self.assertFalse(ff.channel_at_rail(458.0))

    def test_aan803_algorithm3_at_20c_equals_plain_formula(self):
        k = ff.table3_factor(ff.H2S_B4_FACTORS[3], 20)
        we_c = ff.aan803_corrected_we(3, k, 500, 300, 458, 360, 310, 359)
        self.assertAlmostEqual(we_c / 1.727952, ff.h2s_ppb(500, 458, 360, 359, 1.727952))
        self.assertAlmostEqual(ff.table3_factor(ff.H2S_B4_FACTORS[3], 35), -1.2)

    def test_k2t_is_nA_times_board_gain(self):
        self.assertAlmostEqual(ff.aan803_factor(4, 30, gain_mv_per_na=0.8), -52.0)   # -65 nA x 0.8 mV/nA
        self.assertIsNone(ff.aan803_factor(4, 30))

    def test_sensitivity_at_temperature(self):
        self.assertAlmostEqual(ff.sensitivity_pct("H2S-B4", 35), 104.25)                    # datasheet Fig. 1
        self.assertAlmostEqual(ff.sensitivity_pct("NH3-B1+", 40), 110)                      # datasheet Fig. 2
        self.assertAlmostEqual(ff.sensitivity_pct("PIDX-A-040", 40), 100 * 293.15 / 313.15)  # ideal gas law
        self.assertEqual(ff.sensitivity_pct("H2S-B4", 20), 100)


if __name__ == "__main__":
    unittest.main()
