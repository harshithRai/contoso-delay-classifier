'use strict';
const CARRIERS = ['Delhivery', 'BlueDart', 'EcomExp', 'IndiaPost'];
const BOUNDS = {
  distance_km: [1, 10000, true], weight_kg: [0.01, 50, false],
  items: [1, 50, true], order_hour: [0, 23, true], is_sale_day: [0, 1, true],
  warehouse_backlog: [0, 1000, true], weather_index: [0, 1, false]
};
const FEATURES = ['carrier', ...Object.keys(BOUNDS)];
function validUserId(value) { return typeof value === 'string' && /^[A-Za-z0-9_-]{3,64}$/.test(value); }
function validate(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) throw Error('Send a JSON object with all eight order fields.');
  const extra = Object.keys(body).filter(k => ![...FEATURES, 'userId'].includes(k));
  if (extra.length) throw Error('Unexpected fields in the order.');
  if (body.userId !== undefined && !validUserId(body.userId)) throw Error('userId must contain 3–64 letters, digits, underscores or hyphens.');
  if (!CARRIERS.includes(body.carrier)) throw Error('Choose a supported carrier.');
  const input = {carrier: body.carrier};
  for (const [key, [min, max, integer]] of Object.entries(BOUNDS)) {
    const value = body[key];
    if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max || (integer && !Number.isInteger(value))) {
      throw Error(`${key} must be ${integer ? 'an integer' : 'a number'} between ${min} and ${max}.`);
    }
    input[key] = value;
  }
  return input;
}
// Log only known numeric fields and known carrier names, even for rejected input.
function safeInput(body) {
  const result = {};
  if (CARRIERS.includes(body?.carrier)) result.carrier = body.carrier;
  for (const key of Object.keys(BOUNDS)) if (typeof body?.[key] === 'number' && Number.isFinite(body[key])) result[key] = body[key];
  return result;
}
module.exports = {CARRIERS, BOUNDS, FEATURES, validate, validUserId, safeInput};
