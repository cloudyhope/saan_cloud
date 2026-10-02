export const fa = (value, digits = 0) => (value === null || value === undefined || Number.isNaN(value) ? '—'
  : Number(value).toLocaleString('fa-IR', { maximumFractionDigits: digits, minimumFractionDigits: 0 }));
export const faId = value => Number(value).toLocaleString('fa-IR', { useGrouping: false });
export const percent = value => (value === null || value === undefined ? '—' : fa(Math.round(value * 100)) + '٪');
export function jDate(iso, options = { month: 'short', day: 'numeric' }) {
  if (!iso) return '—';
  const date = new Date(String(iso).length === 10 ? iso + 'T12:00:00Z' : iso);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('fa-IR', options);
}
