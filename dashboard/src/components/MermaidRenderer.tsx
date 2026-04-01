'use client'

import { useEffect } from 'react'
import mermaid from 'mermaid'

export default function MermaidRenderer() {
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      darkMode: true,
      themeVariables: {
        background: '#111827',
        primaryColor: '#3b82f6',
        primaryTextColor: '#f3f4f6',
        lineColor: '#6b7280',
        edgeLabelBackground: '#1f2937',
        clusterBkg: '#1f2937',
        titleColor: '#f3f4f6',
      },
    })

    const blocks = document.querySelectorAll('pre code.language-mermaid')
    blocks.forEach(async (el) => {
      const code = el.textContent || ''
      const pre = el.parentElement
      if (!pre) return

      try {
        const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`
        const { svg } = await mermaid.render(id, code)
        const wrapper = document.createElement('div')
        wrapper.className = 'my-6 flex justify-center overflow-x-auto rounded-lg bg-gray-900 p-4'
        wrapper.innerHTML = svg
        pre.replaceWith(wrapper)
      } catch (e) {
        console.error('[MermaidRenderer] 렌더 실패:', e)
      }
    })
  }, [])

  return null
}
