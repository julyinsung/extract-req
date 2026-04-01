/**
 * OriginalReqTable 컴포넌트 단위 테스트.
 * UT-003-01: rows 5건 → 테이블 행 5개 렌더링
 * UT-003-06: sessionId 없을 때 다운로드 링크 미표시
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OriginalReqTable } from '../components/OriginalReqTable'
import { useAppStore } from '../store/useAppStore'
import type { OriginalRequirement } from '../types'

vi.mock('../api', () => ({
  uploadHwp: vi.fn(),
  getDownloadUrl: (sessionId: string, stage: number) =>
    `http://localhost:8000/api/v1/download?session_id=${sessionId}&stage=${stage}`,
}))

/** 테스트용 원본 요구사항 생성 헬퍼 */
function makeReq(n: number): OriginalRequirement {
  return {
    id: `REQ-00${n}`,
    category: '기능',
    name: `요구사항 명칭 ${n}`,
    content: `요구사항 내용 ${n}`,
    order_index: n,
  }
}

beforeEach(() => {
  useAppStore.getState().reset()
})

describe('OriginalReqTable — 행 렌더링 (UT-003-01)', () => {
  it('originalReqs 5건이면 tbody 행이 5개 렌더링된다', () => {
    const reqs = Array.from({ length: 5 }, (_, i) => makeReq(i + 1))
    useAppStore.getState().setOriginalReqs(reqs)

    render(<OriginalReqTable />)

    // 헤더 행을 제외한 데이터 행만 확인
    expect(screen.getByText('REQ-001')).toBeInTheDocument()
    expect(screen.getByText('REQ-002')).toBeInTheDocument()
    expect(screen.getByText('REQ-003')).toBeInTheDocument()
    expect(screen.getByText('REQ-004')).toBeInTheDocument()
    expect(screen.getByText('REQ-005')).toBeInTheDocument()
  })

  it('건수 텍스트에 5건이 표시된다', () => {
    const reqs = Array.from({ length: 5 }, (_, i) => makeReq(i + 1))
    useAppStore.getState().setOriginalReqs(reqs)

    render(<OriginalReqTable />)
    expect(screen.getByText('원본 요구사항 (5건)')).toBeInTheDocument()
  })

  it('테이블 행 각각의 내용이 올바르게 표시된다', () => {
    const reqs = [makeReq(1)]
    useAppStore.getState().setOriginalReqs(reqs)

    render(<OriginalReqTable />)
    expect(screen.getByText('REQ-001')).toBeInTheDocument()
    expect(screen.getByText('기능')).toBeInTheDocument()
    expect(screen.getByText('요구사항 명칭 1')).toBeInTheDocument()
    expect(screen.getByText('요구사항 내용 1')).toBeInTheDocument()
  })
})

describe('OriginalReqTable — 빈 상태', () => {
  it('originalReqs가 비어있으면 빈 상태 메시지를 표시한다', () => {
    render(<OriginalReqTable />)
    expect(screen.getByText('데이터가 없습니다')).toBeInTheDocument()
  })

  it('빈 상태에서 건수는 0건으로 표시된다', () => {
    render(<OriginalReqTable />)
    expect(screen.getByText('원본 요구사항 (0건)')).toBeInTheDocument()
  })
})

describe('OriginalReqTable — 다운로드 링크 (UT-003-06)', () => {
  it('sessionId가 null이면 1단계 다운로드 링크가 렌더링되지 않는다', () => {
    useAppStore.getState().setOriginalReqs([makeReq(1)])
    // sessionId는 reset() 후 null 상태

    render(<OriginalReqTable />)
    expect(screen.queryByTestId('download-stage1')).not.toBeInTheDocument()
  })

  it('sessionId가 있으면 1단계 다운로드 링크가 렌더링된다', () => {
    useAppStore.getState().setOriginalReqs([makeReq(1)])
    useAppStore.getState().setSessionId('session-abc')

    render(<OriginalReqTable />)
    const link = screen.getByTestId('download-stage1')
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute(
      'href',
      'http://localhost:8000/api/v1/download?session_id=session-abc&stage=1'
    )
  })
})

describe('OriginalReqTable — 상세요구사항 생성 버튼', () => {
  it('detailReqs가 비어있으면 생성 버튼이 표시된다', () => {
    useAppStore.getState().setOriginalReqs([makeReq(1)])

    render(<OriginalReqTable />)
    expect(screen.getByTestId('generate-detail-btn')).toBeInTheDocument()
  })

  it('detailReqs가 있으면 생성 버튼이 표시되지 않는다', () => {
    useAppStore.getState().setOriginalReqs([makeReq(1)])
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '상세 명칭',
      content: '상세 내용',
      order_index: 1,
      is_modified: false,
    })

    render(<OriginalReqTable />)
    expect(screen.queryByTestId('generate-detail-btn')).not.toBeInTheDocument()
  })
})

describe('OriginalReqTable — 접근성', () => {
  it('테이블에 aria-label이 있어야 한다', () => {
    render(<OriginalReqTable />)
    expect(screen.getByRole('table', { name: '원본 요구사항 테이블' })).toBeInTheDocument()
  })

  it('테이블 헤더 셀에 scope 속성이 있어야 한다', () => {
    render(<OriginalReqTable />)
    const headers = screen.getAllByRole('columnheader')
    headers.forEach((th) => {
      expect(th).toHaveAttribute('scope', 'col')
    })
  })
})
