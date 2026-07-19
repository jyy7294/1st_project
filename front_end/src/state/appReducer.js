// 앱 전체 상태 전이. 순수 함수 — 타이머·fetch 같은 부수효과는 화면 컴포넌트가 가집니다.

import { recommendedIndex } from '../utils/compare.js'

export const A = {
  SET_SCREEN: 'SET_SCREEN',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAIL: 'LOGIN_FAIL',
  CLEAR_LOGIN_ERROR: 'CLEAR_LOGIN_ERROR',
  SET_SOCIAL: 'SET_SOCIAL',
  SET_CARDS: 'SET_CARDS',
  TOGGLE_EXPANDED: 'TOGGLE_EXPANDED',
  SELECT_CARD: 'SELECT_CARD',
  START_PAY: 'START_PAY',
  SET_PAY_STEP: 'SET_PAY_STEP',
  SET_RESULT: 'SET_RESULT',
  SET_ERROR: 'SET_ERROR',
  SET_NO_ELIGIBLE: 'SET_NO_ELIGIBLE',
  SELECT_PAY_CARD: 'SELECT_PAY_CARD',
  RESET_PAY: 'RESET_PAY',
}

export const initialState = {
  screen: 'splash', // 'splash' | 'login' | 'home' | 'qr'
  payStep: 'none', // 'none' | 'received' | 'analyzing' | 'recommend'
  //                  | 'confirm' | 'faceid' | 'approving' | 'done'
  cards: [], // fetchMyCards() 결과
  expanded: false, // 홈 카드 스택 펼침 여부
  active: 0, // 홈에서 선택된 카드 index
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
      return { ...state, cards: action.cards }

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
