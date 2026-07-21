// 카드 상세의 '최근 결제내역' 목업.
// 백엔드에 거래내역 API가 없어서 카드별 고정 내역을 씁니다.
// 등록한 지 얼마 안 된 카드(여기에 없는 card_id)는 빈 배열이 되고,
// 상세 화면이 '아직 결제내역이 없어요' 빈 상태를 보여줍니다.

const RECENT_BY_CARD = {
  // 신한카드 Mr.Life — 공과금·편의점·병원 위주
  13: [
    { id: 't13-1', place: '서울도시가스', category: '공과금', icon: '🧾', date: '2026.07.18', amount: 48200, saved: '할인 3,000원' },
    { id: 't13-2', place: 'GS25 역삼점', category: '편의점', icon: '🏪', date: '2026.07.17', amount: 12300, saved: '할인 1,000원' },
    { id: 't13-3', place: '연세이비인후과', category: '병원/약국', icon: '🏥', date: '2026.07.15', amount: 32000, saved: '할인 1,000원' },
    { id: 't13-4', place: 'SK텔레콤 요금', category: '통신', icon: '📱', date: '2026.07.13', amount: 55000, saved: '할인 3,000원' },
    { id: 't13-5', place: '쿠팡', category: '온라인쇼핑', icon: '🛒', date: '2026.07.11', amount: 24800, saved: '할인 1,000원' },
  ],

  // LOCA LIKIT Eat — 카페·배달·외식 위주
  2262: [
    { id: 't2262-1', place: '스타벅스 강남R점', category: '카페', icon: '☕', date: '2026.07.19', amount: 5600, saved: '할인 3,360원' },
    { id: 't2262-2', place: '배달의민족', category: '배달앱', icon: '🛵', date: '2026.07.18', amount: 23400, saved: '할인 14,040원' },
    { id: 't2262-3', place: '노브랜드버거', category: '푸드/외식', icon: '🍔', date: '2026.07.16', amount: 11900, saved: '할인 7,140원' },
    { id: 't2262-4', place: '메가MGC커피', category: '카페', icon: '☕', date: '2026.07.14', amount: 3800, saved: '할인 2,280원' },
    { id: 't2262-5', place: '요기요', category: '배달앱', icon: '🛵', date: '2026.07.12', amount: 18700, saved: '할인 11,220원' },
  ],

  // LOCA LIKIT 1.2 — 실적 조건 없는 기본 할인
  2261: [
    { id: 't2261-1', place: '카카오T 택시', category: '교통', icon: '🚕', date: '2026.07.19', amount: 9800, saved: '할인 117원' },
    { id: 't2261-2', place: '올리브영 강남', category: '쇼핑', icon: '🧴', date: '2026.07.17', amount: 28900, saved: '할인 346원' },
    { id: 't2261-3', place: '네이버페이', category: '온라인쇼핑', icon: '🛒', date: '2026.07.15', amount: 42000, saved: '할인 630원' },
    { id: 't2261-4', place: '서울교통공사', category: '교통', icon: '🚇', date: '2026.07.14', amount: 1400, saved: '할인 16원' },
    { id: 't2261-5', place: 'CU 삼성점', category: '편의점', icon: '🏪', date: '2026.07.12', amount: 7200, saved: '할인 86원' },
  ],
}

/** 카드의 최근 결제내역. 내역이 없는 카드면 빈 배열. */
export function recentForCard(card) {
  return RECENT_BY_CARD[card?.card_id] || []
}
