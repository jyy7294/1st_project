import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { fetchEligibilities, updateEligibilities } from '../api/picka.js'
import styles from './MemberInfo.module.css'

// 최초 카드 등록 전에 받는 자격/소비 조건. 시연에서는 최초 등록이 불가능해서
// 더보기 → '회원정보 수정' 으로 이 값들을 나중에 채워 넣습니다.
// 값 형식은 백엔드 user_eligibilities 규칙을 그대로 따릅니다.

const SHOPPING_MAX = 3 // 쇼핑 계열 복수선택 상한
const TRANSPORT_MAX = 2 // 교통수단 복수선택 상한
const AIRLINE_MAX = 2 // 항공사 복수선택 상한

// 예/아니오 토글 항목 (백엔드에는 'true'/'false' 문자열로 저장)
const BOOL_FIELDS = [
  ['MILITARY_SERVICE', '현역 군 복무 중'],
  ['BUSINESS_OWNER', '개인사업자 여부'],
  ['COMPACT_CAR_OWNER', '경차 소유 여부'],
  ['VEHICLE_OWNER', '차량 보유 여부'],
  ['KPASS_USER', 'K-패스 이용'],
  ['HIGHPASS_USER', '하이패스 이용'],
  ['PREGNANCY_CHILDCARE_SUPPORT_ELIGIBLE', '임신·출산·육아지원카드 대상'],
  ['WELFARE_BENEFIT_ELIGIBLE', '기타 복지카드 대상'],
]

// 단일 선택 항목(드롭다운). 값은 백엔드 코드값, 라벨만 한글.
const SELECT_FIELDS = [
  ['TELECOM_PROVIDER', '이용 통신사', [
    ['SKT', 'SKT'], ['KT', 'KT'], ['LGU+', 'LG U+'], ['MVNO', '알뜰폰'],
  ]],
]

// 복수선택(칩) 항목
const SHOPPING_OPTIONS = [
  ['LOTTE', '롯데 계열'], ['SHINSEGAE_EMART', '신세계·이마트 계열'],
  ['HYUNDAI', '현대백화점 계열'], ['HOMEPLUS', '홈플러스'], ['COUPANG', '쿠팡'],
  ['NAVER_SHOPPING', '네이버쇼핑'], ['OPEN_MARKET', 'G마켓·옥션·11번가'],
  ['FASHION_PLATFORM', '패션 플랫폼'], ['MARKET_KURLY', '마켓컬리'],
  ['HOME_SHOPPING', '홈쇼핑'], ['OVERSEAS', '해외 쇼핑'], ['OTHER', '기타'], ['NONE', '없음'],
]

const TRANSPORT_OPTIONS = [
  ['PUBLIC_TRANSIT', '대중교통'], ['CAR', '자가용'], ['TRAIN', '기차'], ['TAXI', '택시'],
  ['MOTORCYCLE', '오토바이·스쿠터'], ['SHARED_KICKBOARD', '공유 킥보드'],
  ['SHARED_BICYCLE', '공유 자전거'], ['BICYCLE', '자전거'], ['WALK', '도보'],
]

const AIRLINE_OPTIONS = [
  ['KOREAN_AIR', '대한항공'], ['ASIANA', '아시아나항공'], ['JEJU_AIR', '제주항공'],
  ['JIN_AIR', '진에어'], ['TWAY_AIR', '티웨이항공'], ['AIR_BUSAN', '에어부산'],
  ['AIR_SEOUL', '에어서울'], ['EASTAR_JET', '이스타항공'], ['AIR_PREMIA', '에어프레미아'],
  ['OTHER', '기타'], ['NONE', '선호 없음'],
]

const CHILD_AGE_OPTIONS = [
  ['INFANT', '영유아'], ['PRESCHOOL', '미취학'], ['ELEMENTARY_SCHOOL', '초등학생'],
  ['MIDDLE_SCHOOL', '중학생'], ['HIGH_SCHOOL', '고등학생'],
]

