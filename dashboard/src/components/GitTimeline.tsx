import { GitEntry } from '@/lib/project'
import { RotateCcw, GitCommit, Rocket } from 'lucide-react'

interface Props {
  entries: GitEntry[]
}

const TYPE_META = {
  session:  { icon: GitCommit,  color: 'text-blue-400',   dot: 'bg-blue-500',   label: 'session'  },
  rollback: { icon: RotateCcw,  color: 'text-yellow-400', dot: 'bg-yellow-500', label: 'rollback' },
  init:     { icon: Rocket,     color: 'text-green-400',  dot: 'bg-green-500',  label: 'init'     },
}

function formatMessage(message: string): string {
  // "session: gate2 done - Gate 2 설계 (기능명)" → "Gate 2 설계 done (기능명)"
  // "rollback: gate2부터 재시작 - Gate 2 설계 (사유)" → "Gate 2 설계 롤백 (사유)"
  return message
    .replace(/^session:\s*/, '')
    .replace(/^rollback:\s*/, '')
    .replace(/^init:\s*/, '')
    .trim()
}

export default function GitTimeline({ entries }: Props) {
  if (entries.length === 0) return null

  return (
    <div>
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">Gate 히스토리</h2>
      <div className="relative">
        {/* 세로선 */}
        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-gray-800" />

        <ul className="space-y-4">
          {entries.map((entry, i) => {
            const meta = TYPE_META[entry.type]
            const Icon = meta.icon
            return (
              <li key={i} className="flex items-start gap-3 pl-1">
                {/* 도트 */}
                <div className={`w-3.5 h-3.5 rounded-full flex-shrink-0 mt-0.5 border-2 border-gray-950 ${meta.dot}`} />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${meta.color}`} />
                    <span className="text-sm text-gray-300 truncate">{formatMessage(entry.message)}</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-0.5 pl-5">{entry.date}</div>
                </div>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
