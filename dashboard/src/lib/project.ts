import fs from 'fs'
import path from 'path'

// dashboard/의 부모 디렉토리 = 프로젝트 루트
export const PROJECT_ROOT = path.join(process.cwd(), '..')

export interface Session {
  project: string
  vulcan_version?: string
  current_gate: string
  gate_status: Record<string, 'pending' | 'done'>
  feature: string
  started: string
  completed: string[]
  pending: string[]
  blocked: string[]
}

export interface DocNode {
  name: string
  slug: string[]
  type: 'file' | 'dir'
  children?: DocNode[]
}

export function readSession(): Session {
  const p = path.join(PROJECT_ROOT, 'session.json')
  try {
    return JSON.parse(fs.readFileSync(p, 'utf-8'))
  } catch {
    return {
      project: 'Unknown Project',
      current_gate: 'gate1',
      gate_status: {
        gate1: 'pending',
        gate2: 'pending',
        gate3: 'pending',
        gate4: 'pending',
        gate5: 'pending',
      },
      feature: '',
      started: '',
      completed: [],
      pending: [],
      blocked: [],
    }
  }
}

export function buildDocTree(dir: string, slugPrefix: string[] = []): DocNode[] {
  if (!fs.existsSync(dir)) return []

  return fs
    .readdirSync(dir)
    .filter(f => !f.startsWith('.') && !f.endsWith('.gitkeep'))
    .sort()
    .map(f => {
      const fullPath = path.join(dir, f)
      const slug = [...slugPrefix, f]
      const stat = fs.statSync(fullPath)

      if (stat.isDirectory()) {
        const children = buildDocTree(fullPath, slug)
        if (children.length === 0) return null
        return { name: f, slug, type: 'dir' as const, children }
      }

      if (!f.endsWith('.md')) return null
      return { name: f.replace('.md', ''), slug, type: 'file' as const }
    })
    .filter(Boolean) as DocNode[]
}

export function readDoc(slug: string[]): string | null {
  // slug가 ['_root', 'FILE.md'] 형태면 프로젝트 루트에서 읽기
  const base = slug[0] === '_root' ? PROJECT_ROOT : path.join(PROJECT_ROOT, 'docs')
  const parts = slug[0] === '_root' ? slug.slice(1) : slug
  const p = path.join(base, ...parts)
  if (!fs.existsSync(p)) return null
  return fs.readFileSync(p, 'utf-8')
}

// ── 통계 파싱 ───────────────────────────────────────────────────────────────

export interface RequirementsStats {
  groups: number        // REQ-NNN 그룹 수
  total: number         // REQ-NNN-NN 상세 요구사항 수
  acDefined: number     // AC 참조가 있는 REQ 수
  missing: string[]     // AC 참조 없는 REQ-ID 목록 (- 제외)
  implemented: number   // 상태=구현완료 수
}

export interface TestStats {
  total: number         // TST-ID 전체 수
  passed: number        // ✅ Pass 수
  failed: number        // ❌ Fail 수
  skipped: number       // ⏭ Skip 수
}

export function parseRequirementsStats(): RequirementsStats {
  const p = path.join(PROJECT_ROOT, 'docs', '01-requirements', 'REQUIREMENTS.md')
  if (!fs.existsSync(p)) return { groups: 0, total: 0, acDefined: 0, missing: [], implemented: 0 }

  const content = fs.readFileSync(p, 'utf-8')

  // REQ-NNN 그룹 수 (헤딩 또는 테이블에서 REQ-NNN만 추출)
  const allReqIds = [...new Set(content.match(/\bREQ-\d{3}\b/g) ?? [])]
  const groups    = allReqIds.filter(r => !/\bREQ-\d{3}-\d{2}\b/.test(r)).length

  // 구형 문서 호환: AC-NNN-NN 목록 (AC 참조 컬럼 없는 경우 폴백용)
  const legacyAcIds = new Set(content.match(/\bAC-\d{3}-\d{2}\b/g) ?? [])

  let total = 0
  let acDefined = 0
  let implemented = 0
  const missing: string[] = []

  for (const line of content.split('\n')) {
    if (!/\|\s*REQ-\d{3}-\d{2}\s*\|/.test(line)) continue

    // | REQ-001-01 | 요구사항 | 우선순위 | 상태 | AC 참조 |
    const cols = line.split('|').map(c => c.trim())
    // cols[0]='' cols[1]=REQ-ID cols[2]=요구사항 cols[3]=우선순위 cols[4]=상태 cols[5]=AC참조
    const reqId = cols[1]
    if (!reqId || !/^REQ-\d{3}-\d{2}$/.test(reqId)) continue

    total++

    if (cols[4] === '구현완료') implemented++

    const acRef = cols[5] ?? ''
    if (/^AC-\d{3}-\d{2}/.test(acRef)) {
      // AC-NNN-NN 패턴으로 시작 → 커버됨
      acDefined++
    } else if (acRef.startsWith('없음:')) {
      // 의도적으로 AC 없음 + 이유 명시 → missing 아님
    } else if (acRef === '') {
      // 구형 폴백: AC-NNN-NN이 문서 어딘가에 존재하는지 확인
      const expectedAc = reqId.replace('REQ-', 'AC-')
      if (legacyAcIds.has(expectedAc)) {
        acDefined++
      } else {
        missing.push(reqId)
      }
    } else {
      // AC 참조 컬럼이 있지만 형식 불일치 → 미정의로 처리
      missing.push(reqId)
    }
  }

  return { groups, total, acDefined, missing, implemented }
}

export function parseTestStats(): TestStats {
  const p = path.join(PROJECT_ROOT, 'docs', '03-test-plan', 'TEST_PLAN.md')
  if (!fs.existsSync(p)) return { total: 0, passed: 0, failed: 0, skipped: 0 }

  const content = fs.readFileSync(p, 'utf-8')

  const tstIds = [...new Set(content.match(/\bTST-\d{3}-\d{2}\b/g) ?? [])]

  // 테이블 행에서 Pass/Fail/Skip 마커 파싱
  // 예: | TST-001-01 | ... | ✅ Pass | 또는 | Pass |
  const passCount   = (content.match(/✅\s*Pass/gi) ?? []).length
  const failCount   = (content.match(/❌\s*Fail/gi) ?? []).length
  const skipCount   = (content.match(/⏭\s*Skip|⚠️\s*Skip/gi) ?? []).length

  return {
    total: tstIds.length,
    passed: passCount,
    failed: failCount,
    skipped: skipCount,
  }
}
