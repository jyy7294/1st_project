import { useEffect, useRef, useState } from 'react'
import styles from './CardArt.module.css'

/**
 * 실물 카드 이미지.
 *
 * 카드사 이미지가 어떤 건 가로, 어떤 건 세로로 들어옵니다.
 * 이미지 방향이 넣을 자리와 다르면 90도 돌려서 카드가 눕거나 서 있도록 맞춥니다.
 *
 * @param {object} props
 * @param {string} props.src 이미지 주소
 * @param {'landscape'|'portrait'} [props.frame] 이 이미지를 넣을 자리의 방향
 */
export default function CardArt({ src, frame = 'landscape' }) {
  const wrapRef = useRef(null)
  const [box, setBox] = useState(null) // 넣을 자리의 크기
  const [portrait, setPortrait] = useState(null) // 이미지가 세로형인지
  const [failed, setFailed] = useState(false)

  // 자리 크기가 바뀌면 회전 후 크기도 다시 계산해야 합니다.
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return undefined
    const measure = () => setBox({ w: el.clientWidth, h: el.clientHeight })
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  if (!src || failed) return null

  const frameIsPortrait = frame === 'portrait'
  // 이미지와 자리의 방향이 어긋날 때만 돌립니다.
  const rotate = portrait !== null && box && portrait !== frameIsPortrait

  // 90도 돌리면 가로·세로가 뒤바뀌므로 크기를 서로 바꿔 넣습니다.
  const style = rotate ? { width: box.h, height: box.w } : undefined

  return (
    <span className={styles.wrap} ref={wrapRef} aria-hidden="true">
      <img
        src={src}
        alt=""
        draggable={false}
        className={`${styles.art} ${rotate ? styles.rotated : ''}`}
        style={style}
        onLoad={(e) => setPortrait(e.currentTarget.naturalHeight > e.currentTarget.naturalWidth)}
        // 이미지를 못 불러오면 아무것도 그리지 않고 배경 그라데이션만 남깁니다.
        onError={() => setFailed(true)}
      />
    </span>
  )
}
