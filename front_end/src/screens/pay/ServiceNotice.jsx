import { useState } from 'react'
import { NOTICE_SECTIONS, NOTICE_SUMMARY } from '../../data/notice.js'
import styles from './ServiceNotice.module.css'

/**
 * 결제 확인 화면 하단의 주요 안내사항.
 * 접힌 상태에서는 요약 두 문단만 보이고, '자세히 보기'를 누르면 ①~⑥ 전체가 펼쳐집니다.
 * (펼친 상태에서는 ① 본문이 요약과 같아 요약을 따로 반복하지 않습니다.)
 */
export default function ServiceNotice() {
  const [open, setOpen] = useState(false)

  return (
    <div className={styles.notice}>
      {open ? (
        <div className={styles.full}>
          <div className={styles.heading}>주요 안내사항</div>
          {NOTICE_SECTIONS.map((section) => (
            <section key={section.title} className={styles.section}>
              <div className={styles.sectionTitle}>{section.title}</div>
              {section.paragraphs.map((text) => (
                <p key={text} className={styles.text}>
                  {text}
                </p>
              ))}
              {section.bullets && (
                <ul className={styles.bullets}>
                  {section.bullets.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
              {section.footer?.map((text) => (
                <p key={text} className={styles.text}>
                  {text}
                </p>
              ))}
            </section>
          ))}
        </div>
      ) : (
        NOTICE_SUMMARY.map((text) => (
          <p key={text} className={styles.text}>
            {text}
          </p>
        ))
      )}

      <button
        type="button"
        className={styles.toggle}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? '접기' : '자세히 보기'}
      </button>
    </div>
  )
}
