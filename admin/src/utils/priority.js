// Shared vocabulary for service priority (scores 0-100 computed by the API).
// Levels use the fixed status colours and always appear with their label.
export const PRIORITY_LEVELS = [
  { key: 'critical', label: 'بحرانی', color: '#d03b3b', soft: '#fdeceb', ink: '#a12b2b' },
  { key: 'high', label: 'بالا', color: '#ec835a', soft: '#fdeee6', ink: '#974217' },
  { key: 'medium', label: 'متوسط', color: '#fab219', soft: '#fff4dc', ink: '#7a5300' },
  { key: 'low', label: 'عادی', color: '#8c9bb0', soft: '#eef1f6', ink: '#4a566c' },
];
export const PRIORITY_LEVEL = Object.fromEntries(PRIORITY_LEVELS.map(level => [level.key, level]));
export const TARGETS = [
  { key: 'building', label: 'ساختمان' }, { key: 'elevator', label: 'آسانسور' }, { key: 'client', label: 'مشتری' },
];
export const TARGET_LABEL = Object.fromEntries(TARGETS.map(t => [t.key, t.label]));

export function levelOf(score) {
  if (score === null || score === undefined) return null;
  return score >= 80 ? PRIORITY_LEVEL.critical : score >= 60 ? PRIORITY_LEVEL.high : score >= 40 ? PRIORITY_LEVEL.medium : PRIORITY_LEVEL.low;
}

export function detailRoute(target, id) {
  return { building: '/elevatormanagement/buildingdetail/', elevator: '/elevatormanagement/elevatordetail/', client: '/customermanagement/detail/' }[target] + id;
}

export const faScore = value => (value === null || value === undefined ? '—' : Number(value).toLocaleString('fa-IR', { maximumFractionDigits: 1 }));
