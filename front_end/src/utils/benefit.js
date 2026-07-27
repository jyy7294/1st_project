// 혜택 원본 데이터(data/benefits.js)를 화면에 쓸 문자열·아이콘으로 바꿉니다.
// 카드 상세와 전체 혜택 화면이 같은 표기를 쓰도록 이 파일 하나만 씁니다.

import { krw, normalizeBenefitRate } from './format.js'

// 배경 틴트 — 아이콘 색감에 맞춰 몇 가지만 돌려 씁니다.
const BLUE = '#e6f0ff'
const MINT = '#e6faf7'
const PEACH = '#fdeee2'
const CREAM = '#fef3e2'
const LILAC = '#eef0ff'
const PINK = '#fdeaf1'
const GRAY = '#f4f6fa'

/*
 * 카테고리별 아이콘과 배경 틴트.
 *
 * 카드 DB 의 카테고리 43종을 모두 덮어 두어, 서로 다른 업종이 같은 아이콘으로
 * 보이지 않게 했습니다. (예전에는 표에 없는 업종이 전부 ✦ 로 떨어졌습니다.)
 * 포인트·마일리지 계열만 의도적으로 보석 아이콘을 함께 씁니다.
 */
const STYLE_BY_CATEGORY = {
  // 생활 · 쇼핑
  '마트/쇼핑': { icon: '🛒', tint: CREAM },
  온라인쇼핑: { icon: '📦', tint: CREAM },
  백화점: { icon: '🛍️', tint: PINK },
  편의점: { icon: '🏪', tint: CREAM },
  생활: { icon: '🏠', tint: MINT },
  '공과금/생활요금': { icon: '🧾', tint: BLUE },
  통신: { icon: '📱', tint: BLUE },
  '반려동물': { icon: '🐾', tint: MINT },

  // 먹거리
  '푸드/외식': { icon: '🍽️', tint: PEACH },
  '카페/디저트': { icon: '☕', tint: PEACH },
  배달앱: { icon: '🛵', tint: PEACH },
  베이커리: { icon: '🥐', tint: PEACH },

  // 이동
  교통: { icon: '🚇', tint: BLUE },
  주유: { icon: '⛽', tint: CREAM },
  '자동차/정비': { icon: '🚗', tint: BLUE },

  // 여가 · 문화
  '영화/문화': { icon: '🎬', tint: LILAC },
  '테마파크/레저': { icon: '🎢', tint: PINK },
  '구독/멤버십': { icon: '📺', tint: LILAC },
  '여행/숙박': { icon: '🏨', tint: BLUE },
  '항공/마일리지': { icon: '✈️', tint: BLUE },
  공항서비스: { icon: '🛫', tint: BLUE },
  공항라운지: { icon: '🛋️', tint: LILAC },
  PP: { icon: '🎫', tint: LILAC },
  면세점: { icon: '🛍️', tint: PINK },
  해외: { icon: '🌏', tint: MINT },

  // 건강 · 뷰티 · 교육
  '뷰티/피트니스': { icon: '💄', tint: PINK },
  '병원/약국': { icon: '🏥', tint: MINT },
  '교육/육아': { icon: '🎓', tint: LILAC },

  // 금융 · 결제
  모든가맹점: { icon: '💳', tint: GRAY },
  금융서비스: { icon: '🏦', tint: BLUE },
  간편결제: { icon: '📲', tint: BLUE },
  캐시백: { icon: '💰', tint: CREAM },
  '멤버십/포인트': { icon: '💎', tint: LILAC },
  멤버십포인트: { icon: '💎', tint: LILAC },
  '바우처/기프트': { icon: '🎁', tint: PINK },
  할인: { icon: '🏷️', tint: CREAM },

  // 기타 표기용
  프리미엄서비스: { icon: '🛎️', tint: LILAC },
  '우대 서비스': { icon: '🎖️', tint: CREAM },
  '기본 혜택': { icon: '✅', tint: MINT },
  '추가 혜택': { icon: '➕', tint: MINT },
  선택형: { icon: '🔀', tint: GRAY },
  국민행복: { icon: '🤝', tint: PINK },
  유의사항: { icon: 'ℹ️', tint: GRAY },
  기타: { icon: '✦', tint: GRAY },
}

