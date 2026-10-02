export function requestKey() {
  const crypto = window.crypto;
  if (crypto.randomUUID) return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
export function pageRows(data) {
  return Array.isArray(data) ? data : (data && Array.isArray(data.results) ? data.results : []);
}
const pendingKeys = new Map();
export function persistentRequestKey(scope, payload) {
  const storageKey = 'saan.service-request.v1.' + scope;
  const fingerprint = JSON.stringify(payload);
  let saved = pendingKeys.get(storageKey);
  try { saved = JSON.parse(window.localStorage.getItem(storageKey)) || saved; } catch (error) { /* Memory retry remains available when storage is disabled. */ }
  if (!saved || saved.fingerprint !== fingerprint || !/^[a-f0-9-]{36}$/.test(saved.key)) {
    saved = { fingerprint, key: requestKey() };
  }
  pendingKeys.set(storageKey, saved);
  try { window.localStorage.setItem(storageKey, JSON.stringify(saved)); } catch (error) { /* The API still validates ownership and uniqueness. */ }
  return saved.key;
}
export function clearRequestKey(scope, key) {
  const storageKey = 'saan.service-request.v1.' + scope;
  if (pendingKeys.get(storageKey) && pendingKeys.get(storageKey).key === key) pendingKeys.delete(storageKey);
  try {
    const saved = JSON.parse(window.localStorage.getItem(storageKey));
    if (saved && saved.key === key) window.localStorage.removeItem(storageKey);
  } catch (error) { /* Disabled storage needs no cleanup. */ }
}
export function errorMessage(response) {
  if (response.status === 403) return 'برای این عملیات دسترسی ندارید.';
  if (response.status === 404) return 'اطلاعات پیدا نشد یا در دسترس شما نیست.';
  const strings = value => typeof value === 'string' ? [value] :
    value && typeof value === 'object' ? Object.values(value).flatMap(strings) : [];
  return strings(response.data).join('؛ ') || 'عملیات انجام نشد. دوباره تلاش کنید.';
}
