import type { Metadata } from 'next'
import './globals.css'
import fs from 'fs'
import path from 'path'
import { readSession, buildDocTree, PROJECT_ROOT } from '@/lib/project'
import Sidebar from '@/components/Sidebar'
import AutoRefresh from '@/components/AutoRefresh'

export const metadata: Metadata = {
  title: 'Anvil Dashboard',
  description: 'Vulcan-Claude-Anvil Project Dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const session = readSession()
  const docs = buildDocTree(path.join(PROJECT_ROOT, 'docs'))

  // 프로젝트 루트의 주요 .md 파일도 포함
  const rootFiles = ['ENVIRONMENT.md', 'GATE_GUIDE.md', 'commenting-standards.md']
  const rootDocs = rootFiles
    .filter(f => fs.existsSync(path.join(PROJECT_ROOT, f)))
    .map(f => ({ name: f.replace('.md', ''), slug: ['_root', f], type: 'file' as const }))

  return (
    <html lang="ko">
      <body className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
        <AutoRefresh />
        <Sidebar session={session} docs={docs} rootDocs={rootDocs} />
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </body>
    </html>
  )
}
