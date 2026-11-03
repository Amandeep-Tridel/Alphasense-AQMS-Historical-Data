/*
 * Alphasense formulas for the three AQMS gas sensors. Nothing else.
 *
 * Each gas uses a zero (mV) and a sensitivity: the sensitivity from the sensor's Alphasense
 * factory calibration sheet, the zero from that sheet or from a site zero measured on the
 * station in clean air. No filtering, no smoothing.
 *
 *   H2S-B4 (4 electrodes, on ISB):
 *       H2S (ppb) = ((WE - WE zero) - (AE - AE zero)) / sensitivity (mV/ppb)
 *       Alphasense AAN 803-05 Algorithm 3 at 20 degC, where its factor k'T is 1
 *       (AAN 803-05, Table 3).
 *   NH3-B1 (3 electrodes, on ISB):
 *       NH3 (ppm) = (WE - WE zero) / sensitivity (mV/ppm)
 *       As printed on the factory sheet, e.g. sensor 77840031: (mV - 328) / 58.624
 *       This is AAN 803-05 Algorithm 4 with no AE and k''T = 0 (20 degC).
 *   PIDX-A-040 (PID):
 *       VOC (ppm as isobutylene) = (V - V zero) / sensitivity (mV/ppm)
 *
 * "WE zero" and "AE zero" are the TOTAL zero offsets (board offset and sensor zero together),
 * from the factory sheet or from a site zero (AAN 803-05, "Initial calibration").
 * All voltages are in millivolts (mV).
 *
 * Temperature correction is at the end of this file. It needs the temperature at the top of
 * the sensor, which the station does not send yet. At 20 degC it changes nothing.
 *   - Sensitivity (all three sensors): AAN 803-05 step 5 divides by a temperature-corrected
 *     sensitivity, read from the datasheet chart (H2S-B4 Fig. 1, NH3-B1 Fig. 2). The
 *     PIDX-A-040 datasheet (Fig. 2) says its output follows the ideal gas law.
 *   - Zero (H2S-B4 only): AAN 803-05 Tables 1 and 3. Also needs the board's electronic
 *     offsets (WEe, AEe); Algorithm 4 also needs the board gain, because k''T is in nA.
 */

// The station's ADC: 16-bit, bipolar, 2.56 V full scale (as wired on the test station).
const ADC_FULL_SCALE_MV = 2560;
const ADC_STEPS = 32768;

// A channel this close to either end of the ADC range is stuck (unplugged, no power or
// shorted), not measuring gas. An Alphasense ISB output sits at 200-300 mV plus the sensor.
const RAIL_HIGH_MV = 2550;
const RAIL_LOW_MV = 5;

/** Raw ADC number -> mV. Only needed if a station sends counts. */
function countsToMv(counts, fullScaleMv = ADC_FULL_SCALE_MV, steps = ADC_STEPS) {
  return (counts * fullScaleMv) / steps;
}

/** True when the voltage is stuck at the top or bottom of the ADC range. */
function channelAtRail(mv) {
  return mv >= RAIL_HIGH_MV || mv <= RAIL_LOW_MV;
}

/** H2S (ppb) = ((WE - WE zero) - (AE - AE zero)) / sensitivity */
function h2sPpb(weMv, weZeroMv, aeMv, aeZeroMv, sensitivityMvPerPpb) {
  const weSignal = weMv - weZeroMv;
  const aeSignal = aeMv - aeZeroMv;
  return (weSignal - aeSignal) / sensitivityMvPerPpb;
}

/** NH3 (ppm) = (WE - WE zero) / sensitivity */
function nh3Ppm(weMv, weZeroMv, sensitivityMvPerPpm) {
  return (weMv - weZeroMv) / sensitivityMvPerPpm;
}

/** VOC (ppm as isobutylene) = (V - V zero) / sensitivity */
function vocPpm(vMv, vZeroMv, sensitivityMvPerPpm) {
  return (vMv - vZeroMv) / sensitivityMvPerPpm;
}

/** A negative gas result counts as 0 (apply before averaging). */
const noNegative = (value) => (value === null || value === undefined ? null : Math.max(0, value));

/** A PID voltage below its zero means a faulty sensor, not clean air. */
function vocSensorFault(vMv, vZeroMv) {
  return vMv < vZeroMv;
}

// ---- Temperature correction (only with the temperature at the top of the sensor) ----

const TABLE3_TEMPS_C = [-30, -20, -10, 0, 10, 20, 30, 40, 50];

