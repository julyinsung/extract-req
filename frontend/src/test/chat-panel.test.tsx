/**
 * ChatPanel 단위 테스트.
 *
 * UT-004-05: detailReqs 비어있을 때 ChatInput disabled
 * UT-004-03: 메시지 전송 → chatHistory에 user 메시지 추가
 * UT-004-02: patch 이벤트 → patchDetailReq + req-highlight CustomEvent 발행
 * UT-011-02: sticky 상태에서 채팅 전송 버튼 클릭 → handleSend 호출 (기능 정상 동작)
 */
import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatPanel } from '../components/ChatPanel'
import { useAppStore } from '../store/useAppStore'
import { chatStream } from '../api'

/** api 모듈 mock — 테스트에서 HTTP 요청 방지 */
vi.mock('../api', () => ({
  uploadHwp: vi.fn(),
  generateDetailStream: vi.fn(),
  chatStream: vi.fn(),
  getDownloadUrl: vi.fn(),
}))

/** uuid mock — 결정적 ID 생성 */
vi.mock('uuid', () => ({ v4: vi.fn(() => 'test-uuid') }))

const mockedChatStream = chatStream as Mock

beforeEach(() => {
  useAppStore.getState().reset()
  vi.clearAllMocks()
  // chatStream 기본 mock: 아무 콜백도 호출하지 않고 cleanup 함수 반환
  mockedChatStream.mockReturnValue(() => {})
})

// ---------------------------------------------------------------------------
// UT-004-05: detailReqs 비어있을 때 입력창 disabled
// ---------------------------------------------------------------------------
describe('ChatPanel — 비활성화 (UT-004-05)', () => {
  it('detailReqs가 비어있으면 textarea가 disabled이다', () => {
    // sessionId 설정 없음 → detailReqs 없음 → 둘 다 disabled 조건
    useAppStore.getState().setSessionId('session-1')
    // detailReqs 비어있는 상태 유지

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    expect(textarea).toBeDisabled()
  })

  it('sessionId가 없으면 textarea가 disabled이다', () => {
    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    expect(textarea).toBeDisabled()
  })

  it('sessionId와 detailReqs 모두 있으면 textarea가 활성화된다', () => {
    useAppStore.getState().setSessionId('session-1')
    // REQ-004-04: selectedReqGroup도 함께 설정해야 활성화된다
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '명칭',
      content: '내용',
      order_index: 1,
      is_modified: false,
    })

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    expect(textarea).not.toBeDisabled()
  })

  it('detailReqs 없을 때 전송 버튼도 disabled이다', () => {
    useAppStore.getState().setSessionId('session-1')

    render(<ChatPanel />)

    const btn = screen.getByTestId('chat-send-btn')
    expect(btn).toBeDisabled()
  })
})

// ---------------------------------------------------------------------------
// UT-004-03: 메시지 전송 → chatHistory에 user 메시지 추가
// ---------------------------------------------------------------------------
describe('ChatPanel — 메시지 전송 (UT-004-03)', () => {
  beforeEach(() => {
    useAppStore.getState().setSessionId('session-1')
    // REQ-004-04: 채팅 전송을 위해 selectedReqGroup도 함께 설정한다
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '명칭',
      content: '내용',
      order_index: 1,
      is_modified: false,
    })
  })

  it('입력 후 전송 버튼 클릭 시 chatHistory에 user 메시지가 추가된다', () => {
    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '테스트 메시지' } })
    fireEvent.click(screen.getByTestId('chat-send-btn'))

    const history = useAppStore.getState().chatHistory
    expect(history).toHaveLength(1)
    expect(history[0].role).toBe('user')
    expect(history[0].content).toBe('테스트 메시지')
  })

  it('Enter 키 전송 후 입력창이 비워진다', () => {
    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '테스트 메시지' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })

    expect(textarea).toHaveValue('')
  })

  it('Shift+Enter는 메시지를 전송하지 않는다', () => {
    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '줄바꿈 테스트' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })

    expect(useAppStore.getState().chatHistory).toHaveLength(0)
  })

  it('전송 후 chatStream이 호출된다', () => {
    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '요청 메시지' } })
    fireEvent.click(screen.getByTestId('chat-send-btn'))

    expect(mockedChatStream).toHaveBeenCalledTimes(1)
    expect(mockedChatStream.mock.calls[0][0]).toMatchObject({
      session_id: 'session-1',
      message: '요청 메시지',
    })
  })

  it('빈 입력값은 전송되지 않는다', () => {
    render(<ChatPanel />)

    fireEvent.click(screen.getByTestId('chat-send-btn'))

    expect(mockedChatStream).not.toHaveBeenCalled()
    expect(useAppStore.getState().chatHistory).toHaveLength(0)
  })

  it('입력 2000자 초과분은 잘린다', () => {
    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    const longText = 'a'.repeat(2100)
    fireEvent.change(textarea, { target: { value: longText } })

    expect((textarea as HTMLTextAreaElement).value).toHaveLength(2000)
  })
})

