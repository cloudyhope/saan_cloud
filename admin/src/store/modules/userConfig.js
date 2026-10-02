export const userConfig = {
	namespaced: true,
	state: {
		accessToken: '',
		refreshToken: '',
		otpId: '',
		loginTempToken: '',
		userPhoneNumber: '',
		userInfo: null,
		vinData: null,
		selectedItem: null,
		setProjectId:null,
		role:null
	},
	mutations: {
		setAccessToken(state, payload) {
			state.accessToken = payload;
		},
		setRefreshToken(state, payload) {
			state.refreshToken = payload;
		},
		setOtpId(state, payload) {
			state.otpId = payload;
		},
		setLoginTempToken(state, payload) {
			state.loginTempToken = payload;
		},
		setUserPhoneNumber(state, payload) {
			state.userPhoneNumber = payload;
		},
		setUserInfo(state, payload) {
			state.userInfo = payload;
		},
		setProjectInfo(state, payload) {
			state.setProjectId = payload;
		},
		setVinData(state, payload) {
			state.vinData = payload;
		},
		setSelectedItem(state, payload) {
			state.selectedItem = payload;
		},
		setUserRole(state, payload) {
			state.role = payload;
		},
		clearAllConfigs(state) {
			Object.assign(state, {
				accessToken: '', refreshToken: '', otpId: '', loginTempToken: '',
				userPhoneNumber: '', userInfo: null, vinData: null, selectedItem: null,
				setProjectId: null, role: null,
			});
		},
	},
};
