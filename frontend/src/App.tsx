import { useAppStore } from './store/useAppStore'
import { UploadPanel } from './components/UploadPanel'
import { OriginalReqTable } from './components/OriginalReqTable'
import { DetailReqTable } from './components/DetailReqTable'
import { ChatPanel } from './components/ChatPanel'
import { DownloadBar } from './components/DownloadBar'
import './App.css'

/**
 * 애플리케이션 루트 레이아웃 컴포넌트.
 * phase 상태에 따라 화면 영역을 조건부 렌더링한다.
 * upload → UploadPanel, parsed → 테이블 영역,
 * generated → 테이블 + 우측 ChatPanel + 상단 DownloadBar (REQ-004, REQ-005).
 */
export default function App() {
  const phase = useAppStore((s) => s.phase)
  const error = useAppStore((s) => s.error)
  const reset = useAppStore((s) => s.reset)
  const detailReqs = useAppStore((s) => s.detailReqs)
  const isGenerating = useAppStore((s) => s.isGenerating)

  return (
    <div style={{ fontFamily: 'Pretendard, Inter, sans-serif', width: '100%', padding: '24px 32px', boxSizing: 'border-box' }}>
      {/* 헤더: 제목 + (parsed 이후) 새 파일 업로드 버튼 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#2563EB', margin: 0, fontSize: 24, fontWeight: 700 }}>
          HWP 상세요구사항 자동생성 도구
        </h1>
        {phase !== 'upload' && (
          <button
            onClick={reset}
            style={{
              padding: '8px 16px',
              background: '#fff',
              color: '#475569',
              border: '1px solid #E2E8F0',
              borderRadius: 8,
              fontSize: 14,
              cursor: 'pointer',
            }}
            data-testid="new-upload-btn"
          >
            새 파일 업로드
          </button>
        )}
      </div>

      {/* 전역 에러 배너 — role="alert"로 스크린리더에 즉시 알림 */}
      {error && (
        <div
          role="alert"
          style={{
            background: '#FEF2F2',
            color: '#991B1B',
            border: '1px solid #FECACA',
            padding: '12px 16px',
            borderRadius: 8,
            marginBottom: 16,
            fontSize: 14,
          }}
        >
          {error}
        </div>
      )}

      {/* 화면 1: 업로드 (phase === 'upload') */}
      {phase === 'upload' && (
        <div id="upload-area" data-testid="upload-area">
          <UploadPanel />
        </div>
      )}

      {/* 화면 2/3: 테이블 영역 + 다운로드 + 채팅 패널 (phase !== 'upload') */}
      {phase !== 'upload' && (
        <>
          {/* 다운로드 바: 파싱 완료 후 항상 표시 (REQ-005) */}
          <DownloadBar />

          <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
            <div style={{ flex: 1, minWidth: 0 }} id="table-area" data-testid="table-area">
              <OriginalReqTable />
              {/* DetailReqTable: 생성 중이거나 상세 행이 1개 이상일 때 표시 (REQ-003-02) */}
              {(detailReqs.length > 0 || isGenerating) && <DetailReqTable />}
            </div>

            {/* 채팅 패널: generated 단계에서만 우측에 표시 (REQ-004) */}
            {/* REQ-011: position sticky로 스크롤 시에도 뷰포트 내 고정 */}
            {phase === 'generated' && (
              <div
                style={{
                  width: 380,
                  flexShrink: 0,
                  alignSelf: 'flex-start',
                  position: 'sticky',
                  top: 24,
                  maxHeight: 'calc(100vh - 48px)',
                  overflowY: 'auto',
                }}
                id="chat-area"
                data-testid="chat-area"
              >
                <ChatPanel />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
