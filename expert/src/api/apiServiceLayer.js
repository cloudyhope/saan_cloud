import axios from 'axios';
import store from '@/store/index';
import router from '../router';

const apiRoot = String(process.env.VUE_APP_SAAN_APP_PATH || '').replace(/\/+$/, '');
let refreshPromise = null;

async function refreshAccessToken() {
  const refresh = store.state.userConfig.refreshToken;
  if (!refresh) return false;
  if (!refreshPromise) {
    refreshPromise = axios.post(`${apiRoot}/api/v1/username/password/refresh/`, { refresh })
      .then(({ data }) => {
        if (!data || !data.access) return false;
        store.commit('userConfig/setAccessToken', `Bearer ${data.access}`);
        if (data.refresh) store.commit('userConfig/setRefreshToken', data.refresh);
        return true;
      })
      .catch(() => false)
      .finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

export async function logoutSession() {
  const refresh = store.state.userConfig.refreshToken;
  if (refresh) {
    try {
      await axios.post(`${apiRoot}/api/v1/username/password/logout/`, { refresh });
    } catch (_) { /* Local session is still cleared below. */ }
  }
  store.commit('userConfig/clearAllConfigs');
}

export default class ApiServiceLayer {
  async request(method, url, service = '', data, headers = {}, isAuthorized = true, responseType = 'json') {
    const parts = [process.env.VUE_APP_SAAN_APP_PATH, service]
      .filter(Boolean).map(part => String(part).replace(/^\/+|\/+$/g, ''));
    parts.push(String(url).replace(/^\/+/, ''));
    const fullHeaders = { 'saanapp-client': 'web-app', ...headers };
    const token = store.state.userConfig.accessToken;
    if (isAuthorized && token) fullHeaders.Authorization = token;
    try {
      const response = await axios({ method, url: parts.join('/'), data, headers: fullHeaders, responseType });
      if (response.data && response.data.code === 200) response.data.status = 'OK';
      return response;
    } catch (error) {
      let response = error.response || { status: 0, data: { detail: 'ارتباط برقرار نشد. اتصال اینترنت را بررسی کنید و دوباره تلاش کنید.' } };
      if (isAuthorized && response.status === 401) {
        if (await refreshAccessToken()) {
          try {
            return await axios({ method, url: parts.join('/'), data, responseType,
              headers: { ...fullHeaders, Authorization: store.state.userConfig.accessToken } });
          } catch (retryError) {
            response = retryError.response || response;
          }
        }
        store.commit('userConfig/clearAllConfigs');
        if (router.currentRoute.name !== 'login') router.replace({ name: 'login' }).catch(() => {});
      }
      return response;
    }
  }
  get(url, service = '', headers = {}, queryStrings = '', isAuthorized = true) {
    return this.request('get', url + (queryStrings || ''), service, undefined, headers, isAuthorized);
  }
  getBlob(url) {
    return this.request('get', url, '', undefined, {}, true, 'blob');
  }
  auth_post(url, service = '', data, headers = {}) {
    return this.request('post', url, service, data, headers, false);
  }
  post(url, service = '', data, headers = {}, isAuthorized = true) {
    return this.request('post', url, service, data, headers, isAuthorized);
  }
  put(url, service = '', data, headers = {}, isAuthorized = true) {
    return this.request('put', url, service, data, headers, isAuthorized);
  }
  patch(url, service = '', data, headers = {}, isAuthorized = true) {
    return this.request('patch', url, service, data, headers, isAuthorized);
  }
  delete(url, service = '', headers = {}, isAuthorized = true) {
    return this.request('delete', url, service, undefined, headers, isAuthorized);
  }
}
