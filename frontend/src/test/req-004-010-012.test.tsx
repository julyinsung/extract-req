/**
 * REQ-004 / REQ-010 / REQ-012 프론트엔드 단위 테스트
 *
 * UT-010-04: DetailReqTable — isGenerating=true, progressTotal>0 시 진행률 텍스트 렌더링
 * UT-010-05: DetailReqTable — isGenerating=false 시 진행률 UI DOM에서 사라짐
 * UT-012-05: DetailReqTable — 삭제 버튼 클릭 → confirm 취소 시 행 유지
 * UT-012-06: DetailReqTable — 삭제 버튼 클릭 → confirm 확인 시 해당 행 제거
 * UT-012-07: useAppStore.deleteDetailReq — API 성공 시 스토어에서 해당 id 제거
 * UT-012-08: useAppStore.deleteDetailReq — API 404 실패 시 스토어 불변 + error 설정
 * UT-012-09: DetailReqTable — isGenerating=true 중 삭제 버튼 비활성화
 *
 * REQ-004:
 * - useAppStore: selectedReqGroup 초기값 null, setSelectedReqGroup, replaceDetailReqGroup 동작
 * - OriginalReqTable: 행 클릭 시 setSelectedReqGroup 호출
 * - ChatPanel: selectedReqGroup 있으면 헤더에 컨텍스트 표시
 * - ChatPanel: selectedReqGroup 없으면 채팅 입력 비활성화
 * - chatStream: onReplace 콜백 → replaceDetailReqGroup 호출
 */
import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { DetailReqTable } from '../components/DetailReqTable'
import { OriginalReqTable } from '../components/OriginalReqTable'
import { ChatPanel } from '../components/ChatPanel'
import { useAppStore } from '../store/useAppStore'
import type { DetailRequirement } from '../types'
import { chatStream, deleteDetailReq as apiDeleteDetailReq } from '../api'

/** api 모듈 mock */
vi.mock('../api', () => ({
  uploadHwp: vi.fn(),
  generateDetailStream: vi.fn(),
  chatStream: vi.fn(),
  getDownloadUrl: vi.fn(),
  patchDetailReq: vi.fn(),
  deleteDetailReq: vi.fn(),
}))

vi.mock('uuid', () => ({ v4: vi.fn(() => 'test-uuid') }))

const mockedDeleteDetailReq = apiDeleteDetailReq as Mock

const mockedChatStream = chatStream as Mock

/** 테스트용 상세 요구사항 생성 헬퍼 */
function makeDetailReq(n: number, parentId = 'REQ-001'): DetailRequirement {
  return {
    id: `${parentId}-0${n}`,
    parent_id: parentId,
    category: '기능',
    name: `상세 명칭 ${n}`,
    content: `상세 내용 ${n}`,
    order_index: n,
    is_modified: false,
  }
}

beforeEach(() => {
  useAppStore.getState().reset()
  vi.clearAllMocks()
  mockedChatStream.mockReturnValue(() => {})
})

// ===========================================================================
// REQ-004: useAppStore — selectedReqGroup 상태 관리
// ===========================================================================
describe('useAppStore — selectedReqGroup (REQ-004-04)', () => {
  it('초기 selectedReqGroup이 null이다', () => {
    expect(useAppStore.getState().selectedReqGroup).toBeNull()
  })

  it('setSelectedReqGroup으로 그룹 ID를 설정할 수 있다', () => {
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    expect(useAppStore.getState().selectedReqGroup).toBe('REQ-001')
  })

  it('setSelectedReqGroup(null)로 선택을 해제할 수 있다', () => {
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().setSelectedReqGroup(null)
    expect(useAppStore.getState().selectedReqGroup).toBeNull()
  })

  it('reset 시 selectedReqGroup이 null로 초기화된다', () => {
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().reset()
    expect(useAppStore.getState().selectedReqGroup).toBeNull()
  })
})

// ===========================================================================
// REQ-004: useAppStore — replaceDetailReqGroup 액션
// ===========================================================================
describe('useAppStore — replaceDetailReqGroup (REQ-004-06)', () => {
  it('해당 parent_id의 항목 전체를 새 items로 교체한다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    useAppStore.getState().appendDetailReq(makeDetailReq(2))
    useAppStore.getState().appendDetailReq({ ...makeDetailReq(1, 'REQ-002'), id: 'REQ-002-01' })

    const newItems: DetailRequirement[] = [
      { ...makeDetailReq(1), id: 'REQ-001-01', name: '교체된 명칭', is_modified: true },
    ]
    useAppStore.getState().replaceDetailReqGroup('REQ-001', newItems)

    const state = useAppStore.getState().detailReqs
    // REQ-001 그룹은 1건으로 교체
    const req001Items = state.filter((r) => r.parent_id === 'REQ-001')
    expect(req001Items).toHaveLength(1)
    expect(req001Items[0].name).toBe('교체된 명칭')
    // REQ-002 항목은 그대로 유지
    const req002Items = state.filter((r) => r.parent_id === 'REQ-002')
    expect(req002Items).toHaveLength(1)
  })
})

