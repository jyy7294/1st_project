// 소비 리포트의 계산만 모아둔 곳. 화면(Report.jsx)은 여기 결과를 그리기만 합니다.

import { assignColors, DEFAULT_CATEGORY_COLOR } from '../data/report.js'

// 꺾은선 그래프 좌표계 (SVG viewBox 300×150 기준)
const WIDTH = 300
const HEIGHT = 150
const PAD_LEFT = 34
const PAD_RIGHT = 6
const PAD_TOP = 8
const PAD_BOTTOM = 26
/** 'YYYY-MM' 의 실제 일수. (2월 28/29일, 6월 30일 …) */
export function daysInMonth(monthKey) {
  const [year, month] = String(monthKey || '').split('-').map(Number)
  if (!year || !month) return 31
  return new Date(year, month, 0).getDate()
}

/** day(1~totalDays)를 X 좌표로. 달마다 마지막 날이 다르므로 일수를 받습니다. */
const xOf = (day, totalDays = 31) =>
  PAD_LEFT + ((day - 1) / Math.max(1, totalDays - 1)) * (WIDTH - PAD_LEFT - PAD_RIGHT)
const yOf = (won, yMax) =>
  HEIGHT - PAD_BOTTOM - (won / yMax) * (HEIGHT - PAD_BOTTOM - PAD_TOP)

/** 축 상단값을 보기 좋은 10만원 단위로 올림합니다 (최소 10만원). */
function niceCeil(won) {
  const step = 100000
  return Math.max(step, Math.ceil((won || 0) / step) * step)
}

/** 눈금 간격을 1·2·5 × 10^n 중 보기 좋은 값으로 올립니다. */
function niceStep(raw) {
  const pow = 10 ** Math.floor(Math.log10(Math.max(raw, 1)))
  const n = raw / pow
  const mult = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10
  return mult * pow
}

/**
 * 막대 그래프 Y축 눈금. 금액에 맞춰 만원 단위로 딱 떨어지게 잡습니다.
 *
 * @param {number} maxAmount 가장 큰 막대의 금액(원)
 * @returns {{yMax: number, ticks: {won:number, label:string, pct:number}[]}}
 */
export function buildBarAxis(maxAmount, tickCount = 4) {
  const safeMax = Math.max(maxAmount || 0, 10000)
  const step = niceStep(safeMax / tickCount)
  const yMax = Math.ceil(safeMax / step) * step

  const ticks = []
  for (let won = step; won <= yMax + 1; won += step) {
    ticks.push({
      won,
      label: String(Math.round(won / 10000)), // 만원 단위
      pct: (won / yMax) * 100,
    })
  }
  return { yMax, ticks }
}

/** [{day, amount}] 누적 포인트를 SVG polyline 좌표 문자열로. */
function polylineFrom(points, yMax, totalDays) {
  return points
    .map((p) => `${xOf(p.day, totalDays).toFixed(1)},${yOf(p.amount, yMax).toFixed(1)}`)
    .join(' ')
}

/**
 * 이번 달·지난달 실제 일별 누적 지출 곡선.
 *
 * 달마다 일수가 달라(6월 30일, 2월 28일) X축을 그 달 길이에 맞춥니다.
 * 지난달 선은 자기 달 길이 기준으로 그려, 두 곡선 모두 '그 달의 처음~끝'을
 * 같은 폭에 채웁니다(월 진행률 비교).
 *
 * @param {{day:number, amount:number}[]} daily 이번 달 누적 (백엔드 dailyCumulative)
 * @param {{day:number, amount:number}[]} prevDaily 지난달 누적. 비면 지난달 선을 안 그립니다.
 * @param {{days:number, prevDays:number}} [span] 각 달의 일수
 */
