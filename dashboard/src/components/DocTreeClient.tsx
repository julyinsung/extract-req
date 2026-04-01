'use client'

import { useState } from 'react'
import { ChevronRight, ChevronDown, FileText, Folder, FolderOpen } from 'lucide-react'
import SidebarLink from './SidebarLink'
import type { DocNode } from '@/lib/project'

function DocTreeNode({ node, depth = 0 }: { node: DocNode; depth?: number }) {
  const [open, setOpen] = useState(depth === 0)

  if (node.type === 'file') {
    return (
      <SidebarLink href={`/docs/${node.slug.join('/')}`}>
        <span className="flex items-center gap-1.5" style={{ paddingLeft: depth * 12 }}>
          <FileText className="w-3 h-3 flex-shrink-0 opacity-60" />
          <span className="truncate">{node.name}</span>
        </span>
      </SidebarLink>
    )
  }

  return (
    <div>
      <button
        onClick={() => setOpen(prev => !prev)}
        className="w-full flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold
          text-gray-500 hover:text-gray-300 transition-colors rounded hover:bg-gray-800"
        style={{ paddingLeft: `${12 + depth * 12}px` }}
      >
        {open
          ? <ChevronDown className="w-3 h-3 flex-shrink-0" />
          : <ChevronRight className="w-3 h-3 flex-shrink-0" />
        }
        {open
          ? <FolderOpen className="w-3 h-3 flex-shrink-0" />
          : <Folder className="w-3 h-3 flex-shrink-0" />
        }
        <span className="uppercase tracking-wide truncate">{node.name}</span>
      </button>

      {open && node.children && (
        <ul className="space-y-0.5">
          {node.children.map(child => (
            <li key={child.slug.join('/')}>
              <DocTreeNode node={child} depth={depth + 1} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function DocTreeClient({ nodes }: { nodes: DocNode[] }) {
  return (
    <ul className="space-y-0.5">
      {nodes.map(node => (
        <li key={node.slug.join('/')}>
          <DocTreeNode node={node} depth={0} />
        </li>
      ))}
    </ul>
  )
}
