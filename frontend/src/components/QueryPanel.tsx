import { useState, useCallback } from 'react'

interface PipelineEvent {
  type: 'stage' | 'token'
  stage?: string
  message?: string
  token?: string
  [key: string]: unknown
}

interface QueryPanelProps {
  onEvents: (events: PipelineEvent[]) => void
  onResponse: (text: string) => void
  onRunningChange: (running: boolean) => void
}

const EXAMPLE_QUERIES = [
  'What causes climate change?',
  'How does machine learning work?',
  'What is quantum computing?',
  'What are the health benefits of the Mediterranean diet?',
  'How was the internet invented?',
  'What are the challenges of long-duration space travel?',
]

export default function QueryPanel({ onEvents, onResponse, onRunningChange }: QueryPanelProps) {
  const [query, setQuery] = useState('')
  const [isRunning, setIsRunning] = useState(false)

  const runQuery = useCallback(async (q: string) => {
    if (!q.trim() || isRunning) return

    setIsRunning(true)
    onRunningChange(true)
    onEvents([])
    onResponse('')

    const events: PipelineEvent[] = []
    let fullResponse = ''

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      if (!res.body) throw new Error('No response body')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event: PipelineEvent = JSON.parse(line.slice(6))
            if (event.type === 'token') {
              fullResponse += event.token ?? ''
              onResponse(fullResponse)
            } else {
              events.push(event)
              onEvents([...events])
            }
          } catch {
            // ignore malformed SSE lines
          }
        }
      }
    } catch (e) {
      events.push({ type: 'stage', stage: 'error', message: String(e) })
      onEvents([...events])
    } finally {
      setIsRunning(false)
      onRunningChange(false)
    }
  }, [isRunning, onEvents, onResponse, onRunningChange])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    runQuery(query)
  }

  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-purple-400">🔍</span> Query
      </h2>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Ask a question about the uploaded documents..."
          disabled={isRunning}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isRunning || !query.trim()}
          className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg font-medium text-sm transition-colors flex items-center gap-2"
        >
          {isRunning ? (
            <>
              <span className="animate-spin">⟳</span> Running
            </>
          ) : (
            <>Send</>
          )}
        </button>
      </form>

      {/* Example queries */}
      <div className="mt-3">
        <p className="text-xs text-gray-500 mb-2">Try:</p>
        <div className="flex flex-wrap gap-1.5">
          {EXAMPLE_QUERIES.map(q => (
            <button
              key={q}
              onClick={() => { setQuery(q); runQuery(q) }}
              disabled={isRunning}
              className="text-xs px-3 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-full transition-colors disabled:opacity-40"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
