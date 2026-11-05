<template>
  <span class="count-up" :class="{ 'is-prefix': prefix, 'is-suffix': suffix }">
    <span v-if="prefix" class="count-prefix">{{ prefix }}</span>
    <span class="count-value">{{ displayValue }}</span>
    <span v-if="suffix" class="count-suffix">{{ suffix }}</span>
  </span>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps({
  endValue: { type: [Number, String], default: 0 },
  startValue: { type: Number, default: 0 },
  duration: { type: Number, default: 1500 },
  decimals: { type: Number, default: 0 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  separator: { type: String, default: ',' },
  delay: { type: Number, default: 0 },
  easing: { type: String, default: 'easeOutExpo' },
})

const displayValue = ref('0')
let rafId = null
let startTime = null

const easingFns = {
  linear: t => t,
  easeOutExpo: t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t),
  easeOutCubic: t => 1 - Math.pow(1 - t, 3),
  easeOutQuart: t => 1 - Math.pow(1 - t, 4),
  easeOutBack: t => {
    const c1 = 1.70158
    const c3 = c1 + 1
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
  },
}

const formatNumber = (num) => {
  const fixed = Number(num).toFixed(props.decimals)
  if (!props.separator) return fixed
  const parts = fixed.split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, props.separator)
  return parts.join('.')
}

const animate = (timestamp) => {
  if (!startTime) startTime = timestamp
  const progress = Math.min((timestamp - startTime) / props.duration, 1)
  const eased = easingFns[props.easing]?.(progress) || progress
  const current = props.startValue + (Number(props.endValue) - props.startValue) * eased
  displayValue.value = formatNumber(current)

  if (progress < 1) {
    rafId = requestAnimationFrame(animate)
  }
}

const startAnimation = () => {
  cancelAnimationFrame(rafId)
  startTime = null
  displayValue.value = formatNumber(props.startValue)
  if (props.delay > 0) {
    setTimeout(() => { rafId = requestAnimationFrame(animate) }, props.delay)
  } else {
    rafId = requestAnimationFrame(animate)
  }
}

watch(() => props.endValue, () => { startAnimation() })

onMounted(() => { startAnimation() })
onUnmounted(() => { cancelAnimationFrame(rafId) })
</script>

<style scoped>
.count-up {
  display: inline-flex;
  align-items: baseline;
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}

.count-value {
  font-weight: inherit;
  font-size: inherit;
  color: inherit;
  line-height: inherit;
}

.count-prefix {
  margin-right: 2px;
  font-size: 0.6em;
  opacity: 0.7;
}

.count-suffix {
  margin-left: 4px;
  font-size: 0.55em;
  font-weight: 500;
  opacity: 0.65;
}
</style>
