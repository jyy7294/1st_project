// 앱 전체 상태 전이. 순수 함수 — 타이머·fetch 같은 부수효과는 화면 컴포넌트가 가집니다.

import { recommendedIndex } from '../utils/compare.js'
import { REPORT_TAB_COUNT } from '../data/report.js'

export const A = {
  SET_SCREEN: 'SET_SCREEN',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGOUT: 'LOGOUT',
  AUTH_RESTORED: 'AUTH_RESTORED',
  AUTH_INIT_DONE: 'AUTH_INIT_DONE',
  SESSION_EXPIRED: 'SESSION_EXPIRED',
  SET_CARDS_ERROR: 'SET_CARDS_ERROR',
  LOGIN_FAIL: 'LOGIN_FAIL',
  CLEAR_LOGIN_ERROR: 'CLEAR_LOGIN_ERROR',
  SET_CARDS: 'SET_CARDS',
  TOGGLE_EXPANDED: 'TOGGLE_EXPANDED',
  SELECT_CARD: 'SELECT_CARD',
  OPEN_CARD: 'OPEN_CARD',
  GO_HOME: 'GO_HOME',
  SET_MENU: 'SET_MENU',
  SET_CARD_STATS: 'SET_CARD_STATS',
  SET_CARD_STATS_FOR: 'SET_CARD_STATS_FOR',
  REMOVE_CARD: 'REMOVE_CARD',
  START_RECO: 'START_RECO',
  SET_RECO_TYPE: 'SET_RECO_TYPE',
  OPEN_RECO_DETAIL: 'OPEN_RECO_DETAIL',
  OPEN_BENEFITS: 'OPEN_BENEFITS',
  SET_RECO_CARDS: 'SET_RECO_CARDS',
  SET_RECO_STATUS: 'SET_RECO_STATUS',
  SET_REPORT_MONTH: 'SET_REPORT_MONTH',
  TOGGLE_REPORT_CARD: 'TOGGLE_REPORT_CARD',
  SET_REPORT_DATA: 'SET_REPORT_DATA',
  SET_REPORT_STATUS: 'SET_REPORT_STATUS',
  SET_SPENDING_MIX: 'SET_SPENDING_MIX',
  START_ADD: 'START_ADD',
  SET_ADD_STEP: 'SET_ADD_STEP',
  SET_ADD_FORM: 'SET_ADD_FORM',
  TOGGLE_TERM: 'TOGGLE_TERM',
  SET_ALL_TERMS: 'SET_ALL_TERMS',
  ADD_CARD: 'ADD_CARD',
  START_PAY: 'START_PAY',
  SET_PAY_STEP: 'SET_PAY_STEP',
  SET_RESULT: 'SET_RESULT',
  SET_ERROR: 'SET_ERROR',
  SET_NO_ELIGIBLE: 'SET_NO_ELIGIBLE',
  SELECT_PAY_CARD: 'SELECT_PAY_CARD',
  RESET_PAY: 'RESET_PAY',
}

/** 카드 등록 폼 초기값. 등록을 새로 시작할 때마다 이 값으로 되돌립니다. */
export const EMPTY_ADD_FORM = { number: '', expiry: '', cvc: '', pin: '' }

/** 약관 4개. t1~t3 필수, t4(마케팅) 선택. */
export const EMPTY_TERMS = { t1: false, t2: false, t3: false, t4: false }

