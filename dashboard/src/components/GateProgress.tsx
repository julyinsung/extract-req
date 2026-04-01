import { Session } from '@/lib/project'
import { CheckCircle, AlertCircle } from 'lucide-react'

const GATES = [
  { key: 'gate1', label: 'Gate 1', sub: '요구사항' },
  { key: 'gate2', label: 'Gate 2', sub: '설계' },
  { key: 'gate3', label: 'Gate 3', sub: '테스트 플랜' },
  { key: 'impl',  label: '구현',   sub: 'FE + BE' },
  { key: 'gate4', label: 'Gate 4', sub: 'QA 검토' },
  { key: 'gate5', label: 'Gate 5', sub: '최종 승인' },
]

export default function GateProgress({ session }: { session: Session }) {
  return (
    <div className="space-y-10">
      {/* 프로젝트 헤더 */}
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Vulcan Anvil</p>
        <h1 className="text-3xl font-bold text-white">{session.project}</h1>
        {session.feature && (
          <p className="text-gray-400 mt-2 text-sm">{session.feature}</p>
        )}
        {session.started && (
          <p className="text-gray-600 text-xs mt-1">시작일: {session.started}</p>
        )}
      </div>

      {/* Gate 진행 바 */}
      <div>
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">Gate 진행 현황</h2>
        <div className="flex items-start">
          {GATES.map((gate, i) => {
            const isImpl = gate.key === 'impl'
            const status = session.gate_status[gate.key]
            const isDone = status === 'done'
            const isCurrent = session.current_gate === gate.key

            return (
              <div key={gate.key} className="flex items-start">
                <div className="flex flex-col items-center gap-2">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-colors
                      ${isDone
                        ? 'bg-green-500 text-white'
                        : isCurrent
                          ? 'bg-blue-500 text-white ring-2 ring-blue-400 ring-offset-2 ring-offset-gray-950'
                          : isImpl
                            ? 'bg-gray-700 text-gray-400'
                            : 'bg-gray-800 text-gray-500'
                      }`}
                  >
                    {isDone ? '✓' : i + 1}
                  </div>
                  <div className="text-center">
                    <div className={`text-xs font-medium ${isCurrent ? 'text-blue-400' : isDone ? 'text-green-400' : 'text-gray-500'}`}>
                      {gate.label}
                    </div>
                    <div className="text-xs text-gray-600">{gate.sub}</div>
                  </div>
                </div>
                {i < GATES.length - 1 && (
                  <div className={`h-0.5 w-10 mt-5 mx-1 ${isDone ? 'bg-green-500' : 'bg-gray-800'}`} />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Blocked */}
      {session.blocked.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold text-red-400 uppercase tracking-wide mb-3">Blocked</h2>
          <ul className="space-y-2">
            {session.blocked.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-red-300 bg-red-950/30 rounded-lg px-4 py-3">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 완료 목록 */}
      {session.completed.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">완료</h2>
          <ul className="space-y-1.5">
            {session.completed.map((item, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-gray-400">
                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
