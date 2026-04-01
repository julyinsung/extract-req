import { RequirementsStats, TestStats } from '@/lib/project'
import { FileText, FlaskConical, CheckCircle, XCircle, AlertCircle, Layers } from 'lucide-react'

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  color?: 'default' | 'green' | 'red' | 'yellow' | 'blue'
}

function StatCard({ icon, label, value, sub, color = 'default' }: StatCardProps) {
  const valueColor = {
    default: 'text-white',
    green:   'text-green-400',
    red:     'text-red-400',
    yellow:  'text-yellow-400',
    blue:    'text-blue-400',
  }[color]

  return (
    <div className="bg-gray-900 rounded-lg px-5 py-4 flex items-center gap-4 border border-gray-800">
      <div className="text-gray-500">{icon}</div>
      <div className="min-w-0">
        <div className="text-xs text-gray-500 truncate">{label}</div>
        <div className={`text-2xl font-bold ${valueColor}`}>{value}</div>
        {sub && <div className="text-xs text-gray-500 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

interface Props {
  reqStats: RequirementsStats
  testStats: TestStats
}

export default function StatsCards({ reqStats, testStats }: Props) {
  const acCoverage = reqStats.total > 0
    ? Math.round((reqStats.acDefined / reqStats.total) * 100)
    : 0

  const testPassRate = testStats.total > 0
    ? Math.round((testStats.passed / testStats.total) * 100)
    : 0

  return (
    <div className="space-y-4">
      {/* 요구사항 현황 */}
      <div>
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          요구사항 현황
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <StatCard
            icon={<Layers className="w-5 h-5" />}
            label="REQ 그룹"
            value={reqStats.groups}
            sub="REQ-NNN"
            color="blue"
          />
          <StatCard
            icon={<FileText className="w-5 h-5" />}
            label="상세 요구사항"
            value={reqStats.total}
            sub="REQ-NNN-NN"
          />
          <StatCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="구현완료"
            value={reqStats.implemented}
            sub={`/ ${reqStats.total}건`}
            color={reqStats.implemented === reqStats.total && reqStats.total > 0 ? 'green' : 'yellow'}
          />
          <StatCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="AC 정의 완료"
            value={reqStats.acDefined}
            sub={`/ ${reqStats.total}건`}
            color={reqStats.missing.length === 0 && reqStats.total > 0 ? 'green' : 'yellow'}
          />
          <StatCard
            icon={reqStats.missing.length > 0
              ? <AlertCircle className="w-5 h-5" />
              : <CheckCircle className="w-5 h-5" />
            }
            label="AC 커버리지"
            value={`${acCoverage}%`}
            sub={reqStats.missing.length > 0 ? `미정의 ${reqStats.missing.length}건` : '완전 커버'}
            color={reqStats.missing.length === 0 && reqStats.total > 0 ? 'green' : 'yellow'}
          />
        </div>

        {/* AC 미정의 목록 */}
        {reqStats.missing.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {reqStats.missing.map(id => (
              <span key={id} className="text-xs bg-yellow-950/50 text-yellow-400 border border-yellow-800/50 px-2 py-0.5 rounded">
                {id} AC 없음
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 테스트 현황 */}
      <div>
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          테스트 현황
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard
            icon={<FlaskConical className="w-5 h-5" />}
            label="전체 테스트"
            value={testStats.total}
            sub="TST-ID"
            color="blue"
          />
          <StatCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="통과"
            value={testStats.passed}
            sub={testStats.total > 0 ? `${testPassRate}%` : '-'}
            color={testStats.passed > 0 ? 'green' : 'default'}
          />
          <StatCard
            icon={<XCircle className="w-5 h-5" />}
            label="실패"
            value={testStats.failed}
            color={testStats.failed > 0 ? 'red' : 'default'}
          />
          <StatCard
            icon={<AlertCircle className="w-5 h-5" />}
            label="미실행"
            value={testStats.total - testStats.passed - testStats.failed - testStats.skipped}
            sub={testStats.skipped > 0 ? `Skip ${testStats.skipped}건` : undefined}
            color="yellow"
          />
        </div>
      </div>
    </div>
  )
}
