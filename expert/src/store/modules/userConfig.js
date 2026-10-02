export const userConfig = {
  namespaced: true,
  state: {
    accessToken: null,
    refreshToken: null,
    otpId: null,
    loginTempToken: null,
    userPhoneNumber: null,
    userInfo: null,
    assignments: [],
    navigation: [],
    navigationProject: null,
    selectedProject:null,
    selectedItem: null,
    ckeckCartRoute: null,
    checkProfileRoute: null,
    checkSaanAppPlusRoute: null,
  },
  mutations: {
    setAssignments(state, payload) { state.assignments = payload; },
    setNavigation(state, payload) { state.navigation = payload.items; state.navigationProject = payload.project; },
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
      state.selectedProject = payload;
      state.navigation = [];
      state.navigationProject = null;
    },
    setCartRoute(state, payload) {
      state.ckeckCartRoute = payload;
    },
    setProfileRoute(state, payload) {
      state.checkProfileRoute = payload;
    },
    setSaanAppPlusCartRoute(state, payload) {
      state.checkSaanAppPlusRoute = payload;
    },
    setSelectedItem(state, payload) {
      state.selectedItem = payload;
    },
    clearCartRoute(state) {
      state.ckeckCartRoute = null;
    },
    clearProfileRoute(state) {
      state.checkProfileRoute = null;
    },
    clearSaanAppPlusRoute(state) {
      state.checkSaanAppPlusRoute = null;
    },
    clearAllConfigs(state) {
      state.accessToken = null;
      state.refreshToken = null;
      state.userPhoneNumber = null;
      state.loginTempToken = null;
      state.otpId = null;
      state.selectedProject = null
      state.userInfo = null;
      state.assignments = [];
      state.navigation = [];
      state.navigationProject = null;
      state.selectedItem = null;
    },
    clearLoginToken(state) {
      state.loginTempToken = null;
      state.otpId = null;
    }
  },
};
