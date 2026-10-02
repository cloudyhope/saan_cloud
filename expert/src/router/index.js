import Vue from "vue";
import VueRouter from "vue-router";
import store from "@/store/index";
import ApiServiceLayer from '@/api/apiServiceLayer';
import { enterSession, navigation, landing, requiredMenu } from '@/utils/fieldSession';

Vue.use(VueRouter);

const PUBLIC_ROUTES = ["login", "password-login"];
const OTP_ROUTES = ["verify"];

const routes = [
  { path: '/no-access', name: 'noAccess', component: () => import('@/views/NoAccess.vue') },
  {
    path: "/",
    name: "",
    redirect: "/login",
  },
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/Login/index.vue"),
  },
  {
    path: "/password-login",
    name: "password-login",
    component: () => import("@/views/Login/password.vue"),
  },
  {
    path: "/verify",
    name: "verify",
    component: () => import("@/views/Verify/index.vue"),
  },
    {
      path: "/projects",
      name: "projects",
      component: () => import("@/views/Projects/selectProject.vue"),
    },
      
  {
    path: "/layout",
    name: "/layout",
    redirect: "/dashboard",
    component: () => import("@/layout/Layout.vue"),
    children: [
      { path: '/client/visits', name: 'clientVisits', component: () => import('@/views/Client/Visits/index.vue') },
      { path: '/client/visits/:id', name: 'clientVisitDetail', component: () => import('@/views/Client/Visits/detail.vue') },
      { path: '/client/warranty', name: 'clientWarranty', component: () => import('@/views/Client/Warranty/index.vue') },
      { path: '/client/support', name: 'clientSupport', component: () => import('@/views/Client/Support/index.vue') },
      {
        path: "/home",
        name: "home",
        // meta: {
        //   title: "لیست ویزیت‌ها",
        // },
       
        component: () => import("@/views/Client/Home/index.vue"),
      },
      {
        path: "/notifications",
        name: "notif",
        // meta: {
        //   title: "لیست ویزیت‌ها",
        // },
       
        component: () => import("@/views/Client/Notification/index.vue"),
      },
      { path: '/Notification', redirect: { name: 'notif' } },
      {
        path: "/tasks",
        name: "tasks",
        // meta: {
        //   title: "لیست ویزیت‌ها",
        // },
       
        component: () => import("@/views/Home/index.vue"),
      },
      {
        path: "/wares",
        name: "wares",
        // meta: {
        //   title: "لیست پرسشنامه ها",
        // },
        component: () => import("@/views/Wares/index.vue"),
      },
      {
        path: "/edu",
        name: "edu",
        // meta: {
        //   title: "آکادمی",
        // },
        component: () => import("@/views/Academy/index.vue"),
      },
      {
        path: "/wallet",
        name: "wallet",
        // meta: {
        //   title: "حساب کاربری",
        // },
        component: () => import("@/views/Client/Invoice/index.vue"),
      },
      {
        path: "/setting",
        name: "setting",
        // meta: {
        //   title: "حساب کاربری",
        // },
        component: () => import("@/views/SharedAccount.vue"),
      },
      
      
    ],
  },
  
  {
    path: "/visitDetail/:id",
    name: "storeDetail",

    component: () => import("@/views/Store/index.vue"),
  },
  { path: "/visitchat/:id", name: "visitChat", component: () => import("@/views/VisitChat/index.vue") },
  { path: "/client/visitchat/:id", name: "clientVisitChat", component: () => import("@/views/VisitChat/index.vue") },
  { path: "/visitparts/:id", name: "visitParts", component: () => import("@/views/Wares/partRequests.vue") },
  {
    path: "/supervisordetail/:id",
    name: "superVisorDetail",

    component: () => import("@/views/Supervisor/superVisorDetail.vue"),
  },
  {
    path: "/supervisorpromoterview/:id",
    name: "superVisorPromoterView",

    component: () => import("@/views/Supervisor/superVisorPromoterView.vue"),
  },
 
  {
    path: "/pickimage/:minImg/:type/:id",
    name: "pickImage",
    meta: {
      title: "بارگزاری تصویر",
    },
    component: () => import("@/views/Image/pickImage.vue"),
  },
  {
    path: "/supervisorimage/:minImg/:type/:id",
    name: "superVisorImage",
    meta: {
      title: "بارگزاری تصویر",
    },
    component: () => import("@/views/Supervisor/superVisorImg.vue"),
  },
  {
    path: "/supervisorimageview/:minImg/:type/:id",
    name: "superVisorImageView",
    meta: {
      title: "مشاهده تصویر",
    },
    component: () => import("@/views/Supervisor/superVisorImgView.vue"),
  },
  
  {
    path: "/generalquestion/:type/:id",
    name: "generalQuestion",
   
    component: () => import("@/views/Question/generalQuestion.vue"),
  },
  {
    path: "/supervisorvisithistory",
    name: "superVisorVisitHistory",
    meta: {
      title: "تاریخچه ویزیت",
    },
    component: () => import("@/views/Supervisor/superVisorVisitHistory.vue"),
  },
  {
    path: "/surveydetail/",
    name: "surveyList",
   
    component: () => import("@/views/Survey/index.vue"),
  },
  {
    path: "/surveydetail/:id",
    name: "surveyDetail",
   
    component: () => import("@/views/Survey/surveyDetail.vue"),
  },
  {
    path: "/surveydetailinvisit/:visit_id/:fill_id",
    name: "surveyDetailInVisit",
    
    component: () => import("@/views/Survey/surveyDetail.vue"),
  },
  {
    path: "/guideline",
    name: "guideLine",
    
    component: () => import("@/views/Guideline/index.vue"),
  },
  {
    path: "/actionplan",
    name: "actionPlan",
    meta: {
      title: "برنامه ی جدید",
    },
    component: () => import("@/views/Supervisor/actionPlan.vue"),
  },
  {
    path: "/visithistory",
    name: "visitHistory",
    meta: {
      title: "تاریخچه ویزیت",
    },
    component: () => import("@/views/visitHistory/index.vue"),
  },
  {
    path: "/surveyquestions/:surveyId/:id",
    name: "surveyQuestions",
   
    component: () => import("@/views/Survey/surveyQuestions.vue"),
  },
  {
    path: "/surveyImage/:surveyId/:id",
    name: "surveyImage",
    meta: {
      title: "بارگزاری تصویر",
    },
    component: () => import("@/views/Survey/surveyImage.vue"),
  },
  {
    path: "/salequestion/:type/:id",
    name: "saleQuestion",
    
    component: () => import("@/views/Question/saleQuestion.vue"),
  },
  {
    path: "/shelfquestion/:type/:id",
    name: "shelfQuestion",
   
    component: () => import("@/views/Question/shelfQuestion.vue"),
  },
  {
    path: "/supervisorquestions/:type/:id",
    name: "superVisiorQuestions",
   
    component: () => import("@/views/Supervisor/superVisiorQuestions.vue"),
  },
  {
    path: "/supervisorquestionsView/:type/:id",
    name: "superVisiorQuestionsView",
   
    component: () => import("@/views/Supervisor/superVisiorQuestionsView.vue"),
  },
  {
    path: "/onlinechat/:id",
    name: "onlineChat",
    component: () => import("@/views/Client/Support/index.vue"),
  },
  {
    path: "/chathistory",
    name: "chatHistory",
    component: () => import("@/views/Client/Support/index.vue"),
  },
  {
    path: "/authentication/uploadimg",
    name: "authenticationPage",
    meta: {
      title: "احراز هویت",
    },
    component: () => import("@/views/Authentication/index.vue"),
  },
  {
    path: "/costs/:id",
    name: "costs",
    component: () => import("@/views/Costs/index.vue"),
  },
  {
    path: "/qrcode/:id",
    name: "qrCode",
    component: () => import("@/views/Costs/qrCode.vue"),
  },
  {
    path: "/qrcodescanner/:layer?",
    name: "qrCodeScanner",
    component: () => import("@/views/Client/Invoice/qrCodeScanner.vue"),
  },
  
  {
    path: "/usercreateinvoice/:id/:layer?",
    name: "userCreateInvoice",
    component: () => import("@/views/Client/Invoice/createInvoice.vue"),
  },
  {
    path: "/successpurchaseinvoice/:id",
    name: "successPurchaseInvoice",
    component: () => import("@/views/Client/Invoice/successPurchaseInvoice.vue"),
  },
  {
    path: "/visitwares",
    name: "visitWares",
    meta: {
      title: "ابزار و تجهیزات",
    },
    component: () => import("@/views/Wares/index.vue"),
  },
  {
    path: "/verifyprofile/:id",
    name: "verifyProfile",
    meta: {
      title: "استعلام",
    },
    component: () => import("@/views/Profile/verifyUser.vue"),
  },
  {
    path: "/rules",
    name: "rules",
    meta: {
      title: "قوانین و مقررات",
    },
    component: () => import("@/views/Profile/rules.vue"),
  },
  {
    path: "/faq",
    name: "faq",
    meta: {
      title: "سوالات متداول",
    },
    component: () => import("@/views/Profile/faq.vue"),
  },
  {
    path: "/contact",
    name: "contact",
    meta: {
      title: "تماس با ما",
    },
    component: () => import("@/views/Profile/contact.vue"),
  },
  {
    path: "/personalInfo",
    name: "personalInfo",
    meta: {
      title: "اطلاعات شخصی",
    },
    component: () => import("@/views/Profile/personalInfo.vue"),
  },
  {
    path: "/aboutus",
    name: "aboutUs",
    meta: {
      title: "درباره ما",
    },
    component: () => import("@/views/Profile/aboutUs.vue"),
  },
  {
    path: "/client/create-project",
    redirect: { name: 'clientSupport', query: { topic: 'building' } },
  },
  {
    path: "/client/explanation-request",
    redirect: { name: 'clientSupport', query: { topic: 'assignment' } },
  },
  {
    path: "/client/building/:id",
    name: "buildingDetail",
    component: () => import("@/views/Client/Building/index.vue"),
  },
  {
    path: "/academy/:id",
    name: "academyDetail",
    component: () => import("@/views/Academy/academyDetail.vue"),
  },
  
];

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes,
  scrollBehavior (to, from, savedPosition) {
    return { x: 0, y: 0 }
  }
});

