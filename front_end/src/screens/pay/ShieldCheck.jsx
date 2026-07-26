/**
 * 보안/안전결제 아이콘.
 *
 * 어두운 배경 위에서도 또렷하게 읽히도록, 파란 원 안에 흰 방패와 체크를 얹었습니다.
 * 예전의 글로우 오브(빙글빙글 도는 링·발광)를 걷어내고 담백한 플랫 아이콘으로 대체합니다.
 *
 * @param {{ size?: number }} props
 */
export default function ShieldCheck({ size = 72 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      role="img"
      aria-label="안전"
    >
      <circle cx="32" cy="32" r="32" fill="url(#pk-shieldBg)" />
      {/* 위쪽에 옅은 하이라이트를 깔아 살짝 입체감을 줍니다. */}
      <ellipse cx="32" cy="19" rx="22" ry="13" fill="#fff" opacity=".16" />
      <path
        d="M32 14.5 L45.5 19.5 V31.6 C45.5 40.6 39.4 47.4 32 50.5 C24.6 47.4 18.5 40.6 18.5 31.6 V19.5 Z"
        fill="#fff"
      />
      <path
        d="M26 32.2 L30.4 36.6 L38.4 27"
        stroke="#2F6BFF"
        strokeWidth="3.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <defs>
        <linearGradient
          id="pk-shieldBg"
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