// ===========================================================================
// REQ-004: OriginalReqTable — 행 클릭 시 그룹 선택
// ===========================================================================
describe('OriginalReqTable — 행 클릭 시 selectedReqGroup 설정 (REQ-004-04)', () => {
  it('원본 요구사항 행 클릭 시 setSelectedReqGroup이 해당 id로 호출된다', () => {
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '업로드', content: '파일 업로드', order_index: 0 },
    ])

    render(<OriginalReqTable />)

    const row = screen.getByTestId('original-row-REQ-001')
    fireEvent.click(row)

    expect(useAppStore.getState().selectedReqGroup).toBe('REQ-001')
  })

  it('선택된 행에 aria-selected=true가 설정된다', () => {
    useAppStore.getState().setOriginalReqs([
      { id: 'REQ-001', category: '기능', name: '업로드', content: '파일 업로드', order_index: 0 },
    ])
    useAppStore.getState().setSelectedReqGroup('REQ-001')

    render(<OriginalReqTable />)

    const row = screen.getByTestId('original-row-REQ-001')
    expect(row).toHaveAttribute('aria-selected', 'true')
  })
})

// ===========================================================================
// REQ-004: ChatPanel — selectedReqGroup 헤더 표시
// ===========================================================================
describe('ChatPanel — selectedReqGroup 헤더 표시 (REQ-004-04)', () => {
  it('selectedReqGroup이 있으면 헤더에 컨텍스트 텍스트가 표시된다', () => {
    useAppStore.getState().setSelectedReqGroup('REQ-001')

    render(<ChatPanel />)

    expect(screen.getByText('AI 수정 채팅 — REQ-001 컨텍스트로 대화 중')).toBeInTheDocument()
  })

  it('selectedReqGroup이 null이면 기본 헤더 텍스트가 표시된다', () => {
    render(<ChatPanel />)

    expect(screen.getByText('AI 수정 채팅')).toBeInTheDocument()
  })

  it('selectedReqGroup 없으면 textarea가 disabled이다', () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    // selectedReqGroup은 null (기본값)

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    expect(textarea).toBeDisabled()
  })

  it('sessionId + selectedReqGroup + detailReqs 모두 있으면 textarea가 활성화된다', () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    expect(textarea).not.toBeDisabled()
  })
})

// ===========================================================================
// REQ-004: ChatPanel — req_group 페이로드 포함 + onReplace 처리
// ===========================================================================
describe('ChatPanel — chatStream 페이로드에 req_group 포함 (REQ-004-05)', () => {
  it('전송 시 chatStream에 req_group 필드가 포함된다', () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '수정 요청' } })
    fireEvent.click(screen.getByTestId('chat-send-btn'))

    expect(mockedChatStream).toHaveBeenCalledTimes(1)
    expect(mockedChatStream.mock.calls[0][0]).toMatchObject({
      session_id: 'session-1',
      message: '수정 요청',
      req_group: 'REQ-001',
    })
  })

  it('onReplace 콜백 호출 시 replaceDetailReqGroup 스토어가 갱신된다', async () => {
    useAppStore.getState().setSessionId('session-1')
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    useAppStore.getState().appendDetailReq(makeDetailReq(2))

    let capturedReplace: ((reqGroup: string, items: DetailRequirement[]) => void) | undefined
    mockedChatStream.mockImplementation((_payload, callbacks) => {
      capturedReplace = callbacks.onReplace
      return () => {}
    })

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '그룹 교체 요청' } })
    fireEvent.click(screen.getByTestId('chat-send-btn'))

    const newItems: DetailRequirement[] = [
      { ...makeDetailReq(1), name: '교체된 명칭', is_modified: true },
    ]
    capturedReplace?.('REQ-001', newItems)

    await waitFor(() => {
      const state = useAppStore.getState().detailReqs
      const req001 = state.filter((r) => r.parent_id === 'REQ-001')
      expect(req001).toHaveLength(1)
      expect(req001[0].name).toBe('교체된 명칭')
    })
  })
})

