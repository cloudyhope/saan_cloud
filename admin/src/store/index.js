import Vue from 'vue';
import Vuex from 'vuex';
import VuexPersistence from 'vuex-persist';
import { appConfig } from './modules/appConfig';
import { userConfig } from './modules/userConfig';
import { order } from './modules/order';

Vue.use(Vuex);

const vuexLocal = new VuexPersistence({
	key: 'cp-seller-panel',
	storage: window.localStorage,
	reducer: (state) => ({
		userConfig: state.userConfig,
		appConfig: { closeMenu: state.appConfig.closeMenu, mobileMobile: state.appConfig.mobileMobile },
		order: state.order,
	}),
});

export default new Vuex.Store({
	modules: { appConfig, userConfig, order },
	plugins: [vuexLocal.plugin],
});
