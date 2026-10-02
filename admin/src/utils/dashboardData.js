// Pure aggregation for the management dashboard. Every widget reads the same filtered rows,
// so cards, charts and the schedule always agree. Rows come from /core/api/admin/dashboard/.

// Lifecycle states. Judgement states use the fixed status colours (always with a label);
// neutral states use the blue ramp and grey.
export const BUCKETS = [
  { key: 'pending', label: 'درخواست بررسی‌نشده', color: '#8c9bb0' },
  { key: 'planned', label: 'برنامه‌ریزی‌شده', color: '#86b6ef' },
  { key: 'progress', label: 'در حال انجام', color: '#2a78d6' },
  { key: 'suspended', label: 'متوقف', color: '#a3a29c' },
  { key: 'review', label: 'منتظر بررسی', color: '#fab219' },
  { key: 'returned', label: 'برگشت برای اصلاح', color: '#ec835a' },
  { key: 'approved', label: 'تأیید شده', color: '#0ca30c' },
  { key: 'rejected', label: 'رد شده', color: '#d03b3b' },
];
export const BUCKET = Object.fromEntries(BUCKETS.map(item => [item.key, item]));
export const SERIES = { created: '#2a78d6', completed: '#eb6834' };
export const STATUS_FOCUS = {
  open: 'مأموریت باز', overdue: 'دارای دیرکرد', completed: 'پایان‌یافته در بازه', ...Object.fromEntries(BUCKETS.map(b => [b.key, b.label])),
};
const OPEN = ['0', '1', '5', '6'];
// Service-priority level of a visit (score from client, building and elevator factors).
export function priorityLevel(score) {
  if (score === null || score === undefined) return 'none';
  return score >= 80 ? 'critical' : score >= 60 ? 'high' : score >= 40 ? 'medium' : 'low';
}

export function bucketOf(visit) {
  if (visit.p) return 'pending';
  return { 0: 'planned', 1: 'progress', 2: 'review', 3: 'approved', 4: 'rejected', 5: 'returned', 6: 'suspended' }[visit.s] || 'planned';
}
export const day = value => (value ? String(value).slice(0, 10) : null);
export const isOpen = visit => !visit.p && visit.a && OPEN.includes(visit.s);
export const isOverdue = (visit, today) => isOpen(visit) && !!visit.du && visit.du < today;
export const inRange = (value, range) => !!value && value >= range.from && value <= range.to;
export const completedInRange = (visit, range) => inRange(day(visit.co), range);

function matchesStatus(visit, status, ctx) {
  if (!status) return true;
  if (status === 'open') return isOpen(visit);
  if (status === 'overdue') return isOverdue(visit, ctx.today);
  if (status === 'completed') return completedInRange(visit, ctx.range);
  return bucketOf(visit) === status;
}

// Applies every active filter except the one named in `except`, so a chart keeps showing all of
// its own options while the rest of the dashboard is narrowed.
export function applyFilters(visits, filters, ctx, except = '') {
  return visits.filter(visit =>
    (except === 'type' || !filters.type || visit.t === filters.type)
    && (except === 'expert' || !filters.expert || (filters.expert === 'none' ? !visit.e : visit.e === filters.expert))
    && (except === 'client' || !filters.client || visit.c === filters.client)
    && (except === 'building' || !filters.building || visit.b === filters.building)
    && (except === 'priority' || !filters.priority || priorityLevel(visit.pr) === filters.priority)
    && (except === 'status' || matchesStatus(visit, filters.status, ctx))
    && (except === 'day' || !filters.day || day(visit.cr) === filters.day || day(visit.co) === filters.day));
}

const average = values => (values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null);

export function kpis(visits, ctx) {
  const created = visits.filter(v => inRange(day(v.cr), ctx.range));
  const completed = visits.filter(v => completedInRange(v, ctx.range));
  const withDue = completed.filter(v => v.du);
  const cycles = completed.filter(v => v.st).map(v => (new Date(v.co) - new Date(v.st)) / 86400000).filter(v => v >= 0);
  const rated = completed.filter(v => v.ra);
  return {
    created: created.length,
    completed: completed.length,
    open: visits.filter(isOpen).length,
    openUrgent: visits.filter(v => isOpen(v) && v.pr >= 60).length,
    overdue: visits.filter(v => isOverdue(v, ctx.today)).length,
    review: visits.filter(v => v.s === '2').length,
    returned: visits.filter(v => v.s === '5' && !v.p).length,
    pending: visits.filter(v => v.p).length,
    onTime: withDue.length ? withDue.filter(v => day(v.co) <= v.du).length / withDue.length : null,
    onTimeBase: withDue.length,
    rating: average(rated.map(v => v.ra)),
    ratingBase: rated.length,
    cycleDays: average(cycles),
  };
}

export function delta(current, previous) {
  if (!previous) return current ? null : 0;
  return (current - previous) / previous;
}

function addDays(iso, count) {
  const date = new Date(iso + 'T00:00:00Z');
  date.setUTCDate(date.getUTCDate() + count);
  return date.toISOString().slice(0, 10);
}
export function daysBetween(from, to) { return Math.round((new Date(to + 'T00:00:00Z') - new Date(from + 'T00:00:00Z')) / 86400000); }

// Daily points for short ranges, weekly (7-day) buckets for long ones.
export function trend(visits, range) {
  const span = daysBetween(range.from, range.to) + 1;
  const step = span > 62 ? 7 : 1;
  const points = [];
  for (let start = range.from; start <= range.to; start = addDays(start, step)) {
    const end = step === 1 ? start : (addDays(start, step - 1) > range.to ? range.to : addDays(start, step - 1));
    points.push({ from: start, to: end, created: 0, completed: 0 });
  }
  const find = value => points.find(point => value >= point.from && value <= point.to);
  visits.forEach(visit => {
    const created = day(visit.cr);
    const completed = day(visit.co);
    if (inRange(created, range)) find(created).created += 1;
    if (inRange(completed, range)) find(completed).completed += 1;
  });
  return { step, points };
}

