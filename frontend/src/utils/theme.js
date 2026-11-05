/**
 * ECharts 主题感知工具
 * 读取 CSS 变量生成图表配色，监听暗色切换后自动重绘
 */
import echarts from '@/utils/echarts'

const _charts = new Set()
let _listening = false

function _readVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

export function isDark() {
  return document.documentElement.getAttribute('data-theme') === 'dark'
}

/** 当前主题下的图表通用配色 */
export function chartPalette() {
  const dark = isDark()
  return {
    dark,
    text: _readVar('--text-regular', dark ? '#D1D5DB' : '#4B5563'),
    textSecondary: _readVar('--text-secondary', dark ? '#6B7280' : '#9CA3AF'),
    axisLine: dark ? '#374151' : '#E5E7EB',
    splitLine: dark ? '#242838' : '#F3F4F6',
    tooltipBg: dark ? 'rgba(26,29,40,0.95)' : 'rgba(255,255,255,0.95)',
    tooltipBorder: dark ? '#2D3142' : '#E5E7EB',
    tooltipText: dark ? '#F3F4F6' : '#1F2937',
  }
}

/** 常用渐变色板（亮暗通用） */
export const SERIES_COLORS = [
  ['#2D6BFF', '#5B8CFF'],
  ['#22C55E', '#4ADE80'],
  ['#F59E0B', '#FBBF24'],
  ['#EF4444', '#F87171'],
  ['#8B5CF6', '#A78BFA'],
  ['#EC4899', '#F472B6'],
  ['#06B6D4', '#22D3EE'],
  ['#F97316', '#FB923C'],
]

export function linearGradient(colorStops, direction = 'vertical') {
  const coords = direction === 'horizontal'
    ? [0, 0, 1, 0]
    : [0, 0, 0, 1]
  return new echarts.graphic.LinearGradient(...coords, colorStops.map((c, i) => ({
    offset: i / (colorStops.length - 1), color: c
  })))
}

/**
 * 注册图表实例，主题切换时自动调用重绘回调
 * @param {object} chart  echarts 实例
 * @param {Function} render  () => void  重新 setOption 的回调
 */
export function registerChart(chart, render) {
  if (!chart) return
  _charts.add({ chart, render })
  _ensureListener()
}

export function unregisterChart(chart) {
  for (const item of _charts) {
    if (item.chart === chart) _charts.delete(item)
  }
}

function _ensureListener() {
  if (_listening) return
  _listening = true
  const observer = new MutationObserver(() => {
    _charts.forEach(({ chart, render }) => {
      try {
        if (chart && !chart.isDisposed()) render()
      } catch (e) { /* ignore */ }
    })
  })
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
}