export const initialState = {
  screen: 'splash', // 'splash' | 'login' | 'home' | 'detail' | 'benefits'
  //                   | 'cards' | 'report' | 'recommend' | 'recoDetail' | 'add' | 'qr'
  payStep: 'none', // 'none' | 'received' | 'analyzing' | 'recommend'
  //                  | 'confirm' | 'faceid' | 'approving' | 'done'
  cards: [], // fetchMyCards() 결과
  cardsLoaded: false, // 한 번 불러온 뒤에는 다시 요청하지 않습니다
  expanded: false, // 홈 카드 스택 펼침 여부
  active: 0, // 홈에서 선택된 카드 index
  detailReturn: 'home', // 카드 상세에서 뒤로 갈 화면 ('home' | 'cards')
  // 상세 혜택 화면이 어떤 카드 것인지. 'owned'(보유 카드) | 'reco'(추천 카드)
  benefitsSource: 'owned',
  menuOpen: false, // 상세 화면 ⋯ 메뉴
  showCardStats: false, // 카드 앞면에 사용금액·받은 혜택을 표시할지. 기본은 숨김
  // 카드별 예외. { [card_id]: true|false } — 없으면 위 전체 설정을 따릅니다.
  cardStatsById: {},
  addStep: 'scan', // 'scan' | 'input' | 'terms' | 'done'
  addForm: EMPTY_ADD_FORM,
  terms: EMPTY_TERMS,
  addedCard: null, // 방금 등록한 카드 (등록 완료 화면에 표시)
  recoType: 'credit', // 카드 추천 화면 탭: 'credit' | 'check'
  recoSelId: null, // 분석 결과를 보고 있는 추천 카드 id. null 이면 1위
  // 결제 직후 '구경하러 가기'로 들어오면 그 결제 업종이 담깁니다. null 이면 일반 추천.
  recoCategory: null,
  // 소비패턴 기반(광고 배너) 추천을 백엔드에서 받아 탭별로 담아 둡니다. null = 미로딩.
  recoCards: { credit: null, check: null },
  recoMeta: null, // 분석 기간·상위 업종·상위 가맹점
  recoStatus: 'idle', // 'idle' | 'loading' | 'ready' | 'error'
  reportMonth: REPORT_TAB_COUNT - 1, // 리포트에서 보고 있는 달 (기본 = 이번 달)
  reportCardOpen: -1, // 리포트 '카드별 혜택'에서 펼친 카드 index. -1 이면 모두 접힘
  // 월(YYYY-MM)별 소비 리포트를 백엔드에서 받아 캐시합니다.
  reportData: {},
  reportStatus: 'idle', // 'idle' | 'loading' | 'ready' | 'error'
  // 최근 3개월 업종별 소비(빈도·금액). 추천 분석 화면의 원형 차트에 씁니다.
  spendingMix: null,
  transaction: null, // QR로 읽은 결제정보
  payIdx: 0, // comparison 배열(백엔드 순서)에서 결제에 쓸 카드 index
  result: null, // 백엔드 추천 응답
  error: null, // 추천 호출 실패 메시지
  noEligibleCard: false, // 404 — 이 업종에 혜택 카드가 없음
  loginError: '',
  // 로그인한 사용자. 사용자 식별용 user_id 는 API 경로에, 인증은 JWT 헤더로 처리합니다.
  user: null, // { userId, email, name }
  // JWT 인증 상태. 토큰 원본은 API 계층(client.js)+sessionStorage 가 단일 원본이라
  // 여기엔 화면 분기용 상태만 둡니다.
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  // 앱 시작 시 sessionStorage 의 refresh_token 으로 세션 복구를 시도하는 동안 true.
  // 이 값이 true 인 동안에는 보유카드·추천 API 를 호출하지 않습니다.
  authInitializing: true,
  cardsError: null, // 보유카드 조회 실패 메시지
}

