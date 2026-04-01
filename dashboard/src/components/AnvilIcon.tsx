export default function AnvilIcon({ className = 'w-4 h-4' }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* 모루 상판 */}
      <path
        d="M8 28h48l-4 8H12l-4-8z"
        fill="currentColor"
        opacity="0.9"
      />
      {/* 모루 뿔 (horn) */}
      <path
        d="M56 28h-4l8-6v6h-4z"
        fill="currentColor"
        opacity="0.7"
      />
      {/* 모루 몸통 */}
      <path
        d="M18 36h28v8H18z"
        fill="currentColor"
        opacity="0.8"
      />
      {/* 모루 받침대 */}
      <path
        d="M14 44h36v6H14z"
        fill="currentColor"
        opacity="0.6"
      />
      {/* 망치 */}
      <rect
        x="26" y="8" width="4" height="18" rx="1"
        fill="currentColor"
        opacity="0.5"
        transform="rotate(-30 28 17)"
      />
      <rect
        x="20" y="6" width="12" height="6" rx="1.5"
        fill="currentColor"
        opacity="0.7"
        transform="rotate(-30 26 9)"
      />
    </svg>
  )
}
