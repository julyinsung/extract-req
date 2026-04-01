import { readDoc } from '@/lib/project'
import DocViewer from '@/components/DocViewer'
import MermaidRenderer from '@/components/MermaidRenderer'
import { notFound } from 'next/navigation'
import ExportButton from '@/components/ExportButton'
import { marked } from 'marked'

export const dynamic = 'force-dynamic'

interface Props {
  params: Promise<{ slug: string[] }>
}

export default async function DocPage({ params }: Props) {
  const { slug } = await params
  const content = readDoc(slug)
  if (!content) notFound()

  // marked는 서버(Server Component)에서만 실행 → hydration 불일치 없음
  const html = marked(content, { gfm: true }) as string
  const title = slug[slug.length - 1].replace('.md', '')

  return (
    <main className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6 no-print">
        <h1 className="text-lg font-semibold text-gray-300">{title}</h1>
        <ExportButton />
      </div>
      <DocViewer html={html} />
      <MermaidRenderer />
    </main>
  )
}
