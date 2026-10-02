<template>
  <div class="user-managment-edit">
    <Loading v-if="loading" />
    <div class="box">
      <h2 class="form-title">جست‌وجوی کاربر</h2>
      <form class="user-search" @submit.prevent="searchUser">
        <input
          v-model="searchNumberInput"
          class="search-input"
          type="tel"
          dir="ltr"
          inputmode="tel"
          aria-label="شماره همراه کاربر"
          @input="validateMobileNumber"
          placeholder="09xxxxxxxxx"
        />
        <button type="submit" :disabled="isValidMobileNumberBtn" class="search">جست‌وجو</button>
      </form>
    </div>
    <div>
      <div class="box">
        <h2 class="form-title">اطلاعات کاربر</h2>
        <div class="user-form-grid">
          <div class="d-flex align-item.center col-lg-12 col-sm-12 mb-4">
            <div></div>
            <div class="user-name">
              <span class="text ml-2">نام کاربری :</span>
              <span class="persian">{{ phoneNumber }}</span>
            </div>
            <!-- <Materialnput
							label="شماره تلفن همراه"
							:readonly="!isEdit"
							v-model="phoneNumber"
							inputType="number"
						/> -->
          </div>
          <div class="col-lg-6 col-sm-12">
            <Materialnput label="نام" v-model="formattedFirstName" :readonly="Boolean(model.id)" />
          </div>
          <div class="col-lg-6 col-sm-12">
            <Materialnput label="نام خانوادگی" v-model="formattedLastName" :readonly="Boolean(model.id)" />
          </div>
          <div class="col-lg-6 col-sm-12">
            <Materialnput
              label="کد ملی"
              v-model="formattedNationalCode"
              inputType="text"
              inputMode="numeric"
              :maxlength="10"
              :readonly="Boolean(model.id)"
              ltr
            />
          </div>
          <!-- <div class="col-lg-6 col-sm-12">
						<Materialnput label="نقش" v-model="formattedRole" />
					</div> -->

          <div class="col-lg-6 col-sm-12">
            <Materialnput label="ایمیل" v-model="formatEmail" inputType="email" :readonly="Boolean(model.id)" ltr />
          </div>

          <div class="col-lg-6 col-sm-12">
            <label for="edit-user-province">استان</label>
            <select
              id="edit-user-province"
              @change="getCityOnChange"
              v-model="pickProvince"
              :disabled="Boolean(model.id)"
              class="search-input"
            >
              <option value="">انتخاب استان</option>
              <option
                v-for="province in provinceLists"
                :value="province.id"
                :key="`province-` + province.id"
              >
                {{ province.name }}
              </option>
            </select>
          </div>
          <div class="col-lg-6 col-sm-12">
            <label for="edit-user-city">شهر</label>
            <select id="edit-user-city" v-model="pickCity" class="search-input" :disabled="Boolean(model.id)">
              <option value="">انتخاب شهر</option>
              <option v-for="city in cityLists" :value="city.city.id" :key="`city-` + city.city.id">
                {{ city.city.name }}
              </option>
            </select>
          </div>
          <div class="col-lg-6 col-sm-12">
            <label for="edit-user-role">نقش</label>
            <select id="edit-user-role" class="search-input" v-model="model.role.id">
              <option :value="null" disabled>انتخاب نقش</option>
              <option v-for="role in roles" :key="role.id + `-role-`" :value="role.id">
                {{ role.verbose_name }}
              </option>
            </select>
          </div>
        </div>
        <p v-if="model.id" class="form-note">مشخصات این حساب فقط برای مشاهده است؛ در این فرم می‌توانید نقش او را تغییر دهید.</p>
        <p v-else class="form-note">حساب تازه بدون رمز پیش‌فرض ساخته می‌شود. برای حسابی که از قبل وجود دارد، عضویت در پروژه به دعوت و تأیید صاحب حساب نیاز دارد.</p>
        <p v-if="submitError" class="form-error" role="alert">{{ submitError }}</p>
        <div class="d-flex justify-content-end">
          <button @click="submitHandler" class="submit-btn" :disabled="loading || !phoneNumber || !model.role.id">{{ loading ? 'در حال ثبت…' : 'ثبت و ذخیره' }}</button>
          <!-- <button @click="searchUser" class="search">ثبت</button> -->
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Materialnput from '../../components/MaterialInput/indx.vue';
import Loading from '../../components/Loading/index.vue';

