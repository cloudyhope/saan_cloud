const fs = require('fs');
const vm = require('vm');
const assert = require('assert').strict;
const crypto = require('crypto');
const config = { accessToken: 'Bearer local-test', assignments: [], navigation: [], selectedProject: null };
let logout = 0, send, sent;
const store = { state: { userConfig: config }, commit(name, value) {
  if (name.endsWith('/setAssignments')) config.assignments = value;
  if (name.endsWith('/setNavigation')) { config.navigation = value.items; config.navigationProject = value.project; }
  if (name.endsWith('/setProjectInfo')) config.selectedProject = value;
  if (name.endsWith('/clearAllConfigs')) logout++;
} };
const savedKeys = new Map();
const context = vm.createContext({ window: { localStorage: { getItem: key => savedKeys.get(key) || null, setItem: (key, value) => savedKeys.set(key, value), removeItem: key => savedKeys.delete(key) }, crypto: { randomUUID: crypto.randomUUID, getRandomValues: bytes => crypto.randomFillSync(bytes) } }, Uint8Array, URLSearchParams, process: { env: { VUE_APP_SAAN_APP_PATH: 'http://localhost:18110/' } }, axios: async options => { sent = options; return send(options); }, store, router: { currentRoute: { name: 'home' }, replace: async () => {} }, console });
function load(path) {
  const source = fs.readFileSync(path, 'utf8').replace(/^import .*;\r?\n/gm, '').replace(/export default class /, 'class ').replace(/export /g, '');
  vm.runInContext(source, context, { filename: path });
}
load('src/utils/clientRequests.js'); load('src/utils/fieldSession.js'); load('src/api/apiServiceLayer.js');
const run = code => vm.runInContext(code, context);
(async () => {
  assert.match(run('requestKey()'), /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/);
  assert.equal(run('pageRows({results: [1, 2]}).length'), 2);
  assert.equal(run('pageRows(null).length'), 0);
  const persisted = run('persistentRequestKey("user.project.building", {type: 1, buildings: [2]})');
  run('pendingKeys.clear()');
  assert.equal(run('persistentRequestKey("user.project.building", {type: 1, buildings: [2]})'), persisted);
  assert.notEqual(run('persistentRequestKey("other.project.building", {type: 1, buildings: [2]})'), persisted);
  run(`clearRequestKey("user.project.building", "${persisted}")`);
  assert.notEqual(run('persistentRequestKey("user.project.building", {type: 1, buildings: [2]})'), persisted);
  assert.equal(run('errorMessage({status: 400, data: {buildings: [{elevators: ["bad selection"]}]}})'), 'bad selection');
  send = async () => ({ status: 201, data: {} });
  await run('new ApiServiceLayer().post("/api/service/create/", "core", {id: 1})');
  assert.equal(sent.url, 'http://localhost:18110/core/api/service/create/');
  assert.equal(sent.headers.Authorization, 'Bearer local-test');
  await run('new ApiServiceLayer().auth_post("/v1/token/", "api", {})');
  assert.equal(sent.headers.Authorization, undefined);
  send = async () => { throw { response: { status: 403, data: { detail: 'forbidden' } } }; };
  assert.equal((await run('new ApiServiceLayer().patch("api/items/1/", "", {})')).status, 403);
  assert.equal(logout, 0);
  send = async () => { throw new Error('offline'); };
  assert.equal((await run('new ApiServiceLayer().delete("api/items/1/", "")')).status, 0);
  send = async () => { throw { response: { status: 401, data: {} } }; };
  await run('new ApiServiceLayer().get("api/items/", "")');
  assert.equal(logout, 1);
  const membership = { project: { id: 42, is_active: true }, role: { id: 99, is_active: true, priority: 7 } };
  send = async options => ({ status: 200, data: options.url.includes('/auth/me/') ? [membership] : [{ route: 'home', is_landing: true }, { route: 'home' }, { route: 'clientVisits' }] });
  assert.equal(await run('enterSession(new ApiServiceLayer())'), 'home');
  assert.equal(config.selectedProject, 42);
  assert.equal(config.navigation.length, 2);
  assert.equal(run('requiredMenu("buildingDetail")'), 'home');
  assert.equal(run('requiredMenu("surveyQuestions")'), 'tasks');
  assert.equal(run('landing([])'), 'noAccess');
  send = async () => ({ status: 200, data: [membership, { ...membership, project: { id: 43, is_active: true } }] });
  assert.equal(await run('enterSession(new ApiServiceLayer())'), 'projects');
  send = async () => ({ status: 200, data: [{ ...membership, project: { id: 42, is_active: false } }] });
  assert.equal(await run('enterSession(new ApiServiceLayer())'), 'noAccess');
  console.log('Field flow checks passed (API, UUID, validation, project selection, menu routing).');
})().catch(error => { console.error(error); process.exitCode = 1; });
