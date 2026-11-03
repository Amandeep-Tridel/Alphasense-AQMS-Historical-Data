/*
 * Alphasense factory-calibration formulas for the three AQMS gas sensors (JavaScript).
 * Same as factory_formulas.py. Only the zero and sensitivity printed on each sensor's
 * Alphasense factory calibration sheet are used. No temperature tables, no filtering,
 * no smoothing. All voltages in mV.
 *
 *   H2S (ppb) = ((WE - WE zero) - (AE - AE zero)) / sensitivity   AAN 803-05 Alg. 3 at factory temperature (k'T = 1)
 *   NH3 (ppm) = (WE - WE zero) / sensitivity                       sensor 77840031: (mV - 328) / 58.624
 *   VOC (ppm) = (V - V zero) / sensitivity                         AAN 302-04, no temperature correction
 */

const ADC_FULL_SCALE_MV = 2560;
const ADC_STEPS = 32768;

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

const api = { ADC_FULL_SCALE_MV, ADC_STEPS, countsToMv, h2sPpb, nh3Ppm, vocPpm, noNegative, vocSensorFault };
if (typeof module !== "undefined" && module.exports) module.exports = api;
if (typeof window !== "undefined") window.FactoryFormulas = api;
