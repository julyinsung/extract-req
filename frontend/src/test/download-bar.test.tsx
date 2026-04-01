/**
 * DownloadBar 단위 테스트.
 *
 * UT-005 관련: sessionId 없을 때 렌더링 안 됨,
 *             detailReqs.length === 0 시 2단계 버튼 없음 (활성화 조건).
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DownloadBar } from '../components/DownloadBar'
import { useAppStore } from '../store/useAppStore'

/** api 모듈 mock — 실제 URL 생성 로직은 단순하므로 원본 구현 활용 */
vi.mock('../api', () => ({
  uploadHwp: vi.fn(),
  generateDetailStream: vi.fn(),
  chatStream: vi.fn(),
  getDownloadUrl: (sessionId: string, stage: number) =>
    `http://localhost:8000/api/v1/download?session_id=${sessionId}&stage=${stage}`,
}))

beforeEach(() => {
  useAppStore.getState().reset()
})

// ---------------------------------------------------------------------------
// DownloadBar — sessionId 없으면 렌더링 안 됨
// ---------------------------------------------------------------------------
describe('DownloadBar — 렌더링 조건', () => {
  it('sessionId가 없으면 렌더링되지 않는다', () => {
    render(<DownloadBar />)
    expect(screen.queryByTestId('download-bar')).not.toBeInTheDocument()
  })

  it('sessionId 있어도 originalReqs가 비어있으면 렌더링되지 않는다', () => {
    useAppStore.getState().setSessionId('session-1')

    render(<DownloadBar />)
    expect(screen.queryByTestId('download-bar')).not.toBeInTheDocument()
  })

  it('sessionId와 originalReqs 모두 있으면 렌더링된다', () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '기능 명칭', content: '기능 내용', order_index: 1 },
    ])

    render(<DownloadBar />)
    expect(screen.getByTestId('download-bar')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// DownloadBar — 1단계/2단계 버튼 활성화 조건 (UT-005)
// ---------------------------------------------------------------------------
describe('DownloadBar — 버튼 활성화 조건 (UT-005)', () => {
  it('originalReqs 있을 때 1단계 버튼이 표시된다', () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '기능 명칭', content: '기능 내용', order_index: 1 },
    ])

    render(<DownloadBar />)
    expect(screen.getByTestId('download-stage1')).toBeInTheDocument()
  })

  it('detailReqs가 없으면 2단계 버튼이 표시되지 않는다', () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '기능 명칭', content: '기능 내용', order_index: 1 },
    ])
    // detailReqs 비어있음 — 2단계 버튼 미표시 조건

    render(<DownloadBar />)
    expect(screen.queryByTestId('download-stage2')).not.toBeInTheDocument()
  })

  it('detailReqs가 있으면 2단계 버튼이 표시된다', () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '기능 명칭', content: '기능 내용', order_index: 1 },
    ])
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '상세 명칭',
      content: '상세 내용',
      order_index: 1,
      is_modified: false,
    })

    render(<DownloadBar />)
    expect(screen.getByTestId('download-stage2')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// DownloadBar — 다운로드 URL 정확성
// ---------------------------------------------------------------------------
describe('DownloadBar — 다운로드 URL', () => {
  it('1단계 링크의 href에 stage=1이 포함된다', () => {
    useAppStore.getState().setSessionId('session-abc')
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '명칭', content: '내용', order_index: 1 },
    ])

    render(<DownloadBar />)

    const link = screen.getByTestId('download-stage1') as HTMLAnchorElement
    expect(link.href).toContain('stage=1')
    expect(link.href).toContain('session_id=session-abc')
  })

  it('2단계 링크의 href에 stage=2가 포함된다', () => {
    useAppStore.getState().setSessionId('session-abc')
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '명칭', content: '내용', order_index: 1 },
    ])
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '상세 명칭',
      content: '상세 내용',
      order_index: 1,
      is_modified: false,
    })

    render(<DownloadBar />)

    const link = screen.getByTestId('download-stage2') as HTMLAnchorElement
    expect(link.href).toContain('stage=2')
    expect(link.href).toContain('session_id=session-abc')
  })

  it('1단계 링크에 download 속성이 있다', () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '명칭', content: '내용', order_index: 1 },
    ])

    render(<DownloadBar />)

    const link = screen.getByTestId('download-stage1')
    expect(link).toHaveAttribute('download')
  })
})
