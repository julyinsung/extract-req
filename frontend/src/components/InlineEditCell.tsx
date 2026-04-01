import { useRef, useEffect } from 'react'
import type { DetailRequirement } from '../types'

/** InlineEditCell 컴포넌트 Props */
interface Props {
  value: string
  field: keyof DetailRequirement
  detailId: string
  onSave: (field: string, value: string) => void
  onCancel: () => void
}

/** 입력 요소 공통 스타일 — 포커스 강조를 위해 파란 테두리 사용 (디자인 토큰: #2563EB) */
const INPUT_STYLE: React.CSSProperties = {
  width: '100%',
  padding: '4px 6px',
  border: '2px solid #2563EB',
  borderRadius: 4,
  fontSize: 14,
  boxSizing: 'border-box',
}

/**
 * 인라인 편집 셀 컴포넌트.
 * field가 'content'이면 <textarea>, 그 외(name/category)는 <input>으로 렌더링한다.
 * - blur: 변경 내용 저장 (onSave 콜백)
 * - Escape: 편집 취소 (onCancel 콜백)
 * - Enter (content 제외): 변경 내용 저장
 *
 * REQ-003-03 / AC-003-03 대응
 */
export function InlineEditCell({ value, field, onSave, onCancel }: Props) {
  const ref = useRef<HTMLInputElement & HTMLTextAreaElement>(null)

  // 편집 모드 진입 시 즉시 포커스
  useEffect(() => {
    ref.current?.focus()
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel()
    }
    // content 필드는 Shift+Enter로 줄바꿈을 허용하므로 Enter 저장에서 제외
    if (e.key === 'Enter' && !e.shiftKey && field !== 'content') {
      onSave(field as string, ref.current?.value ?? '')
    }
  }

  if (field === 'content') {
    return (
      <textarea
        ref={ref as React.RefObject<HTMLTextAreaElement>}
        defaultValue={value}
        rows={3}
        style={INPUT_STYLE}
        onBlur={(e) => onSave(field, e.target.value)}
        onKeyDown={handleKeyDown}
        aria-label="내용 편집"
        data-testid={`inline-edit-textarea`}
      />
    )
  }

  return (
    <input
      ref={ref as React.RefObject<HTMLInputElement>}
      defaultValue={value}
      type="text"
      style={INPUT_STYLE}
      onBlur={(e) => onSave(field, e.target.value)}
      onKeyDown={handleKeyDown}
      aria-label={`${field} 편집`}
      data-testid={`inline-edit-input`}
    />
  )
}