const DEFAULT_STYLE = { icon: '✦', tint: GRAY }

/*
 * 카드 DB 의 카테고리·혜택유형에는 뜻이 없는 자리표시 값이 섞여 있습니다.
 * 제목을 '카테고리 + 값 + 유형'으로 이어 붙일 때 이 토큰이 그대로 남으면
 * '기타' 나 '프리미엄서비스 기타' 처럼 무슨 혜택인지 알 수 없는 제목이 됩니다.
 */
const GENERIC_TOKENS = new Set(['기타', '일반', '불명', '해당없음'])

/** 유의사항으로 펼칠 카드사 원문 줄 수. 이보다 길면 잘라내고 안내 문구를 답니다. */
const NOTE_LIMIT = 4

/** 부제로 쓰기에 무리 없는 길이. 넘으면 짧은 요약을 찾아 쓰고 원문은 유의사항으로 내립니다. */
const DESC_LIMIT = 70

/*
 * 카드 '혜택'이 아니라 플레이트 디자인 안내이거나 순수 홍보 문장인 행을 걸러내기 위한 패턴.
 * (예: '메탈 플레이트 제공', '꼭 확인하세요!', 'the Red Edition5의 특별한 디자인을 소개합니다.')
 *
 * 다만 '메탈 플레이트 제공·공항 라운지 무료 이용' 처럼 실제 혜택이 함께 적힌 행도 있어,
 * REAL_BENEFIT 이 걸리면 디자인 문구가 섞여 있어도 남깁니다.
 */
const DESIGN_ONLY = /디자인|플레이트|plate|소재/i
const PROMO_ONLY = /소개합니다|뿜뿜|꼭 확인하세요|당신을 위해|만나보세요|선보입니다|새롭고/
const REAL_BENEFIT =
  /라운지|발레파킹|priority\s*pass|무료\s?이용|할인|적립|면제|바우처|쿠폰|캐시백/i

/** 카드사가 쓴 문구의 첫 줄. 제목 후보이자 표시 여부 판단의 근거입니다. */
function headline(benefit) {
  const raw = benefit.desc || benefit.summary || benefit.detailText || ''
  return String(raw).split('\n')[0].trim()
}

/** '[특별 서비스] 전월실적 채워드림' → '전월실적 채워드림' */
function stripTag(text) {
  return text.replace(/^\[[^\]]*\]\s*/, '').trim()
}

/** '제공대상', '[마이신한포인트 적립]' 처럼 내용이 아니라 구획을 나누는 줄. */
function isHeadingLine(line) {
  if (/^\[[^\]]*\]$/.test(line)) return true
  return line.length <= 6 && !/[.,·:]/.test(line)
}

/*
 * 카드사 상세 설명에서 문장만 골라 냅니다.
 *
 * 원문에는 표가 줄바꿈으로 눌러 담겨 있습니다. 예를 들어 '할인기준' 표는
 *   '구분 전월 30만원 이상 … 쇼핑 4,000원' / '8,000원' / '16,000원' / '보육 4,000원'
 * 처럼 셀 하나가 한 줄씩 떨어져 들어옵니다. 이걸 줄마다 유의사항으로 찍으면
 * '8,000원' 같은 조각이 그대로 노출되고, '넷플릭스,' 와 '유튜브 프리미엄 …' 처럼
 * 한 문장이 두 개로 잘려 보입니다.
 *
 * 실제 설명 문장은 예외 없이 '-' 나 '*' 로 시작하고 표 조각·구획 머리글은 그렇지 않아,
 * 머리 기호가 있는 줄만 남깁니다.
 */
const BULLET = /^[\s]*[-*※·•]+\s*/

function detailLines(benefit) {
  return String(benefit.detailText || '')
    .split('\n')
    .filter((line) => BULLET.test(line))
    .map((line) => line.replace(BULLET, '').trim())
    .filter(Boolean)
}

/**
 * 화면에 보여줄 혜택인지 판단합니다.
 *
 * 값이 없다고 해서 혜택이 아닌 건 아닙니다 — '해외 이용 수수료 면제'처럼 수치로
 * 표현할 수 없는 서비스가 전체의 절반 가까이 됩니다. 그래서 값 유무가 아니라
 * '카드 플레이트 디자인 안내인가 / 홍보 문장인가'로만 걸러냅니다.
 *
 * @param {object} benefit adaptBenefit() 결과 또는 data/benefits.js 의 원소
 */
