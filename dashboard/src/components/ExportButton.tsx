'use client'

import { Printer } from 'lucide-react'

export default function ExportButton() {
  return (
    <button
      onClick={() => window.print()}
      className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-400
        hover:text-gray-100 hover:bg-gray-800 rounded transition-colors no-print"
    >
      <Printer className="w-4 h-4" />
      PDF 저장
    </button>
  )
}