export function byBucket(visits) {
  const counts = Object.fromEntries(BUCKETS.map(b => [b.key, 0]));
  visits.forEach(visit => { counts[bucketOf(visit)] += 1; });
  return BUCKETS.map(b => ({ ...b, value: counts[b.key] }));
}

export function byExpert(visits, ctx, names) {
  const rows = new Map();
  visits.forEach(visit => {
    const key = visit.e || 'none';
    if (!rows.has(key)) rows.set(key, { key, label: key === 'none' ? 'بدون کارشناس' : names[key] || 'کارشناس ' + key, overdue: 0, open: 0, completed: 0, ratings: [] });
    const row = rows.get(key);
    if (isOverdue(visit, ctx.today)) row.overdue += 1;
    else if (isOpen(visit)) row.open += 1;
    if (completedInRange(visit, ctx.range)) { row.completed += 1; if (visit.ra) row.ratings.push(visit.ra); }
  });
  return [...rows.values()].map(row => ({ ...row, total: row.overdue + row.open + row.completed, rating: average(row.ratings) }))
    .filter(row => row.total).sort((a, b) => b.overdue - a.overdue || b.total - a.total);
}

export function byType(visits, names) {
  const counts = new Map();
  visits.forEach(visit => counts.set(visit.t, (counts.get(visit.t) || 0) + 1));
  return [...counts.entries()].map(([key, value]) => ({ key, label: names[key] || 'خدمت ' + key, value }))
    .sort((a, b) => b.value - a.value);
}

// Buildings that need a manager's attention: late work weighs most, then returned and waiting reports.
export function attention(visits, ctx, names, clients) {
  const rows = new Map();
  visits.forEach(visit => {
    if (!visit.b) return;
    if (!rows.has(visit.b)) rows.set(visit.b, { key: visit.b, label: names[visit.b] || 'ساختمان ' + visit.b, client: clients[visit.c] || '', overdue: 0, returned: 0, review: 0, open: 0 });
    const row = rows.get(visit.b);
    if (isOverdue(visit, ctx.today)) row.overdue += 1;
    if (visit.s === '5' && !visit.p) row.returned += 1;
    if (visit.s === '2') row.review += 1;
    if (isOpen(visit)) row.open += 1;
  });
  return [...rows.values()].map(row => ({ ...row, score: row.overdue * 3 + row.returned * 2 + row.review }))
    .filter(row => row.score).sort((a, b) => b.score - a.score || b.open - a.open);
}

// Schedule rows per field worker. Planned span: creation to due date; actual span: start to finish
// (or to today while the work is still open).
export function gantt(visits, ctx, names) {
  const rows = new Map();
  visits.forEach(visit => {
    if (visit.p) return;
    const created = day(visit.cr);
    const plannedEnd = visit.du || created;
    const actualStart = day(visit.st);
    const actualEnd = day(visit.co) || (actualStart && isOpen(visit) ? ctx.today : actualStart);
    const first = [created, actualStart].filter(Boolean).sort()[0];
    const last = [plannedEnd, actualEnd].filter(Boolean).sort().slice(-1)[0];
    if (!first || last < ctx.range.from || first > ctx.range.to) return;
    // Only work with a milestone inside the window; long-open legacy records would span every row.
    if (![created, actualStart, visit.du, day(visit.co)].some(value => inRange(value, ctx.range))) return;
    const key = visit.e || 'none';
    if (!rows.has(key)) rows.set(key, { key, label: key === 'none' ? 'بدون کارشناس' : names[key] || 'کارشناس ' + key, items: [] });
    rows.get(key).items.push({
      id: visit.id, bucket: bucketOf(visit), plannedStart: created, plannedEnd: plannedEnd < created ? created : plannedEnd,
      actualStart, actualEnd, late: isOverdue(visit, ctx.today) || (!!visit.du && !!visit.co && day(visit.co) > visit.du),
      due: visit.du, building: visit.b, type: visit.t, priority: visit.pr,
    });
  });
  return [...rows.values()].map(row => ({ ...row, items: row.items.sort((a, b) => (a.plannedStart < b.plannedStart ? -1 : 1)) }))
    .sort((a, b) => b.items.length - a.items.length);
}

// Packs bars into lanes so overlapping work for one person never draws on top of itself.
export function lanes(items) {
  const ends = [];
  return items.map(item => {
    const start = [item.plannedStart, item.actualStart].filter(Boolean).sort()[0];
    const end = [item.plannedEnd, item.actualEnd].filter(Boolean).sort().slice(-1)[0];
    let lane = ends.findIndex(value => value < start);
    if (lane < 0) { lane = ends.length; ends.push(end); } else ends[lane] = end;
    return { ...item, lane };
  });
}

export function presetRange(preset, today) {
  if (preset === '7') return { from: addDays(today, -6), to: today };
  if (preset === '90') return { from: addDays(today, -89), to: today };
  if (preset === 'month') {
    const dayOfMonth = Number(new Intl.DateTimeFormat('en-u-ca-persian-nu-latn', { day: 'numeric' }).format(new Date(today + 'T12:00:00Z')));
    return { from: addDays(today, -(dayOfMonth - 1)), to: today };
  }
  return { from: addDays(today, -29), to: today };
}
export { addDays };
