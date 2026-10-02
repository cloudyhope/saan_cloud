import velocity from 'velocity-animate';
import Notifications from 'vue-notification';
import vuePersianFilters from 'vue-persian-filters';
import ActionIcon from '@/components/ActionIcon/index.vue';

const GlobalComponents = {
  // use packages
  install(Vue) {
    Vue.component('ActionIcon', ActionIcon);
    Vue.use(Notifications, { velocity });
    Vue.use(vuePersianFilters);
  },
};

export default GlobalComponents;
