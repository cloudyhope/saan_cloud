<template>
  <div class="follow-order">
    <FilterPanel @apply="applyFilters">
      <div class="filter-field">
        <label for="user-province">استان</label>
        <select
          id="user-province"
          @change="getCityOnChange"
          v-model="pickProvince"
          class="form-select"
        >
          <option value="">همه استان‌ها</option>
          <option
            v-for="province in provinceLists"
            :value="province.id"
            :key="`province-` + province.id"
          >
            {{ province.name }}
          </option>
        </select>
      </div>
      <div class="filter-field">
        <label for="user-city">شهر</label>
        <select id="user-city" v-model="pickCity" class="form-select">
          <option value="">همه شهرها</option>
          <option v-for="city in cityLists" :value="city.city.id" :key="`city-` + city.city.id">
            {{ city.city.name }}
          </option>
        </select>
      </div>
      <div class="filter-field">
        <label for="user-phone">شماره همراه</label>
        <input
          id="user-phone"
          type="tel"
          inputmode="tel"
          dir="ltr"
          class="inputs"
          v-model="phoneNumber"
          placeholder="09xxxxxxxxx"
        />
      </div>
      <div class="filter-field">
        <label for="user-first-name">نام</label>
        <input
          id="user-first-name"
          class="inputs"
          v-model="userFirstName"
          placeholder="وارد کنید…"
        />
      </div>
      <div class="filter-field">
        <label for="user-last-name">نام خانوادگی</label>
        <input id="user-last-name" class="inputs" v-model="userLastName" placeholder="وارد کنید…" />
      </div>
      <template #actions>
        <button type="submit" class="accept" :disabled="loadingList">اعمال فیلتر</button>
        <button type="button" class="remove-filtes" @click="removeFilter">پاک کردن فیلترها</button>
      </template>
    </FilterPanel>
    <div class="box list-box">
      <div>
        <Tableview
          :recordCount="totalDataCount"
          :page="page"
          :hover="true"
          :bordered="true"
          :showNoContent="loadingList"
          :showNoData="!loadingList && dataPackage.length === 0"
          :errorMessage="listError"
          @retry="getDataPackage(20, 20 * (page - 1))"
        >
          <template #controls
            ><label class="ordering-title">مرتب‌سازی</label
            ><b-form-select
              aria-label="مرتب‌سازی"
              v-model="selected"
              :options="options"
              class="ordering"
              value-field="item"
              text-field="name"
              @change="applyFilters"
            ></b-form-select
          ></template>
          <template #footer
            ><pagination
              :disabled="loadingList"
              v-model="page"
              :per-page="20"
              :records="totalDataCount"
              @paginate="myCallback"
          /></template>

          <template #TableTitle>
            <tr>
              <th>ردیف</th>
              <th>موبایل</th>
              <th>نام و نام خانوادگی</th>
              <th>کدملی</th>
              <th>شهر</th>
              <th>نقش</th>
              <th>ایمیل</th>
              <th class="actions-column">عملیات</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="`list-` + item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>{{ item.user.username }}</td>
              <td>{{ item.user.first_name + ' ' + item.user.last_name }}</td>
              <td class="persian-number">
                {{ (item.user.extended && item.user.extended.national_code) || '—' }}
              </td>
              <td class="persian-number">
                {{
                  (item.user.extended && item.user.extended.city && item.user.extended.city.name) ||
                  '—'
                }}
              </td>
              <td>
                <select class="role-select" v-model="item.role" @change="changeRole(item)" :disabled="roleChangingId === item.id" :aria-label="`نقش ${item.user.first_name} ${item.user.last_name}`">
                  <option v-for="role in roles" :key="item.id + `-role-` + role.id" :value="role">
                    {{ role.verbose_name }}
                  </option>
                </select>
              </td>
              <td>{{ item.user.email }}</td>
              <td class="actions-cell">
                <div class="action-buttons">
                  <button
                    type="button"
                    class="icon-action"
                    @click="editUser(item)"
                    aria-label="ویرایش"
                  >
                    <ActionIcon name="edit" />
                  </button>
                  <button
                    type="button"
                    class="icon-action"
                    @click="openSetPasswordModal(item)"
                    aria-label="تغییر رمز عبور"
                  >
                    <ActionIcon name="lock" />
                  </button>
                  <button
                    type="button"
                    class="icon-action"
                    @click="deleteUserModal(item)"
                    aria-label="حذف دسترسی"
                  >
                    <ActionIcon name="delete" />
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </Tableview>
      </div>
    </div>
    <b-modal v-model="showSetPasswordModal" hide-footer hide-header centered>
      <div class="p-3">
        <div class="d-flex flex-column justify-content-center">
          <label for="password">رمز ورود</label>
          <input
            id="password"
            type="password"
            autocomplete="new-password"
            minlength="10"
            class="inputs password-field"
            v-model="changedPasswordItem.user.password"
          />
          <small>رمز جدید باید دست‌کم ۱۰ نویسه داشته باشد.</small>
          <p v-if="setPasswordError" class="text-danger mt-2" role="alert">{{ setPasswordError }}</p>
          <div class="d-flex justify-content-end mt-4">
            <button @click="setPassword" class="confirm-item" :disabled="setPasswordBusy || !changedPasswordItem.user.password || changedPasswordItem.user.password.length < 10">{{ setPasswordBusy ? 'در حال ثبت…' : 'ثبت رمز جدید' }}</button>
            <button @click="denySetPass" class="reject-item" :disabled="setPasswordBusy">انصراف</button>
          </div>
        </div>
      </div>
    </b-modal>
    <b-modal v-model="showDeleteUserModal" hide-footer hide-header centered>
      <div class="p-3">
        <div class="d-flex flex-column justify-content-center">
          <strong>حذف دسترسی کاربر</strong>
          <p class="mt-2">دسترسی {{ deletedUserName }} به پروژه فعلی حذف شود؟</p>
          <p v-if="deleteUserError" class="text-danger" role="alert">{{ deleteUserError }}</p>
          <div class="d-flex justify-content-end mt-4">
            <button @click="deleteUser" class="confirm-item" :disabled="deleteUserBusy">{{ deleteUserBusy ? 'در حال حذف…' : 'حذف دسترسی' }}</button>
            <button @click="showDeleteUserModal = false" class="reject-item" :disabled="deleteUserBusy">انصراف</button>
          </div>
        </div>
      </div>
    </b-modal>
  </div>
