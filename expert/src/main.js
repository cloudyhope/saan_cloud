import Vue from 'vue'
import App from './App.vue'
import './registerServiceWorker'
import './utils/globalLibraries'
import './assets/css/field-theme.css'
import './assets/css/visit-flow.css'
import '@mdi/font/css/materialdesignicons.css'
import ApiServiceLayer from '@/api/apiServiceLayer';
import router from './router'
import Store from './store/index';
import datePicker from '@alireza-ab/vue-persian-datepicker'

import vuetify from './plugins/vuetify'
const Path = require('./utils/applicationPath');

Vue.prototype.$ApiServiceLayer = new ApiServiceLayer();
Vue.prototype.$PATH = Path;
Vue.prototype.$STORE = Store;
Vue.component('date-picker', datePicker);

new Vue({
  router,
  vuetify,
  render: h => h(App)
}).$mount('#app')
