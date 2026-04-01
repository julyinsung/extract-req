import { readSession, parseRequirementsStats, parseTestStats } from '@/lib/project'
import GateProgress from '@/components/GateProgress'
import StatsCards from '@/components/StatsCards'

export const dynamic = 'force-dynamic'

export default function Home() {
  const session  = readSession()
  const reqStats = parseRequirementsStats()
  const testStats = parseTestStats()

  return (
    <main className="p-8 max-w-4xl space-y-10">
      <GateProgress session={session} />
      <StatsCards reqStats={reqStats} testStats={testStats} />
    </main>
  )
}
