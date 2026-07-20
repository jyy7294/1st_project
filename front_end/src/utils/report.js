// 소비 리포트의 계산만 모아둔 곳. 화면(Report.jsx)은 여기 결과를 그리기만 합니다.

import { CATEGORY_COLORS, DEFAULT_CATEGORY_COLOR } from '../data/report.js'

// 꺾은선 그래프 좌표계 (SVG viewBox 300×150 기준)
const WIDTH = 300
const HEIGHT = 150
const PAD_LEFT = 34
const PAD_RIGHT = 6
const PAD_TOP = 8
const PAD_BOTTOM = 26
const DAYS = 31 // 한 달을 31일로 그립니다
const TODAY = 12 // 이번 달은 12일까지 그립니다
const Y_MAX = 4000000 // Y축 상단 = 400만원

const xOf = (day) => PAD_LEFT + ((day - 1) / (DAYS - 1)) * (WIDTH - PAD_LEFT - PAD_RIGHT)
const yOf = (won) => HEIGHT - PAD_BOTTOM - (won / Y_MAX) * (HEIGHT - PAD_BOTTOM - PAD_TOP)

/**
 * 일별 누적 비율. 주말에 지출이 몰리고 평일은 완만한 실제 소비 패턴을 흉내냅니다.
 * seed 를 달리하면 달마다 곡선 모양이 달라집니다.
 * @returns {number[]} 길이 days, 마지막 값이 1인 누적 비율
 */
function cumulativeFractions(days, seed) {
  const acc = []
  let sum = 0

  for (let day = 1; day <= days; day++) {
    const weekday = (day + seed) % 7
    let increment
    if (weekday === 1) increment = 0.1
    else if (weekday === 4) increment = 0.15
    else if (weekday === 6) increment = 2.6
    else if (weekday === 0) increment = 1.9
    else increment = 0.5 + ((day * seed + 2) % 4) * 0.3

    sum += increment
    acc.push(sum)
  }

  return acc.map((v) => v / sum)
}

function polyline(total, days, seed) {
  const fractions = cumulativeFractions(days, seed)
  const points = []
  for (let day = 1; day <= days; day++) {
    points.push(`${xOf(day).toFixed(1)},${yOf(total * fractions[day - 1]).toFixed(1)}`)
  }
  return points.join(' ')
}

/**
 * 이번 달(12일까지)과 지난달(31일 전체) 누적 지출 곡선.
 *
 * @param {object} cur data/report.js 의 이번 달
 * @param {object|null} prev 지난달. 없으면 지난달 선을 그리지 않습니다.
 */
export function buildSpendChart(cur, prev) {
  const yTicks = []
  for (let i = 1; i <= 4; i++) {
    const won = i * 1000000
    yTicks.push({ label: String(i * 100), y: yOf(won).toFixed(1) })
  }

  return {
    lineCur: polyline(cur.spent, TODAY, 3),
    linePrev: prev ? polyline(prev.full, DAYS, 5) : '',
    yTicks,
    todayX: xOf(TODAY).toFixed(1),
    todayY: yOf(cur.spent).toFixed(1),
    axisTop: PAD_TOP,
    axisBottom: HEIGHT - PAD_BOTTOM,
    axisLeft: PAD_LEFT,
    axisRight: WIDTH - PAD_RIGHT,
  }
}

// 도넛 (반지름 52, stroke 18 → viewBox 140×140)
const RADIUS = 52
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const SEGMENT_GAP = 2

/**
 * 카테고리별 지출 도넛.
 * @param {{name: string, amount: number}[]} categories
 */
export function buildDonut(categories) {
  const total = categories.reduce((sum, c) => sum + c.amount, 0) || 1

  let offsetAcc = 0
  const segments = categories.map((c) => {
    const fraction = c.amount / total
    const length = Math.max(0, fraction * CIRCUMFERENCE - SEGMENT_GAP)
    const segment = {
      name: c.name,
      color: CATEGORY_COLORS[c.name] || DEFAULT_CATEGORY_COLOR,
      dash: `${length} ${CIRCUMFERENCE - length}`,
      offset: -offsetAcc * CIRCUMFERENCE + CIRCUMFERENCE / 4,
    }
    offsetAcc += fraction
    return segment
  })

  const items = categories.map((c) => ({
    name: c.name,
    amount: c.amount,
    color: CATEGORY_COLORS[c.name] || DEFAULT_CATEGORY_COLOR,
    percent: `${((c.amount / total) * 100).toFixed(1)}%`,
  }))

  const top = items[0] || { name: '-', amount: 0, color: DEFAULT_CATEGORY_COLOR }

  return {
    segments,
    items,
    total,
    topName: top.name,
    topColor: top.color,
    topPercent: `${Math.round((top.amount / total) * 100)}%`,
  }
}

/**
 * 한 카드가 받은 혜택을 그 카드의 주요 혜택 카테고리로 나눠 봅니다.
 * 실제 카테고리별 집계 API가 없어서 상위 3개 카테고리에 고정 비율로 배분합니다.
 *
 * @param {number} total 그 달 이 카드가 받은 총 혜택(원)
 * @param {{category: string}[]} benefits data/benefits.js 의 혜택 목록
 */
const SPLIT = [0.45, 0.33, 0.22]

export function splitBenefitByCategory(total, benefits) {
  const categories = []
  for (const b of benefits) {
    if (!categories.includes(b.category)) categories.push(b.category)
    if (categories.length === SPLIT.length) break
  }

  if (categories.length === 0) return [{ category: '기본 적립', amount: total }]

  // 카테고리가 3개 미만이면 남는 비율을 앞쪽에 몰아줍니다.
  const weights = SPLIT.slice(0, categories.length)
  const weightSum = weights.reduce((a, b) => a + b, 0)

  return categories.map((category, i) => ({
    category,
    amount: Math.round((total * weights[i]) / weightSum),
  }))
}
