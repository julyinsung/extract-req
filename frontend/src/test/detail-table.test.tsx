/**
 * DetailReqTable 및 InlineEditCell 단위 테스트.
 * UT-003-02: appendDetailReq 3회 → 행 3개 렌더링
 * UT-003-03: 셀 클릭 → 편집 모드, blur → onSave 호출, Escape → onCancel 호출
 * UT-003-04: 상세 행 배경색 #F0F9FF 확인
 * 추가: isGenerating=true 시 셀 클릭해도 편집 모드 전환 안 됨
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DetailReqTable } from '../components/DetailReqTable'
import { InlineEditCell } from '../components/InlineEditCell'
import { useAppStore } from '../store/useAppStore'
import type { DetailRequirement } from '../types'

/** api 모듈 mock — 테스트에서 HTTP 요청 방지 */
vi.mock('../api', () => ({
  uploadHwp: vi.fn(),
  generateDetailStream: vi.fn(),
  chatStream: vi.fn(),
  getDownloadUrl: vi.fn(),
}))

/** 테스트용 상세 요구사항 생성 헬퍼 */
function makeDetailReq(n: number): DetailRequirement {
  return {
    id: `REQ-001-0${n}`,
    parent_id: 'REQ-001',
    category: '기능',
    name: `상세 명칭 ${n}`,
    content: `상세 내용 ${n}`,
    order_index: n,
    is_modified: false,
  }
}

beforeEach(() => {
  useAppStore.getState().reset()
})

