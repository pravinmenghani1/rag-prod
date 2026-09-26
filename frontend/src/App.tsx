import { useState, useCallback } from 'react'
import UploadPanel from './components/UploadPanel'
import QueryPanel from './components/QueryPanel'
import PipelineTrace from './components/PipelineTrace'
import MetricsPanel from './components/MetricsPanel'
import ResponsePanel from './components/ResponsePanel'

interface PipelineEvent {
  type: 'stage' | 'token'
  stage?: string
  message?: string
  token?: string
  ground_truth_found?: boolean
  precision_at_k?: number | null
  recall_at_k?: number | null
  ndcg_at_k?: number | null
  k?: number
  relevant_doc_ids?: string[]
  retrieved_doc_ids?: string[]
  query_id?: string
  [key: string]: unknown
}

interface MetricsData {
  ground_truth_found: boolean
  precision_at_k?: number | null
  recall_at_k?: number | null
  ndcg_at_k?: number | null
  k?: number
  relevant_doc_ids?: string[]
  retrieved_doc_ids?: string[]
  query_id?: string
}

export default function App() {
  const [events, setEvents] = useState<PipelineEvent[]>([])
  const [response, setResponse] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [_docsLoaded, setDocsLoaded] = useState(false)

  const handleEvents = useCallback((newEvents: PipelineEvent[]) => {
    setEvents(newEvents)
    // Extract metrics when they arrive
    const metricsEvent = newEvents.find(e => e.stage === 'metrics')
    if (metricsEvent) {
      setMetrics({
        ground_truth_found: metricsEvent.ground_truth_found ?? false,
        precision_at_k: metricsEvent.precision_at_k as number | null,
        recall_at_k: metricsEvent.recall_at_k as number | null,
        ndcg_at_k: metricsEvent.ndcg_at_k as number | null,
        k: metricsEvent.k as number,
        relevant_doc_ids: metricsEvent.relevant_doc_ids as string[],
        retrieved_doc_ids: metricsEvent.retrieved_doc_ids as string[],
        query_id: metricsEvent.query_id as string,
      })
    }
  }, [])

  const handleRunningChange = useCallback((running: boolean) => {
    setIsRunning(running)
    if (running) {
      setMetrics(null)
      setResponse('')
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="text-2xl">⚡</div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">RAG Portal</h1>
            <p className="text-xs text-gray-500">Hybrid Search · Reranker · Metrics · LLM</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs text-gray-400">Ollama connected</span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-5">
          {/* Left sidebar */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            <UploadPanel onPreload={() => setDocsLoaded(true)} />
            {metrics && <MetricsPanel metrics={metrics} />}
          </div>

          {/* Main content */}
          <div className="col-span-12 lg:col-span-9 space-y-5">
            <QueryPanel
              onEvents={handleEvents}
              onResponse={setResponse}
              onRunningChange={handleRunningChange}
            />

            {(response || isRunning) && (
              <ResponsePanel response={response} isStreaming={isRunning} />
            )}

            <PipelineTrace events={events} isRunning={isRunning} />
          </div>
        </div>
      </div>
    </div>
  )
}
