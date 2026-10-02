// Shared vocabulary and API steps for the field visit flow (detail, questions, photos, history).
import store from '@/store';

export const OPEN_STATES = ['0', '1', '5', '6'];

export const VISIT_STATUS = {
  '0': { label: 'آماده شروع', tone: 'ready', icon: 'mdi-play-circle-outline',
    hint: 'برای ثبت پاسخ و عکس، ابتدا مأموریت را شروع کنید.' },
  '1': { label: 'در حال انجام', tone: 'progress', icon: 'mdi-progress-wrench',
    hint: 'مراحل را تکمیل کنید؛ پس از کامل‌شدن موارد الزامی، مأموریت را پایان دهید.' },
  '2': { label: 'ثبت‌شده؛ در انتظار بررسی', tone: 'review', icon: 'mdi-timer-sand',
    hint: 'گزارش شما ثبت شد و پس از بررسی شرکت نتیجه اعلام می‌شود.' },
  '3': { label: 'تأیید شده', tone: 'done', icon: 'mdi-check-decagram',
    hint: 'گزارش این مأموریت تأیید شده است.' },
  '4': { label: 'رد شده', tone: 'danger', icon: 'mdi-close-octagon-outline',
    hint: 'گزارش این مأموریت رد شده و بسته است.' },
  '5': { label: 'برگشت برای اصلاح', tone: 'warning', icon: 'mdi-backup-restore',
    hint: 'گزارش برای اصلاح برگشت خورده است. موارد را اصلاح و دوباره ثبت کنید.' },
  '6': { label: 'متوقف شده', tone: 'muted', icon: 'mdi-pause-circle-outline',
    hint: 'این مأموریت متوقف شده است؛ با ادامه، وضعیت آن «در حال انجام» می‌شود.' },
};

export function visitStatus(status) {
  return VISIT_STATUS[status] || { label: 'نامشخص', tone: 'muted', icon: 'mdi-help-circle-outline', hint: '' };
}

export function faNumber(value) {
  if (value === null || value === undefined || value === '') return '';
  return Number(value).toLocaleString('fa-IR');
}

// Identifiers read as codes, so they are never grouped (۵۰۰۰۰۰۱, not ۵,۰۰۰,۰۰۱).
export function faId(value) {
  return value === null || value === undefined ? '' : Number(value).toLocaleString('fa-IR', { useGrouping: false });
}

export function faDate(value, withTime = false) {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '';
  return parsed.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric',
    ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}) });
}

export function dueInfo(visit) {
  if (!visit || !visit.has_due_date || !visit.due_date) return { label: 'بدون موعد مشخص', tone: 'muted' };
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const due = new Date(visit.due_date + 'T00:00:00');
  const days = Math.round((due - today) / 86400000);
  const date = faDate(visit.due_date);
  if (!OPEN_STATES.includes(visit.status)) return { label: date, tone: 'muted' };
  if (days < 0) return { label: `${date} · ${faNumber(-days)} روز تأخیر`, tone: 'danger' };
  if (days === 0) return { label: `${date} · امروز`, tone: 'warning' };
  return { label: `${date} · ${faNumber(days)} روز دیگر`, tone: 'ready' };
}

export function personName(user) {
  if (!user) return '';
  const extended = user.extended || {};
  return extended.full_name || [user.first_name, user.last_name].filter(Boolean).join(' ') || user.username || '';
}

export function project() {
  return store.state.userConfig.selectedProject;
}

export function withProject(path, query = {}) {
  const params = new URLSearchParams({ ...query, p: project() });
  return path + (path.includes('?') ? '&' : '?') + params.toString();
}

// Moves an open visit to «in progress». Returns { ok, message }.
export async function startVisit(api, paths, visitId) {
  try {
    const response = await api.put(withProject(paths.RELATIVE_PATH.MULTI.GET_STATUS_QUESTIONS + visitId + '/'),
      paths.SERVICE_NAME.AUTH, { status: '1' });
    if (response.status === 200) return { ok: true, visit: response.data };
    const detail = response.data && (response.data.status || response.data.detail);
    return { ok: false, message: Array.isArray(detail) ? detail.join(' ') : detail || 'شروع مأموریت ممکن نشد.' };
  } catch (_) {
    return { ok: false, message: 'شروع مأموریت ممکن نشد. اتصال اینترنت را بررسی کنید.' };
  }
}

