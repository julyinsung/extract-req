import { Session, DocNode } from '@/lib/project'
import SidebarLink from './SidebarLink'
import ExportButton from './ExportButton'
import DocTreeClient from './DocTreeClient'
import { LayoutDashboard } from 'lucide-react'
import AnvilIcon from './AnvilIcon'

const GATE_LABELS: Record<string, string> = {
  gate1: 'Gate 1 — 요구사항',
  gate2: 'Gate 2 — 설계',
  gate3: 'Gate 3 — 테스트 플랜',
  gate4: 'Gate 4 — QA 검토',
  gate5: 'Gate 5 — 최종 승인',
  completed: '완료',
}

interface Props {
  session: Session
  docs: DocNode[]
  rootDocs?: DocNode[]
}

export default function Sidebar({ session, docs, rootDocs = [] }: Props) {
  const currentLabel = GATE_LABELS[session.current_gate] ?? session.current_gate

  return (
    <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col h-full overflow-hidden flex-shrink-0">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-1.5 text-xs text-gray-500 font-semibold uppercase tracking-widest">
          <AnvilIcon className="w-4 h-4 text-amber-500" />
          Vulcan Anvil
        </div>
        <div className="text-sm font-bold text-white mt-1 truncate">{session.project}</div>
        <div className="text-xs text-blue-400 mt-0.5 truncate">{currentLabel}</div>
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* 대시보드 */}
        <div>
          <SidebarLink href="/">
            <span className="flex items-center gap-2">
              <LayoutDashboard className="w-4 h-4" />
              대시보드
            </span>
          </SidebarLink>
        </div>

        {/* 문서 트리 */}
        {docs.length > 0 && (
          <div>
            <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              문서
            </div>
            <DocTreeClient nodes={docs} />
          </div>
        )}

        {/* 프로젝트 참조 문서 */}
        {rootDocs.length > 0 && (
          <div>
            <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              참조
            </div>
            <DocTreeClient nodes={rootDocs} />
          </div>
        )}
      </nav>

      {/* 푸터 */}
      <div className="p-3 border-t border-gray-800 space-y-1">
        {session.vulcan_version && (
          <div className="text-xs text-gray-600 px-3">v{session.vulcan_version}</div>
        )}
        <ExportButton />
      </div>
    </aside>
  )
}
