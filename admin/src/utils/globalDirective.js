import AutoFocus from "../directives/focus.js";

const GlobalDirectives = {
  install(Vue) {
    Vue.directive("focus", AutoFocus);
  }
};


export default GlobalDirectives