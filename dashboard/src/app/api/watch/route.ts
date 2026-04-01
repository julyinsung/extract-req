import { NextResponse } from 'next/server'
import path from 'path'
import { PROJECT_ROOT } from '@/lib/project'

let chokidar: typeof import('chokidar') | null = null

async function getChokidar() {
  if (!chokidar) {
    chokidar = await import('chokidar')
  }
  return chokidar
}

export async function GET() {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      const send = (event: string) => {
        controller.enqueue(encoder.encode(`data: ${event}\n\n`))
      }

      try {
        const { watch } = await getChokidar()
        const watcher = watch(
          [
            path.join(PROJECT_ROOT, 'session.json'),
            path.join(PROJECT_ROOT, 'docs'),
          ],
          {
            ignoreInitial: true,
            awaitWriteFinish: { stabilityThreshold: 300, pollInterval: 100 },
          },
        )

        let debounceTimer: ReturnType<typeof setTimeout> | null = null

        const notify = () => {
          if (debounceTimer) clearTimeout(debounceTimer)
          debounceTimer = setTimeout(() => {
            try {
              send('reload')
            } catch {
              // stream closed
            }
          }, 500)
        }

        watcher.on('add', notify)
        watcher.on('change', notify)
        watcher.on('unlink', notify)

        // cleanup when client disconnects
        const cleanup = () => {
          if (debounceTimer) clearTimeout(debounceTimer)
          watcher.close()
        }

        // keep-alive ping every 30s
        const keepAlive = setInterval(() => {
          try {
            controller.enqueue(encoder.encode(': ping\n\n'))
          } catch {
            clearInterval(keepAlive)
            cleanup()
          }
        }, 30000)
      } catch {
        send('error')
        controller.close()
      }
    },
  })

  return new NextResponse(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
