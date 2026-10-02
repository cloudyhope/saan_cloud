import store from '@/store';
import { pageRows, errorMessage } from './clientRequests';
export async function assignments(api) {
  const response = await api.get('core/api/auth/me/');
  if (response.status !== 200) throw new Error(errorMessage(response));
  const rows = pageRows(response.data).filter(row => !row.is_deleted && row.project && row.project.is_active && row.role && row.role.is_active);
  store.commit('userConfig/setAssignments', rows);
  return rows;
}
export async function navigation(api, project) {
  const response = await api.get('config/navbar/List/?ordering=priority&p=' + project);
  if (response.status !== 200) throw new Error(errorMessage(response));
  const byRoute = new Map();
  pageRows(response.data).forEach(item => { if (item.route && !byRoute.has(item.route)) byRoute.set(item.route, item); });
  const items = Array.from(byRoute.values());
  store.commit('userConfig/setNavigation', { project, items });
  return items;
}
export function landing(items) {
  const supported = items.filter(item => ['home', 'clientVisits', 'clientWarranty', 'tasks', 'edu', 'wares', 'setting', 'wallet', 'notif'].includes(item.route));
  const item = supported.find(item => item.is_landing) || supported[0];
  return item ? item.route : 'noAccess';
}
export async function selectProject(api, project, rows = store.state.userConfig.assignments || []) {
  const membership = rows.filter(row => row.project.id === Number(project)).sort((a, b) => (a.role.priority || 0) - (b.role.priority || 0))[0];
  if (!membership) throw new Error('عضویت فعالی برای این پروژه پیدا نشد.');
  store.commit('userConfig/setProjectInfo', Number(project));
  store.commit('userConfig/setUserInfo', membership);
  return landing(await navigation(api, project));
}
export async function enterSession(api) {
  const rows = await assignments(api);
  const projects = [...new Set(rows.map(row => row.project.id))];
  if (!projects.length) return 'noAccess';
  if (projects.length > 1) return 'projects';
  return selectProject(api, projects[0], rows);
}
export function requiredMenu(route) {
  if (['home', 'buildingDetail', 'clientSupport',
       'qrCodeScanner', 'userCreateInvoice', 'successPurchaseInvoice'].includes(route)) return 'home';
  if (route === 'clientVisitDetail') return 'clientVisits';
  if (route === 'clientVisits' || route === 'clientWarranty') return route;
  if (['setting', 'verifyProfile', 'rules', 'faq', 'contact', 'personalInfo', 'aboutUs', 'authenticationPage'].includes(route)) return 'setting';
  if (['edu', 'academyDetail', 'guideLine'].includes(route)) return 'edu';
  if (['wares', 'visitWares'].includes(route)) return 'wares';
  if (route === 'wallet') return 'wallet';
  if (route === 'notif') return 'notif';
  return 'tasks';
}
