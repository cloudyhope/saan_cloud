export const appConfig = {
	namespaced: true,
	state: {
		closeMenu: false,
		error: '',
		mobileMobile: false,
		// Sidebar menu of the selected project (not persisted); headers reuse its icons.
		menu: [],
	},
	mutations: {
		changeMenuStatus(state, payload) {
			state.closeMenu = payload;
		},
		setMenu(state, payload) {
			state.menu = payload;
		},
		openMenuMobile(state, payload) {
			state.mobileMobile = payload;
		},
		setError(state, payload) {
			state.error = payload;
			setTimeout(() => {
				state.error = null;
			}, 3000);
		},
	},
};