</template>
<script>
import FilterPanel from '../../components/FilterPanel/index.vue';
import Tableview from '../../components/Tableview/index.vue';
import Pagination from '@/components/ListPagination/index.vue';

export default {
  components: {
    FilterPanel,
    Tableview,
    Pagination,
  },
  data() {
    return {
      loadingList: true,
      listError: '',
      dataPackage: [],
      roles: [],
      cityLists: [],
      promoterLists: [],
      provinceLists: [],
      pickCity: '',
      showSetPasswordModal: false,
      changedPasswordItem: { user: { password: '' } },
      setPasswordBusy: false,
        setPasswordError: '',
      roleChangingId: null,
      deleteUserBusy: false,
      deleteUserError: '',
      deletedUserName: '',
      dueDate: '',
      pickProvince: '',
      pickPromoter: '',
      visitTurn: '',
      phoneNumber: '',
      pickStore: '',
      selectedkCity: '',
      outletCat: [],
      page: 1,
      totalDataCount: 0,
      selected: '-user',
      userId: null,
      showDeleteUserModal: false,
      options: [
        { item: '-user', name: 'نزولی' },
        { item: 'user', name: 'صعودی' },
      ],
      userFirstName: '',
      userLastName: '',
    };
  },
  mounted() {
    this.getDataPackage();
    this.getCity();
    // this.getPromoterLists();
    this.getProvince();
    // this.getOutletCat();
    this.getRoles();
  },
  computed: {
    selectedPromoterId() {
      return this.pickPromoter.id;
    },
    selectedCityId() {
      return this.pickCity.id;
    },
    selectedProvinceId() {
      return this.pickProvince.id;
    },
    showContnetFunc() {
      return this.dataPackage === 0;
    },
    showDataFunc() {
      if (this.dataPackage.length !== undefined) {
        return this.dataPackage.length === 0;
      }
      return false;
    },
  },
  methods: {
    applyFilters() {
      this.page = 1;
      return this.getDataPackage();
    },
    getCityOnChange() {
      this.selectedkCity = this.pickProvince;
      this.pickCity = '';
      this.getCity();
    },
    removeFilter() {
      this.page = 1;
      this.userFirstName = '';
      this.userLastName = '';
      this.pickCity = '';
      this.pickPromoter = '';
      this.visitTurn = '';
      this.phoneNumber = '';
      this.pickProvince = '';
      this.pickStore = '';
      this.dueDate = '';
      this.selectedkCity = '';
      this.getDataPackage();
      this.getCity();
      this.getProvince();
    },
    // async getOutletCat() {
    // 	const res = await this.$ApiServiceLayer.get(
    // 		this.$PATH.RELATIVE_PATH.GET.OUTLET_CAT + '?p=' + this.$STORE.state.userConfig.setProjectId,
    // 		this.$PATH.SERVICE_NAME.AUTH,
    // 	);
    // 	if (res.status === 200) {
    // 		this.outletCat = res.data;
    // 	}
    // },
    editUser(item) {
      item;
      let routeData = this.$router.resolve({
        name: 'userEditPage',
        params: { pn: item.user.username },
      });
      window.open(routeData.href);
    },
    openSetPasswordModal(item) {
      this.showSetPasswordModal = true;
      this.setPasswordError = '';
      this.changedPasswordItem = { ...item, user: { ...item.user } };
      this.changedPasswordItem.user.password = '';
      item;
      // this.userEditPost(item, true);
    },
    async deleteUser() {
      if (this.deleteUserBusy) return;
      this.deleteUserBusy = true;
      this.deleteUserError = '';
      try {
        const res = await this.$ApiServiceLayer.delete(
          this.$PATH.RELATIVE_PATH.DELETE.DELETE_ROLE_ASSIGNMENT +
            this.userId + '/?p=' + this.$STORE.state.userConfig.setProjectId,
          this.$PATH.SERVICE_NAME.AUTH,
          {}
        );
        if (res.status !== 204) {
          this.deleteUserError = (res.data && res.data.detail) || this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        this.showDeleteUserModal = false;
        this.$notify({ group: 'tc', type: 'success', text: 'دسترسی کاربر حذف شد.' });
        await this.getDataPackage(20, 20 * (this.page - 1));
      } catch (_) {
        this.deleteUserError = 'ارتباط برقرار نشد. دوباره تلاش کنید.';
      } finally {
        this.deleteUserBusy = false;
      }
    },
    deleteUserModal(item) {
      this.userId = item.id;
      this.deletedUserName = `${item.user.first_name || ''} ${item.user.last_name || ''}`.trim() || item.user.username;
      this.deleteUserError = '';
      this.showDeleteUserModal = true;
    },
    denySetPass() {
      this.showSetPasswordModal = false;
      this.setPasswordError = '';
      this.changedPasswordItem = { user: { password: '' } };
    },
    async setPassword() {
      if (this.setPasswordBusy) return;
      this.setPasswordBusy = true;
      this.setPasswordError = '';
      try {
        const res = await this.setPasswordApi({
          username: this.changedPasswordItem.user.username,
          password: this.changedPasswordItem.user.password,
        });
        if (res.status !== 200) {
          const data = res.data || {};
          this.setPasswordError = (Array.isArray(data.password) && data.password[0]) || data.detail || 'تغییر رمز انجام نشد.';
          return;
        }
        this.denySetPass();
        this.$notify({ group: 'tc', type: 'success', text: 'رمز ورود تغییر کرد.' });
      } catch (error) {
        this.setPasswordError = 'ارتباط برقرار نشد. دوباره تلاش کنید.';
      } finally {
        this.setPasswordBusy = false;
      }
    },
    async setPasswordApi(data) {
      return this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.POST.USER_SET_PASSWORD +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        '/auth',
        data
      );
    },
    async userEditPost(item) {
      const data = {
        id: item.id,
        role: item.role.id,
        project: item.project.id,
      };
      return this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.POST.USER_EDIT + '?p=' + this.$STORE.state.userConfig.setProjectId,
        '',
        data
      );
    },
    async getDataPackage(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        let res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.GET_USER_LIST +
            '?city=' +
            this.pickCity +
            '&province=' +
            this.pickProvince +
            '&user__first_name=' +
            this.userFirstName +
            '&user__last_name=' +
            this.userLastName +
            '&user__username=' +
            this.phoneNumber +
            '&limit=' +
            limit +
            '&offset=' +
            offset +
            '&is_deleted=false' +
            '&ordering=' +
            this.selected +
            '&p=' +
            this.$STORE.state.userConfig.setProjectId
        );
        if (res.status !== 200) {
          this.listError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        if (res.status === 200) {
          this.dataPackage = res.data.results;
          // this.dataPackage.changedRoleId = this.dataPackage.role.id;
          'here data:', this.dataPackage;
          this.totalDataCount = res.data.count;
        }
      } finally {
        this.loadingList = false;
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
    // async getDataPackage(limit = 20, offset = 0) {
    // 	const res = await this.$ApiServiceLayer.get(
    // 		this.$PATH.RELATIVE_PATH.GET.GET_USER_LIST +
    // 			'?city=' +
    // 			this.pickCity +
    // 			'&province=' +
    // 			this.pickProvince +
    // 			'&user__username=' +
    // 			this.phoneNumber +
    // 			'&limit=' +
    // 			limit +
    // 			'&offset=' +
    // 			offset +
    // 			'&ordering=' +
    // 			this.selected +
    // 			'&p=' + this.$STORE.state.userConfig.setProjectId
    // 			,
    // 		'',
    // 		{},
    // 	);
    // 	if (res.status === 200) {
    // 		this.dataPackage = res.data.results;
    // 		("here data:", this.dataPackage)
    // 		this.totalDataCount = res.data.count;
    // 	}
    // },
    async myCallback() {
      await this.getDataPackage(20, 20 * (this.page - 1));
    },
    visitDetail(id) {
      let routeData = this.$router.resolve({ name: 'answerList', params: { id: id } });
      window.open(routeData.href);
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
    async changeVisitStatus(item) {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.VISITS_STATUS +
          item.id +
          '/' +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH,
        { status: item.status, rejection_reason: item.status === '4' ? 'nadarad' : '' }
      );
      if (res.status === 200) {
        this.$notify({
          group: 'tc',
          type: 'success',
          text: 'وضعیت با موفقیت تغییر پیدا کرد!',
        });
      }
    },
    async changeRole(item) {
      if (this.roleChangingId !== null) return;
      this.roleChangingId = item.id;
      try {
        const res = await this.userEditPost(item);
        if (res.status === 200) {
          this.$notify({ group: 'tc', type: 'success', text: 'نقش کاربر تغییر کرد.' });
        } else {
          this.$notify({ group: 'tc', type: 'error', text: (res.data && res.data.detail) || this.$ApiServiceLayer.getErrorMessage(res) });
        }
      } catch (_) {
        this.$notify({ group: 'tc', type: 'error', text: 'ارتباط برقرار نشد. دوباره تلاش کنید.' });
      } finally {
        this.roleChangingId = null;
        await this.getDataPackage(20, 20 * (this.page - 1));
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
    async getPromoterLists() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_PROMOTER_LIST +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        'promoter:', res.data;
        this.promoterLists = res.data;
      }
    },
  },
};
</script>
