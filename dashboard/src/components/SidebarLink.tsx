'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface Props {
  href: string
  children: React.ReactNode
}

export default function SidebarLink({ href, children }: Props) {
  const pathname = usePathname()
  const isActive = pathname === href

  return (
    <Link
      href={href}
      className={`block px-3 py-1.5 rounded text-sm transition-colors truncate
        ${isActive
          ? 'bg-blue-600 text-white'
          : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
        }`}
    >
      {children}
    </Link>
  )
}
