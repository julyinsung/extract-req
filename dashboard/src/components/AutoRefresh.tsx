'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function AutoRefresh() {
  const router = useRouter()

  useEffect(() => {
    const es = new EventSource('/api/watch')

    es.onmessage = (e) => {
      if (e.data === 'reload') {
        router.refresh()
      }
    }

    es.onerror = () => {
      // 연결 끊기면 자동 재접속 (EventSource 기본 동작)
    }

    return () => es.close()
  }, [router])

  return null
}
