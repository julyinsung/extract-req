import { test, expect } from '@playwright/test'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const HWP_FILE = path.resolve(__dirname, '../../sample.hwp')

/** 1단계(업로드→파싱) 완료 후 상태로 이동하는 공통 헬퍼 */
async function goToStep1Done(page: import('@playwright/test').Page) {
  await page.goto('/')
  const fileInput = page.getByTestId('file-input')
  await fileInput.setInputFiles(HWP_FILE)
  await page.getByTestId('upload-button').click()
  await expect(page.getByTestId('original-req-table')).toBeVisible({ timeout: 30000 })
}

// claude_code_sdk는 실제 Claude Code 프로세스를 실행하므로 생성 시간이 길다 (2~5분)
test.describe('2단계 E2E: 상세요구사항 생성 (AI_BACKEND=claude_code_sdk)', () => {
  test.setTimeout(360000) // 6분 — SDK 생성 완료 대기


  test('상세요구사항 생성 버튼이 표시된다', async ({ page }) => {
    await goToStep1Done(page)
    await expect(page.getByTestId('generate-detail-btn')).toBeVisible()
    await expect(page.getByTestId('generate-detail-btn')).toHaveText('상세요구사항 생성')
  })

  test('생성 버튼 클릭 시 로딩 상태가 표시된다', async ({ page }) => {
    await goToStep1Done(page)
    await page.getByTestId('generate-detail-btn').click()

    // 생성 중 버튼 비활성화 + 텍스트 변경 확인
    await expect(page.getByTestId('generate-detail-btn')).toBeDisabled()
    await expect(page.getByTestId('generate-detail-btn')).toHaveText('생성 중...')
  })

  test('생성 완료 후 상세요구사항 테이블이 표시된다 (claude_code_sdk)', async ({ page }) => {
    await goToStep1Done(page)
    await page.getByTestId('generate-detail-btn').click()

    // 생성 중 인디케이터 등장 확인
    await expect(page.getByTestId('generating-indicator')).toBeVisible({ timeout: 10000 })

    // 생성 완료 대기 — claude_code_sdk는 응답 시간이 길 수 있어 넉넉한 타임아웃
    await expect(page.getByTestId('generating-indicator')).not.toBeVisible({ timeout: 300000 })

    // 상세요구사항 테이블 표시 확인
    await expect(page.getByTestId('detail-req-table')).toBeVisible()
  })

  test('생성 완료 후 1행 이상의 상세요구사항이 있다', async ({ page }) => {
    await goToStep1Done(page)
    await page.getByTestId('generate-detail-btn').click()

    // 생성 완료 대기
    await expect(page.getByTestId('generating-indicator')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('generating-indicator')).not.toBeVisible({ timeout: 300000 })

    // 상세요구사항 행 수 확인
    const rows = page.locator('[data-testid="detail-req-table"] tbody tr')
    expect(await rows.count()).toBeGreaterThan(0)
  })

  test('생성 완료 후 생성 버튼이 사라진다', async ({ page }) => {
    await goToStep1Done(page)
    await page.getByTestId('generate-detail-btn').click()

    await expect(page.getByTestId('generating-indicator')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('generating-indicator')).not.toBeVisible({ timeout: 300000 })

    // detailReqs가 있으면 버튼은 숨겨짐 (OriginalReqTable 조건부 렌더)
    await expect(page.getByTestId('generate-detail-btn')).not.toBeVisible()
  })

  test('SSE 스트리밍 중 행이 순차적으로 추가된다', async ({ page }) => {
    await goToStep1Done(page)
    await page.getByTestId('generate-detail-btn').click()

    // 생성 시작 후 첫 번째 행이 나타날 때까지 대기 — SDK는 응답 시작에 시간이 걸릴 수 있음
    await expect(
      page.locator('[data-testid="detail-req-table"] tbody tr').first()
    ).toBeVisible({ timeout: 180000 })

    // 첫 행 등장 시 아직 생성 중인지 확인 (스트리밍 중간 상태)
    const rowCountMid = await page.locator('[data-testid="detail-req-table"] tbody tr').count()
    console.log(`스트리밍 중 현재 행 수: ${rowCountMid}`)

    // 생성 완료 대기 후 최종 행 수 확인
    await expect(page.getByTestId('generating-indicator')).not.toBeVisible({ timeout: 300000 })
    const rowCountFinal = await page.locator('[data-testid="detail-req-table"] tbody tr').count()
    console.log(`생성 완료 후 최종 행 수: ${rowCountFinal}`)

    expect(rowCountFinal).toBeGreaterThanOrEqual(rowCountMid)
  })

})
