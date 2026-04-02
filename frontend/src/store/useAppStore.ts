import { create } from 'zustand'
import type { OriginalRequirement, DetailRequirement, ChatMessage, AppPhase } from '../types'
import { patchDetailReq as apiPatchDetailReq } from '../api'

interface AppState {
  phase: AppPhase
  sessionId: string | null
  originalReqs: OriginalRequirement[]
  detailReqs: DetailRequirement[]
  chatHistory: ChatMessage[]
  isUploading: boolean
  isGenerating: boolean
  isChatting: boolean
  error: string | null
}

interface AppActions {
  setPhase: (phase: AppPhase) => void
  setSessionId: (id: string) => void
  setOriginalReqs: (reqs: OriginalRequirement[]) => void
  appendDetailReq: (req: DetailRequirement) => void
  /**
   * 특정 상세 요구사항 필드를 수정하고 is_modified를 true로 마킹한다.
   * 채팅 패치 및 인라인 편집 모두 이 액션을 통해 상태를 갱신한다.
   */
  patchDetailReq: (id: string, field: keyof DetailRequirement, value: string) => void
  /**
   * 인라인 편집 완료 시 서버 PATCH API를 호출하고, 성공 응답 후 스토어를 갱신한다 (REQ-008-02).
   * 낙관적 업데이트를 사용하지 않는다 — 서버 응답 확인 후 갱신하여 데이터 일관성을 보장한다 (AC-008-03).
   * API 실패 시 스토어를 갱신하지 않고 에러 상태를 설정한다.
   */
  syncPatchDetailReq: (
    id: string,
    field: 'name' | 'content' | 'category',
    value: string
  ) => Promise<void>
  appendChatMessage: (msg: ChatMessage) => void
  setIsUploading: (v: boolean) => void
  setIsGenerating: (v: boolean) => void
  setIsChatting: (v: boolean) => void
  setError: (msg: string | null) => void
  /**
   * 새 HWP 파일 업로드 시 전체 상태를 초기값으로 되돌린다.
   * persist 미사용이므로 메모리에서만 초기화된다.
   */
  reset: () => void
}

const initialState: AppState = {
  phase: 'upload',
  sessionId: null,
  originalReqs: [],
  detailReqs: [],
  chatHistory: [],
  isUploading: false,
  isGenerating: false,
  isChatting: false,
  error: null,
}

export const useAppStore = create<AppState & AppActions>((set) => ({
  ...initialState,
  setPhase: (phase) => set({ phase }),
  setSessionId: (sessionId) => set({ sessionId }),
  setOriginalReqs: (originalReqs) => set({ originalReqs }),
  appendDetailReq: (req) => set((s) => ({ detailReqs: [...s.detailReqs, req] })),
  patchDetailReq: (id, field, value) =>
    set((s) => ({
      detailReqs: s.detailReqs.map((r) =>
        r.id === id ? { ...r, [field]: value, is_modified: true } : r
      ),
    })),
  syncPatchDetailReq: async (id, field, value) => {
    // 서버 응답 확인 후 스토어를 갱신하여 서버-클라이언트 일관성을 보장한다 (AC-008-03).
    // 실패 시 스토어는 이전 값을 유지하고 에러 상태만 설정한다.
    try {
      const updated = await apiPatchDetailReq(id, field, value)
      set((s) => ({
        detailReqs: s.detailReqs.map((r) => (r.id === id ? updated : r)),
        error: null,
      }))
    } catch (e) {
      const message =
        e instanceof Error ? e.message : '인라인 편집 저장에 실패했습니다.'
      set({ error: message })
    }
  },
  appendChatMessage: (msg) => set((s) => ({ chatHistory: [...s.chatHistory, msg] })),
  setIsUploading: (isUploading) => set({ isUploading }),
  setIsGenerating: (isGenerating) => set({ isGenerating }),
  setIsChatting: (isChatting) => set({ isChatting }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),
}))
