import { useState, useRef } from 'react'
import { useAppStore } from '../store/useAppStore'
import { uploadHwp } from '../api'

/** .hwp 확장자 여부를 판별한다. 대소문자 구분 없이 처리한다. */
function isHwpFile(file: File): boolean {
  return file.name.toLowerCase().endsWith('.hwp')
}

/**
 * HWP 파일 업로드 패널 컴포넌트.
 * 드래그앤드롭과 파일 선택 다이얼로그를 모두 지원한다 (AC-001-01).
 * .hwp 이외 파일은 클라이언트에서 즉시 거부하여 불필요한 서버 요청을 방지한다 (REQ-001-04).
 */
export function UploadPanel() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const { isUploading, setIsUploading, setSessionId, setOriginalReqs, setPhase, setError } =
    useAppStore()

  /**
   * 파일 선택 처리 진입점.
   * .hwp 검증 실패 시 선택 상태를 변경하지 않고 에러만 노출한다.
   */
  const handleFile = (file: File) => {
    if (!isHwpFile(file)) {
      setError('HWP 파일만 업로드 가능합니다.')
      return
    }
    setError(null)
    setSelectedFile(file)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => setDragging(false)

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  /**
   * 업로드 실행.
   * 서버 응답으로 sessionId·originalReqs를 스토어에 저장하고 phase를 'parsed'로 전환한다.
   * 에러 메시지는 백엔드 detail.message를 우선 사용하고, 없으면 기본 문자열로 fallback한다.
   */
  const handleUpload = async () => {
    if (!selectedFile) return
    setIsUploading(true)
    try {
      const result = await uploadHwp(selectedFile)
      setSessionId(result.session_id)
      setOriginalReqs(result.requirements)
      setPhase('parsed')
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: { message?: string } } } })?.response?.data?.detail
          ?.message ?? '업로드에 실패했습니다.'
      setError(msg)
    } finally {
      setIsUploading(false)
    }
  }

  const dropzoneStyle: React.CSSProperties = {
    border: `2px dashed ${dragging ? '#2563EB' : '#CBD5E1'}`,
    borderRadius: 12,
    padding: 48,
    textAlign: 'center',
    cursor: isUploading ? 'not-allowed' : 'pointer',
    background: dragging ? '#EFF6FF' : '#F8FAFC',
    transition: '150ms ease',
  }

  return (
    <div
      style={{ maxWidth: 600, margin: '0 auto', paddingTop: 48 }}
      data-testid="upload-panel"
    >
      {/* 드롭존 — role="button" + tabIndex로 키보드 접근성 확보 (a11y 체크리스트) */}
      <div
        role="button"
        tabIndex={0}
        aria-label="HWP 파일을 드래그하거나 클릭하여 선택하세요"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !isUploading) inputRef.current?.click()
        }}
        style={dropzoneStyle}
        data-testid="dropzone"
      >
        {/* 숨김 파일 입력 — accept로 OS 파일 선택 다이얼로그 기본 필터 적용 */}
        <input
          ref={inputRef}
          type="file"
          accept=".hwp"
          aria-label="HWP 파일 선택"
          style={{ display: 'none' }}
          onChange={handleInputChange}
          data-testid="file-input"
        />
        <div style={{ fontSize: 48, marginBottom: 12 }}>&#128196;</div>
        <p style={{ margin: '0 0 8px', fontWeight: 600, fontSize: 16, color: '#0F172A' }}>
          HWP 파일을 드래그하거나 클릭하여 선택하세요
        </p>
        <p style={{ margin: 0, fontSize: 12, color: '#94A3B8' }}>.hwp 파일만 지원합니다</p>
        {selectedFile && (
          <p
            style={{ marginTop: 12, color: '#2563EB', fontWeight: 600, fontSize: 14 }}
            data-testid="selected-filename"
          >
            {selectedFile.name}
          </p>
        )}
      </div>

      <button
        onClick={handleUpload}
        disabled={!selectedFile || isUploading}
        aria-busy={isUploading}
        style={{
          marginTop: 16,
          width: '100%',
          padding: '12px 0',
          background: '#2563EB',
          color: '#fff',
          border: 'none',
          borderRadius: 8,
          fontSize: 16,
          fontWeight: 600,
          cursor: selectedFile && !isUploading ? 'pointer' : 'not-allowed',
          opacity: selectedFile && !isUploading ? 1 : 0.5,
          transition: '150ms ease',
        }}
        data-testid="upload-button"
      >
        {isUploading ? '업로드 중...' : '업로드 및 파싱'}
      </button>
    </div>
  )
}
