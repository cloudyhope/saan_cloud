const assert = require('assert');
const fs = require('fs');
const path = require('path');

(async () => {
  const source = fs.readFileSync(path.join(__dirname, '../src/utils/dashboardData.js'), 'utf8');
  const d = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
  const ctx = { range: { from: '2026-09-01', to: '2026-09-30' }, today: '2026-09-30' };
  const visits = [
    { id: 1, s: '0', a: true, p: false, t: 1, e: 7, b: 3, c: 9, cr: '2026-09-02T09:00+03:30', st: null, du: '2026-09-10', co: null },
    { id: 2, s: '3', a: true, p: false, t: 1, e: 7, b: 3, c: 9, cr: '2026-09-05T09:00+03:30', st: '2026-09-06T10:00+03:30', du: '2026-09-08', co: '2026-09-07T10:00+03:30', ra: 5 },
    { id: 3, s: '3', a: true, p: false, t: 2, e: 8, b: 4, c: null, cr: '2026-09-05T09:00+03:30', st: '2026-09-06T10:00+03:30', du: '2026-09-06', co: '2026-09-09T10:00+03:30', ra: 3 },
    { id: 4, s: '0', a: false, p: true, t: 2, e: null, b: 4, c: null, cr: '2026-09-20T09:00+03:30', st: null, du: null, co: null },
    { id: 5, s: '5', a: true, p: false, t: 1, e: 8, b: 4, c: null, cr: '2026-01-01T09:00+03:30', st: '2026-01-02T09:00+03:30', du: null, co: null },
  ];
  let checks = 0;
  const eq = (a, b) => { assert.deepStrictEqual(a, b); checks++; };
  eq(d.bucketOf(visits[3]), 'pending');
  eq(d.isOverdue(visits[0], ctx.today), true);
  const k = d.kpis(visits, ctx);
  eq([k.created, k.completed, k.open, k.overdue, k.pending, k.returned], [4, 2, 2, 1, 1, 1]);
  eq(k.onTime, 0.5); eq(k.rating, 4);
  eq(d.applyFilters(visits, { status: 'overdue' }, ctx).map(v => v.id), [1]);
  eq(d.applyFilters(visits, { expert: 'none' }, ctx).map(v => v.id), [4]);
  eq(d.applyFilters(visits, { expert: 7, status: 'overdue' }, ctx, 'expert').map(v => v.id), [1]);
  eq(d.applyFilters(visits, { day: '2026-09-07' }, ctx).map(v => v.id), [2]);
  const t = d.trend(visits, ctx.range);
  eq([t.step, t.points.length, t.points[1].created, t.points[6].completed], [1, 30, 1, 1]);
  eq(d.trend(visits, { from: '2026-07-01', to: '2026-09-30' }).step, 7);
  eq(d.byExpert(visits, ctx, { 7: 'A', 8: 'B' })[0].label, 'A');
  eq(d.attention(visits, ctx, { 3: 'T3', 4: 'T4' }, {}).map(r => r.key), [3, 4]);
  const g = d.gantt(visits, ctx, {});
  eq(g.flatMap(row => row.items.map(i => i.id)).sort(), [1, 2, 3]); // pending and long-open legacy work stay out
  eq(d.lanes([{ plannedStart: '2026-09-01', plannedEnd: '2026-09-05' }, { plannedStart: '2026-09-03', plannedEnd: '2026-09-04' }, { plannedStart: '2026-09-06', plannedEnd: '2026-09-07' }]).map(i => i.lane), [0, 1, 0]);
  eq(d.presetRange('7', '2026-09-30'), { from: '2026-09-24', to: '2026-09-30' });
  console.log(`Dashboard data checks passed (${checks}).`);
})().catch(error => { console.error(error); process.exitCode = 1; });