export function buildSpendChart(daily = [], prevDaily = [], span = {}) {
  const days = span.days || 31
  const prevDays = span.prevDays || days
  const curLast = daily.length ? daily[daily.length - 1] : { day: 1, amount: 0 }
  const prevMax = prevDaily.reduce((m, p) => Math.max(m, p.amount), 0)
  const yMax = niceCeil(Math.max(curLast.amount, prevMax))

  const yTicks = []
  for (let i = 1; i <= 4; i += 1) {
    const won = (yMax / 4) * i
    // 라벨은 만원 단위 (소수 첫째자리까지, 정수면 정수로).
    const man = won / 10000
    yTicks.push({
      label: Number.isInteger(man) ? String(man) : man.toFixed(0),
      y: yOf(won, yMax).toFixed(1),
    })
  }

  return {
    lineCur: polylineFrom(daily, yMax, days),
    linePrev: prevDaily.length ? polylineFrom(prevDaily, yMax, prevDays) : '',
    yTicks,
    days,
    lastDayLabel: `${String(days).padStart(2, '0')}일`,
    todayX: xOf(curLast.day, days).toFixed(1),
    todayY: yOf(curLast.amount, yMax).toFixed(1),
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
  // 같은 차트 안에서 색이 겹치지 않도록 한 번에 배정합니다.
  const colors = assignColors(categories.map((c) => c.name))

  let offsetAcc = 0
  const segments = categories.map((c, i) => {
    const fraction = c.amount / total
    const length = Math.max(0, fraction * CIRCUMFERENCE - SEGMENT_GAP)
    const segment = {
      name: c.name,
      color: colors[i],
      dash: `${length} ${CIRCUMFERENCE - length}`,
      offset: -offsetAcc * CIRCUMFERENCE + CIRCUMFERENCE / 4,
    }
    offsetAcc += fraction
    return segment
  })

  const items = categories.map((c, i) => ({
    name: c.name,
    amount: c.amount,
    color: colors[i],
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

/** 상위 n개만 남기고 나머지는 '기타'로 합칩니다. 도넛이 잘게 쪼개지지 않게. */
function topWithOther(list, n = 5) {
  if (list.length <= n) return list
  const top = list.slice(0, n)
  const restSum = list.slice(n).reduce((sum, c) => sum + c.amount, 0)
  return restSum > 0 ? [...top, { name: '기타', amount: restSum }] : top
}

/**
 * 최근 n개월 결제내역을 업종별로 집계합니다.
 *
 * 백엔드에 '빈도' 집계 API 가 없어서 카드별 거래내역을 모아 여기서 셉니다.
 * 도넛이 바로 쓰도록 {name, amount} 모양으로 돌려줍니다(빈도는 amount 가 횟수).
 *
 * @param {object[]} transactions 거래내역 원본 (payment_category / original_payment_amount / approved_at)
 * @param {number} monthsBack 몇 개월치를 볼지
 * @returns {{byCount: {name,amount}[], byAmount: {name,amount}[], totalCount: number, totalAmount: number}}
 */
export function buildSpendingMix(transactions = [], monthsBack = 3, today = new Date()) {
  // n개월 전 1일부터 (예: 7월 기준 3개월 → 5/1 이후)
  const cutoff = new Date(today.getFullYear(), today.getMonth() - monthsBack + 1, 1)

  const counts = new Map()
  const amounts = new Map()
  let totalCount = 0
  let totalAmount = 0

  for (const tx of transactions) {
    const at = tx.approved_at ? new Date(tx.approved_at) : null
    if (at && !Number.isNaN(at.getTime()) && at < cutoff) continue

    const category = tx.payment_category || '기타'
    const amount = tx.original_payment_amount || 0
    counts.set(category, (counts.get(category) || 0) + 1)
    amounts.set(category, (amounts.get(category) || 0) + amount)
    totalCount += 1
    totalAmount += amount
  }

  const toList = (map) =>
    [...map.entries()]
      .map(([name, amount]) => ({ name, amount }))
      .filter((c) => c.amount > 0)
      .sort((a, b) => b.amount - a.amount)

  return {
    byCount: topWithOther(toList(counts)),
    byAmount: topWithOther(toList(amounts)),
    totalCount,
    totalAmount,
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