router.beforeEach(async (to, from, next) => {
  const { accessToken, loginTempToken, otpId } = store.state.userConfig;
  const isAuthenticated = !!accessToken;
  const hasOtpSession = !!(loginTempToken && otpId);

  if (PUBLIC_ROUTES.includes(to.name)) {
    if (isAuthenticated) {
      try { return next({ name: await enterSession(new ApiServiceLayer()) }); }
      catch (error) { return next({ name: 'noAccess' }); }
    }
    return next();
  }

  if (OTP_ROUTES.includes(to.name)) {
    if (isAuthenticated) {
      try { return next({ name: await enterSession(new ApiServiceLayer()) }); }
      catch (error) { return next({ name: 'noAccess' }); }
    }
    if (hasOtpSession) {
      return next();
    }
    return next({ name: "login" });
  }

  if (!isAuthenticated) {
    return next({ name: "login" });
  }

  if (['projects', 'noAccess'].includes(to.name)) return next();
  try {
    const config = store.state.userConfig;
    if (!config.selectedProject) return next({ name: await enterSession(new ApiServiceLayer()) });
    const items = config.navigationProject === config.selectedProject && config.navigation
      ? config.navigation : await navigation(new ApiServiceLayer(), config.selectedProject);
    const allowedByLanding = (to.name === 'wallet' && items.some(item => item.route === 'home')) ||
      (to.name === 'notif' && items.some(item => ['home', 'tasks'].includes(item.route)));
    if (!allowedByLanding && !items.some(item => item.route === requiredMenu(to.name))) {
      const target = landing(items);
      return next({ name: target === to.name ? 'noAccess' : target });
    }
    return next();
  } catch (error) { return next({ name: 'noAccess' }); }
});

// Pages with a back button need to know whether an in-app page precedes them.
router.afterEach((to, from) => { if (from.name) window.__saanInAppNavigation = true; });

export default router;
