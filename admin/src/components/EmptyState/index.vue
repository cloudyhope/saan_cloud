<template>
  <div class="empty-state" :class="['size-' + size, { inline }]">
    <svg class="art" viewBox="0 0 240 180" aria-hidden="true" focusable="false">
      <!-- Shared scene: ground shadow, soft backdrop and a few quiet sparkles. -->
      <ellipse cx="120" cy="156" rx="84" ry="9" class="soft" />
      <circle cx="120" cy="86" r="68" class="soft" />
      <g class="sparkle"><path d="M42 52v10M37 57h10" /><path d="M200 38v8M196 42h8" /><path d="M208 118v8M204 122h8" /><circle cx="52" cy="112" r="2.4" /><circle cx="190" cy="70" r="2" /></g>

      <!-- The elevator cabin is the brand motif: doors open a little more or less depending on the story. -->
      <g v-if="hasCabin">
        <!-- floor display, frame, doors and the call button: reads as an elevator at a glance -->
        <rect x="98" y="20" width="44" height="16" rx="8" class="ink" /><path d="M110 24l4.5 8h-9z" class="accent" /><path d="M130 32l4.5-8h-9z" class="paper-fill" />
        <rect x="86" y="42" width="68" height="102" rx="9" class="paper ink-stroke" />
        <rect x="94" y="52" width="52" height="86" rx="4" class="soft2" />
        <template v-if="kind !== 'error'">
          <rect :x="94" y="52" :width="26 - gap / 2" height="86" rx="3" class="primary" />
          <rect :x="120 + gap / 2" y="52" :width="26 - gap / 2" height="86" rx="3" class="primary" />
          <path :d="`M${99} 60v70M${125 + gap / 2} 60v70`" class="shine" />
        </template>
        <template v-else>
          <rect x="94" y="52" width="22" height="86" rx="3" class="primary" />
          <g transform="rotate(-9 134 138)"><rect x="124" y="54" width="22" height="84" rx="3" class="primary" /></g>
        </template>
        <rect x="64" y="84" width="14" height="30" rx="7" class="paper ink-stroke" /><circle cx="71" cy="94" r="3" class="accent" /><circle cx="71" cy="104" r="3" class="soft2" />
      </g>

      <g v-if="kind === 'visits'"><!-- clipboard checklist -->
        <g transform="translate(136 82)"><rect width="50" height="62" rx="7" class="paper ink-stroke" /><rect x="14" y="-5" width="22" height="10" rx="4" class="ink" />
          <path d="M11 20l4 4 7-8" class="ok-line" /><path d="M28 21h13M11 36h4M20 36h21M11 50h4M20 50h15" class="line" /></g>
      </g>

      <g v-else-if="kind === 'search'"><!-- magnifier -->
        <circle cx="160" cy="104" r="22" class="glass ink-stroke" /><path d="M150 96a13 13 0 0 1 10-6" class="glare" />
        <path d="M176 120l17 17" class="handle" />
      </g>

      <g v-else-if="kind === 'notifications'"><!-- calm bell with a settled check -->
        <path d="M120 40c-21 0-33 15-33 35v17l-10 16h86l-10-16V75c0-20-12-35-33-35z" class="primary ink-stroke" />
        <circle cx="120" cy="36" r="5" class="ink" /><path d="M110 117a10 10 0 0 0 20 0" class="ink-stroke paper" />
        <path d="M70 62c-5 7-5 16 0 23M170 62c5 7 5 16 0 23" class="wave" />
        <circle cx="160" cy="48" r="15" class="ok" /><path d="M153 48l5 5 9-10" class="check" />
      </g>

      <g v-else-if="kind === 'chat'"><!-- two conversation bubbles -->
        <path d="M74 46h84a14 14 0 0 1 14 14v28a14 14 0 0 1-14 14h-46l-18 14v-14H74a14 14 0 0 1-14-14V60a14 14 0 0 1 14-14z" class="primary ink-stroke" />
        <circle cx="96" cy="74" r="4.5" class="paper" /><circle cx="116" cy="74" r="4.5" class="paper" /><circle cx="136" cy="74" r="4.5" class="paper" />
        <path d="M150 112h26a12 12 0 0 1 12 12v8a12 12 0 0 1-12 12h-6v12l-14-12h-6a12 12 0 0 1-12-12v-8a12 12 0 0 1 12-12z" class="paper ink-stroke" />
        <path d="M152 126h22M152 136h14" class="line" />
      </g>

      <g v-else-if="kind === 'parts'"><!-- parts box and gear -->
        <rect x="68" y="78" width="82" height="64" rx="7" class="paper ink-stroke" /><rect x="68" y="78" width="82" height="18" rx="6" class="primary ink-stroke" />
        <rect x="104" y="78" width="10" height="28" class="accent ink-stroke" /><path d="M82 118h22M82 128h14" class="line" />
        <circle cx="170" cy="66" r="19" class="gear-teeth" /><circle cx="170" cy="66" r="14" class="soft2 ink-stroke" /><circle cx="170" cy="66" r="5.5" class="ink" />
      </g>

      <g v-else-if="kind === 'history'"><!-- clock with a rewind arrow -->
        <circle cx="120" cy="86" r="44" class="paper ink-stroke" /><path d="M120 86V62M120 86l17 10" class="ink-line" /><circle cx="120" cy="86" r="4" class="ink" />
        <path d="M120 49v5M157 86h-5M120 123v-5M83 86h5" class="line" />
        <path d="M66 62a58 58 0 0 1 100-12" class="arrow" /><path d="M170 36l-2 17-16-6z" class="primary-fill" />
      </g>

      <g v-else-if="kind === 'photos'"><!-- camera and a photo card -->
        <g transform="rotate(8 176 60)"><rect x="152" y="40" width="48" height="40" rx="6" class="paper ink-stroke" /><path d="M158 74l12-14 9 10 6-7 10 11z" class="soft2" /><circle cx="186" cy="52" r="4" class="accent" /></g>
        <rect x="64" y="66" width="96" height="68" rx="12" class="paper ink-stroke" /><rect x="92" y="56" width="40" height="14" rx="5" class="ink" />
        <circle cx="112" cy="100" r="22" class="primary ink-stroke" /><circle cx="112" cy="100" r="11" class="soft2" /><path d="M105 95a8 8 0 0 1 8-4" class="glare" />
        <circle cx="146" cy="78" r="3.5" class="accent" />
      </g>

      <g v-else-if="kind === 'documents'"><!-- stacked documents -->
        <path d="M100 48h44l22 22v70a6 6 0 0 1-6 6h-60a6 6 0 0 1-6-6V54a6 6 0 0 1 6-6z" class="soft2 ink-stroke" transform="rotate(7 120 100)" />
        <path d="M86 40h44l24 24v78a6 6 0 0 1-6 6H86a6 6 0 0 1-6-6V46a6 6 0 0 1 6-6z" class="paper ink-stroke" />
        <path d="M130 40v18a6 6 0 0 0 6 6h18" class="primary ink-stroke" /><path d="M94 86h46M94 100h46M94 114h30" class="line" />
      </g>

      <g v-else-if="kind === 'building'"><!-- building with its elevator tower -->
        <rect x="78" y="42" width="66" height="100" rx="5" class="paper ink-stroke" />
        <g class="soft2"><rect x="88" y="54" width="14" height="12" rx="2" /><rect x="110" y="54" width="14" height="12" rx="2" /><rect x="88" y="76" width="14" height="12" rx="2" /><rect x="110" y="76" width="14" height="12" rx="2" /><rect x="88" y="98" width="14" height="12" rx="2" /></g>
        <rect x="110" y="98" width="14" height="12" rx="2" class="accent" /><rect x="100" y="120" width="22" height="22" rx="3" class="ink" />
        <rect x="144" y="70" width="30" height="72" rx="5" class="primary ink-stroke" /><rect x="150" y="104" width="18" height="26" rx="2" class="paper" />
        <path d="M159 80l-4 6h8zM159 96l-4-6h8z" class="paper-fill" />
      </g>

      <g v-else-if="kind === 'done'"><!-- all clear -->
        <circle cx="168" cy="54" r="21" class="ok ink-stroke" /><path d="M158 54l8 8 14-15" class="check" />
        <path d="M70 70l5 5M74 66l-5 5" class="line" /><path d="M186 100l5 5M190 96l-5 5" class="line" />
      </g>

      <g v-else-if="kind === 'error'"><!-- cabin out of order -->
        <path d="M120 20V10" class="ink-line" /><path d="M106 12l-6-4M134 12l6-4M120 4V0" class="spark" />
        <path d="M168 82l25 44h-50z" class="accent ink-stroke" /><path d="M168 98v14" class="ink-line" /><circle cx="168" cy="119" r="2.4" class="ink" />
      </g>

      <g v-else-if="kind === 'wallet'"><!-- cards -->
        <g transform="rotate(-9 120 90)"><rect x="76" y="54" width="94" height="60" rx="9" class="soft2 ink-stroke" /></g>
        <rect x="68" y="70" width="104" height="66" rx="10" class="primary ink-stroke" /><rect x="68" y="86" width="104" height="14" class="ink" />
        <rect x="80" y="112" width="26" height="14" rx="3" class="accent ink-stroke" /><path d="M126 120h34" class="paper-line" />
      </g>

      <g v-else-if="kind === 'warranty'"><!-- shield -->
        <path d="M120 38l46 15v34c0 29-19 47-46 59-27-12-46-30-46-59V53z" class="paper ink-stroke" />
        <path d="M120 54l30 10v23c0 19-12 31-30 40-18-9-30-21-30-40V64z" class="primary" /><path d="M105 90l11 11 20-22" class="check" />
      </g>
    </svg>
    <h3 v-if="heading" class="title">{{ heading }}</h3>
    <p v-if="text" class="text">{{ text }}</p>
    <div v-if="$slots.default" class="actions"><slot /></div>
  </div>
