import { useState, useEffect } from 'react'
import { useAppStore } from '../store/useAppStore'
import { InlineEditCell } from './InlineEditCell'
import type { DetailRequirement } from '../types'

/** 테이블 헤더 셀 공통 스타일 */
const TH_STYLE: React.CSSProperties = {
  padding: '10px 8px',
  textAlign: 'left',
  fontWeight: 600,
  fontSize: 14,
}

/** 테이블 데이터 셀 공통 스타일 */
const TD_STYLE: React.CSSProperties = {
  padding: '4px 8px',
  fontSize: 14,
  verticalAlign: 'top',
}

/**
 * 상세요구사항 테이블 컴포넌트.
 * Zustand 스토어에서 detailReqs를 직접 구독하여 SSE 수신 시 행을 동적으로 추가한다.
 *
 * - isGenerating 중 셀 편집 비활성화 (REQ-003-02)
 * - 셀 클릭 → InlineEditCell 전환 (REQ-003-03, name/content/category 편집)
 * - req-highlight 이벤트 수신 시 해당 행 3초간 노란 배경 강조 (REQ-003-05)
 * - 상세 행 배경: #F0F9FF (디자인 토큰 req-003-design.md)
 * - isGenerating && progressTotal > 0 시 실제 진행률 바 표시 (REQ-010-02)
 * - 각 행에 삭제 버튼 추가, isGenerating 중 비활성화 (REQ-012-01)
 */
