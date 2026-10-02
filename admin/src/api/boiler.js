import axios from 'axios';
import store from '@/store/index';
import router from '../router';
// import Vue from 'vue';

// const toastDuration = 3000;
const baseURL = process.env.VUE_APP_CAR_PIECE_PATH;

const HttpMethods = Object.freeze({
	GET: 'get',
	POST: 'post',
	DELETE: 'delete',
	PUT: 'put',
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
	localStorage.removeItem('cp_pwa');
	store.commit('userConfig/clearAllConfigs');
}

function handleError({ status, data }) {
    console.log("data is : ")
    console.log(data)
	switch (status) {
		case 401:
			// use refresh token for renewing the access token
			break;
		case 403:
			clearLocalData();
			// TODO: remove the magic
			router.push({ name: 'login' });
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
			default:
				throw new Error('Unsupported HTTP method');
		}
	} catch (error) {
		handleError(error.response);
		return await error.response;
	}
}

export default {
	error_code: null,
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
};
