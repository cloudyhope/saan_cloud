// Titles, priority, hierarchy and destinations are supplied by the backend.
export function normalizeMenu(payload) {
  const source = Array.isArray(payload) ? payload : payload.results || [];
  const nodes = new Map();
  const register = (items, parent = null) =>
    items.forEach((item) => {
      if (!item || item.is_active === false) return;
      nodes.set(String(item.id), {
        ...item,
        parent: parent === null ? item.parent : parent,
        children: [],
      });
      if (Array.isArray(item.children)) register(item.children, item.id);
    });
  register(source);
  const roots = [];
  nodes.forEach((node) => {
    const parentId = node.parent && typeof node.parent === 'object' ? node.parent.id : node.parent;
    const parent = nodes.get(String(parentId));
    if (parent && parent !== node) parent.children.push(node);
    else roots.push(node);
  });
  const sort = (items) =>
    items
      .sort((a, b) => (a.priority || 0) - (b.priority || 0))
      .map((item) => ({ ...item, children: sort(item.children) }));
  return sort(roots);
}

export function menuDestination(menu) {
  // frontend_api_queryparams contains API filter values (e.g. photo types),
  // rather than navigation query parameters. The detail view reads that field.
  return menu.frontend_route_url || '/dashboard';
}

export function menuContainsRoute(menu, path) {
  const canonical = (value) => (value || '').split('?')[0].replace(/\/$/, '').toLowerCase();
  const details = {
    '/visitmanagment/answerlist': '/visitmanagment/lists',
    '/visitmanagment/answerlistcustomers': '/visitmanagment/lists',
    '/surveymanagment/answerlist': '/suveymanagment/lists',
    '/surveymanagment/answerlistcustomers': '/suveymanagment/lists',
    '/elevatormanagement/buildingdetail': '/elevatormanagement/groupbuildinglist',
    '/elevatormanagement/elevatordetail': '/elevatormanagement/elevatorlist',
    '/customermanagement/detail': '/customermanagement/list',
    '/storemng/detail': '/storemng/listall',
    '/storemng/editstore': '/storemng/listall',
    '/supervision/answerlist': '/supervisionmanagment/lists',
    '/supervision/answerlistcustomer': '/supervisionmanagment/lists',
    '/ticket/ticketdetail': '/ticket/ticketlist',
    '/warehouse/waredetail': '/warehouse/warelist',
  };
  const route = Object.keys(details).find((prefix) => canonical(path).startsWith(prefix + '/'));
  return (
    canonical(menu.frontend_route_url) === canonical(route ? details[route] : path) ||
    (menu.children || []).some((child) => menuContainsRoute(child, path))
  );
}

// A menu group may ask to be shown as a single sidebar link whose children become tabs above the page
// (AdminMenu.frontend_route_params = {"display": "tabs"}); the children stay ordinary menu rows with their own grants.
export function isTabGroup(menu) {
  const params = menu && menu.frontend_route_params;
  return !!(params && params.display === 'tabs' && (menu.children || []).length);
}

// The tab group containing a page, with its tabs, or null.
export function tabsForRoute(menus, path) {
  const find = (items) => {
    for (const item of items || []) {
      if (isTabGroup(item) && menuContainsRoute(item, path)) return item;
      const inner = find(item.children);
      if (inner) return inner;
    }
    return null;
  };
  const group = find(menus);
  return group ? { group, tabs: group.children } : null;
}

// Every navigable leaf as { id, title, trail, path, menu } for search; a group's own link duplicates its
// first child, so only leaves (including the tabs of a tab group) are listed.
export function searchableEntries(menus) {
  const entries = [];
  const walk = (items, trail) => (items || []).forEach((item) => {
    const hasChildren = (item.children || []).length > 0;
    const label = item.verbose_name || item.name || '';
    if (item.frontend_route_url && !hasChildren) {
      entries.push({ id: String(item.id), title: label, trail, path: item.frontend_route_url, menu: item });
    }
    walk(item.children, trail.concat(label));
  });
  walk(menus, []);
  return entries;
}

// The menu entry for a page: an exact destination wins, otherwise the deepest item containing it.
export function menuForRoute(menus, path) {
  const canonical = (value) => (value || '').split('?')[0].replace(/\/$/, '').toLowerCase();
  const flat = [];
  const walk = (items, depth) => items.forEach((item) => { flat.push({ item, depth }); walk(item.children || [], depth + 1); });
  walk(menus || [], 0);
  const exact = flat.filter(({ item }) => canonical(item.frontend_route_url) === canonical(path));
  const found = (exact.length ? exact : flat.filter(({ item }) => menuContainsRoute(item, path)))
    .sort((a, b) => b.depth - a.depth)[0];
  return found ? found.item : null;
}

export function menuIconSource(menu, active) {
  const source = active
    ? menu.active_icon || menu.deactive_icon
    : menu.deactive_icon || menu.active_icon;
  if (!source) return '';
  if (/^(https?:|data:)/.test(source)) return source;
  return process.env.VUE_APP_SAAN_APP_PATH.replace(/\/$/, '') + '/' + source.replace(/^\//, '');
}
