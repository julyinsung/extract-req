import { create } from 'zustand'
import type { OriginalRequirement, DetailRequirement, ChatMessage, AppPhase } from '../types'

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
  appendChatMessage: (msg) => set((s) => ({ chatHistory: [...s.chatHistory, msg] })),
  setIsUploading: (isUploading) => set({ isUploading }),
  setIsGenerating: (isGenerating) => set({ isGenerating }),
  setIsChatting: (isChatting) => set({ isChatting }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),
}))
