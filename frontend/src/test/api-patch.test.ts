/**
 * UT-008-06: patchDetailReq() — 정상 응답 시 DetailRequirement 객체 반환
 * UT-008-07: patchDetailReq() — 서버 404 응답 시 예외 throw
 * UT-008-08: syncPatchDetailReq — API 성공 후 Zustand 스토어 해당 항목 갱신
 * UT-008-09: syncPatchDetailReq — API 실패 시 스토어 값 불변, 에러 상태 설정
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import axios from 'axios'
import { patchDetailReq } from '../api'
import { useAppStore } from '../store/useAppStore'
import type { DetailRequirement } from '../types'

// axios 모킹 — 실제 HTTP 요청 없이 API 함수 동작만 검증한다
vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

// 테스트에서 사용할 픽스처 상세 요구사항
const FIXTURE: DetailRequirement = {
  id: 'REQ-001-02',
  parent_id: 'REQ-001',
  category: '기능 요구사항',
  name: '로그인 기능',
  content: '원래 내용',
  order_index: 1,
  is_modified: false,
}

// 서버 PATCH 성공 시 반환되는 수정된 항목
const PATCHED: DetailRequirement = {
  ...FIXTURE,
  content: '수정된 내용 텍스트',
  is_modified: true,
}

beforeEach(() => {
  useAppStore.getState().reset()
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

// ─────────────────────────────────────────────────────────────
// UT-008-06: patchDetailReq() API 함수 — 정상 응답
// ─────────────────────────────────────────────────────────────
describe('UT-008-06: patchDetailReq() — 정상 응답 시 DetailRequirement 반환', () => {
  it('서버 200 응답 시 수정된 DetailRequirement 객체를 반환한다', async () => {
    // axios.patch가 수정된 항목을 반환하도록 mock 설정
    mockedAxios.patch = vi.fn().mockResolvedValue({ data: PATCHED })

    const result = await patchDetailReq('REQ-001-02', 'content', '수정된 내용 텍스트')

    expect(result).toEqual(PATCHED)
    expect(result.content).toBe('수정된 내용 텍스트')
    expect(result.is_modified).toBe(true)
  })

  it('올바른 경로와 바디로 PATCH 요청을 전송한다', async () => {
    mockedAxios.patch = vi.fn().mockResolvedValue({ data: PATCHED })

    await patchDetailReq('REQ-001-02', 'content', '수정된 내용 텍스트')

    expect(mockedAxios.patch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/detail/REQ-001-02',
      { detail_id: 'REQ-001-02', field: 'content', value: '수정된 내용 텍스트' }
    )
  })
})

// ─────────────────────────────────────────────────────────────
// UT-008-07: patchDetailReq() API 함수 — 404 응답 시 예외 throw
// ─────────────────────────────────────────────────────────────
describe('UT-008-07: patchDetailReq() — 서버 404 응답 시 예외 throw', () => {
  it('존재하지 않는 id로 요청 시 예외를 throw한다', async () => {
    // axios는 4xx 응답에서 자동으로 예외를 발생시킨다
    const notFoundError = Object.assign(new Error('Request failed with status code 404'), {
      response: { status: 404, data: { code: 'NOT_FOUND', message: '해당 ID의 상세요구사항을 찾을 수 없습니다: REQ-999-99' } },
    })
    mockedAxios.patch = vi.fn().mockRejectedValue(notFoundError)

    await expect(
      patchDetailReq('REQ-999-99', 'content', '수정값')
    ).rejects.toThrow()
  })

  it('네트워크 오류 시에도 예외를 throw한다', async () => {
    mockedAxios.patch = vi.fn().mockRejectedValue(new Error('Network Error'))

    await expect(
      patchDetailReq('REQ-001-02', 'content', '수정값')
    ).rejects.toThrow('Network Error')
  })
})

// ─────────────────────────────────────────────────────────────
// UT-008-08: syncPatchDetailReq — API 성공 후 스토어 갱신
// ─────────────────────────────────────────────────────────────
describe('UT-008-08: syncPatchDetailReq — API 성공 후 Zustand 스토어 해당 항목 갱신', () => {
  it('API 성공 응답 후 스토어의 해당 항목 content 값이 갱신된다', async () => {
    mockedAxios.patch = vi.fn().mockResolvedValue({ data: PATCHED })

    // 스토어에 초기 항목 추가
    useAppStore.getState().appendDetailReq(FIXTURE)

    await useAppStore.getState().syncPatchDetailReq('REQ-001-02', 'content', '수정된 내용 텍스트')

    const updated = useAppStore.getState().detailReqs.find(r => r.id === 'REQ-001-02')
    expect(updated?.content).toBe('수정된 내용 텍스트')
    expect(updated?.is_modified).toBe(true)
  })

  it('API 성공 후 에러 상태가 null로 초기화된다', async () => {
    mockedAxios.patch = vi.fn().mockResolvedValue({ data: PATCHED })

    useAppStore.getState().appendDetailReq(FIXTURE)
    // 사전에 에러 상태가 설정되어 있었다고 가정
    useAppStore.getState().setError('이전 오류')

    await useAppStore.getState().syncPatchDetailReq('REQ-001-02', 'content', '수정된 내용 텍스트')

    expect(useAppStore.getState().error).toBeNull()
  })

  it('서버 응답의 전체 DetailRequirement 객체로 스토어 항목을 교체한다', async () => {
    // 서버가 반환한 name 변경도 반영되어야 한다
    const serverResponse: DetailRequirement = { ...FIXTURE, name: '서버에서 바뀐 명칭', is_modified: true }
    mockedAxios.patch = vi.fn().mockResolvedValue({ data: serverResponse })

    useAppStore.getState().appendDetailReq(FIXTURE)

    await useAppStore.getState().syncPatchDetailReq('REQ-001-02', 'name', '서버에서 바뀐 명칭')

    const updated = useAppStore.getState().detailReqs.find(r => r.id === 'REQ-001-02')
    expect(updated?.name).toBe('서버에서 바뀐 명칭')
  })
})

// ─────────────────────────────────────────────────────────────
// UT-008-09: syncPatchDetailReq — API 실패 시 스토어 불변, 에러 상태 설정
// ─────────────────────────────────────────────────────────────
describe('UT-008-09: syncPatchDetailReq — API 실패 시 스토어 값 불변, 에러 상태 설정', () => {
  it('API 404 실패 시 스토어의 해당 항목 값이 변경되지 않는다', async () => {
    const notFoundError = Object.assign(new Error('Request failed with status code 404'), {
      response: { status: 404 },
    })
    mockedAxios.patch = vi.fn().mockRejectedValue(notFoundError)

    useAppStore.getState().appendDetailReq(FIXTURE)

    await useAppStore.getState().syncPatchDetailReq('REQ-001-02', 'content', '시도했지만 실패')

    // 스토어 값은 원래 값을 유지해야 한다
    const unchanged = useAppStore.getState().detailReqs.find(r => r.id === 'REQ-001-02')
    expect(unchanged?.content).toBe('원래 내용')
    expect(unchanged?.is_modified).toBe(false)
  })

  it('API 실패 시 에러 상태가 설정된다', async () => {
    mockedAxios.patch = vi.fn().mockRejectedValue(new Error('인라인 편집 저장에 실패했습니다.'))

    useAppStore.getState().appendDetailReq(FIXTURE)

    await useAppStore.getState().syncPatchDetailReq('REQ-001-02', 'content', '시도했지만 실패')

    expect(useAppStore.getState().error).toBeTruthy()
    expect(useAppStore.getState().error).toContain('인라인 편집 저장에 실패했습니다.')
  })

  it('API 네트워크 오류 시에도 스토어 값이 유지된다', async () => {
    mockedAxios.patch = vi.fn().mockRejectedValue(new Error('Network Error'))

    const OTHER_FIXTURE: DetailRequirement = {
      id: 'REQ-001-03',
      parent_id: 'REQ-001',
      category: '기능 요구사항',
      name: '다른 항목',
      content: '다른 내용',
      order_index: 2,
      is_modified: false,
    }
    useAppStore.getState().appendDetailReq(FIXTURE)
    useAppStore.getState().appendDetailReq(OTHER_FIXTURE)

    await useAppStore.getState().syncPatchDetailReq('REQ-001-02', 'content', '실패할 수정')

    // 실패한 항목 확인
    const failed = useAppStore.getState().detailReqs.find(r => r.id === 'REQ-001-02')
    expect(failed?.content).toBe('원래 내용')

    // 다른 항목은 영향 없음
    const other = useAppStore.getState().detailReqs.find(r => r.id === 'REQ-001-03')
    expect(other?.content).toBe('다른 내용')
  })
})
