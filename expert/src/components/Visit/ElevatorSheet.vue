<template>
  <v-bottom-sheet :value="value" max-width="576px" @input="$emit('input', $event)">
    <v-sheet class="vf-sheet" role="dialog" aria-labelledby="elevator-sheet-title">
      <div class="vf-sheet-handle" aria-hidden="true" />
      <div class="vf-sheet-head">
        <div>
          <span class="vf-muted">مشخصات فنی</span>
          <h2 id="elevator-sheet-title">{{ elevator ? elevator.title || 'آسانسور' : 'آسانسور' }}</h2>
        </div>
        <button type="button" class="vf-icon-btn" aria-label="بستن" @click="$emit('input', false)">
          <v-icon size="22">mdi-close</v-icon>
        </button>
      </div>
      <template v-if="elevator">
        <section v-if="context" class="elevator-section">
          <h3>قطعات نصب‌شده</h3>
          <p v-if="!context.installed.length" class="vf-muted context-empty">قطعه‌ای با سریال برای این آسانسور ثبت نشده است.</p>
          <ul v-else class="context-list">
            <li v-for="part in context.installed" :key="part.id"><strong>{{ part.model }}</strong>
              <span><span v-if="part.serial" class="vf-ltr">{{ part.serial }}</span>{{ part.installed_at ? ' · نصب ' + faDate(part.installed_at) : '' }}</span></li>
          </ul>
        </section>
        <section v-if="context" class="elevator-section">
          <h3>سوابق خدمت این آسانسور</h3>
          <p v-if="!context.history.length" class="vf-muted context-empty">سابقه خدمت ثبت‌شده‌ای ندارد.</p>
          <ul v-else class="context-list">
            <li v-for="row in context.history" :key="row.id"><strong>{{ row.type || 'خدمت' }} · {{ statusLabel(row.status) }}</strong>
              <span>{{ faDate(row.date) }}{{ row.expert ? ' · ' + row.expert : '' }}</span>
              <span v-if="row.note" class="context-note">{{ row.note }}</span></li>
          </ul>
        </section>
        <div v-if="!filledSections.length" class="vf-empty">
          <v-icon color="#7c9aa9" size="30">mdi-file-question-outline</v-icon>
          مشخصات فنی این آسانسور هنوز ثبت نشده است.
        </div>
        <section v-for="section in filledSections" :key="section.title" class="elevator-section">
          <h3>{{ section.title }}</h3>
          <dl class="vf-kv">
            <div v-for="row in section.rows" :key="row.key" class="vf-kv-row">
              <dt>{{ row.label }}</dt><dd :class="{ 'vf-ltr': row.ltr }">{{ row.value }}</dd>
            </div>
          </dl>
        </section>
        <p v-if="missingCount" class="vf-muted elevator-missing">{{ faNumber(missingCount) }} مورد ثبت نشده است و نمایش داده نمی‌شود.</p>
      </template>
    </v-sheet>
  </v-bottom-sheet>
</template>

<script>
import { ELEVATOR_SECTIONS, elevatorValue, faDate, faNumber, visitStatus } from '@/utils/visitFlow';

export default {
  name: 'ElevatorSheet',
  props: {
    value: { type: Boolean, default: false }, elevator: { type: Object, default: null },
    // Installed parts and recent service history (VisitAssetContextView), when available.
    context: { type: Object, default: null },
  },
  computed: {
    sections() {
      const elevator = this.elevator || {};
      return ELEVATOR_SECTIONS.map(section => ({
        title: section.title,
        rows: section.fields.map(([key, label]) => ({
          key, label, value: elevatorValue(elevator[key]), ltr: /serial|voltage/.test(key),
        })),
      }));
    },
    filledSections() {
      return this.sections.map(section => ({ ...section, rows: section.rows.filter(row => row.value) }))
        .filter(section => section.rows.length);
    },
    missingCount() {
      return this.sections.reduce((total, section) => total + section.rows.filter(row => !row.value).length, 0);
    },
  },
  methods: { faNumber, faDate, statusLabel: status => visitStatus(status).label },
};
</script>

<style scoped>
.elevator-section { border: 1px solid var(--vf-line); border-radius: 16px; padding: 14px; margin-bottom: 12px; }
.elevator-section h3 { font-size: 13.5px; font-weight: 800; margin: 0 0 10px; color: var(--vf-brand); }
.elevator-missing { text-align: center; margin: 4px 0 0; }
.context-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.context-list li { display: grid; font-size: 12.5px; padding-bottom: 8px; border-bottom: 1px solid #edf2f5; }
.context-list li:last-child { border-bottom: 0; padding-bottom: 0; }
.context-list span { color: var(--vf-muted); font-size: 11.5px; }
.context-list .context-note { color: #7a4d0f; }
.context-empty { margin: 0; }
</style>
