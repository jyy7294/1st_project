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

/** 카테고리 도넛·범례 색. 없는 이름은 회색으로 떨어집니다. */
export const CATEGORY_COLORS = {
  식비: '#19D3C5',
  생활비: '#2F6BFF',
  교통: '#7B61FF',
  여행: '#F26DB0',
  '의료/건강': '#5BC0FF',
  쇼핑: '#FFB020',
  카페: '#F2884B',
  문화: '#9B8CFF',
  기타: '#C7CEDB',
}

export const DEFAULT_CATEGORY_COLOR = '#C7CEDB'

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
