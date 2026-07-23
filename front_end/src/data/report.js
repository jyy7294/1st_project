// 월별 소비 리포트 목업. 백엔드에 소비내역 집계 API가 없어서 프론트 상수로 씁니다.
//
// spent       해당 월 1~12일 누적 지출(원). 이번 달(마지막 원소)은 '오늘까지'의 값입니다.
// full        해당 월 전체 지출(원). 지난달 누적 곡선을 31일까지 그릴 때 씁니다.
// benefitByCard  카드(card_id)별 그 달에 받은 혜택(원). 합이 그 달의 총 혜택입니다.
// categories  카테고리별 지출(원). 합은 spent 와 일치합니다.
//
// 7월(이번 달) 값은 data/cards.js 의 카드별 spent·benefit 합과 일부러 맞춰 두었습니다.
// 318,000 + 506,000 + 152,000 = 976,000 / 22,400 + 31,200 + 9,800 = 63,400

export const REPORT_MONTHS = [
  {
    key: '3월',
    spent: 1320000,
    full: 3600000,
    benefitByCard: { 13: 16000, 2262: 18000, 2261: 10000 },
    categories: [
      { name: '여행', amount: 480000 },
      { name: '식비', amount: 300000 },
      { name: '생활비', amount: 220000 },
      { name: '쇼핑', amount: 180000 },
      { name: '교통', amount: 90000 },
      { name: '기타', amount: 50000 },
    ],
  },
  {
    key: '4월',
    spent: 1240000,
    full: 3300000,
    benefitByCard: { 13: 17000, 2262: 21000, 2261: 10000 },
    categories: [
      { name: '식비', amount: 360000 },
      { name: '쇼핑', amount: 300000 },
      { name: '생활비', amount: 250000 },
      { name: '교통', amount: 140000 },
      { name: '문화', amount: 110000 },
      { name: '기타', amount: 80000 },
    ],
  },
  {
    key: '5월',
    spent: 1150000,
    full: 3050000,
    benefitByCard: { 13: 18000, 2262: 24000, 2261: 10000 },
    categories: [
      { name: '생활비', amount: 340000 },
      { name: '식비', amount: 300000 },
      { name: '교통', amount: 200000 },
      { name: '여행', amount: 160000 },
      { name: '의료/건강', amount: 90000 },
      { name: '기타', amount: 60000 },
    ],
  },
  {
    key: '6월',
    spent: 1116000,
    full: 2800000,
    benefitByCard: { 13: 20000, 2262: 26000, 2261: 11000 },
    categories: [
      { name: '식비', amount: 366000 },
      { name: '생활비', amount: 260000 },
      { name: '카페', amount: 180000 },
      { name: '교통', amount: 150000 },
      { name: '문화', amount: 100000 },
      { name: '기타', amount: 60000 },
    ],
  },
  {
    key: '7월',
    spent: 976000,
    full: 2560000,
    benefitByCard: { 13: 22400, 2262: 31200, 2261: 9800 },
    categories: [
      { name: '식비', amount: 320000 },
      { name: '생활비', amount: 226000 },
      { name: '교통', amount: 150000 },
      { name: '여행', amount: 130000 },
      { name: '의료/건강', amount: 90000 },
      { name: '기타', amount: 60000 },
    ],
  },
]

/**
 * 도넛·범례 색 팔레트.
 *
 * 색상환에서 최대한 떨어진 색을 골라 조각끼리 헷갈리지 않게 했고,
 * 채도는 중간으로 낮춰 형광처럼 튀지 않게 했습니다. 흰 배경에서 모두 읽힙니다.
 */
export const PALETTE = [
  '#3B82F6', // 파랑
  '#F97316', // 오렌지
  '#14B8A6', // 틸
  '#EF4444', // 레드
  '#8B5CF6', // 퍼플
  '#22C55E', // 그린
  '#EC4899', // 핑크
  '#06B6D4', // 시안
]

/** '기타'처럼 묶음 항목은 눈에 덜 띄는 중립 회색으로 둡니다. */
export const DEFAULT_CATEGORY_COLOR = '#9AA3B2'

/** 자주 나오는 카테고리는 팔레트에서 고정 배정합니다. */
export const CATEGORY_COLORS = {
  식비: PALETTE[1], // 오렌지
  생활비: PALETTE[0], // 파랑
  교통: PALETTE[4], // 퍼플
  여행: PALETTE[6], // 핑크
  '의료/건강': PALETTE[7], // 시안
  쇼핑: PALETTE[2], // 틸
  카페: PALETTE[3], // 레드
  문화: PALETTE[5], // 그린
  기타: DEFAULT_CATEGORY_COLOR,
}

/**
 * 카테고리 색. 이름이 같으면 언제나 같은 색이 나오므로
 * 빈도·금액 차트 두 개에서 같은 업종이 같은 색으로 보입니다.
 */
export function colorForCategory(name) {
  if (!name) return DEFAULT_CATEGORY_COLOR
  if (name === '기타') return DEFAULT_CATEGORY_COLOR
  if (CATEGORY_COLORS[name]) return CATEGORY_COLORS[name]
  let hash = 0
  for (let i = 0; i < name.length; i += 1) {
    hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  }
  return PALETTE[hash % PALETTE.length]
}

/**
 * 한 차트 안에서 쓸 색들을 정합니다.
 *
 * 기본은 이름 기준 색(두 차트에서 같은 업종 = 같은 색)이지만,
 * 그 색이 이미 쓰였으면 남은 팔레트 색으로 밀어 같은 차트 안에서는
 * 절대 색이 겹치지 않게 합니다.
 *
 * @param {string[]} names 조각 이름들 (표시 순서)
 * @returns {string[]} 같은 순서의 색 배열
 */
export function assignColors(names = []) {
  const used = new Set()
  return names.map((name) => {
    let color = colorForCategory(name)
    if (used.has(color)) {
      color = PALETTE.find((c) => !used.has(c)) || color
    }
    used.add(color)
    return color
  })
}

/**
 * 리포트 탭에 쓸 최근 n개월 (오늘 기준). 백엔드 spending-report 는 월(YYYY-MM)로 조회합니다.
 * @returns {{key: string, label: string}[]} 예: [{key:'2026-05', label:'5월'}, ...]
 */
export function recentMonths(n = 3, today = new Date()) {
  const out = []
  for (let i = n - 1; i >= 0; i -= 1) {
    const d = new Date(today.getFullYear(), today.getMonth() - i, 1)
    out.push({
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: `${d.getMonth() + 1}월`,
    })
  }
  return out
}

/** 리포트 탭에 보여줄 개월 수. 기본 진입은 마지막(이번 달)입니다. */
export const REPORT_TAB_COUNT = 3

/** 이번 달(마지막 원소)과 지난달. 지난달이 없으면 null. */
export function monthAt(index) {
  const cur = REPORT_MONTHS[index] || REPORT_MONTHS[REPORT_MONTHS.length - 1]
  const prev = index > 0 ? REPORT_MONTHS[index - 1] : null
  return { cur, prev }
}

/** 리포트에서 기본으로 열리는 달 = 가장 최근 달. */
export const LATEST_MONTH_INDEX = REPORT_MONTHS.length - 1

/** 한 달의 총 혜택. */
export function totalBenefit(month) {
  return Object.values(month.benefitByCard).reduce((sum, v) => sum + v, 0)
}
