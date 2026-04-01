import axios from 'axios'
import type { ParseResponse, DetailRequirement } from '../types'

const BASE = 'http://localhost:8000/api/v1'

/**
 * HWP 파일을 multipart/form-data로 서버에 전송한다.
 * 서버는 파싱 완료 후 임시 파일을 자동 삭제한다 (REQ-006-03).
 */
export async function uploadHwp(file: File): Promise<ParseResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await axios.post<ParseResponse>(`${BASE}/upload`, form)
  return data
}

/**
 * SSE 스트림으로 상세 요구사항을 수신한다.
 * EventSource 대신 fetch + ReadableStream을 사용하는 이유:
 * POST 바디 전달이 필요하기 때문에 GET 전용인 EventSource는 적합하지 않다 (REQ-006 설계 참조).
 *
 * @returns cleanup 함수 — 컴포넌트 언마운트 또는 중단 시 호출
 */
export function generateDetailStream(
  sessionId: string,
  callbacks: {
    onItem: (req: DetailRequirement) => void
    onDone: (total: number) => void
    onError: (msg: string) => void
  }
): () => void {
  const controller = new AbortController()
  fetch(`${BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
    signal: controller.signal,
  }).then(async (res) => {
    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop()!
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const json = JSON.parse(line.slice(6))
        if (json.type === 'item') callbacks.onItem(json.data)
        else if (json.type === 'done') callbacks.onDone(json.total)
        else if (json.type === 'error') callbacks.onError(json.message)
      }
    }
  }).catch((e) => {
    // AbortError는 정상적인 cleanup 신호이므로 에러로 처리하지 않는다
    if (e.name !== 'AbortError') callbacks.onError(String(e))
  })
  return () => controller.abort()
}

/**
 * 채팅 메시지를 전송하고 AI 응답을 SSE 스트림으로 수신한다.
 * patch 이벤트 수신 시 해당 상세 요구사항 행을 즉시 갱신한다 (REQ-004-02).
 *
 * @returns cleanup 함수
 */
export function chatStream(
  payload: { session_id: string; message: string; history: { role: string; content: string }[] },
  callbacks: {
    onText: (delta: string) => void
    onPatch: (id: string, field: string, value: string) => void
    onDone: () => void
    onError: (msg: string) => void
  }
): () => void {
  const controller = new AbortController()
  fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: controller.signal,
  }).then(async (res) => {
    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop()!
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const json = JSON.parse(line.slice(6))
        if (json.type === 'text') callbacks.onText(json.delta)
        else if (json.type === 'patch') callbacks.onPatch(json.id, json.field, json.value)
        else if (json.type === 'done') callbacks.onDone()
        else if (json.type === 'error') callbacks.onError(json.message)
      }
    }
  }).catch((e) => {
    if (e.name !== 'AbortError') callbacks.onError(String(e))
  })
  return () => controller.abort()
}

/**
 * 엑셀 다운로드 URL을 생성한다.
 * stage 1: 원본 요구사항만, stage 2: 원본 + 상세 요구사항 포함 (REQ-005).
 */
export function getDownloadUrl(sessionId: string, stage: 1 | 2): string {
  return `${BASE}/download?session_id=${sessionId}&stage=${stage}`
}
