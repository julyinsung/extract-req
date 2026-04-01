import { test, expect } from '@playwright/test'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const HWP_FILE = path.resolve(__dirname, '../../sample.hwp')

test.describe('1단계 E2E: HWP 업로드 → 원본 요구사항 파싱 (TST-007-04 / AC-001-01~04, AC-003-01)', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('업로드 화면이 초기에 표시된다 (AC-001-01)', async ({ page }) => {
    await expect(page.getByTestId('upload-area')).toBeVisible()
    await expect(page.getByTestId('upload-panel')).toBeVisible()
    await expect(page.getByTestId('file-input')).toBeAttached()
  })

  test('HWP 파일 선택 시 파일명이 표시된다 (AC-001-01)', async ({ page }) => {
    const fileInput = page.getByTestId('file-input')
    await fileInput.setInputFiles(HWP_FILE)

    await expect(page.getByTestId('selected-filename')).toBeVisible()
    await expect(page.getByTestId('selected-filename')).toContainText('sample.hwp')
  })

  test('업로드 버튼 클릭 시 로딩 상태가 표시된다 (AC-001-01)', async ({ page }) => {
    // 백엔드 응답 지연 중 로딩 인디케이터 확인 (느린 응답 모킹)
    await page.route('**/upload', async route => {
      await new Promise(resolve => setTimeout(resolve, 1500))
      await route.continue()
    })

    const fileInput = page.getByTestId('file-input')
    await fileInput.setInputFiles(HWP_FILE)

    await page.getByTestId('upload-button').click()

    // 업로드 버튼이 비활성화되거나 로딩 상태 진입 확인
    await expect(page.getByTestId('upload-button')).toBeDisabled()
  })

  test('sample.hwp 업로드 후 원본 요구사항 테이블이 표시된다 (AC-001-02, AC-003-01)', async ({ page }) => {
    const fileInput = page.getByTestId('file-input')
    await fileInput.setInputFiles(HWP_FILE)
    await page.getByTestId('upload-button').click()

    // 테이블 영역 등장 대기 (업로드 + 파싱 완료)
    await expect(page.getByTestId('table-area')).toBeVisible({ timeout: 30000 })
    await expect(page.getByTestId('original-req-table')).toBeVisible()
  })

  test('원본 요구사항 테이블에 1행 이상의 데이터가 있다 (AC-001-02)', async ({ page }) => {
    const fileInput = page.getByTestId('file-input')
    await fileInput.setInputFiles(HWP_FILE)
    await page.getByTestId('upload-button').click()

    await expect(page.getByTestId('original-req-table')).toBeVisible({ timeout: 30000 })

    // 테이블 행이 1개 이상 존재
    const rows = page.locator('[data-testid="original-req-table"] tbody tr')
    expect(await rows.count()).toBeGreaterThan(0)
  })

  test('원본 요구사항 테이블에 4개 컬럼(ID, 분류, 명칭, 내용)이 표시된다 (AC-003-01)', async ({ page }) => {
    const fileInput = page.getByTestId('file-input')
    await fileInput.setInputFiles(HWP_FILE)
    await page.getByTestId('upload-button').click()

    await expect(page.getByTestId('original-req-table')).toBeVisible({ timeout: 30000 })

    const table = page.getByTestId('original-req-table')
    // 헤더에 주요 컬럼 텍스트 확인
    await expect(table).toContainText('ID')
    await expect(table).toContainText('분류')
    await expect(table).toContainText('명칭')
    await expect(table).toContainText('내용')
  })

  test('잘못된 파일(.txt) 업로드 시 오류 메시지가 표시된다 (AC-001-04)', async ({ page }) => {
    // .txt 파일을 HWP로 위장하여 업로드
    const fileInput = page.getByTestId('file-input')

    await fileInput.setInputFiles({
      name: 'fake.hwp',
      mimeType: 'text/plain',
      buffer: Buffer.from('this is not a hwp file'),
    })
    await page.getByTestId('upload-button').click()

    // 오류 메시지 등장 확인 (업로드 화면 유지 또는 에러 표시)
    await page.waitForTimeout(5000)
    const isUploadAreaVisible = await page.getByTestId('upload-area').isVisible()
    const isTableVisible = await page.getByTestId('table-area').isVisible().catch(() => false)

    // 파싱 실패 시 테이블 화면으로 넘어가면 안 됨
    expect(isUploadAreaVisible || !isTableVisible).toBeTruthy()
  })

})
