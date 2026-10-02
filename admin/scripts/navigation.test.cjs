// Menu helpers: tab groups, search entries and the Persian-friendly header search.
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const load = (file) => import('data:text/javascript;base64,' + Buffer.from(fs.readFileSync(path.join(__dirname, '../src/utils/' + file), 'utf8')).toString('base64'));

(async () => {
  const nav = await load('adminNavigation.js');
  const text = await load('searchText.js');
  let checks = 0;
  const eq = (a, b) => { assert.deepStrictEqual(a, b); checks++; };

  const leaf = (id, title, url, extra = {}) => ({ id, verbose_name: title, frontend_route_url: url, children: [], ...extra });
  const menu = [
    leaf(1, 'داشبورد', '/dashboard'),
    leaf(2, 'مدیریت ویزیت‌ها', '/visitmanagment/lists', {
      frontend_route_params: { display: 'tabs' },
      children: [leaf(21, 'تکمیل نشده', '/visitmanagment/notcompeletevisits'), leaf(22, 'تکمیل شده', '/visitmanagment/completeVisited'),
        leaf(23, 'لیست ویزیت‌ها', '/visitmanagment/lists')],
    }),
    leaf(3, 'دارایی‌ها', '/customermanagement/list', {
      children: [leaf(31, 'لیست مشتریان', '/customermanagement/list'), leaf(32, 'لیست آسانسور', '/elevatormanagement/elevatorlist')],
    }),
    leaf(4, 'خالی', '/x', { frontend_route_params: { display: 'tabs' }, children: [] }),
  ];

  // tab groups
  eq(nav.isTabGroup(menu[1]), true);
  eq(nav.isTabGroup(menu[2]), false);
  eq(nav.isTabGroup(menu[3]), false); // a tab group without children is just a link
  eq(nav.tabsForRoute(menu, '/visitmanagment/completeVisited').tabs.map((tab) => tab.id), [21, 22, 23]);
  eq(nav.tabsForRoute(menu, '/visitmanagment/answerlist/5').group.id, 2); // a visit detail belongs to its list tab group
  eq(nav.tabsForRoute(menu, '/customermanagement/list'), null);
  eq(nav.tabsForRoute(menu, '/nowhere'), null);

  // search entries: leaves only (group links duplicate their first child), tab children included
  const entries = nav.searchableEntries(menu);
  eq(entries.map((entry) => entry.title), ['داشبورد', 'تکمیل نشده', 'تکمیل شده', 'لیست ویزیت‌ها', 'لیست مشتریان', 'لیست آسانسور', 'خالی']);
  eq(entries[2].trail, ['مدیریت ویزیت‌ها']);

  // text matching
  eq(text.normalize('  كتاب  ي۱۲٣ '), 'کتاب ی123');
  eq(text.normalize('ساختمان‌ها'), 'ساختمانها');
  eq(text.visitNumber('۵۰۰۰۰۰۶'), 5000006);
  eq(text.visitNumber('abc'), null);
  eq(text.visitNumber('1234567890'), null);
  const rank = (query) => text.rankEntries(entries, query).map((entry) => entry.title);
  eq(rank('لیست'), ['لیست ویزیت‌ها', 'لیست مشتریان', 'لیست آسانسور']);
  eq(rank('ویزیت لیست'), ['لیست ویزیت‌ها']); // every word must match, in any order
  eq(rank('مدیریت ویزیتها')[0], 'تکمیل نشده'); // matches through the group name; ZWNJ does not matter
  eq(rank('آسانسور'), ['لیست آسانسور']);
  eq(rank('zzz'), []);
  eq(rank('   '), []);
  eq(text.rankEntries(entries, 'ل', 2).length, 2); // limit

  console.log(`Navigation checks passed (${checks}).`);
})().catch((error) => { console.error(error); process.exit(1); });
