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

export function menuIconSource(menu, active) {
  const source = active
    ? menu.active_icon || menu.deactive_icon
    : menu.deactive_icon || menu.active_icon;
  if (!source) return '';
  if (/^(https?:|data:)/.test(source)) return source;
  return process.env.VUE_APP_SAAN_APP_PATH.replace(/\/$/, '') + '/' + source.replace(/^\//, '');
}
