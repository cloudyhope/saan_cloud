import Vue from 'vue';
import App from './App.vue';
import router from './router';
import './utils/globalLibraries';
import Store from './store/index';
import GlobalMethods from './utils/globalMethods';
import ApiServiceLayer from '@/api/apiServiceLayer';

import GlobalComponents from './utils/globalComponents';
import './utils/fontAwesome';
import GlobalDirectives from './utils/globalDirective';
import BootstrapVue from 'bootstrap-vue';
import VueNumeric from 'vue-numeric';
import VuePersianDatetimePicker from 'vue-persian-datetime-picker';


const Path = require('./utils/applicationPath');
Vue.use(GlobalComponents);
Vue.use(GlobalDirectives);
Vue.use(BootstrapVue);
Vue.use(VueNumeric);

Vue.prototype.$ApiServiceLayer = ApiServiceLayer;
Vue.config.productionTip = false;
Vue.prototype.$PATH = Path;
Vue.prototype.$STORE = Store;
Vue.prototype.$GlobalMethods = GlobalMethods;
Vue.use(VuePersianDatetimePicker, {
	name: 'date-picker',
	props: {
		format: 'YYYY-MM-DD HH:mm',
		displayFormat: 'jYYYY-jMM-jDD HH:mm',
	},
});

new Vue({
	router,
	render: (h) => h(App),
}).$mount('#app');

import '@/assets/css/record-details.css';