const MEMBERSHIP_OPTIONS = [
  '스타벅스 리워드', 'CJ ONE', '네이버플러스 멤버십', '신세계포인트',
  '대한항공 SKYPASS', '아시아나 클럽', 'L.POINT', 'GS&POINT', '해피포인트', 'OK캐쉬백',
]

// 문자열/JSON 을 안전하게 배열로. 예전 단일 코드값('CAR')도 배열로 감쌉니다.
function parseMulti(raw) {
  if (!raw) return []
  const s = String(raw).trim()
  if (s.startsWith('[')) {
    try {
      const v = JSON.parse(s)
      return Array.isArray(v) ? v : []
    } catch {
      return []
    }
  }
  if (!s || s.toLowerCase() === 'unknown') return []
  return [s]
}

export default function MemberInfo() {
  const { state, dispatch } = useApp()
  const userId = state.user?.userId

  const [form, setForm] = useState({}) // { TYPE: 'true'|'false'|코드값 }
  const [shopping, setShopping] = useState([])
  const [transports, setTransports] = useState([])
  const [airlines, setAirlines] = useState([])
  const [childAges, setChildAges] = useState([])
  const [memberships, setMemberships] = useState([])
  const [status, setStatus] = useState('loading') // 'loading'|'ready'|'saving'|'error'
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  // 현재 저장된 값으로 폼을 채웁니다.
  useEffect(() => {
    if (!userId) return
    let cancelled = false
    setStatus('loading')
    fetchEligibilities(userId)
      .then((map) => {
        if (cancelled) return
        setForm(map)
        setShopping(parseMulti(map.PRIMARY_SHOPPING_AFFILIATION))
        setTransports(parseMulti(map.PRIMARY_TRANSPORT))
        setAirlines(parseMulti(map.PREFERRED_AIRLINE))
        setChildAges(parseMulti(map.CHILD_AGE_GROUPS))
        setMemberships(parseMulti(map.MEMBERSHIPS))
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setError(err?.message || '회원정보를 불러오지 못했어요.')
        setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [userId])

  const get = (type, fallback = '') => form[type] ?? fallback
  const setVal = (type, value) => setForm((f) => ({ ...f, [type]: value }))
  const isYes = (type) => get(type, 'false') === 'true'
  const hasChildren = get('HAS_CHILDREN', 'false') === 'true'
  const childrenCount = Number(get('CHILDREN_COUNT', '0')) || 0

  // 복수선택 토글 — 최대 MAX_MULTI개. exclusive 값(선호 없음)은 단독 선택.
  function toggleMulti(setList, value, { exclusive, max = Infinity } = {}) {
    setList((cur) => {
      if (cur.includes(value)) return cur.filter((v) => v !== value)
      if (exclusive && value === exclusive) return [value]
      const base = exclusive ? cur.filter((v) => v !== exclusive) : cur
      if (base.length >= max) return base // 상한 초과 시 무시
      return [...base, value]
    })
  }

  async function save() {
    if (status === 'saving' || !userId) return
    setStatus('saving')
    setError('')

    // 관리하는 항목만 골라 백엔드 형식으로(나머지 자격정보는 서버가 upsert로 유지).
    const values = {}
    for (const [type] of BOOL_FIELDS) values[type] = isYes(type) ? 'true' : 'false'
    for (const [type] of SELECT_FIELDS) values[type] = get(type) || ''
    values.PRIMARY_SHOPPING_AFFILIATION = JSON.stringify(shopping)
    values.PRIMARY_TRANSPORT = JSON.stringify(transports)
    values.PREFERRED_AIRLINE = JSON.stringify(airlines)
    values.MEMBERSHIPS = JSON.stringify(memberships)
    values.HAS_CHILDREN = hasChildren ? 'true' : 'false'
    values.CHILDREN_COUNT = hasChildren ? String(Math.max(0, childrenCount)) : '0'
    values.CHILD_AGE_GROUPS = JSON.stringify(hasChildren ? childAges : [])

    // 드롭다운이 비어 있으면(min_length) 검증에 걸리므로 기본값을 채웁니다.
    for (const [type, , opts] of SELECT_FIELDS) {
      if (!values[type]) values[type] = opts[0][0]
    }

    try {
      await updateEligibilities(userId, values)
      setSaved(true)
      setStatus('ready')
      setTimeout(() => dispatch({ type: A.GO_HOME }), 900)
    } catch (err) {
      setError(err?.message || '저장하지 못했어요. 잠시 후 다시 시도해 주세요.')
      setStatus('error')
    }
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.iconBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.GO_HOME })}
        >
          ‹
        </button>
        <span className={styles.headerTitle}>회원정보 수정</span>
        <span className={styles.spacer} />
      </div>

      <p className={styles.lead}>입력한 조건은 카드 추천에 바로 반영돼요.</p>

      {status === 'loading' && <div className={styles.note}>불러오는 중…</div>}

      {status !== 'loading' && (
        <>
          {/* 자격 조건 */}
          <div className={styles.sectionTitle}>자격 조건</div>
          <div className={styles.card}>
            {BOOL_FIELDS.map(([type, label], i) => (
              <div
                key={type}
                className={`${styles.row} ${i === 0 ? styles.rowFirst : ''}`}
              >
                <span className={styles.rowLabel}>{label}</span>
                <div className={styles.segment}>
                  <button
                    type="button"
                    className={`${styles.segBtn} ${isYes(type) ? styles.segOn : ''}`}
                    onClick={() => setVal(type, 'true')}
                  >
                    예
                  </button>
                  <button
                    type="button"
                    className={`${styles.segBtn} ${!isYes(type) ? styles.segOn : ''}`}
                    onClick={() => setVal(type, 'false')}
                  >
                    아니오
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* 소비·이용 정보 — 통신사 + 쇼핑·교통·항공을 한 카드로 묶습니다. */}
          <div className={styles.sectionTitle}>소비·이용 정보</div>
          <div className={styles.card}>
            {SELECT_FIELDS.map(([type, label, opts]) => (
              <div key={type} className={`${styles.row} ${styles.rowFirst}`}>
                <span className={styles.rowLabel}>{label}</span>
                <select
                  className={styles.select}
                  value={get(type, opts[0][0])}
                  onChange={(e) => setVal(type, e.target.value)}
                >
                  {opts.map(([val, name]) => (
                    <option key={val} value={val}>{name}</option>
                  ))}
                </select>
              </div>
            ))}

            {/* 주 이용 쇼핑 계열 */}
            <div className={`${styles.row} ${styles.rowStack}`}>
              <span className={styles.rowLabel}>
                주 이용 쇼핑 계열<span className={styles.sectionHint}>최대 {SHOPPING_MAX}개</span>
              </span>
              <div className={styles.chips}>
                {SHOPPING_OPTIONS.map(([code, label]) => {
                  const on = shopping.includes(code)
                  const full = !on && code !== 'NONE' && shopping.length >= SHOPPING_MAX
                  return (
                    <button
                      key={code}
                      type="button"
                      className={`${styles.chip} ${on ? styles.chipOn : ''} ${full ? styles.chipOff : ''}`}
                      onClick={() => toggleMulti(setShopping, code, { exclusive: 'NONE', max: SHOPPING_MAX })}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* 주 이용 교통수단 */}
            <div className={`${styles.row} ${styles.rowStack}`}>
              <span className={styles.rowLabel}>
                주 이용 교통수단<span className={styles.sectionHint}>최대 {TRANSPORT_MAX}개</span>
              </span>
              <div className={styles.chips}>
                {TRANSPORT_OPTIONS.map(([code, label]) => {
                  const on = transports.includes(code)
                  const full = !on && transports.length >= TRANSPORT_MAX
                  return (
                    <button
                      key={code}
                      type="button"
                      className={`${styles.chip} ${on ? styles.chipOn : ''} ${full ? styles.chipOff : ''}`}
                      onClick={() => toggleMulti(setTransports, code, { max: TRANSPORT_MAX })}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* 선호 항공사 */}
            <div className={`${styles.row} ${styles.rowStack}`}>
              <span className={styles.rowLabel}>
                선호 항공사<span className={styles.sectionHint}>최대 {AIRLINE_MAX}개</span>
              </span>
              <div className={styles.chips}>
                {AIRLINE_OPTIONS.map(([code, label]) => {
                  const on = airlines.includes(code)
                  const full = !on && code !== 'NONE' && airlines.length >= AIRLINE_MAX
                  return (
                    <button
                      key={code}
                      type="button"
                      className={`${styles.chip} ${on ? styles.chipOn : ''} ${full ? styles.chipOff : ''}`}
                      onClick={() => toggleMulti(setAirlines, code, { exclusive: 'NONE', max: AIRLINE_MAX })}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* 멤버십 */}
          <div className={styles.sectionTitle}>보유 멤버십</div>
          <div className={styles.card}>
            <div className={styles.chips}>
              {MEMBERSHIP_OPTIONS.map((name) => (
                <button
                  key={name}
                  type="button"
                  className={`${styles.chip} ${memberships.includes(name) ? styles.chipOn : ''}`}
                  onClick={() => toggleMulti(setMemberships, name)}
                >
                  {name}
                </button>
              ))}
            </div>
          </div>

          {/* 자녀 */}
          <div className={styles.sectionTitle}>자녀</div>
          <div className={styles.card}>
            <div className={`${styles.row} ${styles.rowFirst}`}>
              <span className={styles.rowLabel}>자녀 유무</span>
              <div className={styles.segment}>
                <button
                  type="button"
                  className={`${styles.segBtn} ${hasChildren ? styles.segOn : ''}`}
                  onClick={() => setVal('HAS_CHILDREN', 'true')}
                >
                  있음
                </button>
                <button
                  type="button"
                  className={`${styles.segBtn} ${!hasChildren ? styles.segOn : ''}`}
                  onClick={() => setVal('HAS_CHILDREN', 'false')}
                >
                  없음
                </button>
              </div>
            </div>

            {hasChildren && (
              <>
                <div className={styles.row}>
                  <span className={styles.rowLabel}>자녀 수</span>
                  <div className={styles.stepper}>
                    <button
                      type="button"
                      className={styles.stepBtn}
                      aria-label="줄이기"
                      onClick={() =>
                        setVal('CHILDREN_COUNT', String(Math.max(0, childrenCount - 1)))
                      }
                    >
                      −
                    </button>
                    <span className={styles.stepNum}>{childrenCount}</span>
                    <button
                      type="button"
                      className={styles.stepBtn}
                      aria-label="늘리기"
                      onClick={() =>
                        setVal('CHILDREN_COUNT', String(Math.min(9, childrenCount + 1)))
                      }
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className={`${styles.row} ${styles.rowStack}`}>
                  <span className={styles.rowLabel}>자녀 연령대</span>
                  <div className={styles.chips}>
                    {CHILD_AGE_OPTIONS.map(([code, label]) => (
                      <button
                        key={code}
                        type="button"
                        className={`${styles.chip} ${childAges.includes(code) ? styles.chipOn : ''}`}
                        onClick={() => toggleMulti(setChildAges, code)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <button
            type="button"
            className={styles.save}
            onClick={save}
            disabled={status === 'saving' || saved}
          >
            {saved ? '저장되었어요 ✓' : status === 'saving' ? '저장 중…' : '저장하기'}
          </button>
        </>
      )}
    </div>
  )
}
