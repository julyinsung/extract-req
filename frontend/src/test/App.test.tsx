/**
 * App 컴포넌트 레이아웃 렌더링 검증.
 * phase 상태에 따라 올바른 영역이 조건부 렌더링되는지 확인한다.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'
import { useAppStore } from '../store/useAppStore'

beforeEach(() => {
  useAppStore.getState().reset()
})

describe('App — 타이틀 렌더링', () => {
  it('애플리케이션 타이틀이 표시되어야 한다', () => {
    render(<App />)
    expect(screen.getByText('HWP 상세요구사항 자동생성 도구')).toBeInTheDocument()
  })
})

describe('App — phase: upload', () => {
  it('upload phase에서 업로드 영역이 렌더링된다', () => {
    render(<App />)
    expect(screen.getByTestId('upload-area')).toBeInTheDocument()
  })

  it('upload phase에서 테이블 영역이 렌더링되지 않는다', () => {
    render(<App />)
    expect(screen.queryByTestId('table-area')).not.toBeInTheDocument()
  })
})

describe('App — phase: parsed', () => {
  it('parsed phase에서 테이블 영역이 렌더링된다', () => {
    useAppStore.getState().setPhase('parsed')
    render(<App />)
    expect(screen.getByTestId('table-area')).toBeInTheDocument()
  })

  it('parsed phase에서 채팅 영역이 렌더링되지 않는다', () => {
    useAppStore.getState().setPhase('parsed')
    render(<App />)
    expect(screen.queryByTestId('chat-area')).not.toBeInTheDocument()
  })
})

describe('App — phase: generated', () => {
  it('generated phase에서 테이블 영역과 채팅 영역이 모두 렌더링된다', () => {
    useAppStore.getState().setPhase('generated')
    render(<App />)
    expect(screen.getByTestId('table-area')).toBeInTheDocument()
    expect(screen.getByTestId('chat-area')).toBeInTheDocument()
  })
})

describe('App — 에러 표시', () => {
  it('error가 설정되면 에러 메시지가 화면에 표시된다', () => {
    useAppStore.getState().setError('파싱 오류가 발생했습니다')
    render(<App />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('파싱 오류가 발생했습니다')).toBeInTheDocument()
  })

  it('error가 null이면 에러 영역이 렌더링되지 않는다', () => {
    render(<App />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
