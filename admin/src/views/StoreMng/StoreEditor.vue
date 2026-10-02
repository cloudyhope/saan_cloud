<template>
  <div class="record-detail">
    <div v-if="loading" class="detail-state" role="status">در حال دریافت اطلاعات فروشگاه…</div>
    <div v-else-if="error" class="detail-state" role="alert">
      <p>{{ error }}</p>
      <button class="accept" @click="load">تلاش دوباره</button>
    </div>
    <form v-else class="record-detail" @submit.prevent="save">
      <section class="detail-hero">
        <div class="detail-hero-top">
          <div>
            <span class="detail-eyebrow">ویرایش فروشگاه · {{ form.id }}</span>
            <h2>{{ form.name }}</h2>
            <p>اطلاعات فروشگاه، مالک و محل فعالیت</p>
          </div>
          <router-link class="detail-back" :to="'/storemng/detail/' + form.id"
            >بازگشت به جزئیات ←</router-link
          >
        </div>
      </section>
      <section class="detail-section">
        <div class="detail-section-heading"><h2>اطلاعات فروشگاه</h2></div>
        <div class="store-form-grid">
          <Materialnput label="نام فروشگاه" v-model="form.name" inputType="text" /><Materialnput
            label="تلفن ثابت"
            v-model="form.phone"
            inputType="tel"
          /><Materialnput label="کد فروشگاه" v-model="form.code" inputType="text" /><Materialnput
            label="کد مشتری"
            v-model="form.customer_code"
            inputType="text"
          />
          <div>
            <label for="store-category">نوع فروشگاه</label
            ><select id="store-category" v-model="form.category">
              <option :value="null">انتخاب کنید</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">
                {{ c.verbose_name }}
              </option>
            </select>
          </div>
        </div>
      </section>
      <section class="detail-section">
        <div class="detail-section-heading"><h2>اطلاعات مالک</h2></div>
        <div class="store-form-grid">
          <Materialnput
            label="نام و نام خانوادگی مالک"
            v-model="form.owner_name"
            inputType="text"
          /><Materialnput
            label="شماره همراه"
            v-model="form.mobile_phone"
            inputType="tel"
          /><Materialnput
            label="کد ملی مالک"
            v-model="form.owner_national_code"
            inputType="text"
            inputMode="numeric"
            :maxlength="10"
          />
        </div>
      </section>
      <section class="detail-section">
        <div class="detail-section-heading"><h2>نشانی و موقعیت</h2></div>
        <div class="store-form-grid">
          <div>
            <label for="store-province">استان</label
            ><select id="store-province" v-model="province" @change="loadCities(true)">
              <option :value="null">انتخاب کنید</option>
              <option v-for="p in provinces" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div>
            <label for="store-city">شهر</label
            ><select id="store-city" v-model="form.city">
              <option :value="null">انتخاب کنید</option>
              <option v-for="c in cities" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <Materialnput
            label="کد پستی"
            v-model="form.postal_code"
            inputType="text"
            inputMode="numeric"
            :maxlength="10"
          />
          <div class="store-form-wide">
            <label for="store-address">نشانی کامل</label
            ><textarea id="store-address" v-model="form.address" rows="3" />
          </div>
        </div>
        <details class="store-map" @toggle="mapOpen = $event.target.open">
          <summary>ویرایش موقعیت روی نقشه</summary>
          <p class="detail-muted">
            انتخاب نقطه اختیاری است؛ موقعیت فعلی تا زمان انتخاب نقطه جدید حفظ می‌شود.
          </p>
          <Map
            v-if="mapOpen"
            :defaultLat="form.latitude"
            :defaultLng="form.longitude"
            @child-event="mapChanged"
          />
        </details>
      </section>
      <section class="detail-review-bar">
        <p v-if="saveError" class="detail-error" role="alert">{{ saveError }}</p>
        <div v-else>
          <h2>ذخیره تغییرات</h2>
          <p>اطلاعات واردشده را پیش از ذخیره بررسی کنید.</p>
        </div>
        <div class="detail-form-actions">
          <router-link class="reject" :to="'/storemng/detail/' + form.id">انصراف</router-link
          ><button class="accept" :disabled="saving || !form.name || !form.code">
            {{ saving ? 'در حال ذخیره…' : 'ذخیره تغییرات' }}
          </button>
        </div>
      </section>
    </form>
  </div>
