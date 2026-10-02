import axios from 'axios';
import store from '@/store/index';
import router from '../router';
// import Vue from 'vue';

// const toastDuration = 3000;
const baseURL = process.env.VUE_APP_SAAN_APP_PATH;
let refreshPromise = null;

async function refreshAccessToken() {
	const refresh = store.state.userConfig.refreshToken;
	if (!refresh) return false;
	if (!refreshPromise) {
		refreshPromise = axios.post(baseURL + '/api/v1/username/password/refresh/', { refresh })
			.then(({ data }) => {
				if (!data || !data.access) return false;
				store.commit('userConfig/setAccessToken', 'Bearer ' + data.access);
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
		try { await axios.post(baseURL + '/api/v1/username/password/logout/', { refresh }); }
		catch (_) { /* Clear the local session even when offline. */ }
	}
	clearLocalData();
}

const HttpMethods = Object.freeze({
	GET: 'get',
	POST: 'post',
	DELETE: 'delete',
	PUT: 'put',
	PATCH: 'patch',
	// UPDATE: "update",
});

// const visibleMessages = new Set();
// function showToast(message, type, duration) {
// 	if (!visibleMessages.has(message)) {
// 		visibleMessages.add(message);

// 		Vue.$toast.open({
// 			message: message,
// 			type: type,
// 			duration: duration,
// 			position: 'top',
// 		});

// 		setTimeout(() => {
// 			visibleMessages.delete(message);
// 		}, toastDuration);
// 	}
// }

function clearLocalData() {
	store.commit('userConfig/clearAllConfigs');
	store.commit('appConfig/openMenuMobile', false);
}

function handleError({ status }, isAuthorized) {
	switch (status) {
		case 401:
			if (isAuthorized) {
				clearLocalData();
				if (router.currentRoute.name !== 'login') router.push({ name: 'login' });
			}

		// use refresh token for renewing the access token
			break;
		case 403:

			// TODO: remove the magic
			break;
	}

	// showToast(data.detail, 'default', toastDuration);
}

async function apiRequest({ method, url, service, headers, data, queryString, isAuthorized }) {
	const apiUrl = baseURL + service + url;
	const token = store.state.userConfig.accessToken;
	//   const refreshToken = store.state.userConfig.refreshToken;

	headers = {
		...headers,
		...(token && isAuthorized && { Authorization: token }),
	};

	try {
		switch (method) {
			case HttpMethods.GET:
				return await axios.get(apiUrl + queryString, {
					headers: headers,
				});
			case HttpMethods.POST:
				return await axios.post(apiUrl, data, {
					headers: headers,
				});
			case HttpMethods.DELETE:
				return await axios.delete(apiUrl, {
					headers: headers,
				});
			case HttpMethods.PUT:
				return await axios.put(apiUrl, data, {
					headers: headers,
				});
				case HttpMethods.PATCH:
				return await axios.patch(apiUrl, data, {
					headers: headers,
				});
			default:
				throw new Error('Unsupported HTTP method');
		}
	} catch (error) {
		let response = error.response || { status: 0, data: { detail: 'ارتباط با سرور برقرار نشد. دوباره تلاش کنید.' } };
		if (isAuthorized && response.status === 401 && await refreshAccessToken()) {
			try {
				return await axios({ method, url: apiUrl + (queryString || ''), data,
					headers: { ...headers, Authorization: store.state.userConfig.accessToken } });
			} catch (retryError) {
				response = retryError.response || response;
			}
		}
		handleError(response, isAuthorized);
		return response;
	}
}

export default {
	error_code: null,
	getErrorMessage(response) {
		if (response.status === 0) return 'ارتباط با سرور برقرار نشد. دوباره تلاش کنید.';
		if (response.status === 403) return 'دسترسی به این بخش برای حساب شما فعال نیست.';
		if (response.status === 404) return 'اطلاعات یا سرویس درخواستی پیدا نشد.';
		return 'دریافت اطلاعات انجام نشد. دوباره تلاش کنید.';
	},
	get: async (url, service = '', headers = {}, queryString = '', isAuthorized = true) => {
		return await apiRequest({
			method: HttpMethods.GET,
			url: url,
			service: service,
			headers: headers,
			queryString: queryString,
			isAuthorized: isAuthorized,
		});
	},
	post: async (url, service = '', data, headers = {}, isAuthorized = true) => {
		return await apiRequest({
			method: HttpMethods.POST,
			url: url,
			service: service,
			headers: headers,
			data: data,
			isAuthorized: isAuthorized,
		});
	},
	delete: async (url, service = '', headers = {}, isAuthorized = true) => {
		return await apiRequest({
			method: HttpMethods.DELETE,
			url: url,
			service: service,
			headers: headers,
			isAuthorized: isAuthorized,
		});
	},
	put: async (url, service = '', data, headers = {}, isAuthorized = true) => {
		return await apiRequest({
			method: HttpMethods.PUT,
			url: url,
			service: service,
			headers: headers,
			data: data,
			isAuthorized: isAuthorized,
		});
	},
	patch: async (url, service = '', data, headers = {}, isAuthorized = true) => {
		return await apiRequest({
			method: HttpMethods.PATCH,
			url: url,
			service: service,
			headers: headers,
			data: data,
			isAuthorized: isAuthorized,
		});
	},
};
