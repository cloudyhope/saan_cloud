<template>
  <div>
    <BaseTopBar title="تماس با ما" />
    <div class="contact-container">
      <!-- Company Information Section -->
      <div class="info-section">
        <h3 class="section-title">اطلاعات شرکت</h3>
        
        <!-- Phone Number -->
        <div class="contact-item">
          <div class="contact-icon">
            <img src="@/assets/images/Icons/phone.svg" alt="phone" />
          </div>
          <div class="contact-content">
            <div class="contact-label">شماره تماس شرکت</div>
            <div class="contact-value">021-91079187</div>
          </div>
        </div>

        <!-- Office Address -->
        <div class="contact-item">
          <div class="contact-icon">
            <img src="@/assets/images/Icons/location.svg" alt="location" />
          </div>
          <div class="contact-content">
            <div class="contact-label">آدرس دفتر</div>
            <div class="contact-value">تهران، خیابان دماوند، حدفاصل سیلان و وحیدیه، روبروی خیابان بخت‌آزاد، پلاک 846، طبقه سوم</div>
          </div>
        </div>

        <!-- Warehouse Address -->
        <div class="contact-item">
          <div class="contact-icon">
            <img src="@/assets/images/Icons/store.svg" alt="warehouse" />
          </div>
          <div class="contact-content">
            <div class="contact-label">ساختمان اداری مرکزی:</div>
            <div class="contact-value">تهران، بزرگراه آیت‌الله آشتیانی، بلوار شقایق (جوانمرد)، نبش کوچه دوم، پلاک 3</div>
          </div>
        </div>
        <div class="contact-item">
          <div class="contact-icon">
            <img src="@/assets/images/Icons/store.svg" alt="warehouse" />
          </div>
          <div class="contact-content">
            <div class="contact-label">دفتر استان قم:</div>
            <div class="contact-value">بلوار امام رضا، مجتمع تجاری‌مسکونی فردوس، پلاک جنوبی، طبقه زیرزمین، واحد شماره 33</div>
          </div>
        </div>

        <!-- Email -->
        <div class="contact-item">
          <div class="contact-icon">
            <img src="@/assets/images/Icons/mail.svg" alt="email" />
          </div>
          <div class="contact-content">
            <div class="contact-label">ایمیل</div>
            <div class="contact-value">info@behsanariansaman.com</div>
          </div>
        </div>
      </div>

      <!-- Working Hours Section -->
      <div class="info-section">
        <h3 class="section-title">ساعات کاری</h3>
        
        <div class="working-hours">
          <div class="hours-item">
            <span class="day">شنبه تا چهارشنبه:</span>
            <span class="time">۸:۰۰ صبح تا ۶:۰۰ عصر</span>
          </div>
          <div class="hours-item">
            <span class="day">پنجشنبه:</span>
            <span class="time">۸:۰۰ صبح تا ۲:۰۰ عصر</span>
          </div>
          <div class="hours-item">
            <span class="day">جمعه:</span>
            <span class="time">تعطیل</span>
          </div>
        </div>
      </div>

      <!-- Support Section -->
      <div class="info-section">
        <h3 class="section-title">پشتیبانی</h3>
        
        <div class="support-item">
          <div class="support-icon">
            <img src="@/assets/images/Icons/call-us.svg" alt="support" />
          </div>
          <div class="support-content">
            <div class="support-label">خط واتساپ</div>
            <div class="support-value">0912-4945334</div>
            <!-- <div class="support-note">شنبه تا چهارشنبه: ۸ صبح تا ۸ شب</div> -->
          </div>
        </div>
        <div class="support-item">
          <div class="support-icon">
            <img src="@/assets/images/Icons/call-us.svg" alt="support" />
          </div>
          <div class="support-content">
            <div class="support-label">خط تلگرام</div>
            <div class="support-value">0911-1099440</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";

export default {
  components: {
    BaseTopBar,
  },
};
</script>

<style lang="scss" scoped>
.contact-container {
  padding: 20px;
}

.info-section {
  margin-bottom: 32px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #404041;
  margin-bottom: 16px;
  text-align: right;
}

.contact-item {
  display: flex;
  align-items: flex-start;
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  margin-bottom: 12px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.contact-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eaf1fb 0%, #f4f9ff 100%);
  border-radius: 8px;
  padding: 12px;
  min-width: 48px;
  height: 48px;
  margin-left: 16px;
  
  img {
    width: 20px;
    height: 20px;
  }
}

.contact-content {
  flex: 1;
}

.contact-label {
  font-size: 14px;
  color: #7F7F80;
  margin-bottom: 4px;
  font-weight: 400;
}

.contact-value {
  font-size: 16px;
  color: #404041;
  font-weight: 500;
  line-height: 1.4;
}

.working-hours {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  padding: 16px;
}

.hours-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f1f3f4;
  
  &:last-child {
    border-bottom: none;
  }
}

.day {
  font-size: 14px;
  color: #404041;
  font-weight: 500;
}

.time {
  font-size: 14px;
  color: #7F7F80;
  font-weight: 400;
}

.support-item {
  display: flex;
  align-items: flex-start;
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  margin-bottom: 16px;
}

.support-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eaf1fb 0%, #f4f9ff 100%);
  border-radius: 8px;
  padding: 12px;
  min-width: 48px;
  height: 48px;
  margin-left: 16px;
  
  img {
    width: 20px;
    height: 20px;
  }
}

.support-content {
  flex: 1;
}

.support-label {
  font-size: 14px;
  color: #7F7F80;
  margin-bottom: 4px;
  font-weight: 400;
}

.support-value {
  font-size: 16px;
  color: #404041;
  font-weight: 500;
  margin-bottom: 4px;
}

.support-note {
  font-size: 12px;
  color: #7F7F80;
  font-weight: 400;
}
</style>
  