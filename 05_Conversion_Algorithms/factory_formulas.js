/*
 * Alphasense formulas for the three AQMS gas sensors (JavaScript). Same as factory_formulas.py.
 * A zero and a sensitivity per gas: sensitivity from the factory sheet, zero from the factory
 * sheet or a site zero (AAN 803-05 "Initial calibration"). No filtering, no smoothing. All mV.
 *
 *   H2S (ppb) = ((WE - WE zero) - (AE - AE zero)) / sensitivity   AAN 803-05 Alg. 3 at 20 degC (k'T = 1)
 *   NH3 (ppm) = (WE - WE zero) / sensitivity                       AAN 803-05 Alg. 4, no AE (3 electrodes)
 *   VOC (ppm) = (V - V zero) / sensitivity                         AAN 302-04, no temperature correction
 *
 * Temperature correction (AAN 803-05 Tables 1 and 3) is at the end; it needs the temperature at
 * the top of the sensor and the board's electronic offsets, and gives the same answer at 20 degC.
 */

const ADC_FULL_SCALE_MV = 2560;
const ADC_STEPS = 32768;
// A channel this close to either end of the ADC range is stuck (unplugged, no power or shorted).
const RAIL_HIGH_MV = 2550;
const RAIL_LOW_MV = 5;

/** True when the voltage is stuck at the top or bottom of the ADC range. */
const channelAtRail = (mv) => mv >= RAIL_HIGH_MV || mv <= RAIL_LOW_MV;

/** Raw ADC number -> mV. Only needed if a station sends counts. */
const countsToMv = (counts, fullScaleMv = ADC_FULL_SCALE_MV, steps = ADC_STEPS) => (counts * fullScaleMv) / steps;

/** H2S (ppb) = ((WE - WE zero) - (AE - AE zero)) / sensitivity */
const h2sPpb = (weMv, weZeroMv, aeMv, aeZeroMv, sensitivityMvPerPpb) =>
  ((weMv - weZeroMv) - (aeMv - aeZeroMv)) / sensitivityMvPerPpb;

/** NH3 (ppm) = (WE - WE zero) / sensitivity */
const nh3Ppm = (weMv, weZeroMv, sensitivityMvPerPpm) => (weMv - weZeroMv) / sensitivityMvPerPpm;

/** VOC (ppm as isobutylene) = (V - V zero) / sensitivity */
const vocPpm = (vMv, vZeroMv, sensitivityMvPerPpm) => (vMv - vZeroMv) / sensitivityMvPerPpm;

/** A negative gas result counts as 0 (apply before averaging). */
const noNegative = (value) => (value === null || value === undefined ? null : Math.max(0, value));

/** A PID voltage below its zero means a faulty sensor, not clean air. */
const vocSensorFault = (vMv, vZeroMv) => vMv < vZeroMv;

// ---- Temperature correction, AAN 803-05 (only with sensor temperature and electronic offsets) ----
// AAN 803-05 Table 3, H2S-B4 row. Factors at -30, -20, ... 50 degC. Table 2 suggests Algorithm 1 for B-type H2S.
const TABLE3_TEMPS_C = [-30, -20, -10, 0, 10, 20, 30, 40, 50];
const H2S_B4_FACTORS = {
  1: [-0.6, -0.6, 0.1, 0.8, -0.7, -2.5, -2.5, -2.2, -1.8], // nT
  2: [0.2, 0.2, 0, -0.3, 0.3, 1, 1, 0.9, 0.7],             // kT
  3: [-14, -14, 3, 3, 2, 1, -1.2, -1.2, -1.2],             // k'T
  4: [52, 51, 48, 45, 26, 0, -65, -125, -180],             // k''T (mV)
};

/** Factor at tempC, linearly interpolated between the Table 3 temperatures. */
function table3Factor(factors, tempC) {
  const T = TABLE3_TEMPS_C;
  if (tempC <= T[0]) return factors[0];
  if (tempC >= T[T.length - 1]) return factors[factors.length - 1];
  for (let i = 0; i < T.length - 1; i++) {
    if (tempC >= T[i] && tempC <= T[i + 1]) return factors[i] + ((factors[i + 1] - factors[i]) * (tempC - T[i])) / (T[i + 1] - T[i]);
  }
  return null;
}

/** Corrected WE output WEc (mV), AAN 803-05 Table 1. WEo = WEt - WEe, AEo = AEt - AEe. */
function aan803CorrectedWe(algorithm, factor, weU, weE, weT, aeU = null, aeE = null, aeT = null) {
  const weO = weT - weE;
  if (algorithm === 4) return weU - weE - weO - factor;
  const aeO = aeT - aeE;
  if (algorithm === 1) return weU - weE - factor * (aeU - aeE);
  if (algorithm === 2) return weU - weE - factor * (weO / aeO) * (aeU - aeE);
  if (algorithm === 3) return weU - weE - (weO - aeO) - factor * (aeU - aeE);
  throw new Error(`unknown AAN 803-05 algorithm ${algorithm}`);
}

const api = {
  ADC_FULL_SCALE_MV, ADC_STEPS, RAIL_HIGH_MV, RAIL_LOW_MV, countsToMv, channelAtRail,
  h2sPpb, nh3Ppm, vocPpm, noNegative, vocSensorFault, TABLE3_TEMPS_C, H2S_B4_FACTORS, table3Factor, aan803CorrectedWe,
};
if (typeof module !== "undefined" && module.exports) module.exports = api;
if (typeof window !== "undefined") window.FactoryFormulas = api;
