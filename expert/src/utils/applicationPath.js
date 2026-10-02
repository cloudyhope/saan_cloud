const PATH = {

	SERVICE_NAME: {
		ORDER: 'core',
		AUTH: 'core',
		EMPTY:'',
		UTILS: "utils",
		CORE:"core",
		WALLET:"wallet"

	},
	RELATIVE_PATH: {
		GET: {
			USER_DETAIL:'/api/auth/user_detail/',
			VISIT_LIST:'/api/promoter/open_visits/list/',
			VISIT_PAGE_SETTING:'/api/promoter/visit_page_settings/',
			GET_QUESTIONS:'/api/promoter/questions/list/visit/',
			GET_IMAGES_ALBUM:'/api/promoter/visit/photo_history/',
			GET_VISIT_HISTORY:'/api/promoter/visit/history/',
			PHOTO_DESC: '/api/admin/retrive_photo_type/',
			PROVINCE_LIST:'/api/province/list/',
			CITY_LIST:'/api/city/list/',
			SURVEY_QUESTIONS:'/api/promoter/survey_question/list/',
			GET_SURVEY_IMAGE:'/api/promoter/survey_photo/list_create/',
			GT_SURVEY_IMAGE_DESC:'/api/promoter/survey_photo_type/edits/',
			PROJECT_LIST:'/api/promoter/project_list/',
			GET_PROJECT_NAME:'/api/active_project/retrieve/',
			GET_GUIDELINE:'config/files/list_create/',
			GET_USER_DETAIL:'/api/auth/me/',
			WAREHOUSE_LIST:'api/warehouse/v1/aggregated/user/list/',
			WAREHOUSE_VISIT_PAGE_SETTING:'api/warehouse/v1/aggregated/visit_page_settings/',
			VISIT_TYPE:'/api/admin/visit_type/list_create/',
			NAVBAR_LIST: "config/navbar/List/",
			MEDIA_LIST: "config/Media/List/",
			MEDIA_TYPE_LIST: "config/MediaType/List/",
			VISIT_RETRIEVE:"/api/visit/retrieve/",
			WALLET_GET_QR_CODE: "wallet/invoice/get_qr_code/",
			WALLET_SIGNATURE:'wallet/get_signature/',
			WALLET_RECEIPT_RETRIEVE:'/api/v1/wallet_receipt/retrieve/',
			WALLET_INVOICE_BUYER_RETRIEVE:'/invoice/client/retrieve/',

		},
		POST: {
			PHONE_NUMBER_OTP_REQ: '/api/auth/otp/request/',
			PASSWORD_AUTH: '/v1/username/password/token/',
			OTP_VERIFY: '/api/auth/otp/verify/',
			UPLOAD_IMAGE:'/api/promoter/open_visit/upload_image/',
			POST_QUESTIONS:'/api/promoter/answer_to_question/',
			SURVEY_VERIFICATION_SEND_CODE:'/api/promoter/verification_code/request/',
			SURVEY_OTP_VALIDATE_VERIFICATION:'/api/promoter/verification_code/validate/',
			UPLOAD_SURVEY_PHOTOS:'/api/promoter/upload_survey_photo/',
			POST_SURVEY_QUESTIONS:'/api/promoter/answer_to_survey_question/',
			WARE_TRANSACTION:'api/warehouse/v1/ware_transaction/ez_create/',
			PERSONAL_INFO_VALIDATE:'api/micro/personalinfo/validate/',
			SERVICE_REQUEST_CREATE: "core/api/service_request/create/",
			INVOICE_CODE_REQUEST:'/invoice/code_request/',
			INVOICE_CODE_VALIDATE:'/invoice/code_validate/',
		},
		MULTI: {
			GET_STATUS_QUESTIONS:'/api/promoter/open_visit/change_status/',
			SURVEY_LIST:'/api/promoter/survey/list_create/',
			SURVEY_FILL_OUT:'/api/promoter/survey_fill_out/list_create/',
			SURVEY_QUESTION_TYPE:'/api/promoter/survey_page_settings/',
			SURVEY_PHOTO_TYPE:'/api/promoter/survey_photo/list_create/',
			SURVEY_FILL_OUT_EDIT:'/api/promoter/survey_fill_out/edits/',
			SURVEY_DELETE_IMG:'/api/admin/survey_photo/edits/',
			SUPERVISOR_LIST_CREATE:'/api/auth/supervisor/list_create/',
			SUPERVISION_VISIT_LIST:'/api/supervisor/supervision_visits/list/',
			AUTH_IMAGE:'/api/promoter/known_image/list_create/',
			PHOTO_EDIT:'/api/admin/photo_edit/',
			CREATE_ACTION_PLAN: '/api/admin/action_plan/create/',
			BULK_UPDATE:'/api/admin/action_plan/bulk_update/',
			VISIT_DETAIL_EDIT:'/api/admin/visit_edit/',
			PERSONAL_INFO_SET_MAIN:'api/micro/personalinfo/set_main/',
			CONVERSATION_LIST_CREATE: "/api/v1/conversation/list_create/",
			STORE_SETTING: "/api/auth/me/",
			BUILDING_LIST_CREATE: "api/visit/BuildingListCreate/",
			BUILDING_CLIENT_LIST_CREATE: "api/visit/BuildingClientListCreate/",
			WALLET_INVOICE_EXPERT_LIST_CREATE:'wallet/invoice/expert/list_create/',
			BUILDING_LIST_CREATE_CLIENT: "api/visit/BuildingListCreate/",
			BUILDING_EDITS: "api/visit/BuildingEdits/",



		},
		DELETE: {
			DELETE_IMAGE:'/api/promoter/visit/delete_photo/'
		}
	},
};

module.exports = PATH;