export function isDisplayableBenefit(benefit) {
  const text = headline(benefit)
  if (!text) return false
  // 수치나 한도가 붙은 행은 따질 것 없이 혜택입니다.
  if (benefit.value > 0) return true
  if (benefit.limitMonth || benefit.limitPerUse || benefit.limitYear) return true
  // 디자인 문구에 걸려도 실제 혜택이 함께 적혀 있으면 남깁니다.
  if (REAL_BENEFIT.test(text)) return true
  return !(DESIGN_ONLY.test(text) || PROMO_ONLY.test(text))
}

/**
 * 카테고리 → 표시 아이콘·배경색. 혜택 목록·결제내역이 같은 표기를 쓰도록
 * 이 한 곳에서 정합니다. 모르는 카테고리는 중립 아이콘으로 떨어집니다.
 * @returns {{ icon: string, tint: string }}
 */
export function categoryStyle(category) {
  return STYLE_BY_CATEGORY[category] || DEFAULT_STYLE
}

/** 만원 단위가 딱 떨어지면 '30만원', 아니면 '350,000원'으로 씁니다. */
function moneyShort(won) {
  if (won >= 10000 && won % 10000 === 0) return `${won / 10000}만원`
  return `${krw(won)}원`
}

/**
 * 혜택 한 건을 화면 표기로 변환합니다.
 *
 * @param {object} benefit data/benefits.js 의 원소
 * @returns {{
 *   id: string, icon: string, tint: string, title: string, rate: string,
 *   desc: string, limitText: string, conditionText: string, notes: string[]
 * }}
 */
