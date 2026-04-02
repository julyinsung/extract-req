import { create } from 'zustand'
import type { OriginalRequirement, DetailRequirement, ChatMessage, AppPhase } from '../types'
import { patchDetailReq as apiPatchDetailReq, deleteDetailReq as apiDeleteDetailReq } from '../api'

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
  /** 현재 채팅 컨텍스트로 선택된 REQ 그룹 ID (REQ-004-04) */
  selectedReqGroup: string | null
  /** 생성 진행률 — 현재까지 완료된 원본 요구사항 수 (REQ-010) */
  progressCurrent: number
  /** 생성 진행률 — 전체 원본 요구사항 수 (REQ-010) */
  progressTotal: number
  /** 생성 진행률 — 방금 완료된 원본 요구사항 ID (REQ-010) */
  progressReqId: string | null
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
  /**
   * REPLACE SSE 이벤트 수신 시 해당 REQ 그룹의 상세요구사항 전체를 교체한다 (REQ-004-06).
   * 서버가 이미 state를 교체한 뒤 이벤트를 발행하므로 API 호출 없이 스토어만 갱신한다.
   */
  replaceDetailReqGroup: (reqGroup: string, items: DetailRequirement[]) => void
  appendChatMessage: (msg: ChatMessage) => void
  setIsUploading: (v: boolean) => void
  /**
   * isGenerating 상태를 변경한다.
   * false로 설정 시 진행률 상태도 함께 초기화한다 (REQ-010).
   */
  setIsGenerating: (v: boolean) => void
  setIsChatting: (v: boolean) => void
  setError: (msg: string | null) => void
  /** 현재 선택된 REQ 그룹 ID를 설정한다 (REQ-004-04). null이면 전체 컨텍스트로 복귀 */
  setSelectedReqGroup: (group: string | null) => void
  /** 생성 진행률 상태를 갱신한다 (REQ-010-01) */
  setProgress: (current: number, total: number, reqId: string) => void
  /** 생성 진행률 상태를 초기화한다 (REQ-010-03) */
  clearProgress: () => void
  /**
   * 상세요구사항 1건을 삭제한다 (REQ-012-01).
   * 서버 DELETE API 호출 성공 후 스토어에서 해당 항목을 제거한다.
   * 실패 시 스토어를 갱신하지 않고 에러 상태를 설정한다 (REQ-012-02).
   */
  deleteDetailReq: (id: string) => Promise<void>
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
  selectedReqGroup: null,
  progressCurrent: 0,
  progressTotal: 0,
  progressReqId: null,
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
  replaceDetailReqGroup: (reqGroup, items) =>
    set((s) => ({
      detailReqs: [
        ...s.detailReqs.filter((r) => r.parent_id !== reqGroup),
        ...items,
      ],
    })),
  appendChatMessage: (msg) => set((s) => ({ chatHistory: [...s.chatHistory, msg] })),
  setIsUploading: (isUploading) => set({ isUploading }),
  setIsGenerating: (isGenerating) => {
    if (!isGenerating) {
      // isGenerating이 false가 될 때 진행률도 함께 초기화한다 (REQ-010)
      set({ isGenerating, progressCurrent: 0, progressTotal: 0, progressReqId: null })
    } else {
      set({ isGenerating })
    }
  },
  setIsChatting: (isChatting) => set({ isChatting }),
  setError: (error) => set({ error }),
  setSelectedReqGroup: (selectedReqGroup) => set({ selectedReqGroup }),
  setProgress: (progressCurrent, progressTotal, progressReqId) =>
    set({ progressCurrent, progressTotal, progressReqId }),
  clearProgress: () => set({ progressCurrent: 0, progressTotal: 0, progressReqId: null }),
  deleteDetailReq: async (id) => {
    // 서버 DELETE 확인 후 스토어 갱신 — 삭제는 되돌릴 수 없으므로 낙관적 업데이트 사용 안 함
    try {
      await apiDeleteDetailReq(id)
      set((s) => ({
        detailReqs: s.detailReqs.filter((r) => r.id !== id),
        error: null,
      }))
    } catch (e) {
      const message =
        e instanceof Error ? e.message : '상세요구사항 삭제에 실패했습니다.'
      set({ error: message })
    }
  },
  reset: () => set(initialState),
}))
