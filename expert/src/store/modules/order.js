export const order = {
	namespaced: true,
	state: {
		detailsOrder: {},
	},
	mutations: {
		setDetialsOrder(state, payload) {
			state.detailsOrder = payload;
		},
	
	},
};
