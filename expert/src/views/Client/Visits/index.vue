<template>
  <main class="field-page client-visits" dir="rtl">
    <header class="visits-hero">
      <router-link :to="{ name: 'home' }" class="visits-back"><v-icon color="white" size="19">mdi-arrow-right</v-icon>داشبورد</router-link>
      <span class="visits-kicker">سان اپ · پیگیری خدمات</span><h1>درخواست‌ها و ویزیت‌ها</h1>
      <p>از ثبت درخواست تا نتیجه مراجعه، وضعیت هر خدمت را اینجا دنبال کنید.</p>
      <router-link :to="{ name: 'home' }" class="visits-new"><v-icon color="#173c50" size="20">mdi-plus</v-icon>ثبت درخواست خدمت<v-icon color="#173c50" size="19">mdi-arrow-left</v-icon></router-link>
    </header>
    <div class="visits-body">
      <div class="visits-toolbar"><div><span class="visits-eyebrow">سوابق شما</span><h2>خدمات ساختمان‌ها</h2><small v-if="loaded">{{ number(visits.length) }} مورد نمایش داده‌شده</small></div><button type="button" class="visits-refresh" :disabled="loading" aria-label="به‌روزرسانی ویزیت‌ها" @click="load(true)"><v-icon size="20">mdi-refresh</v-icon></button></div>
      <v-text-field v-model="search" label="جست‌وجوی نام یا نشانی ساختمان" prepend-inner-icon="mdi-magnify" outlined dense clearable hide-details class="visits-search" />
      <v-alert v-if="error" type="error" outlined role="alert" class="visits-error">{{ error }} <v-btn text color="error" @click="load(true)">تلاش دوباره</v-btn></v-alert>
      <v-skeleton-loader v-if="loading && !loaded" type="article, article" />
      <section v-else-if="loaded && !visits.length && !error" class="visits-empty"><v-icon color="#2b7189" size="35">{{ activeSearch ? 'mdi-magnify' : 'mdi-clipboard-text-outline' }}</v-icon><h2>{{ activeSearch ? 'نتیجه‌ای پیدا نشد' : 'هنوز درخواستی ثبت نشده است' }}</h2><p>{{ activeSearch ? 'نام یا نشانی دیگری را جست‌وجو کنید.' : 'برای شروع، ساختمان و آسانسور موردنظر را انتخاب کنید.' }}</p><button v-if="activeSearch" type="button" class="visits-clear" @click="search = ''">پاک‌کردن جست‌وجو</button><router-link v-else :to="{ name: 'home' }" class="visits-clear">ساختمان‌های من <v-icon size="17">mdi-arrow-left</v-icon></router-link></section>
      <router-link v-for="visit in visits" :key="visit.id" :to="{ name: 'clientVisitDetail', params: { id: visit.id } }" class="visits-card">
        <div class="visits-card-head"><span class="visits-card-icon"><v-icon color="#286c89" size="21">mdi-text-box-check-outline</v-icon></span><div class="visits-card-title"><small>خدمت شماره <bdi>{{ number(visit.id) }}</bdi></small><h3>{{ typeName(visit) }}</h3></div><span class="visits-status" :class="statusClass(visit)">{{ status(visit) }}</span></div>
        <div class="visits-facts"><span><v-icon size="17">mdi-office-building-outline</v-icon>{{ buildingName(visit) }}</span><span><v-icon size="17">mdi-calendar-outline</v-icon>{{ date(visit.datetime_created) }}</span><span v-if="elevatorNames(visit)"><v-icon size="17">mdi-elevator</v-icon>{{ elevatorNames(visit) }}</span></div>
        <div class="visits-card-foot"><span>{{ visit.is_pending_request ? 'در انتظار بررسی و برنامه‌ریزی شرکت' : 'کارشناس: ' + expert(visit) }}</span><strong>جزئیات<v-icon color="#246c8b" size="18">mdi-arrow-left</v-icon></strong></div>
      </router-link>
      <button v-if="hasMore && visits.length" type="button" class="visits-more" :disabled="loading" @click="load(false)">{{ loading ? 'در حال دریافت…' : 'نمایش سوابق بیشتر' }}<v-icon color="#246c8b" size="18">mdi-chevron-down</v-icon></button>
    </div>
  </main>
