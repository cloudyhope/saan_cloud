export function requestKey() {
  const crypto = window.crypto;
  if (crypto.randomUUID) return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function persistentRequestKey(scope, payload) {
  const storageKey = 'saan.stock.v1.' + scope;
  const fingerprint = JSON.stringify(payload);
  let saved;
  try { saved = JSON.parse(window.localStorage.getItem(storageKey)); } catch (error) { /* Storage may be disabled. */ }
  if (!saved || saved.fingerprint !== fingerprint || !/^[a-f0-9-]{36}$/.test(saved.key)) {
    saved = { fingerprint, key: requestKey() };
    try { window.localStorage.setItem(storageKey, JSON.stringify(saved)); } catch (error) { /* In-memory retry remains possible. */ }
  }
  return saved.key;
}

export function clearRequestKey(scope, key) {
  const storageKey = 'saan.stock.v1.' + scope;
  try {
    const saved = JSON.parse(window.localStorage.getItem(storageKey));
    if (saved && saved.key === key) window.localStorage.removeItem(storageKey);
  } catch (error) { /* Storage may be disabled. */ }
}
