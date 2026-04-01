/**
 * UploadPanel 컴포넌트 단위 테스트.
 * UT-001-04: .hwp 이외 파일 선택 시 에러 메시지 표시
 * UT-001-05: 파일 미선택 시 업로드 버튼 disabled
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { UploadPanel } from '../components/UploadPanel'
import { useAppStore } from '../store/useAppStore'

// api 모듈 모킹 — 실제 HTTP 요청 없이 컴포넌트 동작만 검증한다
vi.mock('../api', () => ({
  uploadHwp: vi.fn(),
  getDownloadUrl: (sessionId: string, stage: number) =>
    `http://localhost:8000/api/v1/download?session_id=${sessionId}&stage=${stage}`,
}))

beforeEach(() => {
  useAppStore.getState().reset()
})

describe('UploadPanel — 파일 미선택 상태', () => {
  it('파일을 선택하지 않으면 업로드 버튼이 disabled 상태여야 한다', () => {
    render(<UploadPanel />)
    const uploadBtn = screen.getByTestId('upload-button')
    expect(uploadBtn).toBeDisabled()
  })

  it('초기 상태에서 파일명이 표시되지 않아야 한다', () => {
    render(<UploadPanel />)
    expect(screen.queryByTestId('selected-filename')).not.toBeInTheDocument()
  })
})

describe('UploadPanel — 파일 선택 유효성 검사 (UT-001-04)', () => {
  it('.hwp 이외 파일 선택 시 에러 메시지가 스토어에 설정된다', () => {
    render(<UploadPanel />)
    const input = screen.getByTestId('file-input')

    // PDF 파일 선택 시뮬레이션
    const pdfFile = new File(['content'], 'document.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [pdfFile] } })

    // 스토어의 error 상태가 업데이트되어야 한다
    expect(useAppStore.getState().error).toBe('HWP 파일만 업로드 가능합니다.')
  })

  it('.docx 파일 선택 시 에러 메시지가 표시된다', () => {
    render(<UploadPanel />)
    const input = screen.getByTestId('file-input')

    const docxFile = new File(['content'], 'document.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    fireEvent.change(input, { target: { files: [docxFile] } })

    expect(useAppStore.getState().error).toBe('HWP 파일만 업로드 가능합니다.')
  })

  it('.hwp 이외 파일 선택 후 업로드 버튼이 여전히 disabled여야 한다', () => {
    render(<UploadPanel />)
    const input = screen.getByTestId('file-input')

    const pdfFile = new File(['content'], 'document.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [pdfFile] } })

    const uploadBtn = screen.getByTestId('upload-button')
    expect(uploadBtn).toBeDisabled()
  })

  it('.hwp 파일 선택 시 에러가 초기화되고 업로드 버튼이 활성화된다', () => {
    // 사전에 에러 상태를 설정
    useAppStore.getState().setError('이전 에러')
    render(<UploadPanel />)
    const input = screen.getByTestId('file-input')

    const hwpFile = new File(['content'], 'requirements.hwp', { type: 'application/octet-stream' })
    fireEvent.change(input, { target: { files: [hwpFile] } })

    expect(useAppStore.getState().error).toBeNull()
    const uploadBtn = screen.getByTestId('upload-button')
    expect(uploadBtn).not.toBeDisabled()
  })
})

describe('UploadPanel — 드롭존 렌더링', () => {
  it('드롭존 영역이 렌더링된다', () => {
    render(<UploadPanel />)
    expect(screen.getByTestId('dropzone')).toBeInTheDocument()
  })

  it('드롭존에 role="button" 속성이 있어야 한다 (접근성)', () => {
    render(<UploadPanel />)
    expect(screen.getByRole('button', { name: /HWP 파일을 드래그하거나/ })).toBeInTheDocument()
  })
})
