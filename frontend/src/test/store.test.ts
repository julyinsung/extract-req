/**
 * UT-006-03: useAppStore — 저장/조회/reset 정상 동작 검증
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { useAppStore } from '../store/useAppStore'
import type { OriginalRequirement, DetailRequirement, ChatMessage } from '../types'

// 테스트 간 스토어 상태 격리를 위해 매 테스트 전 reset 호출
beforeEach(() => {
  useAppStore.getState().reset()
})

describe('useAppStore — 기본 상태', () => {
  it('초기 phase가 upload 이어야 한다', () => {
    expect(useAppStore.getState().phase).toBe('upload')
  })

  it('초기 sessionId가 null 이어야 한다', () => {
    expect(useAppStore.getState().sessionId).toBeNull()
  })

  it('초기 originalReqs가 빈 배열이어야 한다', () => {
    expect(useAppStore.getState().originalReqs).toEqual([])
  })

  it('초기 detailReqs가 빈 배열이어야 한다', () => {
    expect(useAppStore.getState().detailReqs).toEqual([])
  })

  it('초기 error가 null 이어야 한다', () => {
    expect(useAppStore.getState().error).toBeNull()
  })
})

describe('useAppStore — setPhase', () => {
  it('phase를 parsed로 변경할 수 있다', () => {
    useAppStore.getState().setPhase('parsed')
    expect(useAppStore.getState().phase).toBe('parsed')
  })

  it('phase를 generated로 변경할 수 있다', () => {
    useAppStore.getState().setPhase('generated')
    expect(useAppStore.getState().phase).toBe('generated')
  })
})

describe('useAppStore — setSessionId', () => {
  it('sessionId를 저장하고 조회할 수 있다', () => {
    useAppStore.getState().setSessionId('session-abc-123')
    expect(useAppStore.getState().sessionId).toBe('session-abc-123')
  })
})

describe('useAppStore — setOriginalReqs', () => {
  it('originalReqs를 설정할 수 있다', () => {
    const reqs: OriginalRequirement[] = [
      { id: 'REQ-001', category: '기능', name: '업로드', content: '파일 업로드', order_index: 0 },
      { id: 'REQ-002', category: '기능', name: '파싱', content: 'HWP 파싱', order_index: 1 },
    ]
    useAppStore.getState().setOriginalReqs(reqs)
    expect(useAppStore.getState().originalReqs).toHaveLength(2)
    expect(useAppStore.getState().originalReqs[0].id).toBe('REQ-001')
  })
})

describe('useAppStore — appendDetailReq', () => {
  it('상세 요구사항을 순서대로 추가할 수 있다', () => {
    const req1: DetailRequirement = {
      id: 'REQ-001-01', parent_id: 'REQ-001', category: '기능',
      name: '파일 선택', content: '파일 선택 UI', order_index: 0, is_modified: false,
    }
    const req2: DetailRequirement = {
      id: 'REQ-001-02', parent_id: 'REQ-001', category: '기능',
      name: '업로드 버튼', content: '업로드 실행', order_index: 1, is_modified: false,
    }
    useAppStore.getState().appendDetailReq(req1)
    useAppStore.getState().appendDetailReq(req2)
    expect(useAppStore.getState().detailReqs).toHaveLength(2)
    expect(useAppStore.getState().detailReqs[1].id).toBe('REQ-001-02')
  })
})

describe('useAppStore — patchDetailReq', () => {
  it('특정 필드를 수정하고 is_modified가 true로 마킹된다', () => {
    const req: DetailRequirement = {
      id: 'REQ-001-01', parent_id: 'REQ-001', category: '기능',
      name: '원래 명칭', content: '원래 내용', order_index: 0, is_modified: false,
    }
    useAppStore.getState().appendDetailReq(req)
    useAppStore.getState().patchDetailReq('REQ-001-01', 'content', '수정된 내용')

    const patched = useAppStore.getState().detailReqs.find(r => r.id === 'REQ-001-01')
    expect(patched?.content).toBe('수정된 내용')
    expect(patched?.is_modified).toBe(true)
  })

  it('존재하지 않는 id를 패치해도 다른 항목은 변경되지 않는다', () => {
    const req: DetailRequirement = {
      id: 'REQ-001-01', parent_id: 'REQ-001', category: '기능',
      name: '명칭', content: '내용', order_index: 0, is_modified: false,
    }
    useAppStore.getState().appendDetailReq(req)
    useAppStore.getState().patchDetailReq('NONEXISTENT', 'content', '무관한 수정')

    const unchanged = useAppStore.getState().detailReqs.find(r => r.id === 'REQ-001-01')
    expect(unchanged?.is_modified).toBe(false)
  })
})

describe('useAppStore — appendChatMessage', () => {
  it('채팅 메시지를 추가할 수 있다', () => {
    const msg: ChatMessage = {
      id: 'msg-1', role: 'user', content: '안녕하세요', timestamp: new Date(),
    }
    useAppStore.getState().appendChatMessage(msg)
    expect(useAppStore.getState().chatHistory).toHaveLength(1)
    expect(useAppStore.getState().chatHistory[0].role).toBe('user')
  })
})

describe('useAppStore — 로딩/에러 플래그', () => {
  it('setIsUploading으로 업로드 상태를 변경할 수 있다', () => {
    useAppStore.getState().setIsUploading(true)
    expect(useAppStore.getState().isUploading).toBe(true)
    useAppStore.getState().setIsUploading(false)
    expect(useAppStore.getState().isUploading).toBe(false)
  })

  it('setIsGenerating으로 생성 상태를 변경할 수 있다', () => {
    useAppStore.getState().setIsGenerating(true)
    expect(useAppStore.getState().isGenerating).toBe(true)
  })

  it('setIsChatting으로 채팅 상태를 변경할 수 있다', () => {
    useAppStore.getState().setIsChatting(true)
    expect(useAppStore.getState().isChatting).toBe(true)
  })

  it('setError로 에러 메시지를 설정하고 null로 초기화할 수 있다', () => {
    useAppStore.getState().setError('파싱 오류가 발생했습니다')
    expect(useAppStore.getState().error).toBe('파싱 오류가 발생했습니다')
    useAppStore.getState().setError(null)
    expect(useAppStore.getState().error).toBeNull()
  })
})

describe('useAppStore — reset (UT-006-03)', () => {
  it('reset 호출 시 모든 상태가 초기값으로 복원된다', () => {
    // 상태를 변경한 뒤
    useAppStore.getState().setPhase('generated')
    useAppStore.getState().setSessionId('session-xyz')
    useAppStore.getState().setError('테스트 오류')
    useAppStore.getState().setIsGenerating(true)
    useAppStore.getState().appendDetailReq({
      id: 'REQ-001-01', parent_id: 'REQ-001', category: '기능',
      name: '명칭', content: '내용', order_index: 0, is_modified: false,
    })

    // reset 호출
    useAppStore.getState().reset()

    const state = useAppStore.getState()
    expect(state.phase).toBe('upload')
    expect(state.sessionId).toBeNull()
    expect(state.originalReqs).toEqual([])
    expect(state.detailReqs).toEqual([])
    expect(state.chatHistory).toEqual([])
    expect(state.isUploading).toBe(false)
    expect(state.isGenerating).toBe(false)
    expect(state.isChatting).toBe(false)
    expect(state.error).toBeNull()
  })
})