</template>

<script>
// Brand illustrations for empty and error states. Colours come from CSS variables so each app can theme
// them (see the defaults below); every piece is decorative, the copy carries the meaning.
const COPY = {
  visits: ['مأموریتی در این بخش نیست', 'وقتی مأموریت تازه‌ای برنامه‌ریزی شود، همین‌جا دیده می‌شود.'],
  search: ['نتیجه‌ای پیدا نشد', 'فیلترها یا عبارت جستجو را تغییر دهید.'],
  notifications: ['اعلان تازه‌ای ندارید', 'رویدادهای مهم شما همین‌جا نمایش داده می‌شود.'],
  chat: ['هنوز گفتگویی شروع نشده', 'پیام‌ها پس از ارسال در این بخش دیده می‌شوند.'],
  parts: ['درخواستی ثبت نشده', 'درخواست قطعه و تحویل آن در این بخش دنبال می‌شود.'],
  history: ['سابقه‌ای وجود ندارد', 'پس از ثبت اولین گزارش، سوابق اینجا جمع می‌شوند.'],
  photos: ['تصویری ثبت نشده', 'عکس‌های ثبت‌شده در این بخش نمایش داده می‌شوند.'],
  documents: ['سندی وجود ندارد', 'فایل‌ها و مستندات پس از بارگذاری اینجا دیده می‌شوند.'],
  building: ['ساختمانی ثبت نشده', 'ساختمان‌ها و آسانسورها پس از ثبت اینجا فهرست می‌شوند.'],
  done: ['همه‌چیز مرتب است', 'کار معوقی باقی نمانده است.'],
  error: ['دریافت اطلاعات انجام نشد', 'اتصال را بررسی کنید و دوباره تلاش کنید.'],
  wallet: ['تراکنشی ثبت نشده', 'فاکتورها و پرداخت‌ها پس از ثبت اینجا دیده می‌شوند.'],
  warranty: ['موردی ثبت نشده', 'درخواست‌های گارانتی و تعمیر اینجا دنبال می‌شوند.'],
  generic: ['موردی برای نمایش نیست', 'پس از ثبت اطلاعات، این بخش پر می‌شود.'],
};
const GAPS = { visits: 10, search: 14, generic: 12, done: 24 };

