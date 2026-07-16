// 지갑에 표시할 사용자 보유 카드 (프론트 목업 데이터).
// 실제 서비스라면 사용자 계정에 등록된 카드를 서버에서 받아오지만,
// 여기서는 홈 화면 UI 시연을 위해 프론트 상수로 시뮬레이션합니다.
export const WALLET_CARDS = [
  {
    id: 'shinhan-deepdream',
    company: '신한카드',
    name: 'Deep Dream',
    label: '생활비',
    last4: '1234',
    // 브랜드 블루 계열 그라데이션
    gradient: 'linear-gradient(135deg, #3a6bff 0%, #1e3fd0 100%)',
  },
  {
    id: 'samsung-taptap',
    company: '삼성카드',
    name: 'taptap O',
    label: '쇼핑',
    last4: '5678',
    // 다크 그라데이션
    gradient: 'linear-gradient(135deg, #3a3f4b 0%, #16181f 100%)',
  },
  {
    id: 'kb-toktok',
    company: 'KB국민',
    name: '톡톡Ⅱ',
    label: '카페',
    last4: '9012',
    // 퍼플 그라데이션
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #5b3fd0 100%)',
  },
  {
    id: 'hyundai-m',
    company: '현대카드',
    name: 'M Edition',
    label: '교통',
    last4: '3456',
    // 틸 그라데이션
    gradient: 'linear-gradient(135deg, #16b8a6 0%, #0e8a7d 100%)',
  },
]