export function DetailReqTable() {
  const detailReqs = useAppStore((s) => s.detailReqs)
  const isGenerating = useAppStore((s) => s.isGenerating)
  const syncPatchDetailReq = useAppStore((s) => s.syncPatchDetailReq)
  const deleteDetailReq = useAppStore((s) => s.deleteDetailReq)
  const progressCurrent = useAppStore((s) => s.progressCurrent)
  const progressTotal = useAppStore((s) => s.progressTotal)
  const progressReqId = useAppStore((s) => s.progressReqId)

  // 현재 편집 중인 셀 — { id, field } 쌍으로 관리
  const [editingCell, setEditingCell] = useState<{
    id: string
    field: keyof DetailRequirement
  } | null>(null)

  // 하이라이트 대상 ID 집합 — Wave 4 채팅 패치 시 req-highlight 이벤트로 트리거
  const [highlighted, setHighlighted] = useState<Set<string>>(new Set())

  // req-highlight 커스텀 이벤트 리스너 — 채팅 패치로 변경된 행을 3초간 강조
  useEffect(() => {
    const handler = (e: CustomEvent) => {
      const id = e.detail as string
      setHighlighted((prev) => new Set(prev).add(id))
      setTimeout(() => {
        setHighlighted((prev) => {
          const next = new Set(prev)
          next.delete(id)
          return next
        })
      }, 3000)
    }
    window.addEventListener('req-highlight', handler as EventListener)
    return () => window.removeEventListener('req-highlight', handler as EventListener)
  }, [])

  /** 셀 저장 핸들러 — syncPatchDetailReq(API 호출 + 스토어 갱신) 후 편집 모드 종료 */
  const handleSave = (
    reqId: string,
    field: keyof DetailRequirement,
    value: string
  ) => {
    syncPatchDetailReq(reqId, field as 'name' | 'content' | 'category', value)
    setEditingCell(null)
  }

  /**
   * 행 삭제 핸들러 (REQ-012-03).
   * window.confirm으로 확인 후 deleteDetailReq 액션을 호출한다.
   * 취소 시 아무 동작 없음.
   */
  const handleDelete = (id: string) => {
    if (!window.confirm('이 항목을 삭제하시겠습니까?')) return
    deleteDetailReq(id)
  }

  /** 편집 가능한 필드 목록 (설계 문서 req-003-design.md) */
  const editableFields: (keyof DetailRequirement)[] = ['category', 'name', 'content']

  // 진행률 표시 여부: 실제 진행률 값이 있을 때만 진행률 바 표시 (REQ-010-02)
  const showProgress = isGenerating && progressTotal > 0
  // pulse 바 표시: isGenerating 중이지만 아직 진행률 데이터가 없을 때 (초기 상태)
  const showPulse = isGenerating && progressTotal === 0
  const progressPercent = progressTotal > 0 ? (progressCurrent / progressTotal) * 100 : 0

  return (
    <div style={{ marginTop: 24 }} data-testid="detail-req-table">
      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: '#0F172A' }}>
        상세요구사항 ({detailReqs.length}건)
        {isGenerating && (
          <span
            style={{ marginLeft: 8, fontSize: 14, fontWeight: 400, color: '#2563EB' }}
            data-testid="generating-indicator"
          >
            — 생성 중...
          </span>
        )}
      </h2>

      {/* 수평 스크롤 처리 — 모바일/태블릿에서 컬럼이 잘리지 않도록 */}
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}
          aria-label="상세요구사항 테이블"
        >
          <caption style={{ display: 'none' }}>AI가 생성한 상세요구사항 목록</caption>
          <thead>
            {/* 디자인 토큰: 헤더 배경 #4472C4 */}
            <tr style={{ background: '#4472C4', color: '#fff' }}>
              <th scope="col" style={{ ...TH_STYLE, width: '14%' }}>
                상세 ID
              </th>
              <th scope="col" style={{ ...TH_STYLE, width: '12%' }}>
                분류
              </th>
              <th scope="col" style={{ ...TH_STYLE, width: '20%' }}>
                명칭
              </th>
              <th scope="col" style={{ ...TH_STYLE }}>
                내용
              </th>
              {/* REQ-012: 삭제 버튼 헤더 컬럼 */}
              <th scope="col" style={{ ...TH_STYLE, width: '56px', textAlign: 'center' }}>
                삭제
              </th>
            </tr>
          </thead>
          <tbody>
            {detailReqs.length === 0 && !isGenerating ? (
              <tr>
                <td
                  colSpan={5}
                  style={{ ...TD_STYLE, textAlign: 'center', color: '#94A3B8', padding: '32px 8px' }}
                >
                  상세요구사항이 없습니다
                </td>
              </tr>
            ) : (
              detailReqs.map((req) => {
                // 하이라이트: req-highlight 이벤트 → 노란 배경, 그 외 → 상세 행 기본 배경
                const rowBg = highlighted.has(req.id) ? '#FEF9C3' : '#F0F9FF'
                return (
                  <tr
                    key={req.id}
                    style={{
                      background: rowBg,
                      borderBottom: '1px solid #E2E8F0',
                      transition: 'background 0.5s',
                    }}
                    data-testid={`detail-row-${req.id}`}
                  >
                    {/* 상세 ID — 16px 들여쓰기로 계층 구조 시각화 (디자인 토큰) */}
                    <td style={{ ...TD_STYLE, fontWeight: 600, paddingLeft: 16 }}>
                      {req.id}
                    </td>
                    {/* 편집 가능 필드: category / name / content */}
                    {editableFields.map((field) => (
                      <td
                        key={field}
                        style={{ ...TD_STYLE }}
                        onClick={() => {
                          // isGenerating 중 편집 비활성화 (REQ-003-02)
                          if (!isGenerating) {
                            setEditingCell({ id: req.id, field })
                          }
                        }}
                        data-testid={`cell-${req.id}-${field}`}
                      >
                        {editingCell?.id === req.id && editingCell?.field === field ? (
                          <InlineEditCell
                            value={req[field] as string}
                            field={field}
                            detailId={req.id}
                            onSave={(f, v) =>
                              handleSave(req.id, f as keyof DetailRequirement, v)
                            }
                            onCancel={() => setEditingCell(null)}
                          />
                        ) : (
                          <span
                            style={{
                              display: 'block',
                              whiteSpace: 'pre-wrap',
                              cursor: isGenerating ? 'default' : 'pointer',
                              minHeight: 24,
                            }}
                          >
                            {req[field] as string}
                          </span>
                        )}
                      </td>
                    ))}
                    {/* REQ-012: 삭제 버튼 셀 */}
                    <td style={{ ...TD_STYLE, textAlign: 'center', verticalAlign: 'middle' }}>
                      <button
                        data-testid={`delete-btn-${req.id}`}
                        onClick={() => handleDelete(req.id)}
                        disabled={isGenerating}
                        aria-label={`${req.id} 삭제`}
                        style={{
                          padding: '4px 8px',
                          background: isGenerating ? '#E2E8F0' : '#FEF2F2',
                          color: isGenerating ? '#94A3B8' : '#DC2626',
                          border: `1px solid ${isGenerating ? '#CBD5E1' : '#FECACA'}`,
                          borderRadius: 6,
                          fontSize: 12,
                          cursor: isGenerating ? 'not-allowed' : 'pointer',
                          fontWeight: 500,
                        }}
                      >
                        삭제
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 생성 중 진행 표시 — REQ-010: 실제 진행률 바로 교체 */}
      {showProgress && (
        <div
          style={{ marginTop: 12 }}
          role="status"
          aria-live="polite"
          data-testid="progress-bar"
        >
          <div
            style={{
              height: 4,
              background: '#DBEAFE',
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                background: '#2563EB',
                width: `${progressPercent}%`,
                borderRadius: 2,
                transition: 'width 0.3s ease',
              }}
            />
          </div>
          <p
            style={{ fontSize: 12, color: '#64748B', marginTop: 4, textAlign: 'center' }}
            data-testid="progress-text"
          >
            {progressCurrent} / {progressTotal} 항목 생성 중
            {progressReqId ? ` (${progressReqId})` : ''}
          </p>
        </div>
      )}

      {/* isGenerating이지만 아직 progress 이벤트가 없는 초기 구간 — pulse 바 유지 */}
      {showPulse && (
        <div
          style={{ marginTop: 12 }}
          role="status"
          aria-live="polite"
          data-testid="progress-bar"
        >
          <div
            style={{
              height: 4,
              background: '#DBEAFE',
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                background: '#2563EB',
                width: '60%',
                borderRadius: 2,
                animation: 'pulse 1.5s ease-in-out infinite',
              }}
            />
          </div>
          <p style={{ fontSize: 12, color: '#64748B', marginTop: 4, textAlign: 'center' }}>
            AI가 상세요구사항을 생성하는 중입니다...
          </p>
        </div>
      )}
    </div>
  )
}
