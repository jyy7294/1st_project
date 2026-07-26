import styles from './PickaLogo.module.css'

/**
 * PICKA 브랜드 로고.
 *
 * 원본은 public/assets/picka_logo.png(마크)·picka_naming.png(워드마크)이고,
 * 화면에는 배경을 걷어내고 여백을 잘라낸 picka-mark.png / picka-wordmark.png 를 씁니다.
 * 로고를 교체할 때는 그 두 파일만 바꾸면 모든 화면에 반영됩니다.
 *
 * 마크는 자체 색을 가지므로 어두운 배경에서도 그대로 쓰고,
 * 네이비 단색인 워드마크만 tone="light" 일 때 흰색으로 반전합니다.
 *
 * @param {object} props
 * @param {number} [props.height] 로고 높이(px). 마크 기준이며 워드마크는 비율로 맞춥니다.
 * @param {'lockup'|'mark'|'wordmark'} [props.variant] 마크+워드마크 / 마크만 / 글자만
 * @param {'dark'|'light'} [props.tone] 배경 톤. light = 어두운 배경용(워드마크 흰색)
 * @param {string} [props.className]
 */
export default function PickaLogo({
  height = 26,
  variant = 'lockup',
  tone = 'dark',
  className = '',
}) {
  // wordmark 단독일 때는 받은 높이를 그대로, 마크와 함께면 살짝 작게 씁니다.
  const wordHeight = variant === 'wordmark' ? height : Math.round(height * 0.74)


  return (
    <span className={`${styles.logo} ${className}`} style={{ gap: Math.round(height * 0.24) }}>
      {variant !== 'wordmark' && (
        <img src="/assets/picka-mark.png" alt="" className={styles.mark} style={{ height }} />
      )}
      {variant !== 'mark' && (
        <img
          src="/assets/picka-wordmark.png"
          alt="picka"
          className={`${styles.wordmark} ${tone === 'light' ? styles.light : ''}`}
          style={{ height: wordHeight }}
        />
      )}
      {variant === 'mark' && <span className={styles.srOnly}>picka</span>}
    </span>
  )
}
