/**
 * HWP 파싱 결과 원본 요구사항 데이터 구조.
 * 백엔드 OriginalRequirement 모델과 1:1 대응한다.
 */
export interface OriginalRequirement {
  id: string
  category: string
  name: string
  content: string
  order_index: number
}

/**
 * AI가 원본 요구사항에서 생성한 상세 요구사항.
 * parent_id로 원본과의 1:N 계층 관계를 표현한다.
 */
export interface DetailRequirement {
  id: string
  parent_id: string
  category: string
  name: string
  content: string
  order_index: number
  is_modified: boolean
}

/**
 * 채팅 대화 메시지.
 * role: 'user' | 'assistant' 구분으로 발화자를 식별한다.
 */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

/**
 * POST /api/v1/upload 응답 스키마.
 * session_id는 이후 모든 API 호출에서 세션 연속성을 보장한다.
 */
export interface ParseResponse {
  session_id: string
  requirements: OriginalRequirement[]
}

/**
 * 애플리케이션 단계 상태.
 * upload → parsed → generated 순서로 단방향 전이한다.
 */
export type AppPhase = 'upload' | 'parsed' | 'generated'
