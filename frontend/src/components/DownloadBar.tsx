import { useAppStore } from '../store/useAppStore'
import { getDownloadUrl } from '../api'

/**
 * 엑셀 다운로드 버튼 바 (REQ-005).
 *
 * - 1단계 버튼: originalReqs 존재 시 항상 표시 (원본 요구사항만 포함)
 * - 2단계 버튼: detailReqs 존재 시에만 표시 (원본 + 상세 포함)
 * - sessionId 없거나 originalReqs 미생성이면 null 반환 (렌더링 생략)
 */
export function DownloadBar() {
  const { sessionId, originalReqs, detailReqs } = useAppStore()

  // sessionId 없거나 파싱 결과 없으면 다운로드 영역 자체를 숨김
  if (!sessionId || originalReqs.length === 0) return null

  return (
    <div
      data-testid="download-bar"
      style={{ display: 'flex', gap: 12, padding: '16px 0', alignItems: 'center' }}
    >
      <span style={{ fontSize: 14, color: '#64748B', fontWeight: 600 }}>다운로드:</span>

      {/* 1단계: 원본 요구사항만 포함한 엑셀 (AC-005-01) */}
      <a
        href={getDownloadUrl(sessionId, 1)}
        download
        data-testid="download-stage1"
        style={{
          padding: '8px 18px',
          background: '#059669',
          color: '#fff',
          borderRadius: 8,
          textDecoration: 'none',
          fontSize: 14,
        }}
      >
        1단계 (원본 엑셀)
      </a>

      {/* 2단계: 상세요구사항 생성 완료 후에만 활성화 (AC-005-02, UT-005 활성화 조건) */}
      {detailReqs.length > 0 && (
        <a
          href={getDownloadUrl(sessionId, 2)}
          download
          data-testid="download-stage2"
          style={{
            padding: '8px 18px',
            background: '#7C3AED',
            color: '#fff',
            borderRadius: 8,
            textDecoration: 'none',
            fontSize: 14,
          }}
        >
          2단계 (상세 포함 엑셀)
        </a>
      )}
    </div>
  )
}