export default {
  name: 'EmptyState',
  props: {
    kind: { type: String, default: 'generic', validator: (value) => Object.prototype.hasOwnProperty.call(COPY, value) },
    title: { type: String, default: '' },
    description: { type: String, default: null }, // '' hides the line; null uses the default copy
    size: { type: String, default: 'md' }, // md | sm
    inline: Boolean,
  },
  computed: {
    hasCabin() { return ['visits', 'search', 'generic', 'done', 'error'].includes(this.kind); },
    gap() { return GAPS[this.kind] || 0; },
    heading() { return this.title || COPY[this.kind][0]; },
    text() { return this.description === null ? COPY[this.kind][1] : this.description; },
  },
};
</script>

<style scoped>
.empty-state {
  --ill-ink: var(--empty-ink, #16264a); --ill-primary: var(--empty-primary, #345de0); --ill-soft: var(--empty-soft, #eef2ff);
  --ill-soft2: var(--empty-soft2, #d9e3ff); --ill-accent: var(--empty-accent, #fab219); --ill-ok: var(--empty-ok, #19b36b);
  display: flex; flex-direction: column; align-items: center; text-align: center; padding: 28px 16px; color: var(--ill-ink);
}
.empty-state.inline { padding: 12px 8px; }
.art { width: 208px; max-width: 70%; height: auto; }
.size-sm .art { width: 140px; }
.title { margin: 6px 0 0; font-size: 16px; font-weight: 800; color: var(--empty-title, #25324b); line-height: 1.6; }
.size-sm .title { font-size: 14px; }
.text { margin: 4px 0 0; max-width: 340px; font-size: 12.5px; color: var(--empty-text, #6b778d); line-height: 1.9; }
.actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin-top: 14px; }

.soft { fill: var(--ill-soft); }
.soft2 { fill: var(--ill-soft2); }
.paper { fill: #fff; }
.primary { fill: var(--ill-primary); }
.primary-fill { fill: var(--ill-primary); }
.paper-fill { fill: #fff; }
.ink { fill: var(--ill-ink); }
.accent { fill: var(--ill-accent); }
.ok { fill: var(--ill-ok); }
.glass { fill: var(--ill-soft2); }
.ink-stroke { stroke: var(--ill-ink); stroke-width: 3; stroke-linejoin: round; }
.ink-line { fill: none; stroke: var(--ill-ink); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
.line { fill: none; stroke: var(--ill-soft2); stroke-width: 3.2; stroke-linecap: round; }
.paper-line { fill: none; stroke: #fff; stroke-width: 3.2; stroke-linecap: round; opacity: .85; }
.shine { fill: none; stroke: #fff; stroke-width: 2; stroke-linecap: round; opacity: .35; }
.sparkle { fill: var(--ill-soft2); stroke: var(--ill-soft2); stroke-width: 2.2; stroke-linecap: round; }
.sparkle circle { stroke: none; }
.check { fill: none; stroke: #fff; stroke-width: 4.2; stroke-linecap: round; stroke-linejoin: round; }
.ok-line { fill: none; stroke: var(--ill-ok); stroke-width: 3.4; stroke-linecap: round; stroke-linejoin: round; }
.wave { fill: none; stroke: var(--ill-soft2); stroke-width: 4; stroke-linecap: round; }
.glare { fill: none; stroke: #fff; stroke-width: 3; stroke-linecap: round; opacity: .8; }
.handle { fill: none; stroke: var(--ill-ink); stroke-width: 7; stroke-linecap: round; }
.arrow { fill: none; stroke: var(--ill-primary); stroke-width: 5; stroke-linecap: round; }
.spark { fill: none; stroke: var(--ill-accent); stroke-width: 3; stroke-linecap: round; }
.gear-teeth { fill: none; stroke: var(--ill-ink); stroke-width: 7; stroke-dasharray: 4.2 10.4; }
</style>
