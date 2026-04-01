import { Session, RequirementsStats, TestStats, DesignDoc, QAResult } from '@/lib/project'
import { FileText, CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'
import Link from 'next/link'

interface Props {
  session: Session
  reqStats: RequirementsStats
  testStats: TestStats
  designDocs: DesignDoc[]
  qaResults: QAResult[]
}

const GATE_META: Record<string, { label: string; description: string; borderColor: string; badgeColor: string }> = {
  gate1: { label: 'Gate 1 — 요구사항', description: 'PM이 REQ-ID와 AC를 정의하는 단계', borderColor: 'border-blue-500',   badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
  gate2: { label: 'Gate 2 — 설계',     description: 'Architect · DBA · UI Designer가 시스템을 설계하는 단계', borderColor: 'border-purple-500', badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/30' },
  gate3: { label: 'Gate 3 — 테스트 계획', description: 'QA가 E2E/Integration TST-ID를 작성하는 단계', borderColor: 'border-yellow-500', badgeColor: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30' },
  impl:  { label: '구현',               description: 'Frontend · Backend Developer가 코드를 작성하는 단계', borderColor: 'border-orange-500', badgeColor: 'bg-orange-500/10 text-orange-400 border-orange-500/30' },
  gate4: { label: 'Gate 4 — QA 리뷰',  description: 'QA가 코드 리뷰와 테스트를 실행하는 단계', borderColor: 'border-red-500',    badgeColor: 'bg-red-500/10 text-red-400 border-red-500/30' },
  gate5: { label: 'Gate 5 — 최종 승인', description: '사용자가 최종 확인하는 단계', borderColor: 'border-green-500',  badgeColor: 'bg-green-500/10 text-green-400 border-green-500/30' },
}

export default function CurrentGatePanel({ session, reqStats, testStats, designDocs, qaResults }: Props) {
  const gate = session.current_gate
  const meta = GATE_META[gate]
  if (!meta) return null

  return (
    <div className={`rounded-xl border-l-4 ${meta.borderColor} bg-gray-900 border border-gray-800 p-6 space-y-4`}>
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${meta.badgeColor}`}>
              진행 중
            </span>
            <h2 className="text-base font-bold text-white">{meta.label}</h2>
          </div>
          <p className="text-sm text-gray-400 mt-1">{meta.description}</p>
        </div>
      </div>

      {/* Gate별 콘텐츠 */}
      <GateContent
        gate={gate}
        reqStats={reqStats}
        testStats={testStats}
        designDocs={designDocs}
        qaResults={qaResults}
      />
    </div>
  )
}

interface GateContentProps extends Omit<Props, 'session'> {
  gate: string
}

function GateContent({ gate, reqStats, testStats, designDocs, qaResults }: GateContentProps) {
  if (gate === 'gate1') {
    return (
      <div className="space-y-3">
        <Row label="REQ 그룹" value={`${reqStats.groups}개`} />
        <Row label="상세 요구사항" value={`${reqStats.total}개`} />
        <Row label="AC 정의 완료" value={`${reqStats.acDefined} / ${reqStats.total}`}
          status={reqStats.missing.length === 0 && reqStats.total > 0 ? 'ok' : 'warn'} />
        {reqStats.missing.length > 0 && (
          <div>
            <p className="text-xs text-gray-500 mb-1.5">AC 미정의 항목</p>
            <div className="flex flex-wrap gap-1.5">
              {reqStats.missing.map(id => (
                <span key={id} className="text-xs bg-yellow-950/50 text-yellow-400 border border-yellow-800/50 px-2 py-0.5 rounded">
                  {id}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  if (gate === 'gate2') {
    return (
      <div className="space-y-2">
        <p className="text-xs text-gray-500">생성된 설계 문서</p>
        {designDocs.length === 0 ? (
          <p className="text-sm text-gray-600 italic">아직 설계 문서가 없습니다</p>
        ) : (
          <ul className="space-y-1.5">
            {designDocs.map(doc => (
              <li key={doc.name}>
                <Link
                  href={`/docs/${doc.slug.join('/')}`}
                  className="flex items-center gap-2 text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded px-2 py-1.5 transition-colors"
                >
                  <FileText className="w-4 h-4 text-purple-400 flex-shrink-0" />
                  {doc.name}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  if (gate === 'gate3') {
    const pending = testStats.total - testStats.passed - testStats.failed - testStats.skipped
    return (
      <div className="space-y-3">
        <Row label="TST-ID 전체" value={`${testStats.total}개`} />
        <Row label="작성 완료" value={`${testStats.total}개`} status={testStats.total > 0 ? 'ok' : 'warn'} />
        {testStats.total > 0 && (
          <Row label="미실행 (실행 대기)" value={`${pending}개`} status={pending > 0 ? 'warn' : 'ok'} />
        )}
        {testStats.total === 0 && (
          <p className="text-sm text-gray-600 italic">TEST_PLAN.md에 TST-ID가 없습니다</p>
        )}
      </div>
    )
  }

  if (gate === 'impl') {
    const pct = reqStats.total > 0 ? Math.round((reqStats.implemented / reqStats.total) * 100) : 0
    return (
      <div className="space-y-3">
        <Row
          label="구현 진행률"
          value={`${reqStats.implemented} / ${reqStats.total} (${pct}%)`}
          status={reqStats.implemented === reqStats.total && reqStats.total > 0 ? 'ok' : 'warn'}
        />
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${pct === 100 ? 'bg-green-500' : 'bg-orange-500'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    )
  }

  if (gate === 'gate4') {
    return (
      <div className="space-y-3">
        {qaResults.length === 0 ? (
          <p className="text-sm text-gray-600 italic">아직 QA 리뷰 문서가 없습니다</p>
        ) : (
          <ul className="space-y-2">
            {qaResults.map(r => (
              <li key={r.name} className="space-y-1">
                <Link
                  href={`/docs/${r.slug.join('/')}`}
                  className="flex items-center gap-2 text-sm hover:bg-gray-800 rounded px-2 py-1.5 transition-colors"
                >
                  {r.verdict === 'pass'    ? <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" /> :
                   r.verdict === 'fail'    ? <XCircle     className="w-4 h-4 text-red-400 flex-shrink-0" />   :
                                             <Clock       className="w-4 h-4 text-gray-500 flex-shrink-0" />}
                  <span className={r.verdict === 'pass' ? 'text-green-300' : r.verdict === 'fail' ? 'text-red-300' : 'text-gray-400'}>
                    {r.name}
                  </span>
                  <span className={`ml-auto text-xs font-medium ${r.verdict === 'pass' ? 'text-green-500' : r.verdict === 'fail' ? 'text-red-500' : 'text-gray-500'}`}>
                    {r.verdict === 'pass' ? 'Pass' : r.verdict === 'fail' ? 'Fail' : '미완료'}
                  </span>
                </Link>
                {r.blockers.length > 0 && (
                  <ul className="pl-8 space-y-0.5">
                    {r.blockers.map((b, i) => (
                      <li key={i} className="text-xs text-red-400 flex items-start gap-1">
                        <span className="mt-0.5">🔴</span>
                        <span className="line-clamp-1">{b}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  if (gate === 'gate5') {
    const allPass = qaResults.length > 0 && qaResults.every(r => r.verdict === 'pass')
    const testPassRate = testStats.total > 0 ? Math.round((testStats.passed / testStats.total) * 100) : 0
    return (
      <div className="space-y-3">
        <Row label="요구사항 구현 완료" value={`${reqStats.implemented} / ${reqStats.total}`}
          status={reqStats.implemented === reqStats.total && reqStats.total > 0 ? 'ok' : 'warn'} />
        <Row label="테스트 통과율" value={`${testPassRate}%`}
          status={testPassRate === 100 && testStats.total > 0 ? 'ok' : 'warn'} />
        <Row label="QA 최종 판정" value={allPass ? '전체 Pass' : qaResults.length === 0 ? '미완료' : '일부 Fail'}
          status={allPass ? 'ok' : 'warn'} />
      </div>
    )
  }

  return null
}

function Row({ label, value, status }: { label: string; value: string; status?: 'ok' | 'warn' }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-400">{label}</span>
      <span className={`font-medium flex items-center gap-1.5 ${status === 'ok' ? 'text-green-400' : status === 'warn' ? 'text-yellow-400' : 'text-white'}`}>
        {status === 'ok'   && <CheckCircle className="w-3.5 h-3.5" />}
        {status === 'warn' && <AlertCircle className="w-3.5 h-3.5" />}
        {value}
      </span>
    </div>
  )
}
