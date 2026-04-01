// Server Component — marked는 서버에서만 실행 (hydration 불일치 방지)
export default function DocViewer({ html }: { html: string }) {
  return (
    <article
      className="prose prose-invert prose-sm max-w-none
        prose-headings:text-white
        prose-p:text-gray-300
        prose-li:text-gray-300
        prose-td:text-gray-300
        prose-th:text-gray-200
        prose-code:text-blue-300
        prose-pre:bg-gray-900
        prose-blockquote:border-gray-600
        prose-blockquote:text-gray-400
        prose-a:text-blue-400
        prose-strong:text-white
        prose-table:text-sm"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