// ---------------------------------------------------------------------------
// UT-003-02: appendDetailReq 3회 → 행 3개 렌더링
// ---------------------------------------------------------------------------
describe('DetailReqTable — 행 렌더링 (UT-003-02)', () => {
  it('appendDetailReq 3회 호출 후 tbody에 행이 3개 렌더링된다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    useAppStore.getState().appendDetailReq(makeDetailReq(2))
    useAppStore.getState().appendDetailReq(makeDetailReq(3))

    render(<DetailReqTable />)

    // 각 행의 상세 ID가 DOM에 존재하는지 확인
    expect(screen.getByText('REQ-001-01')).toBeInTheDocument()
    expect(screen.getByText('REQ-001-02')).toBeInTheDocument()
    expect(screen.getByText('REQ-001-03')).toBeInTheDocument()
  })

  it('건수 텍스트에 3건이 표시된다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    useAppStore.getState().appendDetailReq(makeDetailReq(2))
    useAppStore.getState().appendDetailReq(makeDetailReq(3))

    render(<DetailReqTable />)
    expect(screen.getByText('상세요구사항 (3건)')).toBeInTheDocument()
  })

  it('detailReqs가 비어있으면 빈 상태 메시지를 표시한다', () => {
    render(<DetailReqTable />)
    expect(screen.getByText('상세요구사항이 없습니다')).toBeInTheDocument()
  })

  it('isGenerating=true이면 "생성 중..." 인디케이터가 표시된다', () => {
    useAppStore.getState().setIsGenerating(true)
    render(<DetailReqTable />)
    expect(screen.getByTestId('generating-indicator')).toBeInTheDocument()
  })

  it('isGenerating=true이면 진행 바가 렌더링된다', () => {
    useAppStore.getState().setIsGenerating(true)
    render(<DetailReqTable />)
    expect(screen.getByTestId('progress-bar')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// UT-003-04: 상세 행 배경색 #F0F9FF 확인
// ---------------------------------------------------------------------------
describe('DetailReqTable — 시각 구분 (UT-003-04)', () => {
  it('상세 행의 기본 배경색이 #F0F9FF이어야 한다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    render(<DetailReqTable />)

    const row = screen.getByTestId('detail-row-REQ-001-01')
    expect(row).toHaveStyle({ background: '#F0F9FF' })
  })

  it('테이블에 aria-label이 있어야 한다', () => {
    render(<DetailReqTable />)
    expect(screen.getByRole('table', { name: '상세요구사항 테이블' })).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// 추가: isGenerating=true 시 편집 모드 진입 비활성화
// ---------------------------------------------------------------------------
describe('DetailReqTable — 생성 중 편집 비활성화', () => {
  it('isGenerating=true이면 셀 클릭해도 input이 나타나지 않는다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    useAppStore.getState().setIsGenerating(true)

    render(<DetailReqTable />)

    const cell = screen.getByTestId('cell-REQ-001-01-name')
    fireEvent.click(cell)

    // 편집 input이 렌더링되지 않아야 한다
    expect(screen.queryByTestId('inline-edit-input')).not.toBeInTheDocument()
  })

  it('isGenerating=false이면 셀 클릭 시 input이 나타난다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    // isGenerating 기본값 false

    render(<DetailReqTable />)

    const cell = screen.getByTestId('cell-REQ-001-01-name')
    fireEvent.click(cell)

    expect(screen.getByTestId('inline-edit-input')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// UT-003-03: InlineEditCell — 편집 모드, blur → onSave, Escape → onCancel
// ---------------------------------------------------------------------------
describe('InlineEditCell — 편집 동작 (UT-003-03)', () => {
  it('name 필드이면 <input type="text">를 렌더링한다', () => {
    const onSave = vi.fn()
    const onCancel = vi.fn()

    render(
      <InlineEditCell
        value="초기 명칭"
        field="name"
        detailId="REQ-001-01"
        onSave={onSave}
        onCancel={onCancel}
      />
    )

    expect(screen.getByTestId('inline-edit-input')).toBeInTheDocument()
    expect(screen.queryByTestId('inline-edit-textarea')).not.toBeInTheDocument()
  })

  it('content 필드이면 <textarea>를 렌더링한다', () => {
    const onSave = vi.fn()
    const onCancel = vi.fn()

    render(
      <InlineEditCell
        value="초기 내용"
        field="content"
        detailId="REQ-001-01"
        onSave={onSave}
        onCancel={onCancel}
      />
    )

    expect(screen.getByTestId('inline-edit-textarea')).toBeInTheDocument()
    expect(screen.queryByTestId('inline-edit-input')).not.toBeInTheDocument()
  })

  it('blur 이벤트 발생 시 onSave가 현재 값으로 호출된다', async () => {
    const onSave = vi.fn()
    const onCancel = vi.fn()

    render(
      <InlineEditCell
        value="초기 명칭"
        field="name"
        detailId="REQ-001-01"
        onSave={onSave}
        onCancel={onCancel}
      />
    )

    const input = screen.getByTestId('inline-edit-input')
    await userEvent.clear(input)
    await userEvent.type(input, '수정된 명칭')
    fireEvent.blur(input)

    expect(onSave).toHaveBeenCalledWith('name', '수정된 명칭')
  })

  it('Escape 키 입력 시 onCancel이 호출된다', async () => {
    const onSave = vi.fn()
    const onCancel = vi.fn()

    render(
      <InlineEditCell
        value="초기 명칭"
        field="name"
        detailId="REQ-001-01"
        onSave={onSave}
        onCancel={onCancel}
      />
    )

    const input = screen.getByTestId('inline-edit-input')
    fireEvent.keyDown(input, { key: 'Escape' })

    expect(onCancel).toHaveBeenCalledTimes(1)
    expect(onSave).not.toHaveBeenCalled()
  })

  it('name 필드에서 Enter 키 입력 시 onSave가 호출된다', () => {
    const onSave = vi.fn()
    const onCancel = vi.fn()

    render(
      <InlineEditCell
        value="초기 명칭"
        field="name"
        detailId="REQ-001-01"
        onSave={onSave}
        onCancel={onCancel}
      />
    )

    const input = screen.getByTestId('inline-edit-input')
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(onSave).toHaveBeenCalledTimes(1)
  })

  it('content 필드에서 Enter 키 입력 시 onSave가 호출되지 않는다 (줄바꿈 허용)', async () => {
    const onSave = vi.fn()
    const onCancel = vi.fn()

    render(
      <InlineEditCell
        value="초기 내용"
        field="content"
        detailId="REQ-001-01"
        onSave={onSave}
        onCancel={onCancel}
      />
    )

    const textarea = screen.getByTestId('inline-edit-textarea')
    fireEvent.keyDown(textarea, { key: 'Enter' })

    expect(onSave).not.toHaveBeenCalled()
  })
})

// ---------------------------------------------------------------------------
// DetailReqTable 셀 클릭 → InlineEditCell 전환 통합 확인
// ---------------------------------------------------------------------------
describe('DetailReqTable — 셀 클릭 편집 전환', () => {
  it('name 셀 클릭 시 InlineEditCell(input)이 렌더링된다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    render(<DetailReqTable />)

    const cell = screen.getByTestId('cell-REQ-001-01-name')
    fireEvent.click(cell)

    expect(screen.getByTestId('inline-edit-input')).toBeInTheDocument()
  })

  it('content 셀 클릭 시 InlineEditCell(textarea)이 렌더링된다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    render(<DetailReqTable />)

    const cell = screen.getByTestId('cell-REQ-001-01-content')
    fireEvent.click(cell)

    expect(screen.getByTestId('inline-edit-textarea')).toBeInTheDocument()
  })

  it('blur 후 patchDetailReq가 호출되어 스토어 값이 갱신된다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    render(<DetailReqTable />)

    const cell = screen.getByTestId('cell-REQ-001-01-name')
    fireEvent.click(cell)

    const input = screen.getByTestId('inline-edit-input')
    fireEvent.change(input, { target: { value: '수정된 명칭' } })
    fireEvent.blur(input)

    const patched = useAppStore
      .getState()
      .detailReqs.find((r) => r.id === 'REQ-001-01')
    expect(patched?.name).toBe('수정된 명칭')
    expect(patched?.is_modified).toBe(true)
  })
})
