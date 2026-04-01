import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '../store/useAppStore'
import { chatStream } from '../api'
import type { ChatMessage } from '../types'
import { v4 as uuidv4 } from 'uuid'

/**
 * 채팅 기반 AI 수정 패널 (REQ-004).
 *
 * SSE 스트림으로 AI 응답을 실시간 표시하고,
 * patch 이벤트 수신 시 DetailReqTable 행을 즉시 갱신한다.
 * sessionId 미존재 또는 detailReqs 미생성 시 입력창을 비활성화한다 (UT-004-05).
 */
export function ChatPanel() {
  const {
    sessionId,
    detailReqs,
    chatHistory,
    isChatting,
    appendChatMessage,
    patchDetailReq,
    setIsChatting,
    setError,
  } = useAppStore()

  const [input, setInput] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  // sessionId 없거나 상세요구사항 미생성 또는 채팅 진행 중이면 입력 비활성화 (UT-004-05)
  const disabled = !sessionId || detailReqs.length === 0 || isChatting

  // 새 메시지 또는 스트리밍 텍스트 변경 시 최신 메시지로 자동 스크롤
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, streamingText])

  // 컴포넌트 언마운트 시 진행 중인 SSE 연결 정리
  useEffect(() => {
    return () => {
      cleanupRef.current?.()
    }
  }, [])

  /**
   * 메시지 전송 핸들러.
   * user 메시지를 히스토리에 먼저 추가한 뒤 SSE 스트림을 시작한다 (UT-004-03).
   */
  const handleSend = () => {
    const msg = input.trim()
    if (!msg || disabled || !sessionId) return

    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: msg,
      timestamp: new Date(),
    }
    appendChatMessage(userMsg)
    setInput('')
    setIsChatting(true)
    setStreamingText('')

    let aiText = ''

    cleanupRef.current = chatStream(
      {
        session_id: sessionId,
        message: msg,
        history: chatHistory.map((m) => ({ role: m.role, content: m.content })),
      },
      {
        onText: (delta) => {
          aiText += delta
          setStreamingText(aiText)
        },
        // patch 이벤트: 스토어 갱신 + DetailReqTable 하이라이트 이벤트 발행 (UT-004-02)
        onPatch: (id, field, value) => {
          patchDetailReq(id, field as keyof import('../types').DetailRequirement, value)
          window.dispatchEvent(new CustomEvent('req-highlight', { detail: id }))
        },
        onDone: () => {
          const aiMsg: ChatMessage = {
            id: uuidv4(),
            role: 'assistant',
            content: aiText,
            timestamp: new Date(),
          }
          appendChatMessage(aiMsg)
          setStreamingText('')
          setIsChatting(false)
        },
        onError: (err) => {
          setError(err)
          setIsChatting(false)
        },
      }
    )
  }

  return (
    <div
      data-testid="chat-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: 600,
        border: '1px solid #E2E8F0',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      {/* 패널 헤더 */}
      <div
        style={{
          padding: '12px 16px',
          background: '#2563EB',
          color: '#fff',
          fontWeight: 600,
          flexShrink: 0,
        }}
      >
        AI 수정 채팅
      </div>

      {/* 대화 내역 영역 — flex-grow로 나머지 공간 점유 */}
      <div
        role="log"
        aria-label="채팅 대화 내역"
        aria-live="polite"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        {/* 빈 상태 안내 메시지 */}
        {chatHistory.length === 0 && (
          <p
            style={{ color: '#94A3B8', textAlign: 'center', marginTop: 32, whiteSpace: 'pre-wrap' }}
          >
            {detailReqs.length === 0
              ? '상세요구사항을 먼저 생성해주세요.'
              : '요구사항 수정을 요청해보세요.\n예: "REQ-001-02의 내용을 더 구체적으로 작성해줘"'}
          </p>
        )}

        {/* 채팅 히스토리 메시지 목록 */}
        {chatHistory.map((msg) => (
          <div
            key={msg.id}
            data-testid={`chat-msg-${msg.id}`}
            style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              background: msg.role === 'user' ? '#2563EB' : '#F1F5F9',
              color: msg.role === 'user' ? '#fff' : '#1E293B',
              padding: '10px 14px',
              borderRadius: 12,
              whiteSpace: 'pre-wrap',
              fontSize: 14,
            }}
          >
            {msg.content}
          </div>
        ))}

        {/* 스트리밍 중인 AI 응답 — 커서 깜빡임 표시 */}
        {streamingText && (
          <div
            data-testid="streaming-text"
            style={{
              alignSelf: 'flex-start',
              maxWidth: '80%',
              background: '#F1F5F9',
              color: '#1E293B',
              padding: '10px 14px',
              borderRadius: 12,
              whiteSpace: 'pre-wrap',
              fontSize: 14,
            }}
          >
            {streamingText}
            <span aria-hidden="true" style={{ animation: 'blink 1s infinite' }}>
              ▋
            </span>
          </div>
        )}

        {/* 자동 스크롤 앵커 */}
        <div ref={bottomRef} />
      </div>

      {/* 입력 영역 */}
      <div
        style={{
          padding: 12,
          borderTop: '1px solid #E2E8F0',
          display: 'flex',
          gap: 8,
          flexShrink: 0,
        }}
      >
        <textarea
          data-testid="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value.slice(0, 2000))}
          // Enter 전송, Shift+Enter 줄바꿈 (SEC-004-02: 2000자 제한은 onChange에서 처리)
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          disabled={disabled}
          placeholder={
            disabled
              ? detailReqs.length === 0
                ? '상세요구사항 생성 후 이용 가능합니다.'
                : '처리 중...'
              : '수정 요청을 입력하세요... (Enter 전송, Shift+Enter 줄바꿈)'
          }
          rows={3}
          aria-label="채팅 메시지 입력"
          style={{
            flex: 1,
            resize: 'none',
            padding: '8px 12px',
            border: '1px solid #CBD5E1',
            borderRadius: 8,
            fontSize: 14,
            opacity: disabled ? 0.5 : 1,
          }}
        />
        <button
          data-testid="chat-send-btn"
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          aria-label="메시지 전송"
          style={{
            padding: '0 16px',
            background: '#2563EB',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            cursor: disabled || !input.trim() ? 'not-allowed' : 'pointer',
            opacity: disabled || !input.trim() ? 0.5 : 1,
          }}
        >
          전송
        </button>
      </div>
    </div>
  )
}
