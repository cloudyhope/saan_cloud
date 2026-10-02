<template>
  <div>
    <BaseTopBar title="درباره ما" />

    <div class="about-content">
      <!-- About Text Section -->
      <v-card elevation="0" class="about-section ma-5">
        <h2 class="section-title">شرکت ما</h2>
        <p class="about-text">
          شرکت بهسان آریان سامان با بهره‌گیری از پرسنل مجرب و مطابق با الگوی
          استانداردهای سیستم مدیریت کیفیت، مدیریت رضایت مشتریان، مدیریت رسیدگی
          به شکایات مشتریان، مدیریت اندازه گیری و پایش رضایت مشتریان، رعایت
          مسئولیت های اجتماعی، مدیریت مقررات‌ ایمنی و بهداشت حرفه ای ، مدیریت
          زیست محیطی و مدیریت حقوق مشتری که موفق به اخذ آن شده است، همواره تلاش
          می نماید تا در جهت ارائه خدمات متفاوت و متمایز رسالت خود را در صنف
          آسانسور کشور به انجام رساند.
        </p>
      </v-card>

      <!-- Services Section -->
      <v-card elevation="0" class="services-section ma-5">
        <h2 class="section-title">خدمات ما</h2>
        <div class="services-list">
          <div
            class="service-item"
            v-for="(service, index) in services"
            :key="index"
          >
            <!-- <div class="service-icon">
              <img
                src="@/assets/images/Icons/check-circle-outline.svg"
                alt="check"
              />
            </div> -->
            <span class="service-text">{{ service }}</span>
          </div>
        </div>
      </v-card>

      <!-- Licenses Section -->
      <v-card elevation="0" class="licenses-section ma-5">
        <h2 class="section-title">افتخارات</h2>
        <div class="licenses-grid">
          <div
            class="license-item"
            v-for="(license, index) in licenses"
            :key="index"
          >
            <div class="license-image">
              <img :src="license" :alt="`License ${index + 1}`" />
            </div>
          </div>
        </div>
      </v-card>
    </div>
  </div>
</template>

<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";

export default {
  name: "AboutUs",
  components: {
    BaseTopBar,
  },
  data() {
    return {
      services: [
        "تولید و فروش پکیج الکتریکال آسانسور با نام تجاری بلوایپ تحت لیسانس بلولایت چین",
        "ارائه خدمات بازسازی و ارتقاء آسانسورهای قدیمی",
        "کارشناسی و مشاوره خرید تابلوفرمان",
        "تامین و فروش قطعات یدکی",
        "رفع خرابی بخش الکتریکی آسانسور",
        "راه اندازی و تنطیم مجدد انواع اینورتر و کنترلر",
        "تعمیرات انواع بردهای الکترونیک، یو پی اس و اینورتر",
      ],
      licenses: [
        require("@/assets/images/1.jpeg"),
        require("@/assets/images/2.jpeg"),
        require("@/assets/images/3.jpeg"),
        require("@/assets/images/4.jpeg"),
        require("@/assets/images/5.jpeg"),
        require("@/assets/images/6.jpeg"),
        require("@/assets/images/7.jpeg"),
        require("@/assets/images/8.jpeg"),
      ],
    };
  },
};
</script>

<style lang="scss" scoped>
.about-section,
.services-section,
.licenses-section {
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  margin-bottom: 16px;
  border-radius: 12px;
  padding: 20px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--white-color);
  margin: 0 0 20px 0;
  text-align: center;
//   text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.about-text {
  font-size: 16px;
  line-height: 28px;
  color: var(--white-color);
  text-align: justify;
  margin: 0;
}

.services-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.service-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 18px;
  background: linear-gradient(
    135deg,
    rgba(53, 122, 225, 0.1) 0%,
    rgba(53, 122, 225, 0.05) 100%
  );
  border-radius: 12px;
  border-right: 4px solid #357ae1;
  box-shadow: 0 4px 12px rgba(53, 122, 225, 0.15);
  transition: all 0.3s ease;
}

.service-item:hover {
  transform: translateX(-5px);
  background: linear-gradient(
    135deg,
    rgba(53, 122, 225, 0.15) 0%,
    rgba(53, 122, 225, 0.1) 100%
  );
  box-shadow: 0 6px 20px rgba(53, 122, 225, 0.25);
}

.service-icon {
  flex-shrink: 0;
  margin-top: 2px;

  img {
    width: 20px;
    height: 20px;
    filter: brightness(0) invert(1);
  }
}

.service-text {
  font-size: 14px;
  line-height: 22px;
  color: var(--white-color);
  margin: 0;
  font-weight: 500;
}

.licenses-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-top: 20px;
}

.license-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 8px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.05) 100%
  );
  border-radius: 16px;
  border: 2px solid rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.license-item:hover {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.15) 0%,
    rgba(255, 255, 255, 0.1) 100%
  );
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.25);
  border-color: rgba(255, 255, 255, 0.25);
}

.license-image {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 320px;
  height: 320px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
//   padding: 20px;
  //   box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);

  img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 12px;
    filter: none;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .licenses-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .service-item {
    padding: 16px;
  }

  .license-item {
    padding: 16px;
  }

  .license-image {
    width: 160px;
    height: 160px;
  }
}

@media (max-width: 480px) {
  .about-section,
  .services-section,
  .licenses-section {
    margin: 10px;
    padding: 16px;
  }

  .section-title {
    font-size: 18px;
  }

  .about-text {
    font-size: 14px;
    line-height: 24px;
  }

  .service-text {
    font-size: 12px;
    line-height: 20px;
  }

  .licenses-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .license-image {
    width: 120px;
    height: 120px;
  }
}
</style>
