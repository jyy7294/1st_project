/**
 * 카드 승인(결제 처리) 아이콘.
 *
 * 방패 아이콘과 같은 톤으로, 파란 원 안에 흰 자물쇠를 담백하게 얹었습니다.
 * 예전의 글로우 오브(발광·스핀)를 걷어낸 플랫 스타일입니다.
 *
 * @param {{ size?: number }} props
 */
export default function LockIcon({ size = 84 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      role="img"
      aria-label="보안 결제"
    >
      <circle cx="32" cy="32" r="32" fill="url(#pk-lockBg)" />
      {/* 위쪽 옅은 하이라이트로 살짝 입체감. */}
      <ellipse cx="32" cy="19" rx="22" ry="13" fill="#fff" opacity=".16" />
      {/* 고리(shackle): 몸통 뒤로 올라가는 U자. */}
      <path
        d="M24 30 V25 a8 8 0 0 1 16 0 V30"
        stroke="#fff"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      {/* 몸통. */}
      <rect x="19" y="29" width="26" height="19" rx="5.5" fill="#fff" />
      {/* 열쇠구멍. */}
      <circle cx="32" cy="37" r="3" fill="#2F6BFF" />
      <path d="M32 38.5 L30.7 44 H33.3 Z" fill="#2F6BFF" />
      <defs>
        <linearGradient
          id="pk-lockBg"
          x1="8"
          y1="6"
          x2="56"
          y2="60"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#6aa4ff" />
          <stop offset="1" stopColor="#2F6BFF" />
        </linearGradient>
      </defs>
    </svg>
  )
}
