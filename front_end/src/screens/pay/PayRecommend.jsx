import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { orderedComparison, hasNoEligibleCard } from '../../utils/compare.js'
import { gradientForCard } from '../../data/cards.js'
import { krw } from '../../utils/format.js'
import shared from './payShared.module.css'
import styles from './PayRecommend.module.css'

export default function PayRecommend() {
  const { state, dispatch } = useApp()
  const { transaction, result, error, noEligibleCard, payIdx } = state

  const ranked = orderedComparison(result?.comparison)
  const selectedIdx = payIdx < ranked.length ? payIdx : 0
  const chosen = ranked[selectedIdx] || null
  const amount = transaction?.payment_amount || 0
  const discount = chosen?.expected_benefit || 0

  // 404(보유카드 없음) 뿐 아니라, 200이지만 모든 카드가 eligible=false 인 경우도
  // "이 업종엔 혜택 카드가 없어요" 안내를 보여줍니다. -0원 추천은 띄우지 않습니다.
  const noBenefitAnywhere = noEligibleCard || hasNoEligibleCard(ranked)

  function retry() {
    // 분석 화면으로 되돌리면 추천 API가 다시 호출됩니다.
    dispatch({ type: A.SET_PAY_STEP, payStep: 'analyzing' })
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.scroll}>
        <div className={`${shared.brandRow} ${shared.end}`}>picka</div>

        {error && <ErrorNotice message={error} onRetry={retry} />}

        {noBenefitAnywhere && (
          <div className={styles.notice}>
            <div className={styles.noticeIcon}>💡</div>
            <div className={styles.noticeTitle}>이 업종엔 혜택 카드가 없어요</div>
            <div className={styles.noticeBody}>
              {transaction?.payment_category} 업종에 적용되는 혜택이 없습니다.
              <br />
              아래에서 아무 카드로나 결제하세요.
            </div>
          </div>
        )}

        {chosen && !error && !noBenefitAnywhere && (
          <>
            <div className={styles.badgeRow}>
              <span className={styles.badge}>✦ SMART SUGGESTION</span>
            </div>

            <div className={styles.title}>AI 추천 카드</div>

            {/* 추천 근거 문구는 백엔드(saving_message)를 그대로 씁니다.
                실적 기준 추천일 때 "혜택이 가장 좋아요"는 사실이 아닐 수 있습니다. */}
            <div className={styles.lead}>
              {result?.saving_message || (
                <>
                  {chosen.card_company}가 {transaction?.payment_category}에서
                  {' '}
                  {chosen.benefit_rate ? `${chosen.benefit_rate}% 할인` : '가장 큰 혜택'}으로
                  <br />
                  혜택이 가장 좋아요. 이 카드로 결제할까요?
                </>
              )}
            </div>

            <div
              className={styles.bigCard}
              style={{ background: gradientForCard(chosen) }}
            >
              <div className={styles.bigCardHead}>
                <div>
                  <div className={styles.bigCardCompany}>{chosen.card_company}</div>
                  <div className={styles.bigCardName}>{chosen.card_name}</div>
                </div>
                <span className={styles.bigCardBrand}>VISA</span>
              </div>
              <div className={styles.bigCardNumber}>
                •••• •••• •••• {chosen.last_four}
              </div>
            </div>

            <div className={styles.stats}>
              <div className={styles.stat}>
                <div className={styles.statLabel}>🏷 할인 혜택</div>
                <div className={`${styles.statValue} ${styles.good}`}>
                  -{krw(discount)}원
                </div>
                <div className={styles.statNote}>{transaction?.payment_category}</div>
              </div>
              <div className={styles.stat}>
                <div className={styles.statLabel}>최종 승인 금액</div>
                <div className={`${styles.statValue} ${styles.plain}`}>
                  {krw(amount - discount)}원
                </div>
                <div className={styles.statNote}>정가 {krw(amount)}원</div>
              </div>
            </div>

            <div className={styles.reason}>
              <span style={{ fontSize: 15 }}>💡</span>
              <span className={styles.reasonText}>추천 이유 · {chosen.reason}</span>
            </div>
          </>
        )}
      </div>

      <div className={styles.scrim} />

      <div className={styles.sheet}>
        <div className={styles.sheetHead}>
          <div className={styles.grabber} />
          <div className={styles.sheetTitle}>다른 카드로 결제하기</div>
          <div className={styles.sheetSub}>
            추천 순서대로 정렬했어요. 원하는 카드를 선택하세요.
          </div>
        </div>

        <div className={styles.sheetList}>
          {ranked.map((card, i) => (
            <div
              key={card.card_id}
              className={[
                styles.row,
                i === selectedIdx ? styles.selected : '',
                card.eligible ? '' : styles.dim,
              ].join(' ')}
              onClick={() => dispatch({ type: A.SELECT_PAY_CARD, index: i })}
            >
              <span className={styles.rank}>{i + 1}</span>
              <div
                className={styles.swatch}
                style={{ background: gradientForCard(card) }}
              />
              <div className={styles.rowMain}>
                <div className={styles.rowName}>
                  {card.card_company} {card.card_name}
                </div>
                <div className={styles.rowSub}>
                  {card.eligible
                    ? `할인 -${krw(card.expected_benefit)}원`
                    : '적용 가능한 혜택 없음'}
                </div>
              </div>
              <div className={styles.rowRight}>
                <div className={styles.rowAmount}>
                  {krw(amount - (card.expected_benefit || 0))}원
                </div>
                <div className={styles.rowNote}>결제 예상</div>
              </div>
            </div>
          ))}
        </div>

        <div className={styles.sheetFoot}>
          <button
            type="button"
            className={shared.primaryBtn}
            disabled={!chosen}
            onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'confirm' })}
          >
            이 카드로 결제
          </button>
          <button
            type="button"
            className={shared.ghostBtn}
            onClick={() => dispatch({ type: A.RESET_PAY })}
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    </div>
  )
}

function ErrorNotice({ message, onRetry }) {
  return (
    <div className={styles.notice}>
      <div className={styles.noticeIcon}>⚠️</div>
      <div className={styles.noticeTitle}>추천을 불러오지 못했어요</div>
      <div className={styles.noticeBody}>{message}</div>
      <button type="button" className={styles.retry} onClick={onRetry}>
        다시 시도
      </button>
    </div>
  )
}