export default {
  components: {
    Materialnput,
    Loading,
  },
  data() {
    return {
      model: {
        user: {
          first_name: null,
          last_name: null,
          username: null,
          email: null,
          extended: {
            national_code: null,
          },
        },
        role: {
          id: null,
          verbose_name: null,
        },
      },
      phoneNumber: null,
      searchNumberInput: '',
      isEdit: false,
      isValidMobileNumber: false,
      loading: false,
      submitError: '',
      roles: [],
      cityLists: [],
      provinceLists: [],
      pickCity: '',
      pickProvince: '',
      selectedkCity: '',
    };
  },
  created() {
    this.getPhoneNumber();
  },
  mounted() {
    this.getProfileDetail();
    this.getRoles();
    this.getProvince();
  },
  computed: {
    isValidMobileNumberBtn() {
      // Regular expression for Iranian mobile numbers
      const iranMobileRegex = /^(\+98|0)?9\d{9}$/;

      // Check if the entered mobile number matches the regex
      const x = iranMobileRegex.test(this.searchNumberInput);
      if (x === false) {
        return true;
      } else {
        return false;
      }
    },
    formattedFirstName: {
      get() {
        // Check if model and user are defined before accessing properties
        if (this.model && this.model.user && this.model.user.first_name !== null) {
          return this.model.user.first_name;
        } else {
          return '';
        }
      },
      set(value) {
        // Ensure model and user are defined before updating
        if (this.model && this.model.user) {
          this.$set(this.model.user, 'first_name', value);
        }
      },
    },
    formattedLastName: {
      get() {
        // Check if model and user are defined before accessing properties
        if (this.model && this.model.user && this.model.user.last_name !== null) {
          return this.model.user.last_name;
        } else {
          return '';
        }
      },
      set(value) {
        // Ensure model and user are defined before updating
        if (this.model && this.model.user) {
          this.$set(this.model.user, 'last_name', value);
        }
      },
    },
    formattedNationalCode: {
      get() {
        // Check if model and user are defined before accessing properties
        if (
          this.model &&
          this.model.user.extended &&
          this.model.user.extended.national_code !== null
        ) {
          return this.model.user.extended.national_code;
        } else {
          return '';
        }
      },
      set(value) {
        // Ensure model and user are defined before updating
        if (this.model && this.model.user.extended) {
          this.$set(this.model.user.extended, 'national_code', value);
        }
      },
    },
    // formattedRole: {
    // 	get() {
    // 		// Check if model and user are defined before accessing properties
    // 		if (this.model && this.model.role && this.model.role.verbose_name !== null) {
    // 			return this.model.role.id;
    // 		} else {
    // 			return '';
    // 		}
    // 	},
    // 	set(value) {
    // 		// Ensure model and user are defined before updating
    // 		if (this.model && this.model.role) {
    // 			this.$set(this.model.role.verbose_name, 'verbose_name', value);
    // 		}
    // 	},
    // },
    formatUserName: {
      get() {
        // Check if model and user are defined before accessing properties
        if (this.model && this.model.user && this.model.user.username !== null) {
          return this.model.user.username;
        } else {
          return '';
        }
      },
      set(value) {
        // Ensure model and user are defined before updating
        if (this.model && this.model.user) {
          this.$set(this.model.user, 'username', value);
        }
      },
    },
    formatEmail: {
      get() {
        // Check if model and user are defined before accessing properties
        if (this.model && this.model.user && this.model.user.email !== null) {
          return this.model.user.email;
        } else {
          return '';
        }
      },
      set(value) {
        // Ensure model and user are defined before updating
        if (this.model && this.model.user) {
          this.$set(this.model.user, 'email', value);
        }
      },
    },
  },
  methods: {
    emptyModel(username = '') {
      return {
        user: { username, first_name: '', last_name: '', email: '', extended: { national_code: '' } },
        role: { id: null, verbose_name: null },
      };
    },
    applyProfile(profile) {
      const user = profile.user || {};
      const extended = user.extended || {};
      const city = extended.city;
      this.model = { ...profile, user: { ...user, extended: { ...extended } } };
      this.pickCity = city ? city.id : '';
      this.pickProvince = city && city.province ? city.province.id : '';
      this.selectedkCity = this.pickProvince;
    },
    getPhoneNumber() {
      const url = window.location.href;
      const lastParam = url.split('/').slice(-1)[0];
      if (lastParam === 'add') {
        this.phoneNumber = null;
      } else {
        this.phoneNumber = lastParam;
        this.searchNumberInput = lastParam;
      }
    },
    async getProfileDetail() {
      if (!this.phoneNumber) return;
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_USER_LIST +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId +
          '&user__username=' +
          this.phoneNumber,
        this.$PATH.SERVICE_NAME.EMPTY
      );
      if (res.status === 200) {
        if (res.data.length === 0) {
          this.model = this.emptyModel(this.phoneNumber);
        } else {
          this.applyProfile(res.data[0]);
          this.pickCity;
        }
        this.getCity();
      }
    },
    async searchUser() {
      this.loading = true;
      this.submitError = '';
      try {
        this.phoneNumber = this.searchNumberInput;
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.GET_USER_LIST +
            '?p=' +
            this.$STORE.state.userConfig.setProjectId +
            '&user__username=' +
            this.searchNumberInput +
            '&is_deleted=false',
          this.$PATH.SERVICE_NAME.EMPTY
        );
        if (res.status !== 200) {
          this.submitError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        if (res.data.length) {
          this.applyProfile(res.data[0]);
        } else {
          this.model = this.emptyModel(this.phoneNumber);
          this.pickCity = '';
          this.pickProvince = '';
          this.$notify({ group: 'tc', type: 'warning', text: 'عضوی در این پروژه پیدا نشد. برای حساب تازه، مشخصات و نقش را وارد کنید.' });
        }
      } finally {
        this.loading = false;
      }
    },
    async getRoles() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.LIST_CREATE_ROLE +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.roles = res.data;
        'here roles:', this.roles;
      }
    },
    getCityOnChange() {
      this.selectedkCity = this.pickProvince;
      'ci', this.selectedkCity;
      this.getCity();
    },
    async getProvince() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_PROVINCE_LIST +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.provinceLists = res.data;
      }
    },
    async getCity() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_CITY_LIST +
          '?city__province=' +
          this.selectedkCity +
          '&p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        'city:', res.data;
        this.cityLists = res.data;
      }
    },
    validateMobileNumber() {
      // Remove non-digit characters from the input
      this.searchNumberInput = this.searchNumberInput.replace(/\D/g, '');

      // Limit the input to 11 characters
      if (this.searchNumberInput.length > 11) {
        this.searchNumberInput = this.searchNumberInput.slice(0, 11);
      }

      // Define the regex pattern for an Iranian mobile number
      const iranMobileRegex = /^09\d{9}$/;

      // Test the input against the regex pattern
      this.isValidMobileNumber = iranMobileRegex.test(this.searchNumberInput);
    },
    async submitHandler() {
      if (this.loading) return;
      this.submitError = '';
      if (!/^09\d{9}$/.test(this.phoneNumber || '') || !this.model.role.id) {
        this.submitError = 'شماره همراه معتبر و نقش را وارد کنید.';
        return;
      }
      const data = this.model.id
        ? { id: this.model.id, role: this.model.role.id, project: this.$STORE.state.userConfig.setProjectId }
        : {
            username: this.phoneNumber,
            first_name: (this.model.user.first_name || '').trim(),
            last_name: (this.model.user.last_name || '').trim(),
            email: (this.model.user.email || '').trim(),
            national_code: (this.model.user.extended.national_code || '').trim(),
            city: this.pickCity || null,
            role: this.model.role.id,
            project: this.$STORE.state.userConfig.setProjectId,
          };
      if (!this.model.id && (!data.first_name || !data.last_name)) {
        this.submitError = 'نام و نام خانوادگی حساب تازه را وارد کنید.';
        return;
      }
      this.loading = true;
      try {
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.POST.POST_USER_LIST + '?p=' + this.$STORE.state.userConfig.setProjectId,
          this.$PATH.SERVICE_NAME.EMPTY,
          data
        );
        if (![200, 201].includes(res.status)) {
          const details = res.data || {};
          const firstField = ['username', 'national_code', 'city', 'detail'].map(key => details[key]).find(Boolean);
          this.submitError = (Array.isArray(firstField) ? firstField[0] : firstField) || this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        this.applyProfile(res.data);
        this.$notify({ group: 'tc', type: 'success', text: res.status === 201 ? 'حساب و دسترسی پروژه ساخته شد؛ برای ورود با رمز باید رمز امن تعیین شود.' : 'نقش کاربر تغییر کرد.' });
      } catch (_) {
        this.submitError = 'ارتباط برقرار نشد. دوباره تلاش کنید.';
      } finally {
        this.loading = false;
      }
    },
  },
  watch: {
    'model.user.first_name': {
      immediate: true,
      handler(newValue) {
        // Ensure the model and user are defined before checking for null
        if (this.model && this.model.user && newValue === null) {
          this.formattedFirstName = ''; // Set to empty string if null
        }
      },
    },
    'model.user.last_name': {
      immediate: true,
      handler(newValue) {
        // Ensure the model and user are defined before checking for null
        if (this.model && this.model.user && newValue === null) {
          this.formattedLastName = ''; // Set to empty string if null
        }
      },
    },
    'model.user.extended.national_code': {
      immediate: true,
      handler(newValue) {
        // Ensure the model and user are defined before checking for null
        if (this.model && this.model.user.extended && newValue === null) {
          this.formattedNationalCode = ''; // Set to empty string if null
        }
      },
    },
    'model.user.username': {
      immediate: true,
      handler(newValue) {
        // Ensure the model and user are defined before checking for null
        if (this.model && this.model.user && newValue === null) {
          this.formatUserName = ''; // Set to empty string if null
        }
      },
    },
    'model.user.email': {
      immediate: true,
      handler(newValue) {
        // Ensure the model and user are defined before checking for null
        if (this.model && this.model.user && newValue === null) {
          this.formatEmail = ''; // Set to empty string if null
        }
      },
    },
  },
};
</script>

