import { useRef } from 'react'
import { useAppStore } from '../store/useAppStore'
import { getDownloadUrl, generateDetailStream } from '../api'

/** 테이블 헤더 셀 공통 스타일 */
const TH_STYLE: React.CSSProperties = {
  padding: '10px 8px',
  textAlign: 'center',
  fontWeight: 600,
  fontSize: 14,
}

/** 테이블 데이터 셀 공통 스타일 */
const TD_STYLE: React.CSSProperties = {
  padding: '8px',
  fontSize: 14,
  verticalAlign: 'top',
  textAlign: 'left',
}

/**
 * 원본 요구사항 읽기 전용 테이블 컴포넌트.
 * HWP 파싱 결과를 4컬럼(ID/분류/명칭/내용)으로 표시한다 (AC-003-01, REQ-003-01).
 * 원본 데이터는 편집 불가 — 상세요구사항과 시각적으로 명확히 구분된다 (REQ-003-04).
 */
export function OriginalReqTable() {
  const originalReqs = useAppStore((s) => s.originalReqs)
  const detailReqs = useAppStore((s) => s.detailReqs)
  const sessionId = useAppStore((s) => s.sessionId)
  const isGenerating = useAppStore((s) => s.isGenerating)
  const appendDetailReq = useAppStore((s) => s.appendDetailReq)
  const setIsGenerating = useAppStore((s) => s.setIsGenerating)
  const setPhase = useAppStore((s) => s.setPhase)
  const setError = useAppStore((s) => s.setError)

  // SSE cleanup 함수 참조 보관 — 컴포넌트 언마운트 또는 중단 시 사용
  const cleanupRef = useRef<(() => void) | null>(null)

  /**
   * 상세요구사항 생성 버튼 핸들러.
   * generateDetailStream으로 SSE 연결하여 item 이벤트 수신 시 행을 동적으로 추가한다 (REQ-002).
   */
  const handleGenerate = () => {
    if (!sessionId || isGenerating) return
    setError(null)
    setIsGenerating(true)
    cleanupRef.current = generateDetailStream(sessionId, {
      onItem: (req) => appendDetailReq(req),
      onDone: () => {
        setIsGenerating(false)
        setPhase('generated')
        cleanupRef.current = null
      },
      onError: (msg) => {
        setError(msg)
        setIsGenerating(false)
        cleanupRef.current = null
      },
    })
  }

  return (
    <div data-testid="original-req-table">
      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: '#0F172A' }}>
        원본 요구사항 ({originalReqs.length}건)
      </h2>

      {/* 수평 스크롤 처리 — 모바일/태블릿에서 컬럼이 잘리지 않도록 */}
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}
          aria-label="원본 요구사항 테이블"
        >
          <caption style={{ display: 'none' }}>HWP에서 추출된 원본 요구사항 목록</caption>
          <thead>
            {/* 디자인 토큰: 헤더 배경 #4472C4 (ui-design.md) */}
            <tr style={{ background: '#4472C4', color: '#fff' }}>
              <th scope="col" style={{ ...TH_STYLE, width: '10%' }}>
                요구사항 ID
              </th>
              <th scope="col" style={{ ...TH_STYLE, width: '12%' }}>
                분류
              </th>
              <th scope="col" style={{ ...TH_STYLE, width: '20%' }}>
                명칭
              </th>
              <th scope="col" style={{ ...TH_STYLE, width: '58%' }}>
                내용
              </th>
            </tr>
          </thead>
          <tbody>
            {originalReqs.length === 0 ? (
              <tr>
                <td
                  colSpan={4}
                  style={{ ...TD_STYLE, textAlign: 'center', color: '#94A3B8', padding: '32px 8px' }}
                >
                  데이터가 없습니다
                </td>
              </tr>
            ) : (
              originalReqs.map((req) => (
                <tr
                  key={req.id}
                  style={{ borderBottom: '1px solid #E2E8F0', background: '#FFFFFF' }}
                >
                  {/* 원본 ID 컬럼은 Bold 처리 (디자인 토큰 — req-003-design.md) */}
                  <td style={{ ...TD_STYLE, fontWeight: 700 }}>{req.id}</td>
                  <td style={TD_STYLE}>{req.category}</td>
                  <td style={TD_STYLE}>{req.name}</td>
                  {/* 내용 컬럼은 줄바꿈 허용 — pre-wrap으로 HWP 원문 줄바꿈 유지 */}
                  <td style={{ ...TD_STYLE, whiteSpace: 'pre-wrap' }}>{req.content}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'flex', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
        {/* 1단계 다운로드: sessionId가 있을 때만 표시 (REQ-005-01) */}
        {sessionId && (
          <a
            href={getDownloadUrl(sessionId, 1)}
            download
            style={{
              padding: '10px 20px',
              background: '#059669',
              color: '#fff',
              borderRadius: 8,
              textDecoration: 'none',
              fontSize: 14,
              fontWeight: 600,
            }}
            data-testid="download-stage1"
          >
            1단계 엑셀 다운로드
          </a>
        )}
        {/* 상세요구사항 생성 버튼: detailReqs가 비어있을 때만 표시 (REQ-002) */}
        {detailReqs.length === 0 && (
          <button
            style={{
              padding: '10px 20px',
              background: isGenerating ? '#93C5FD' : '#2563EB',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: isGenerating ? 'not-allowed' : 'pointer',
            }}
            onClick={handleGenerate}
            disabled={isGenerating}
            data-testid="generate-detail-btn"
          >
            {isGenerating ? '생성 중...' : '상세요구사항 생성'}
          </button>
        )}
      </div>
    </div>
  )
}
