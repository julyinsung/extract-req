import { readSession, parseRequirementsStats, parseTestStats, readGitTimeline, readDesignDocs, readQAResults } from '@/lib/project'
import GateProgress from '@/components/GateProgress'
import StatsCards from '@/components/StatsCards'
import CurrentGatePanel from '@/components/CurrentGatePanel'
import GitTimeline from '@/components/GitTimeline'

export const dynamic = 'force-dynamic'

export default function Home() {
  const session     = readSession()
  const reqStats    = parseRequirementsStats()
  const testStats   = parseTestStats()
  const gitEntries  = readGitTimeline()
  const designDocs  = readDesignDocs()
  const qaResults   = readQAResults()

  return (
    <main className="p-8 max-w-4xl space-y-10">
      <GateProgress session={session} />
      <CurrentGatePanel
        session={session}
        reqStats={reqStats}
        testStats={testStats}
        designDocs={designDocs}
        qaResults={qaResults}
      />
      <StatsCards reqStats={reqStats} testStats={testStats} />
      <GitTimeline entries={gitEntries} />
    </main>
  )
}