<style scoped>
.user-managment-edit {
  padding: 0;
}
.form-title {
  margin: 0 0 18px;
  font-size: 15px;
  font-weight: 700;
  color: var(--admin-text);
}
.user-search {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 520px;
}
.user-search .search-input {
  flex: 1;
  min-width: 0;
}
.user-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 24px;
  margin-bottom: 20px;
}
.user-form-grid > div {
  width: 100%;
  max-width: none;
  padding: 0;
  margin-bottom: 18px;
}
.user-form-grid > div:first-child {
  grid-column: 1 / -1;
}
.user-name {
  display: flex;
  gap: 12px;
  align-items: center;
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--admin-border);
  border-radius: 9px;
  background: #f7f9fc;
}
.user-name .text {
  color: var(--admin-muted);
  font-size: 12px;
}
.user-form-grid .edit-container {
  margin: 0;
}
.form-note {
  color: var(--admin-muted);
  font-size: 13px;
  line-height: 1.8;
}
.form-error {
  color: #a52626;
  background: #fff0f0;
  border: 1px solid #edc8c8;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
}
.submit-btn:disabled { opacity: .55; cursor: not-allowed; }
.persian {
  font-family: 'IRANYekanfa', sans-serif;
}
@media (max-width: 575px) {
  .user-form-grid {
    grid-template-columns: 1fr;
  }
  .user-search {
    gap: 8px;
  }
}
</style>