</template>
<script>
import { pageRows, errorMessage } from '@/utils/clientRequests';
export default {
  data: () => ({ visits: [], loading: false, loaded: false, error: '', offset: 0, hasMore: false, search: '', activeSearch: '', timer: null, sequence: 0 }),
  computed: { project() { return this.$STORE.state.userConfig.selectedProject; } },
  mounted() { this.load(true); },
  beforeDestroy() { clearTimeout(this.timer); this.sequence++; },
  watch: {
    project() { clearTimeout(this.timer); this.sequence++; this.visits = []; this.loaded = false; this.offset = 0; this.hasMore = false; this.search = ''; this.activeSearch = ''; this.load(true); },
    search() { clearTimeout(this.timer); this.timer = setTimeout(() => this.load(true), 320); },
  },
  methods: {
    number(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    date(value) { if (!value) return 'تاریخ نامشخص'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? 'تاریخ نامشخص' : parsed.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric' }); },
    typeName(visit) { return (visit.type && (visit.type.verbose_name || visit.type.name)) || 'خدمت آسانسور'; },
    buildingName(visit) { return (visit.building && (visit.building.verbose_name || visit.building.name)) || 'ساختمان نامشخص'; },
    elevatorNames(visit) { return (visit.elevator || []).map(item => item.title || 'آسانسور ' + item.id).join('، '); },
    expert(visit) { const user = visit.expert_details || visit.promoter; return user ? [user.first_name, user.last_name].filter(Boolean).join(' ') || 'تعیین شده' : 'تعیین نشده'; },
    status(visit) { return visit.is_pending_request ? 'در انتظار بررسی' : ({ '0': 'در انتظار مراجعه', '1': 'در حال انجام', '2': 'انجام شده', '3': 'تأیید شده', '4': 'رد شده', '5': 'نیاز به مراجعه مجدد', '6': 'متوقف شده' }[visit.status] || 'در حال پیگیری'); },
    statusClass(visit) { return visit.is_pending_request ? 'pending' : ({ '2': 'done', '3': 'done', '4': 'stopped', '6': 'stopped' }[visit.status] || 'active'); },
    async load(reset) {
      if (!this.project || (!reset && this.loading)) return;
      const project = this.project;
      const query = String(this.search || '').trim();
      const changed = reset && query !== this.activeSearch;
      const sequence = reset ? ++this.sequence : this.sequence;
      if (changed) { this.visits = []; this.loaded = false; this.activeSearch = query; this.offset = 0; this.hasMore = false; }
      const offset = reset ? 0 : this.offset;
      this.loading = true; this.error = '';
      try {
        const url = 'core/api/client/open_visits/list/?p=' + project + '&limit=12&offset=' + offset + '&ordering=-datetime_created' + (query ? '&search=' + encodeURIComponent(query) : '');
        const response = await this.$ApiServiceLayer.get(url);
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status !== 200) { this.error = errorMessage(response); return; }
        const rows = pageRows(response.data);
        this.visits = reset ? rows : [...this.visits, ...rows]; this.offset = offset + rows.length; this.hasMore = !!response.data.next; this.loaded = true;
      } catch (_) { if (sequence === this.sequence) this.error = 'دریافت خدمات ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence) this.loading = false; }
    }
  }
};
</script>
<style scoped>
.client-visits{padding:0 0 calc(112px + env(safe-area-inset-bottom));background:#f4f8fb;color:#17394e}.visits-hero{padding:calc(18px + env(safe-area-inset-top)) 20px 25px;color:#fff;background:linear-gradient(145deg,#10314d,#216d89);border-radius:0 0 29px 29px;box-shadow:0 12px 28px #123c5422}.visits-back{display:inline-flex;align-items:center;gap:6px;min-height:44px;color:#e4f3f8;text-decoration:none;font-size:13px}.visits-kicker{display:block;margin-top:20px;color:#bbe2ec;font-size:12px;font-weight:700}.visits-hero h1{color:#fff;font-size:27px;line-height:1.45;margin:5px 0}.visits-hero p{color:#e2f1f5;font-size:13px;line-height:1.8;max-width:390px;margin:0 0 19px}.visits-new{display:flex;align-items:center;gap:9px;min-height:50px;padding:10px 13px;border-radius:13px;background:#d7f4bb;color:#173c50;text-decoration:none;font-size:13px;font-weight:800}.visits-new .v-icon:last-child{margin-right:auto}.visits-body{padding:23px 20px}.visits-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}.visits-eyebrow{color:#387990;font-size:11px;font-weight:700}.visits-toolbar h2{font-size:19px;margin:2px 0;color:#17394e}.visits-toolbar small{font-size:11px;color:#637f8e}.visits-refresh{width:44px;height:44px;flex:none;display:grid;place-items:center;border:1px solid #d5e5eb;border-radius:12px;background:#fff;color:#286a85}.visits-search{margin-bottom:16px!important}.visits-error{margin-bottom:15px}.visits-empty{display:grid;justify-items:center;gap:8px;padding:28px 17px;border:1px dashed #bfd7e0;border-radius:17px;background:#fff;text-align:center}.visits-empty h2{font-size:16px;margin:4px 0 0}.visits-empty p{margin:0;color:#5e7989;font-size:13px;line-height:1.8}.visits-clear{display:inline-flex;align-items:center;gap:5px;margin-top:6px;border:0;background:transparent;color:#236c8a;font-size:13px;font-weight:700;text-decoration:none}.visits-card{display:block;padding:16px;margin-bottom:11px;border:1px solid #dce9ee;border-radius:17px;background:#fff;box-shadow:0 4px 16px #183e550a;color:#17394e;text-decoration:none}.visits-card-head{display:flex;align-items:center;gap:10px}.visits-card-icon{width:41px;height:41px;flex:none;display:grid;place-items:center;border-radius:12px;background:#e9f3f6}.visits-card-title{min-width:0;flex:1}.visits-card-title small{color:#648192;font-size:11px}.visits-card-title h3{font-size:15px;line-height:1.5;margin:2px 0;overflow-wrap:anywhere}.visits-status{flex:none;max-width:110px;padding:6px 8px;border-radius:9px;font-size:10px;font-weight:700;text-align:center}.visits-status.pending{color:#815516;background:#fff1d8}.visits-status.active{color:#255e89;background:#e6f1fa}.visits-status.done{color:#1d6a51;background:#e3f3e9}.visits-status.stopped{color:#904a46;background:#fbeae7}.visits-facts{display:grid;gap:7px;margin:16px 0;color:#516d7e;font-size:12px}.visits-facts span{display:flex;align-items:flex-start;gap:7px;overflow-wrap:anywhere}.visits-facts .v-icon{color:#6d98aa;flex:none}.visits-card-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;padding-top:12px;border-top:1px solid #edf2f4;color:#627d8c;font-size:11px}.visits-card-foot strong{display:inline-flex;align-items:center;gap:3px;flex:none;color:#246c8b;font-size:12px}.visits-more{display:flex;align-items:center;justify-content:center;gap:6px;min-height:47px;width:100%;margin-top:14px;border:1px solid #b8d3de;border-radius:12px;background:#fff;color:#246c8b;font-size:13px;font-weight:700}.client-visits button:focus-visible,.client-visits a:focus-visible{outline:3px solid #3b9dbf;outline-offset:3px}.visits-card:hover{border-color:#8ebacc;box-shadow:0 8px 22px #183e5518}@media(max-width:350px){.visits-hero{padding-left:16px;padding-right:16px}.visits-body{padding-left:14px;padding-right:14px}.visits-card{padding:13px}.visits-card-head{flex-wrap:wrap}.visits-status{margin-right:51px}.visits-card-foot{align-items:flex-start}}
</style>