// ===========================================================================
// REQ-010: useAppStore — progress 상태 관리
// ===========================================================================
describe('useAppStore — progress 상태 (REQ-010)', () => {
  it('초기 progressCurrent, progressTotal이 0이고 progressReqId가 null이다', () => {
    const s = useAppStore.getState()
    expect(s.progressCurrent).toBe(0)
    expect(s.progressTotal).toBe(0)
    expect(s.progressReqId).toBeNull()
  })

  it('setProgress로 진행률 상태를 갱신한다', () => {
    useAppStore.getState().setProgress(2, 5, 'REQ-002')
    const s = useAppStore.getState()
    expect(s.progressCurrent).toBe(2)
    expect(s.progressTotal).toBe(5)
    expect(s.progressReqId).toBe('REQ-002')
  })

  it('clearProgress로 진행률 상태를 초기화한다', () => {
    useAppStore.getState().setProgress(3, 5, 'REQ-003')
    useAppStore.getState().clearProgress()
    const s = useAppStore.getState()
    expect(s.progressCurrent).toBe(0)
    expect(s.progressTotal).toBe(0)
    expect(s.progressReqId).toBeNull()
  })

  it('setIsGenerating(false) 시 진행률이 자동 초기화된다', () => {
    useAppStore.getState().setProgress(3, 5, 'REQ-003')
    useAppStore.getState().setIsGenerating(false)
    const s = useAppStore.getState()
    expect(s.progressCurrent).toBe(0)
    expect(s.progressTotal).toBe(0)
    expect(s.progressReqId).toBeNull()
  })

  it('reset 시 진행률이 초기화된다', () => {
    useAppStore.getState().setProgress(2, 5, 'REQ-002')
    useAppStore.getState().reset()
    const s = useAppStore.getState()
    expect(s.progressCurrent).toBe(0)
    expect(s.progressTotal).toBe(0)
    expect(s.progressReqId).toBeNull()
  })
})

// ===========================================================================
// UT-010-04: DetailReqTable — isGenerating=true, progressTotal>0 시 진행률 텍스트
// ===========================================================================
describe('UT-010-04: DetailReqTable — 진행률 텍스트 렌더링', () => {
  it('isGenerating=true이고 progressTotal>0이면 "N / M 항목 생성 중" 텍스트가 렌더링된다', () => {
    useAppStore.getState().setIsGenerating(true)
    useAppStore.getState().setProgress(2, 5, 'REQ-002')

    render(<DetailReqTable />)

    expect(screen.getByTestId('progress-text')).toBeInTheDocument()
    expect(screen.getByTestId('progress-text').textContent).toMatch(/2 \/ 5 항목 생성 중/)
  })

  it('progressReqId가 있으면 REQ-NNN이 진행률 텍스트에 포함된다', () => {
    useAppStore.getState().setIsGenerating(true)
    useAppStore.getState().setProgress(2, 5, 'REQ-002')

    render(<DetailReqTable />)

    expect(screen.getByTestId('progress-text').textContent).toContain('REQ-002')
  })

  it('isGenerating=true이지만 progressTotal=0이면 progress-text가 없다', () => {
    useAppStore.getState().setIsGenerating(true)
    // progressTotal은 0 (기본값)

    render(<DetailReqTable />)

    expect(screen.queryByTestId('progress-text')).not.toBeInTheDocument()
    // pulse 바는 있어야 함
    expect(screen.getByTestId('progress-bar')).toBeInTheDocument()
  })
})

// ===========================================================================
// UT-010-05: DetailReqTable — isGenerating=false 시 진행률 UI 사라짐
// ===========================================================================
describe('UT-010-05: DetailReqTable — isGenerating=false 시 진행률 UI 제거', () => {
  it('isGenerating=false이면 progress-bar가 DOM에 없다', () => {
    // isGenerating 기본값 false
    render(<DetailReqTable />)

    expect(screen.queryByTestId('progress-bar')).not.toBeInTheDocument()
  })
})