// Requirement gaps returned by the API, turned into one readable sentence.
export function requirementText(gaps) {
  if (!gaps) return '';
  const parts = [];
  if (gaps.questions && gaps.questions.length) parts.push(`${faNumber(gaps.questions.length)} پرسش اجباری`);
  if (gaps.photo_types && gaps.photo_types.length) parts.push(`${faNumber(gaps.photo_types.length)} بخش عکس`);
  if (gaps.empty_required_question_types && gaps.empty_required_question_types.length) {
    parts.push(`${faNumber(gaps.empty_required_question_types.length)} بخش الزامی بدون پرسش (با پشتیبانی هماهنگ کنید)`);
  }
  return parts.length ? `${parts.join('، ')} هنوز تکمیل نشده است.` : '';
}

export function hasGaps(gaps) {
  return !!gaps && ['questions', 'photo_types', 'empty_required_question_types']
    .some(key => Array.isArray(gaps[key]) && gaps[key].length);
}

const ELEVATOR_VALUES = {
  TRACTION: 'کششی', HYDRAULIC: 'هیدرولیک', RESIDENTIAL: 'مسکونی', OFFICE: 'اداری', COMMERCIAL: 'تجاری',
  INDUSTRIAL: 'صنعتی', SIMPLEX: 'تکی', DUPLEX: 'دوبلکس', GROUP: 'گروهی', GEARED: 'گیربکس‌دار', GEARLESS: 'گیرلس',
  MR: 'با موتورخانه', MRL: 'بدون موتورخانه', SWING: 'لولایی', SEMI_AUTO: 'نیمه‌اتوماتیک', AUTO: 'تمام‌اتوماتیک',
  OPEN_LOOP: 'حلقه باز', CLOSED_LOOP: 'حلقه بسته', NONE: 'ندارد', UPS: 'UPS', HDRU: 'HDRU',
  SINGLE_PHASE: 'تک‌فاز', THREE_PHASE: 'سه‌فاز', OTHER: 'سایر', EXISTS: 'دارد', INACTIVE: 'غیرفعال',
  MODE1: 'حالت ۱', MODE2: 'حالت ۲', SERIAL: 'سریال', PARALLEL: 'موازی', Passenger: 'مسافربری',
};

export const ELEVATOR_SECTIONS = [
  { title: 'مشخصات کلی', fields: [['type', 'نوع'], ['elevator_type', 'سیستم'], ['usage_type', 'کاربری'],
    ['capacity', 'ظرفیت (نفر)'], ['cabin_capacity_kg', 'ظرفیت کابین (کیلوگرم)'], ['number_of_floors', 'تعداد طبقات'],
    ['stops_count', 'تعداد توقف'], ['operation_type', 'نوع عملکرد'], ['elevator_speed_mps', 'سرعت (متر بر ثانیه)'],
    ['standard_type', 'استاندارد']] },
  { title: 'موتور و درایو', fields: [['motor_type', 'نوع موتور'], ['motor_brand', 'برند موتور'],
    ['motor_power_kw', 'توان موتور (کیلووات)'], ['motor_encoder_type', 'انکودر'], ['inverter_type', 'نوع اینورتر'],
    ['inverter_power', 'توان اینورتر']] },
  { title: 'تابلو فرمان', fields: [['control_panel_brand', 'برند تابلو'], ['control_panel_serial', 'سریال تابلو'],
    ['control_panel_type', 'نوع تابلو'], ['control_system_type', 'سیستم کنترل'], ['landing_call_comm_type', 'ارتباط احضار']] },
  { title: 'درب‌ها', fields: [['door_brand', 'برند درب'], ['door_count', 'تعداد درب'], ['door1_type', 'نوع درب ۱'],
    ['door1_voltage', 'ولتاژ درب ۱'], ['door2_type', 'نوع درب ۲'], ['door2_voltage', 'ولتاژ درب ۲'],
    ['door3_type', 'نوع درب ۳'], ['door3_voltage', 'ولتاژ درب ۳']] },
  { title: 'ایمنی و برق', fields: [['emergency_system_type', 'سیستم اضطراری'], ['weight_sensor', 'سنسور وزن'],
    ['firefighter_mode', 'حالت آتش‌نشانی'], ['input_voltage', 'ولتاژ ورودی']] },
];

export function elevatorValue(value) {
  if (value === null || value === undefined || value === '') return '';
  if (typeof value === 'number') return faNumber(value);
  return ELEVATOR_VALUES[value] || String(value);
}

// Questions whose validation rows were never configured still answer by their declared types.
export function answerParams(question) {
  if (question.answer_params && question.answer_params.length) return question.answer_params;
  return (question.answer_type || []).map(type => ({ id: 'type-' + type.id, answer_type: type, validation: {} }));
}