// AAN 803-05 Table 3, H2S-B4 row, copied exactly. Factors at -30, -20, ... 50 degC.
// nT, kT and k'T have no unit. k''T is a current in nA: it matches the H2S-B4 datasheet's
// Fig. 2 zero shift (-65 / -125 / -180 nA at 30 / 40 / 50 degC), so on a board it is
// multiplied by the board gain (mV/nA) before it is taken from a voltage.
const H2S_B4_FACTORS = {
  1: [-0.6, -0.6, 0.1, 0.8, -0.7, -2.5, -2.5, -2.2, -1.8], // nT
  2: [0.2, 0.2, 0, -0.3, 0.3, 1, 1, 0.9, 0.7],             // kT
  3: [-14, -14, 3, 3, 2, 1, -1.2, -1.2, -1.2],             // k'T
  4: [52, 51, 48, 45, 26, 0, -65, -125, -180],             // k''T (nA)
};
// AAN 803-05 Table 2 suggests Algorithm 1 for B-type H2S (alternative: 2). Table 3 has no
// NH3-B1 row, and the NH3-B1 datasheet gives no zero-vs-temperature data ("nd"), so the NH3
// zero gets no temperature correction.

// Sensitivity as % of the 20 degC value, at -30, -20, ... 50 degC. Read from the datasheet
// charts (middle of the typical batch shown), so they are approximate: replace them with
// Alphasense's tabulated values if they send them.
const SENSITIVITY_PCT = {
  "H2S-B4": [77, 82, 87, 92, 96, 100, 103, 105.5, 105.5],   // H2S-B4 datasheet Fig. 1
  "NH3-B1": [116, 112, 104, 100, 98.5, 100, 103, 110, 125], // NH3-B1 datasheet Fig. 2
};
const IDEAL_GAS_REF_K = 293.15; // 20 degC: the PIDX-A-040 is specified at room temperature

/** Value at tempC, linearly interpolated between the Table 3 temperatures. Outside -30..50 degC: the end value. */
function table3Factor(factors, tempC) {
  const T = TABLE3_TEMPS_C;
  if (tempC <= T[0]) return factors[0];
  if (tempC >= T[T.length - 1]) return factors[factors.length - 1];
  for (let i = 0; i < T.length - 1; i++) {
    if (tempC >= T[i] && tempC <= T[i + 1]) {
      return factors[i] + ((factors[i + 1] - factors[i]) * (tempC - T[i])) / (T[i + 1] - T[i]);
    }
  }
  return null;
}

/**
 * The H2S-B4 Table 3 factor for this algorithm and temperature, ready for aan803CorrectedWe.
 * Algorithm 4's k''T (nA) is turned into mV with the board gain; without a gain it returns null.
 */
function aan803Factor(algorithm, tempC, gainMvPerNa = null) {
  const factor = table3Factor(H2S_B4_FACTORS[algorithm], tempC);
  if (algorithm === 4) return gainMvPerNa === null || gainMvPerNa === undefined ? null : factor * gainMvPerNa;
  return factor;
}

/**
 * Corrected WE output WEc (mV), AAN 803-05 Table 1.
 * weU, aeU: raw WE and AE outputs.  weE, aeE: electronic offsets on the board.
 * weT, aeT: total zero offsets (sheet or site zero).  Sensor zeros: WEo = WEt - WEe, AEo = AEt - AEe.
 * factor: from aan803Factor (for Algorithm 4 already in mV).
 */
function aan803CorrectedWe(algorithm, factor, weU, weE, weT, aeU = null, aeE = null, aeT = null) {
  const weO = weT - weE;
  if (algorithm === 4) return weU - weE - weO - factor;
  const aeO = aeT - aeE;
  if (algorithm === 1) return weU - weE - factor * (aeU - aeE);
  if (algorithm === 2) return weU - weE - factor * (weO / aeO) * (aeU - aeE);
  if (algorithm === 3) return weU - weE - (weO - aeO) - factor * (aeU - aeE);
  throw new Error(`unknown AAN 803-05 algorithm ${algorithm}`);
}

/**
 * Sensitivity at tempC as % of the 20 degC value, or null for an unknown sensor.
 * H2S-B4 and NH3-B1: the datasheet chart (AAN 803-05 step 5). PIDX-A-040: the ideal gas law,
 * as its datasheet says: 100 x 293.15 / (273.15 + T).
 */
function sensitivityPct(sensorModel, tempC) {
  const model = String(sensorModel || "").replace(/\+$/, "");
  if (SENSITIVITY_PCT[model]) return table3Factor(SENSITIVITY_PCT[model], tempC);
  if (model === "PIDX-A-040") return (100 * IDEAL_GAS_REF_K) / (273.15 + tempC);
  return null;
}

const api = {
  ADC_FULL_SCALE_MV, ADC_STEPS, RAIL_HIGH_MV, RAIL_LOW_MV, countsToMv, channelAtRail,
  h2sPpb, nh3Ppm, vocPpm, noNegative, vocSensorFault,
  TABLE3_TEMPS_C, H2S_B4_FACTORS, SENSITIVITY_PCT, table3Factor, aan803Factor, aan803CorrectedWe, sensitivityPct,
};
if (typeof module !== "undefined" && module.exports) module.exports = api;
if (typeof window !== "undefined") window.FactoryFormulas = api;
