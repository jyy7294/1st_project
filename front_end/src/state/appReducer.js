// 앱 전체 상태 전이. 순수 함수 — 타이머·fetch 같은 부수효과는 화면 컴포넌트가 가집니다.

import { recommendedIndex } from '../utils/compare.js'
import { LATEST_MONTH_INDEX } from '../data/report.js'

export const A = {
  SET_SCREEN: 'SET_SCREEN',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAIL: 'LOGIN_FAIL',
  CLEAR_LOGIN_ERROR: 'CLEAR_LOGIN_ERROR',
  SET_SOCIAL: 'SET_SOCIAL',
  SET_CARDS: 'SET_CARDS',
  TOGGLE_EXPANDED: 'TOGGLE_EXPANDED',
  SELECT_CARD: 'SELECT_CARD',
  OPEN_CARD: 'OPEN_CARD',
  GO_HOME: 'GO_HOME',
  SET_MENU: 'SET_MENU',
  TOGGLE_NOTIFY: 'TOGGLE_NOTIFY',
  SET_CARD_STATS: 'SET_CARD_STATS',
  REMOVE_CARD: 'REMOVE_CARD',
  SET_REPORT_MONTH: 'SET_REPORT_MONTH',
  TOGGLE_REPORT_CARD: 'TOGGLE_REPORT_CARD',
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
  //                   | 'cards' | 'report' | 'add' | 'qr'
  payStep: 'none', // 'none' | 'received' | 'analyzing' | 'recommend'
  //                  | 'confirm' | 'faceid' | 'approving' | 'done'
  cards: [], // fetchMyCards() 결과
  cardsLoaded: false, // 한 번 불러온 뒤에는 다시 요청하지 않습니다
  expanded: false, // 홈 카드 스택 펼침 여부
  active: 0, // 홈에서 선택된 카드 index
  detailReturn: 'home', // 카드 상세에서 뒤로 갈 화면 ('home' | 'cards')
  menuOpen: false, // 상세 화면 ⋯ 메뉴
  notify: true, // 상세 화면 알림 설정
  showCardStats: true, // 카드 앞면에 사용금액·받은 혜택을 표시할지
  addStep: 'scan', // 'scan' | 'input' | 'terms' | 'done'
  addForm: EMPTY_ADD_FORM,
  terms: EMPTY_TERMS,
  addedCard: null, // 방금 등록한 카드 (등록 완료 화면에 표시)
  reportMonth: LATEST_MONTH_INDEX, // 리포트에서 보고 있는 달
  reportCardOpen: -1, // 리포트 '카드별 혜택'에서 펼친 카드 index. -1 이면 모두 접힘
  transaction: null, // QR로 읽은 결제정보
  payIdx: 0, // comparison 배열(백엔드 순서)에서 결제에 쓸 카드 index
  result: null, // 백엔드 추천 응답
  error: null, // 추천 호출 실패 메시지
  noEligibleCard: false, // 404 — 이 업종에 혜택 카드가 없음
  loginError: '',
  social: null, // 'kakao' | 'naver' | null
}

export function appReducer(state, action) {
  switch (action.type) {
    case A.SET_SCREEN:
      return { ...state, screen: action.screen }

    case A.LOGIN_SUCCESS:
      return { ...state, screen: 'home', loginError: '', social: null }

    case A.LOGIN_FAIL:
      return { ...state, loginError: action.message }

    case A.CLEAR_LOGIN_ERROR:
      return { ...state, loginError: '' }

    case A.SET_SOCIAL:
      return { ...state, social: action.provider }

    case A.SET_CARDS:
      return { ...state, cards: action.cards, cardsLoaded: true }

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

    case A.TOGGLE_NOTIFY:
      return { ...state, notify: !state.notify, menuOpen: false }

    case A.SET_CARD_STATS:
      return { ...state, showCardStats: action.show }

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

    case A.SET_REPORT_MONTH:
      // 달을 바꾸면 펼쳐둔 카드는 접습니다 (다른 달 금액이 남아 보이지 않게).
      return { ...state, reportMonth: action.index, reportCardOpen: -1 }

    case A.TOGGLE_REPORT_CARD:
      return {
        ...state,
        reportCardOpen: state.reportCardOpen === action.index ? -1 : action.index,
      }

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
