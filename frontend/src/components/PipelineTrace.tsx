interface ChunkResult {
  rank: number
  score?: number
  rrf_score?: number
  rerank_score?: number
  doc_id: string
  text: string
}

interface PipelineEvent {
  type: 'stage' | 'token'
  stage?: string
  message?: string
  results?: ChunkResult[]
  token?: string
  ground_truth_found?: boolean
  precision_at_k?: number | null
  recall_at_k?: number | null
  ndcg_at_k?: number | null
  [key: string]: unknown
}

interface PipelineTraceProps {
  events: PipelineEvent[]
  isRunning: boolean
}

const STAGE_ICONS: Record<string, string> = {
  query_received: '🔍',
  retrieval_running: '⚙️',
  retrieval_semantic: '🧠',
  retrieval_bm25: '📊',
  retrieval_fused: '🔀',
  metrics: '📈',
  reranking_start: '⏳',
  reranking_done: '✅',
  llm_start: '🤖',
  done: '🏁',
  error: '❌',
}

const STAGE_COLORS: Record<string, string> = {
  query_received: 'border-blue-500 bg-blue-950',
  retrieval_running: 'border-yellow-500 bg-yellow-950',
  retrieval_semantic: 'border-purple-500 bg-purple-950',
  retrieval_bm25: 'border-orange-500 bg-orange-950',
  retrieval_fused: 'border-cyan-500 bg-cyan-950',
  metrics: 'border-green-500 bg-green-950',
  reranking_start: 'border-yellow-500 bg-yellow-950',
  reranking_done: 'border-emerald-500 bg-emerald-950',
  llm_start: 'border-pink-500 bg-pink-950',
  done: 'border-green-400 bg-green-950',
  error: 'border-red-500 bg-red-950',
}

function ResultList({ results }: { results: ChunkResult[] }) {
  return (
    <div className="mt-2 space-y-1">
      {results.map((r) => (
        <div key={r.rank} className="bg-black/30 rounded px-3 py-2 text-xs">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-yellow-400 font-mono">#{r.rank}</span>
            <span className="text-blue-300 font-medium">{r.doc_id}</span>
            {r.rrf_score !== undefined && (
              <span className="text-gray-400 ml-auto">RRF: {r.rrf_score.toFixed(4)}</span>
            )}
            {r.rerank_score !== undefined && (
              <span className="text-emerald-400 ml-auto">↑ {r.rerank_score.toFixed(4)}</span>
            )}
            {r.score !== undefined && r.rrf_score === undefined && r.rerank_score === undefined && (
              <span className="text-gray-400 ml-auto">{r.score.toFixed(4)}</span>
            )}
          </div>
          <p className="text-gray-300 line-clamp-2">{r.text}</p>
        </div>
      ))}
    </div>
  )
}

export default function PipelineTrace({ events, isRunning }: PipelineTraceProps) {
  const stageEvents = events.filter(e => e.type === 'stage')

  if (stageEvents.length === 0 && !isRunning) return null

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800 flex items-center gap-2">
        <span className="text-blue-400">⚡</span>
        <h2 className="text-lg font-semibold text-white">Pipeline Trace</h2>
        {isRunning && (
          <span className="ml-auto flex items-center gap-1.5 text-xs text-yellow-400">
            <span className="animate-pulse w-2 h-2 rounded-full bg-yellow-400 inline-block" />
            Running
          </span>
        )}
      </div>

      <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
        {stageEvents.map((event, i) => {
          const stage = event.stage ?? ''
          const colorClass = STAGE_COLORS[stage] ?? 'border-gray-600 bg-gray-800'
          const icon = STAGE_ICONS[stage] ?? '•'

          return (
            <div key={i} className={`border-l-4 rounded-r-lg px-4 py-3 ${colorClass}`}>
              <div className="flex items-start gap-2">
                <span className="text-base mt-0.5">{icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-gray-400 uppercase tracking-wide">
                      {stage.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-sm text-gray-200">{event.message}</p>

                  {/* Metrics display */}
                  {stage === 'metrics' && event.ground_truth_found && (
                    <div className="mt-2 flex gap-4">
                      <MetricBadge label="Precision@K" value={(event.precision_at_k ?? null) as number | null} />
                      <MetricBadge label="Recall@K" value={(event.recall_at_k ?? null) as number | null} />
                      <MetricBadge label="nDCG@K" value={(event.ndcg_at_k ?? null) as number | null} />
                    </div>
                  )}
                  {stage === 'metrics' && event.ground_truth_found === false && (
                    <p className="text-xs text-gray-500 mt-1">No ground truth match for this query.</p>
                  )}

                  {/* Result lists */}
                  {event.results && Array.isArray(event.results) && event.results.length > 0 && (
                    <ResultList results={event.results as ChunkResult[]} />
                  )}
                </div>
              </div>
            </div>
          )
        })}

        {isRunning && (
          <div className="flex items-center gap-2 text-sm text-gray-500 px-2">
            <span className="animate-spin">⟳</span> Processing...
          </div>
        )}
      </div>
    </div>
  )
}

function MetricBadge({ label, value }: { label: string; value: number | null }) {
  const pct = value !== null ? Math.round(value * 100) : null
  const color = pct === null
    ? 'text-gray-400'
    : pct >= 80 ? 'text-green-400' : pct >= 50 ? 'text-yellow-400' : 'text-red-400'
  return (
    <div className="bg-black/30 rounded px-3 py-1.5 text-center">
      <p className={`text-lg font-bold font-mono ${color}`}>
        {pct !== null ? `${pct}%` : 'N/A'}
      </p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}
