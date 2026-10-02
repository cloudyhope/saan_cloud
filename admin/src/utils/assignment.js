// Shared vocabulary of the assignment screens.
export const FACTORS = [
  { key: 'skill', label: 'مهارت', hint: 'تطابق مهارت و گرید با نیاز خدمت' },
  { key: 'quality', label: 'کیفیت', hint: 'تأیید بدون اصلاح، نظر مشتری و رعایت موعد در ۱۸۰ روز اخیر' },
  { key: 'workload', label: 'ظرفیت', hint: 'مأموریت‌های باز و بار روز موعد' },
  { key: 'familiarity', label: 'آشنایی', hint: 'خدمت‌های موفق قبلی در همین ساختمان' },
];

export const LEVELS = [1, 2, 3, 4, 5];
export const GRADE_LABEL = { 1: 'کارآموز', 2: 'مبتدی', 3: 'متوسط', 4: 'ارشد', 5: 'استاد' };

export const fa = (value, digits = 0) => (value === null || value === undefined ? '—'
  : Number(value).toLocaleString('fa-IR', { maximumFractionDigits: digits }));
export const faId = (value) => Number(value).toLocaleString('fa-IR', { useGrouping: false });

export function jDate(value) {
  if (!value) return '—';
  const date = new Date(String(value).slice(0, 10) + 'T00:00:00');
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('fa-IR', { month: 'long', day: 'numeric' });
}

// Same colours as the dashboard status palette; always paired with the number, never colour alone.
export function scoreTone(score) {
  if (score >= 70) return { key: 'good', color: '#0ca30c', label: 'مناسب' };
  if (score >= 50) return { key: 'fair', color: '#d99a00', label: 'متوسط' };
  return { key: 'weak', color: '#d03b3b', label: 'ضعیف' };
}

export const errorText = (api, response) => api.getErrorMessage(response) || 'خطای نامشخص';
