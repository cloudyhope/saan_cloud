import Vue from "vue";
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faUserSecret,
  faTimesCircle,
  faBell,
  faTimes,
  faCheck,
  faExclamationCircle,
  faTrashAlt,
  faUsers,
} from "@fortawesome/free-solid-svg-icons";
// import { faTimesCircle } from "@fortawesome/free-regular-svg-icons";

library.add([
  faUserSecret,
  faTimesCircle,
  faBell,
  faTimes,
  faCheck,
  faExclamationCircle,
  faTrashAlt,
  faUsers,
]);

Vue.component("font-awesome-icon", FontAwesomeIcon);