</template>
<script>
import Materialnput from '@/components/MaterialInput/indx.vue';
import Map from '@/components/Map/index.vue';
export default {
  components: { Materialnput, Map },
  data: () => ({
    mapOpen: false,
    form: {},
    categories: [],
    provinces: [],
    cities: [],
    province: null,
    loading: true,
    error: '',
    saving: false,
    saveError: '',
  }),
  mounted() {
    this.load();
  },
  methods: {
    async get(path) {
      const res = await this.$ApiServiceLayer.get(
        path + (path.includes('?') ? '&' : '?') + 'p=' + this.$STORE.state.userConfig.setProjectId,
        ''
      );
      if (res.status !== 200) throw new Error(this.$ApiServiceLayer.getErrorMessage(res));
      return res.data;
    },
    async load() {
      this.loading = true;
      this.error = '';
      try {
        const data = await Promise.all([
          this.get('/core/api/admin/outlet_with_more_info/edits/' + this.$route.params.id + '/'),
          this.get('/core/api/admin/outlet_cat_list/'),
          this.get('/core/api/province/list/'),
        ]);
        this.form = {
          ...data[0],
          city: (data[0].city || {}).id || null,
          category: (data[0].category || {}).id || null,
        };
        const p = (data[0].city || {}).province;
        this.province = p && typeof p === 'object' ? p.id : p;
        this.categories = data[1];
        this.provinces = data[2];
        await this.loadCities();
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async loadCities(reset = false) {
      if (reset) this.form.city = null;
      try {
        const data = await this.get('/config/city/list_create/?province=' + (this.province || ''));
        this.cities = Array.isArray(data) ? data : data.results || [];
      } catch (e) {
        this.saveError = e.message;
      }
    },
    mapChanged(data) {
      if (data.geom && data.geom.coordinates) {
        this.form.longitude = data.geom.coordinates[0];
        this.form.latitude = data.geom.coordinates[1];
      }
      if (data.address) this.form.address = data.address;
    },
    async save() {
      this.saving = true;
      this.saveError = '';
      const fields = [
        'name',
        'phone',
        'mobile_phone',
        'code',
        'customer_code',
        'category',
        'city',
        'owner_name',
        'owner_national_code',
        'postal_code',
        'address',
        'latitude',
        'longitude',
      ];
      const payload = Object.fromEntries(fields.map((key) => [key, this.form[key]]));
      try {
        const res = await this.$ApiServiceLayer.patch(
          '/api/admin/outlet_with_more_info/edits/' +
            this.form.id +
            '/?p=' +
            this.$STORE.state.userConfig.setProjectId,
          '/core',
          payload
        );
        if (res.status !== 200) {
          this.saveError =
            res.status === 400
              ? 'اطلاعات واردشده معتبر نیست. فیلدها را بررسی کنید.'
              : this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        this.$notify({ group: 'tc', type: 'success', text: 'اطلاعات فروشگاه ذخیره شد.' });
        this.$router.push('/storemng/detail/' + this.form.id);
      } finally {
        this.saving = false;
      }
    },
  },
};
</script>
<style scoped>
.store-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}
.store-form-grid label {
  display: block;
  color: #63738b;
  font-size: 12px;
  margin-bottom: 8px;
}
.store-form-wide {
  grid-column: 1/-1;
}
.store-map {
  margin-top: 24px;
}
.store-map summary {
  color: #345de0;
  font-size: 13px;
  padding: 12px 0;
  cursor: pointer;
}
@media (max-width: 640px) {
  .store-form-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
