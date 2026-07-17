<template>
  <div class="calendar-widget shadow-sm" style="height: 100%;">
    <div class="calendar-header">
      <button @click="changeMonth(-1)">&lt;</button>
      <span>{{ monthYearLabel }}</span>
      <button @click="changeMonth(1)">&gt;</button>
    </div>
    <div class="calendar-grid">
      <div v-for="day in dayNames" :key="day" class="calendar-day-name">{{ day }}</div>
      <div v-for="n in firstDayOffset" :key="'empty-' + n" class="calendar-day empty"></div>
      <div v-for="day in daysInMonth" :key="day"
           class="calendar-day"
           :class="{ 'has-entry': calendarData[formatDate(day)], 'selected': modelValue === formatDate(day) }"
           :style="{ '--mood-color': calendarData[formatDate(day)] || 'var(--text-main)' }"
           @click="selectDate(day)">
        {{ day }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api'

const props = defineProps({
  modelValue: String // YYYY-MM-DD
})
const emit = defineEmits(['update:modelValue'])

const currentMonth = ref(new Date().getMonth())
const currentYear = ref(new Date().getFullYear())
const calendarData = ref({})

const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December']
const dayNames = ['S', 'M', 'T', 'W', 'T', 'F', 'S']

const monthYearLabel = computed(() => `${monthNames[currentMonth.value]} ${currentYear.value}`)
const firstDayOffset = computed(() => new Date(currentYear.value, currentMonth.value, 1).getDay())
const daysInMonth = computed(() => new Date(currentYear.value, currentMonth.value + 1, 0).getDate())

const formatDate = (day) => {
  const m = String(currentMonth.value + 1).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  return `${currentYear.value}-${m}-${d}`
}

const changeMonth = (offset) => {
  currentMonth.value += offset
  if (currentMonth.value > 11) {
    currentMonth.value = 0
    currentYear.value++
  } else if (currentMonth.value < 0) {
    currentMonth.value = 11
    currentYear.value--
  }
}

const selectDate = (day) => {
  emit('update:modelValue', formatDate(day))
}

// Sync calendar view when modelValue changes externally (e.g. via date input)
watch(() => props.modelValue, (val) => {
  if (val) {
    const date = new Date(val)
    if (!isNaN(date)) {
      currentYear.value = date.getFullYear()
      currentMonth.value = date.getMonth()
    }
  }
})

onMounted(async () => {
  if (props.modelValue) {
    const date = new Date(props.modelValue)
    if (!isNaN(date)) {
      currentYear.value = date.getFullYear()
      currentMonth.value = date.getMonth()
    }
  }

  try {
    const { data } = await api.get('/api/dates')
    calendarData.value = data
  } catch (e) {
    console.error('Failed to fetch calendar data', e)
  }
})
</script>