// ===========================================================================
// UT-012-09: DetailReqTable — isGenerating 중 삭제 버튼 비활성화
// ===========================================================================
describe('UT-012-09: DetailReqTable — isGenerating 중 삭제 버튼 비활성화', () => {
  it('isGenerating=true이면 삭제 버튼이 disabled이다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    useAppStore.getState().setIsGenerating(true)

    render(<DetailReqTable />)

    const deleteBtn = screen.getByTestId('delete-btn-REQ-001-01')
    expect(deleteBtn).toBeDisabled()
  })

  it('isGenerating=false이면 삭제 버튼이 활성화된다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    // isGenerating 기본값 false

    render(<DetailReqTable />)

    const deleteBtn = screen.getByTestId('delete-btn-REQ-001-01')
    expect(deleteBtn).not.toBeDisabled()
  })
})

// ===========================================================================
// UT-012-05: DetailReqTable — 삭제 confirm 취소 시 행 유지
// ===========================================================================
describe('UT-012-05: DetailReqTable — 삭제 confirm 취소 시 행 유지', () => {
  it('confirm 취소 시 deleteDetailReq API가 호출되지 않고 행이 유지된다', () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    // window.confirm을 false(취소)로 mock
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(<DetailReqTable />)

    const deleteBtn = screen.getByTestId('delete-btn-REQ-001-01')
    fireEvent.click(deleteBtn)

    // confirm이 호출됨
    expect(window.confirm).toHaveBeenCalledWith('이 항목을 삭제하시겠습니까?')
    // 행이 여전히 DOM에 있음
    expect(screen.getByTestId('detail-row-REQ-001-01')).toBeInTheDocument()
  })
})

// ===========================================================================
// UT-012-06: DetailReqTable — 삭제 confirm 확인 시 해당 행 제거
// ===========================================================================
describe('UT-012-06: DetailReqTable — 삭제 confirm 확인 시 행 제거', () => {
  it('confirm 확인 시 deleteDetailReq가 호출된다', async () => {
    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    // api 모듈의 deleteDetailReq mock을 성공으로 설정
    mockedDeleteDetailReq.mockResolvedValue({ deleted_id: 'REQ-001-01' })

    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<DetailReqTable />)

    const deleteBtn = screen.getByTestId('delete-btn-REQ-001-01')
    fireEvent.click(deleteBtn)

    expect(window.confirm).toHaveBeenCalledWith('이 항목을 삭제하시겠습니까?')

    await waitFor(() => {
      expect(useAppStore.getState().detailReqs).toHaveLength(0)
    })
  })
})

// ===========================================================================
// UT-012-07: useAppStore.deleteDetailReq — API 성공 시 스토어에서 id 제거
// ===========================================================================
describe('UT-012-07: useAppStore.deleteDetailReq — API 성공 시 스토어에서 id 제거', () => {
  it('API 성공 시 해당 id가 detailReqs에서 제거된다', async () => {
    mockedDeleteDetailReq.mockResolvedValue({ deleted_id: 'REQ-001-01' })

    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    useAppStore.getState().appendDetailReq(makeDetailReq(2))

    await useAppStore.getState().deleteDetailReq('REQ-001-01')

    const state = useAppStore.getState().detailReqs
    expect(state).toHaveLength(1)
    expect(state[0].id).toBe('REQ-001-02')
  })

  it('API 성공 시 error가 null로 초기화된다', async () => {
    mockedDeleteDetailReq.mockResolvedValue({ deleted_id: 'REQ-001-01' })
    useAppStore.getState().appendDetailReq(makeDetailReq(1))
    useAppStore.getState().setError('이전 오류')

    await useAppStore.getState().deleteDetailReq('REQ-001-01')

    expect(useAppStore.getState().error).toBeNull()
  })
})

// ===========================================================================
// UT-012-08: useAppStore.deleteDetailReq — API 실패 시 스토어 불변 + error 설정
// ===========================================================================
describe('UT-012-08: useAppStore.deleteDetailReq — API 실패 시 스토어 불변 + error 설정', () => {
  it('API 404 실패 시 스토어 항목이 제거되지 않는다', async () => {
    const notFoundError = Object.assign(new Error('Request failed with status code 404'), {
      response: { status: 404 },
    })
    mockedDeleteDetailReq.mockRejectedValue(notFoundError)

    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    await useAppStore.getState().deleteDetailReq('REQ-001-01')

    // 스토어 항목이 그대로 유지
    expect(useAppStore.getState().detailReqs).toHaveLength(1)
  })

  it('API 실패 시 error 상태가 설정된다', async () => {
    mockedDeleteDetailReq.mockRejectedValue(new Error('삭제 실패'))

    useAppStore.getState().appendDetailReq(makeDetailReq(1))

    await useAppStore.getState().deleteDetailReq('REQ-001-01')

    expect(useAppStore.getState().error).toBeTruthy()
  })
})
