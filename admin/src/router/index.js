import Vue from 'vue';
import VueRouter from 'vue-router';
import Store from '@/store/index';

Vue.use(VueRouter);

const routes = [
  {
    path: '/',
    name: '',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'login',
    meta: {
      title: 'ورود',
    },
    component: () => import('@/views/Login/index.vue'),
  },
  {
    path: '/password-login',
    name: 'password',
    meta: {
      title: 'ورود',
    },
    component: () => import('@/views/Login/password.vue'),
  },
  {
    path: '/verify',
    name: 'verify',
    meta: {
      title: 'تایید ورود',
    },
    component: () => import('@/views/Verify/index.vue'),
  },
  {
    path: '/projects',
    name: 'projects',
    meta: { title: 'انتخاب پروژه' },
    component: () => import('@/views/Projects/index.vue'),
  },
  {
    path: '/dashboard',
    name: '/layout',
    redirect: '/dashboard',
    component: () => import('@/layout/Layout.vue'),
    children: [
      {
        path: '/elevatormanagement/buildingdetail/:id',
        name: 'buildingDetail',
        meta: { title: 'جزئیات ساختمان', recordKind: 'building' },
        component: () => import('@/views/RecordDetail.vue'),
      },
      {
        path: '/elevatormanagement/elevatordetail/:id',
        name: 'elevatorDetail',
        meta: { title: 'جزئیات آسانسور', recordKind: 'elevator' },
        component: () => import('@/views/RecordDetail.vue'),
      },
      {
        path: '/customermanagement/detail/:id',
        name: 'customerDetail',
        meta: { title: 'جزئیات مشتری', recordKind: 'customer' },
        component: () => import('@/views/RecordDetail.vue'),
      },
      {
        path: '/storemng/detail/:id',
        name: 'storeDetail',
        meta: { title: 'جزئیات فروشگاه', recordKind: 'store' },
        component: () => import('@/views/RecordDetail.vue'),
      },
      {
        path: '/dashboard',
        name: 'dashboard',
        meta: {
          title: 'داشبورد',
        },
        component: () => import('@/views/Dashboard/index.vue'),
      },
      {
        path: '/notifications',
        name: 'notifications',
        meta: { title: 'اعلان‌ها' },
        component: () => import('@/views/Notifications/index.vue'),
      },
      {
        path: '/service-cases',
        name: 'serviceCases',
        meta: { title: 'گارانتی و تعمیرات' },
        component: () => import('@/views/ServiceCases/index.vue'),
      },
      {
        path: '/priority',
        name: 'priority',
        meta: { title: 'اولویت‌بندی خدمات' },
        component: () => import('@/views/Priority/index.vue'),
      },
      {
        path: '/test-dashboard',
        name: 'test-dashboard',
        meta: {
          title: 'داشبورد',
        },
        component: () => import('@/views/Dashboard/test.vue'),
      },
      {
        path: '/visitmanagment/lists',
        name: 'visitmanagmentLists',
        meta: {
          title: 'لیست ویزیت‌ها',
        },
        component: () => import('@/views/visitManagment/lists.vue'),
      },
      {
        path: '/visitmanagment/completeVisited',
        name: 'visitmanagmentCompleted',
        meta: {
          title: 'ویزیت‌های تکمیل شده',
        },
        component: () => import('@/views/visitManagment/completeVisited.vue'),
      },
      {
        path: '/visitmanagment/acceptedvisits',
        name: 'acceptedvisits',
        meta: {
          title: 'ویزیت‌های تایید شده',
        },
        component: () => import('@/views/visitManagment/acceptedVisits.vue'),
      },
      {
        path: '/visitmanagment/notcompeletevisits',
        name: 'notCompeleteVisits',
        meta: {
          title: 'ویزیت‌های تکمیل نشده',
        },
        component: () => import('@/views/visitManagment/notCompleteVisited.vue'),
      },
      {
        path: '/visitmanagment/answerlist/:id',
        name: 'answerList',
        meta: {
          title: 'جزییات ویزیت',
        },
        component: () => import('@/views/visitManagment/answerList.vue'),
      },
      {
        path: '/supervision/answerlist/:id',
        name: 'supervisionAnswerLists',
        meta: {
          title: 'جزییات سرکشی',
        },
        component: () => import('@/views/Supervision/supervisionAnswerLists.vue'),
      },
      {
        path: '/supervision/answerlistcustomer/:id',
        name: 'supervisionAnswerListCustomer',
        meta: {
          title: 'جزییات سرکشی',
        },
        component: () => import('@/views/Supervision/supervisionAnswerListCustomer.vue'),
      },
      {
        path: '/visitmanagment/answerlistcustomers/:id',
        name: 'answerListCustomers',
        meta: {
          title: 'جزییات ویزیت',
        },
        component: () => import('@/views/visitManagment/answerListCustomers.vue'),
      },
      {
        path: '/suveymanagment/lists',
        name: 'surveymanagmentLists',
        meta: {
          title: 'تمام نتایج',
        },
        component: () => import('@/views/surveyManagment/surveyList.vue'),
      },
      {
        path: '/suveymanagment/completesurvey',
        name: 'surveymanagmentCompleted',
        meta: {
          title: 'تکمیل ‌شده',
        },
        component: () => import('@/views/surveyManagment/completeSurvey.vue'),
      },
      {
        path: '/surveymanagment/acceptedsurvey',
        name: 'acceptedSurvey',
        meta: {
          title: 'تایید شده',
        },
        component: () => import('@/views/surveyManagment/acceptedSurvey.vue'),
      },
      {
        path: '/surveymanagment/notcompeletesurvey',
        name: 'notCompeleteSurvey',
        meta: {
          title: 'تکمیل نشده',
        },
        component: () => import('@/views/surveyManagment/notCompleteSurvey.vue'),
      },
      {
        path: '/surveymanagment/answerlist/:id',
        name: 'surveyAnswerList',
        meta: {
          title: 'جزئیات پرسشنامه',
        },
        component: () => import('@/views/surveyManagment/answerList.vue'),
      },
      {
        path: '/surveymanagment/answerlistcustomers/:id',
        name: 'surveyAnswerListCustomers',
        meta: {
          title: 'جزئیات پرسشنامه',
        },
        component: () => import('@/views/surveyManagment/answerListCustomers.vue'),
      },
      {
        path: '/supervisionmanagment/lists',
        name: 'supervisionManagmentLists',
        meta: {
          title: 'مدیرت سرکشی ها',
        },
        component: () => import('@/views/Supervision/supervisionManagmentLists.vue'),
      },
      {
        path: '/supervisionmanagment/completesupervision',
        name: 'completeSupervision',
        meta: {
          title: 'سرکشی ها تمام شده',
        },
        component: () => import('@/views/Supervision/completeSupervision.vue'),
      },
      {
        path: '/supervisionmanagment/acceptedsupervision',
        name: 'acceptedSupervision',
        meta: {
          title: 'سرکشی ها تایید شده',
        },
        component: () => import('@/views/Supervision/acceptedSupervision.vue'),
      },
      {
        path: '/supervisionmanagment/notcompeletesupervision',
        name: 'notCompeleteSupervision',
        meta: {
          title: 'سرکشی ها تایید نشده',
        },
        component: () => import('@/views/Supervision/notCompeleteSupervision.vue'),
      },
      {
        path: '/surveyresults/surveyresultscensus',
        name: 'surveyResultsCensus',
        meta: {
          title: 'شناسایی مشتری (Census)',
        },
        component: () => import('@/views/surveyResults/census.vue'),
      },
      {
        path: '/actionplan/newaction',
        name: 'newAction',
        meta: {
          title: 'ثبت برنامه جدید',
        },
        component: () => import('@/views/actionPlan/newAction.vue'),
      },
      {
        path: '/actionplan/listactionplan',
        name: 'listActionPlan',
        meta: {
          title: 'لیست برنامه ها',
        },
        component: () => import('@/views/actionPlan/listActionPlan.vue'),
      },
      {
        path: '/filemanagement/uploadfile',
        name: 'uploadFile',
        meta: {
          title: 'آپلود فایل',
        },
        component: () => import('@/views/FileManagement/UploadFile.vue'),
      },
      {
        path: '/filemanagement/filelist',
        name: 'fileList',
        meta: {
          title: 'لیست فایل ها',
        },
        component: () => import('@/views/FileManagement/fileList.vue'),
      },
      {
        path: '/Storeidentification',
        name: 'StoreIdentification',
        meta: {
          title: 'شناسایی مشتری',
        },
        component: () => import('@/views/Storeidentification/index.vue'),
      },
      {
        path: '/pic/poromotionpic',
        name: 'poromotionPic',
        meta: {
          title: 'تصاویر پروموشن',
        },
        component: () => import('@/views/Pic/poromotion.vue'),
      },
      {
        path: '/pic/tablopic',
        name: 'tablopic',
        meta: {
          title: 'تصاویر تابلو',
        },
        component: () => import('@/views/Pic/tablo.vue'),
      },
      {
        path: '/pic/visitpic/:id',
        name: 'visitPic',
        meta: {
          title: 'تصاویر ',
        },
        component: () => import('@/views/Pic/visitPic.vue'),
      },
      {
        path: '/pic/surveypic/:id',
        name: 'surveypic',
        meta: {
          title: 'تصاویر ',
        },
        component: () => import('@/views/Pic/surveyPic.vue'),
      },
      {
        path: '/pic/productpic',
        name: 'productpic',
        meta: {
          title: 'تصاویر محصولات',
        },
        component: () => import('@/views/Pic/productPic.vue'),
      },
      {
        path: '/pic/orderpic',
        name: 'orderpic',
        meta: {
          title: 'تصاویر چیدمان',
        },
        component: () => import('@/views/Pic/orderPic.vue'),
      },
      {
        path: '/pic/decorpic',
        name: 'decorPic',
        meta: {
          title: 'تصاویر دکور داخلی',
        },
        component: () => import('@/views/Pic/decorPic.vue'),
      },
      {
        path: '/storemanagement/brandshop',
        name: 'storeManagmentBrandShop',
        meta: {
          title: 'برند شاپ',
        },
        component: () => import('@/views/storeManagement/brandShop.vue'),
      },
      {
        path: '/storemanagement/chainstore',
        name: 'storeManagmentChainStore',
        meta: {
          title: 'مشتری زنجیره ای',
        },
        component: () => import('@/views/storeManagement/chainStore.vue'),
      },
      {
        path: '/storemanagement/multibrand',
        name: 'storeManagmentMultiBrand',
        meta: {
          title: 'مولتی برند',
        },
        component: () => import('@/views/storeManagement/multiBrand.vue'),
      },
      {
        path: '/storemanagement/storeacceptedvisits/:outlet',
        name: 'storeManagementAcceptedvisits',
        meta: {
          title: 'ویزیت‌های تایید شده',
        },
        component: () => import('@/views/storeManagement/storeAcceptedvisits.vue'),
      },
      {
        path: '/infractionsreport',
        name: 'infractionsReport',
        meta: {
          title: 'گزارش تخلفات برندشاپ',
        },
        component: () => import('@/views/Infractions/index.vue'),
      },
      {
        path: '/feedback',
        name: 'feedback',
        meta: {
          title: 'بازخورد ها',
        },
        component: () => import('@/views/Feedback/index.vue'),
      },
      {
        path: '/exportExcel',
        name: 'exportexcel',
        meta: {
          title: 'خروجی اکسل',
        },
        component: () => import('@/views/exportExcel/index.vue'),
      },
      {
        path: '/ticket/ticketlist',
        name: 'ticketList',
        meta: {
          title: 'فهرست تیکت‌ها',
        },
        component: () => import('@/views/Ticket/ticketList.vue'),
      },
      {
        path: '/ticket/newticket',
        name: 'newTicket',
        meta: {
          title: 'تیکت جدید',
        },
        component: () => import('@/views/Ticket/newTicket.vue'),
      },
      {
        path: '/ticket/ticketdetail/:id',
        name: 'ticketDetail',
        meta: {
          title: 'جزئیات تیکت',
        },
        component: () => import('@/views/Ticket/ticketDetail.vue'),
      },
      {
        path: '/warning/:id',
        name: 'warningPage',
        meta: {
          title: 'اعلان ها',
        },
        component: () => import('@/views/storeManagement/warnings.vue'),
      },
      {
        path: '/warningdetailpage/:id',
        name: 'warningDetailPage',
        meta: {
          title: 'جزییات اعلان',
        },
        component: () => import('@/views/storeManagement/warningDetailPage.vue'),
      },
      {
        path: '/usermanagement/list',
        name: 'userListPage',
        meta: {
          title: 'لیست کاربران',
        },
        component: () => import('@/views/UserManagement/userList.vue'),
      },
      {
        path: '/usermanagement/assignpromoter',
        name: 'assignPromoter',
        meta: {
          title: 'تخصیص نیروی اجرایی به سرپرست',
        },
        component: () => import('@/views/UserManagement/assignPromoter.vue'),
      },
      {
        path: '/usermanagement/add',
        name: 'userCreatePage',
        meta: {
          title: 'افزودن کاربر',
        },
        component: () => import('@/views/UserManagement/userAddEdit.vue'),
      },
      {
        path: '/usermanagement/edit/:pn',
        name: 'userEditPage',
        meta: {
          title: 'ویرایش کاربر',
        },
        component: () => import('@/views/UserManagement/userAddEdit.vue'),
      },
      {
        path: '/storeManagement/add',
        name: 'addStore',
        meta: {
          title: 'ایجاد مشتری',
        },
        component: () => import('@/views/storeManagement/addStore.vue'),
      },
      {
        path: '/storemng/listall',
        name: 'storeMngListAll',
        meta: {
          title: 'لیست مشتری',
        },
        component: () => import('@/views/StoreMng/listAll.vue'),
      },
      {
        path: '/storemng/list/:id',
        name: 'storeMngList',
        meta: {
          title: 'لیست مشتری',
        },
        component: () => import('@/views/StoreMng/list.vue'),
      },
      {
        path: '/storemng/add',
        name: 'storeMngAdd',
        meta: {
          title: 'ایجاد مشتری',
        },
        component: () => import('@/views/StoreMng/add.vue'),
      },
      {
        path: '/storemng/editstore/:id',
        name: 'editStore',
        meta: {
          title: 'ویرایش فروشگاه',
        },
        component: () => import('@/views/StoreMng/editStore.vue'),
      },
      {
        path: '/reports/:id',
        name: 'reports',
        meta: {
          title: 'گزارشات',
        },
        component: () => import('@/views/Reports/index.vue'),
      },
      {
        path: '/warehouse/create',
        name: 'createWareHouse',
        meta: {
          title: 'مدیریت انبار',
        },
        component: () => import('@/views/Warehouse/create.vue'),
      },
      {
        path: '/warehouse/part-requests',
        name: 'partRequests',
        meta: { title: 'درخواست‌های قطعه' },
        component: () => import('@/views/Warehouse/partRequests.vue'),
      },
      {
        path: '/assignment',
        name: 'assignment',
        meta: { title: 'تخصیص هوشمند' },
        component: () => import('@/views/Assignment/index.vue'),
      },
      {
        path: '/visitmanagment/visit-types',
        name: 'visitTypes',
        meta: { title: 'انواع خدمت' },
        component: () => import('@/views/visitManagment/visitTypes.vue'),
      },
      {
        path: '/warehouse/warelist',
        name: 'listWareHouse',
        meta: {
          title: 'لیست انبار',
        },
        component: () => import('@/views/Warehouse/list.vue'),
      },
      {
        path: '/warehouse/waredetail/:id',
        name: 'wareDetail',
        meta: {
          title: 'جزيیات انبار',
        },
        component: () => import('@/views/Warehouse/wareDetail.vue'),
      },
      {
        path: '/warehouse/transactionlist/:id',
        name: 'transactionList',
        meta: {
          title: 'جزيیات انبار',
        },
        component: () => import('@/views/Warehouse/transactionList.vue'),
      },
      {
        path: '/instruction',
        name: 'instruction',
        meta: {
          title: 'راهنما و آموزش',
        },
        component: () => import('@/views/Instruction/index.vue'),
      },
      {
        path: '/elevatormanagement/buildinglist',
        name: 'buildingList',
        meta: {
          title: 'لیست ساختمان ها',
        },
        component: () => import('@/views/ElevatorManagement/buildingList.vue'),
      },
      {
        path: '/elevatormanagement/crearebuilding/:id?',
        name: 'creareBuilding',
        meta: {
          title: 'ایجاد گروه ساختمان',
        },
        component: () => import('@/views/ElevatorManagement/creareBuilding.vue'),
      },
      {
        path: '/elevatormanagement/groupbuildinglist',
        name: 'groupBuildingList',
        meta: {
          title: 'گروه ساختمان ها',
        },
        component: () => import('@/views/ElevatorManagement/groupBuildingList.vue'),
      },
      {
        path: '/elevatormanagement/createelevator/:id',
        name: 'createElevator',
        meta: {
          title: 'ایجاد آسانسور',
        },
        component: () => import('@/views/ElevatorManagement/createElevator.vue'),
      },
      {
        path: '/elevatormanagement/elevatorlist',
        name: 'elevatorList',
        meta: {
          title: 'لیست آسانسور',
        },
        component: () => import('@/views/ElevatorManagement/ElevatorList.vue'),
      },
      {
        path: '/customermanagement/list',
        name: 'customerManagementList',
        meta: {
          title: 'لیست مشتریان',
        },
        component: () => import('@/views/CustomerManagement/list.vue'),
      },
      {
        path: '/customermanagement/create',
        name: 'customerManagementCreate',
        meta: {
          title: 'ایجاد مشتری',
        },
        component: () => import('@/views/CustomerManagement/create.vue'),
      },
      {
        path: '/walletmanagment/manageaccount',
        name: 'walletManageAccounts',
        meta: {
          title: 'مدیریت حساب ها',
        },
        component: () => import('@/views/WalletManagment/manageAccounts.vue'),
      },
      {
        path: '/walletmanagment/rechargewallet',
        name: 'rechargeWallet',
        meta: {
          title: 'شارژ کیف پول',
        },
        component: () => import('@/views/WalletManagment/rechargeWallet.vue'),
      },
      {
        path: '/medialist/list',
        name: 'mediaListList',
        meta: {
          title: 'لیست رسانه ها',
        },
        component: () => import('@/views/MediaList/list.vue'),
      },
      {
        path: '/medialist/create',
        name: 'mediaListCreate',
        meta: {
          title: 'ایجاد رسانه',
        },
        component: () => import('@/views/MediaList/create.vue'),
      },
    ],
  },
];

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
});

router.beforeEach((to, from, next) => {
  const token = Store.state.userConfig.accessToken;
  const publicRoute = ['login', 'password', 'verify'].includes(to.name);
  if (token && publicRoute) return next(Store.state.userConfig.setProjectId ? '/dashboard' : '/projects');
  if (!token && !publicRoute) return next('/login');
  if (to.name === 'verify' && !Store.state.userConfig.loginTempToken) return next('/login');
  if (token && !publicRoute && to.name !== 'projects' && !Store.state.userConfig.setProjectId) return next('/projects');
  next();
});

export default router;