export function appReducer(state, action) {
  switch (action.type) {
    case A.SET_SCREEN:
      return { ...state, screen: action.screen }

    case A.LOGIN_SUCCESS:
      // 사용자가 바뀌면 이전 지갑 데이터는 버리고 다시 불러옵니다.
      return {
        ...state,
        screen: 'home',
        loginError: '',
        user: action.user || state.user,
        accessToken: action.accessToken ?? null,
        refreshToken: action.refreshToken ?? null,
        isAuthenticated: true,
        authInitializing: false,
        cards: [],
        cardsLoaded: false,
        cardsError: null,
        active: 0,
      }

    case A.AUTH_RESTORED:
      // 새로고침 복구 성공 — 토큰·사용자를 되살리고 홈으로 바로 진입합니다.
      return {
        ...state,
        screen: 'home',
        user: action.user,
        accessToken: action.accessToken ?? null,
        refreshToken: action.refreshToken ?? null,
        isAuthenticated: true,
        authInitializing: false,
        cards: [],
        cardsLoaded: false,
        cardsError: null,
        active: 0,
      }

    case A.AUTH_INIT_DONE:
      // 복구할 세션이 없음 — 초기화만 끝내고 스플래시/로그인 흐름을 그대로 둡니다.
      return { ...state, authInitializing: false }

    case A.LOGOUT:
    case A.SESSION_EXPIRED:
      // 토큰은 API 계층에서 지웁니다(auth.logout / client 의 401 처리).
      // 화면 상태는 초기값으로 되돌리고 로그인 화면으로 보냅니다.
      return { ...initialState, screen: 'login', authInitializing: false }

    case A.LOGIN_FAIL:
      return { ...state, loginError: action.message }

    case A.CLEAR_LOGIN_ERROR:
      return { ...state, loginError: '' }

    case A.SET_CARDS:
      return { ...state, cards: action.cards, cardsLoaded: true, cardsError: null }

    case A.SET_CARDS_ERROR:
      return { ...state, cardsLoaded: true, cardsError: action.message }

    case A.TOGGLE_EXPANDED:
      return { ...state, expanded: !state.expanded }

    case A.SELECT_CARD: {
      // 접힌 상태에서 카드를 누르면 펼치고 선택,
      // 펼친 상태에서 다른 카드를 누르면 선택만 옮깁니다.
      if (!state.expanded) {
        return { ...state, expanded: true, active: action.index }
      }
      return { ...state, active: action.index }
    }

    case A.OPEN_CARD:
      // 카드 더블클릭·결제수단 관리 목록에서 상세로 들어옵니다.
      // 뒤로가기가 원래 있던 화면으로 돌아가도록 from 을 기억해 둡니다.
      return {
        ...state,
        screen: 'detail',
        detailReturn: action.from || 'home',
        active: action.index,
        menuOpen: false,
      }

    case A.GO_HOME:
      return { ...state, screen: 'home', expanded: false, menuOpen: false }

    case A.SET_MENU:
      return { ...state, menuOpen: action.open }

    case A.SET_CARD_STATS:
      // 전체 설정을 바꾸면 카드별 예외는 지워 한 번에 맞춥니다.
      return { ...state, showCardStats: action.show, cardStatsById: {} }

    case A.SET_CARD_STATS_FOR:
      return {
        ...state,
        cardStatsById: { ...state.cardStatsById, [action.cardId]: action.show },
      }

    case A.REMOVE_CARD: {
      // 카드를 지우면 선택 index가 배열 밖을 가리킬 수 있어 홈으로 되돌립니다.
      const cards = state.cards.filter((_, i) => i !== action.index)
      return {
        ...state,
        cards,
        active: 0,
        expanded: false,
        menuOpen: false,
        screen: 'home',
      }
    }

    case A.START_RECO:
      return {
        ...state,
        screen: 'recommend',
        recoType: 'credit',
        recoSelId: null,
        recoCategory: action.category || null,
        // 진입할 때 상태를 비워 두면 Recommend 화면이 그날 로컬 캐시에서 즉시 복원하거나
        // (캐시가 있으면 로딩 없음), 그날 최초면 백엔드에서 새로 받아옵니다.
        recoCards: { credit: null, check: null },
        recoMeta: null,
        recoStatus: 'idle',
        // 결제 흐름에서 넘어온 경우 결제 화면을 닫습니다.
        payStep: 'none',
      }

    case A.SET_RECO_TYPE:
      // 탭을 바꾸면 목록이 통째로 달라지므로 선택도 1위로 되돌립니다.
      return { ...state, recoType: action.recoType, recoSelId: null }

    case A.OPEN_RECO_DETAIL:
      return { ...state, screen: 'recoDetail', recoSelId: action.id }

    case A.OPEN_BENEFITS:
      // 보유 카드 상세와 추천 카드 분석에서 같은 '상세 혜택' 화면을 씁니다.
      return { ...state, screen: 'benefits', benefitsSource: action.source || 'owned' }

    case A.SET_RECO_CARDS:
      return {
        ...state,
        recoCards: { ...state.recoCards, [action.cardType]: action.cards },
        recoMeta: action.meta ?? state.recoMeta,
        recoStatus: 'ready',
      }

    case A.SET_RECO_STATUS:
      return { ...state, recoStatus: action.status }

    case A.SET_REPORT_MONTH:
      // 달을 바꾸면 펼쳐둔 카드는 접습니다 (다른 달 금액이 남아 보이지 않게).
      return { ...state, reportMonth: action.index, reportCardOpen: -1 }

    case A.TOGGLE_REPORT_CARD:
      return {
        ...state,
        reportCardOpen: state.reportCardOpen === action.index ? -1 : action.index,
      }

    case A.SET_REPORT_DATA:
      return {
        ...state,
        reportData: { ...state.reportData, [action.month]: action.report },
        reportStatus: 'ready',
      }

    case A.SET_REPORT_STATUS:
      return { ...state, reportStatus: action.status }

    case A.SET_SPENDING_MIX:
      return { ...state, spendingMix: action.mix }

    case A.START_ADD:
      return {
        ...state,
        screen: 'add',
        addStep: 'scan',
        addForm: EMPTY_ADD_FORM,
        terms: EMPTY_TERMS,
        addedCard: null,
      }

    case A.SET_ADD_STEP:
      return { ...state, addStep: action.step }

    case A.SET_ADD_FORM:
      return { ...state, addForm: { ...state.addForm, ...action.patch } }

    case A.TOGGLE_TERM:
      return {
        ...state,
        terms: { ...state.terms, [action.key]: !state.terms[action.key] },
      }

    case A.SET_ALL_TERMS:
      return {
        ...state,
        terms: { t1: action.value, t2: action.value, t3: action.value, t4: action.value },
      }

    case A.ADD_CARD:
      return {
        ...state,
        cards: [...state.cards, action.card],
        addedCard: action.card,
        addStep: 'done',
      }

    case A.START_PAY:
      return {
        ...state,
        transaction: action.transaction,
        payStep: 'received',
        result: null,
        error: null,
        noEligibleCard: false,
        payIdx: 0,
      }

    case A.SET_PAY_STEP:
      return { ...state, payStep: action.payStep }

    case A.SET_RESULT:
      // 기본 선택 카드는 백엔드가 is_recommended 로 표시한 카드입니다.
      // (보통 맨 앞이지만 순서에 기대지 않고 플래그로 찾습니다.)
      return {
        ...state,
        result: action.result,
        error: null,
        noEligibleCard: false,
        payIdx: recommendedIndex(action.result?.comparison),
      }

    case A.SET_ERROR:
      return { ...state, error: action.message, result: null }

    case A.SET_NO_ELIGIBLE:
      return { ...state, noEligibleCard: true, error: null, result: null }

    case A.SELECT_PAY_CARD:
      return { ...state, payIdx: action.index }

    case A.RESET_PAY:
      return {
        ...state,
        payStep: 'none',
        screen: 'home',
        transaction: null,
        result: null,
        error: null,
        noEligibleCard: false,
        payIdx: 0,
      }

    default:
      return state
  }
}

/**
 * 이 카드의 금액을 표시할지. 카드별 설정이 있으면 그것을, 없으면 전체 설정을 따릅니다.
 *
 * @param {object} state
 * @param {{card_id: number|string}} card
 */
export function cardStatsVisible(state, card) {
  const override = state.cardStatsById?.[card?.card_id]
  return override === undefined ? state.showCardStats : override
}
