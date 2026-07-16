import styles from './Loading.module.css'

// 재사용 로딩 화면: 스피너 + 메시지
export default function Loading({ message }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.spinner} />
      <p className={styles.message}>{message}</p>
    </div>
  )
}