export function benefitView(benefit) {
  const style = STYLE_BY_CATEGORY[benefit.category] || DEFAULT_STYLE

  /*
   * '유의사항'은 실제 업종·혜택이 아니라 "카드사 조건을 확인하라"는 안내성 자리표시
   * 데이터입니다. 이걸 제목에 그대로 쓰면 '유의사항 1% 무이자할부'처럼 되어, 아래
   * '유의사항' 섹션 라벨과 겹쳐 무엇을 확인하라는 건지 헷갈립니다.
   * 그래서 뜻이 분명한 안내 문구로 바꿔, 알려주려는 바(조건 확인 필요)를 명확히 합니다.
   */
  if (benefit.category === '유의사항') {
    /*
     * 알릴 내용이 '카드사 안내를 보라'는 것뿐이라 한도·실적·유의사항을 붙여 봐야
     * '한도 없음 / 실적 무관' 같은 빈 칸만 늘어납니다. 문구만 남기고, 화면이
     * 카드고릴라 링크를 대신 달 수 있도록 kind 로 알려 줍니다.
     */
    return {
      kind: 'notice',
      id: benefit.id,
      icon: style.icon,
      tint: style.tint,
      title: '혜택 조건 확인 필요',
      rate: '',
      desc: '적용 조건·한도는 카드사 안내를 확인하세요',
      limitText: '',
      conditionText: '',
      notes: [],
    }
  }

  const where = benefit.detail || benefit.category

  /*
   * '해외 수수료 면제'처럼 숫자가 없는 혜택은 value 가 비어 옵니다.
   * 그대로 이어붙이면 '금융서비스 null 면제/우대' 가 되므로 숫자 부분을 통째로 뺍니다.
   */
  const hasValue = benefit.value !== null && benefit.value !== undefined && benefit.value !== ''
  // 정률(%)에 100 초과 값이 오면 정액(원)으로 정상화해 '1000%' 표기를 막습니다.
  const { value: rateValue, unit: rateUnit } = normalizeBenefitRate(benefit.value, benefit.unit)
  // 금액·마일은 천 단위로 끊어 씁니다. ('15000마일' → '15,000마일')
  const rate = hasValue ? `${krw(rateValue)}${rateUnit}` : ''

  /*
   * 제목 조각을 모읍니다. 뜻 없는 토큰('기타')과 중복은 여기서 빠집니다.
   * 혜택값은 화면이 제목 오른쪽에 따로 크게 찍으므로 제목에 넣지 않습니다 —
   * 넣으면 '멤버십/포인트 15,000마일 마일리지 적립  15,000마일' 처럼 두 번 나옵니다.
   */
  const parts = []
  for (const token of [where, benefit.type]) {
    const piece = String(token || '').trim()
    if (!piece || GENERIC_TOKENS.has(piece) || parts.includes(piece)) continue
    parts.push(piece)
  }
  const combined = parts.join(' ')

  /*
   * '카페/디저트 10% 할인'처럼 업종이나 유형이 남았으면 그 조합이 이미 명확합니다.
   * 남은 게 숫자뿐이거나 아무것도 없으면(카테고리·유형이 전부 '기타') 카드사가 쓴
   * 이름을 제목으로 올립니다 — 예전에는 이 경우 제목이 그냥 '기타'였습니다.
   */
  const issuerLabel = stripTag(headline(benefit))
  const title = rate
    ? combined || issuerLabel
    : issuerLabel || combined || '카드 서비스'

  /*
   * 카드사 상세 설명은 '이름 줄 + 설명 줄들' 구조입니다. 이름 줄은 제목과 겹치므로
   * 버리고, 첫 설명 줄을 부제로, 나머지를 유의사항으로 내립니다.
   * (지금까지는 이 설명이 통째로 버려져 '기타 / 전월실적 채워드림'만 남았습니다.)
   */
  const body = detailLines(benefit).filter(
    (line) => line !== title && line !== issuerLabel && !title.startsWith(line),
  )
  /*
   * 원문에는 '제공대상', '[마이신한포인트 적립]' 같은 머리말 줄이 섞여 있습니다.
   * 부제로 올리면 무슨 혜택인지 알 수 없으니 실제 설명이 나올 때까지 건너뜁니다.
   */
  while (body.length > 1 && isHeadingLine(body[0])) body.shift()
  const [lead, ...rest] = body

  /*
   * 카드사 원문 첫 줄이 100자를 넘는 경우가 있습니다(LOCA 365 의 구독 할인은 147자).
   * 부제로 올리면 카드 머리가 문단이 되므로, 짧은 요약이 따로 있으면 그걸 부제로 쓰고
   * 긴 원문은 유의사항으로 내립니다.
   */
  const tooLong = lead && lead.length > DESC_LIMIT
  const shortAlt = tooLong && benefit.desc && benefit.desc.length <= DESC_LIMIT
    ? benefit.desc
    : ''
  const candidate = shortAlt || lead || benefit.desc || ''
  // 제목을 그대로 되풀이하는 부제는 한 줄만 낭비하므로 비웁니다(화면이 건너뜁니다).
  const desc = candidate === title ? '' : candidate
  if (shortAlt) rest.unshift(lead)

  /*
   * 카드사 원문은 60줄이 넘기도 합니다(예: The CLASSIC-Y 의 Gift Option). 그대로 펼치면
   * 전화번호·약관까지 쏟아져 오히려 읽기 어려워지므로 앞부분만 남기고 잘라 냅니다.
   */
  const detail = []
  for (const line of rest) {
    if (line !== desc && !detail.includes(line)) detail.push(line)
  }
  const notes = detail.slice(0, NOTE_LIMIT)
  if (detail.length > NOTE_LIMIT) notes.push('자세한 조건은 카드사 안내를 확인하세요')
  // 설명이 아예 없던 혜택은 예전처럼 카드사 문구를 유의사항에 남겨 둡니다.
  if (notes.length === 0 && benefit.desc && benefit.desc !== desc) notes.push(benefit.desc)
  notes.push(
    benefit.brands
      ? `적용처 · ${benefit.brands.split('|').join(', ')}`
      : '해당 카테고리 가맹점 전체 적용',
  )
  if (benefit.limitPerUse) notes.push(`건당 최대 ${krw(benefit.limitPerUse)}원까지 적용`)

  return {
    kind: 'benefit',
    id: benefit.id,
    icon: style.icon,
    tint: style.tint,
    title,
    rate,
    desc,
    limitText: benefit.limitMonth
      ? `월 ${krw(benefit.limitMonth)}원`
      : benefit.limitPerUse
        ? `건당 ${krw(benefit.limitPerUse)}원`
        : '한도 없음',
    conditionText: benefit.condition ? `전월 ${moneyShort(benefit.condition)}` : '실적 무관',
    notes,
  }
}