// ---------------------------------------------------------------------------
// UT-004-02: patch 이벤트 → patchDetailReq + req-highlight CustomEvent 발행
// ---------------------------------------------------------------------------
describe('ChatPanel — patch 이벤트 처리 (UT-004-02)', () => {
  it('onPatch 콜백 호출 시 patchDetailReq 스토어가 갱신되고 req-highlight 이벤트가 발행된다', async () => {
    useAppStore.getState().setSessionId('session-1')
    // REQ-004-04: selectedReqGroup 설정 필요
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '원래 명칭',
      content: '원래 내용',
      order_index: 1,
      is_modified: false,
    })

    // chatStream mock에서 onPatch 콜백을 즉시 호출하도록 설정
    let capturedPatch: ((id: string, field: string, value: string) => void) | undefined
    mockedChatStream.mockImplementation((_payload, callbacks) => {
      capturedPatch = callbacks.onPatch
      return () => {}
    })

    // req-highlight CustomEvent 수신 감지
    const highlightEvents: string[] = []
    const handler = (e: Event) => {
      highlightEvents.push((e as CustomEvent).detail)
    }
    window.addEventListener('req-highlight', handler)

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '수정 요청' } })
    fireEvent.click(screen.getByTestId('chat-send-btn'))

    // onPatch 콜백 직접 호출
    capturedPatch?.('REQ-001-01', 'name', '수정된 명칭')

    await waitFor(() => {
      const patched = useAppStore.getState().detailReqs.find((r) => r.id === 'REQ-001-01')
      expect(patched?.name).toBe('수정된 명칭')
      expect(patched?.is_modified).toBe(true)
    })

    expect(highlightEvents).toContain('REQ-001-01')

    window.removeEventListener('req-highlight', handler)
  })

  it('onDone 콜백 호출 시 chatHistory에 assistant 메시지가 추가된다', async () => {
    useAppStore.getState().setSessionId('session-1')
    // REQ-004-04: selectedReqGroup 설정 필요
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '명칭',
      content: '내용',
      order_index: 1,
      is_modified: false,
    })

    let capturedCallbacks: {
      onText: (d: string) => void
      onDone: () => void
    } | undefined
    mockedChatStream.mockImplementation((_payload, callbacks) => {
      capturedCallbacks = callbacks
      return () => {}
    })

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '요청' } })
    fireEvent.click(screen.getByTestId('chat-send-btn'))

    capturedCallbacks?.onText('안녕하세요')
    capturedCallbacks?.onDone()

    await waitFor(() => {
      const history = useAppStore.getState().chatHistory
      const assistantMsg = history.find((m) => m.role === 'assistant')
      expect(assistantMsg?.content).toBe('안녕하세요')
    })
  })

  it('onError 콜백 호출 시 에러 상태가 설정되고 isChatting이 false로 돌아온다', async () => {
    useAppStore.getState().setSessionId('session-1')
    // REQ-004-04: selectedReqGroup 설정 필요
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '명칭',
      content: '내용',
      order_index: 1,
      is_modified: false,
    })

    let capturedOnError: ((msg: string) => void) | undefined
    mockedChatStream.mockImplementation((_payload, callbacks) => {
      capturedOnError = callbacks.onError
      return () => {}
    })

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: '요청' } })
    fireEvent.click(screen.getByTestId('chat-send-btn'))

    capturedOnError?.('서버 오류')

    await waitFor(() => {
      expect(useAppStore.getState().error).toBe('서버 오류')
      expect(useAppStore.getState().isChatting).toBe(false)
    })
  })
})

// ---------------------------------------------------------------------------
// UT-011-02: sticky 상태에서 채팅 전송 버튼 기능 정상 동작 확인 (REQ-011-02)
// ---------------------------------------------------------------------------
describe('ChatPanel — REQ-011 sticky 상태 기능 동작 (UT-011-02)', () => {
  it('채팅 전송 버튼 클릭 시 chatStream이 호출된다 (sticky 적용 후 기능 정상)', () => {
    useAppStore.getState().setSessionId('session-1')
    // REQ-004-04: selectedReqGroup 설정 필요
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '명칭',
      content: '내용',
      order_index: 1,
      is_modified: false,
    })

    render(<ChatPanel />)

    const textarea = screen.getByTestId('chat-input')
    fireEvent.change(textarea, { target: { value: 'sticky 상태 전송 테스트' } })
    fireEvent.click(screen.getByTestId('chat-send-btn'))

    // chatStream이 실제로 호출되어 handleSend가 정상 동작함을 확인
    expect(mockedChatStream).toHaveBeenCalledTimes(1)
    expect(mockedChatStream.mock.calls[0][0]).toMatchObject({
      session_id: 'session-1',
      message: 'sticky 상태 전송 테스트',
    })

    // user 메시지가 chatHistory에 추가됨을 확인
    const history = useAppStore.getState().chatHistory
    expect(history).toHaveLength(1)
    expect(history[0].role).toBe('user')
  })
})

// ---------------------------------------------------------------------------
// ChatPanel — UI 렌더링
// ---------------------------------------------------------------------------
describe('ChatPanel — UI 렌더링', () => {
  it('초기 상태에서 빈 안내 메시지가 표시된다', () => {
    useAppStore.getState().setSessionId('session-1')
    // detailReqs 없음

    render(<ChatPanel />)

    expect(screen.getByText('상세요구사항을 먼저 생성해주세요.')).toBeInTheDocument()
  })

  it('sessionId와 detailReqs 있을 때 빈 대화 안내 문구가 표시된다', () => {
    useAppStore.getState().setSessionId('session-1')
    // REQ-004-04: selectedReqGroup도 함께 설정해야 "요구사항 수정" 안내가 표시된다
    useAppStore.getState().setSelectedReqGroup('REQ-001')
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01',
      parent_id: 'REQ-001',
      category: '기능',
      name: '명칭',
      content: '내용',
      order_index: 1,
      is_modified: false,
    })

    render(<ChatPanel />)

    expect(screen.getByText(/요구사항 수정을 요청해보세요/)).toBeInTheDocument()
  })

  it('chatHistory에 메시지가 있으면 해당 메시지가 화면에 표시된다', () => {
    useAppStore.getState().appendChatMessage({
      id: 'msg-1',
      role: 'user',
      content: '화면에 표시되는 메시지',
      timestamp: new Date(),
    })

    render(<ChatPanel />)

    expect(screen.getByText('화면에 표시되는 메시지')).toBeInTheDocument()
  })
})
