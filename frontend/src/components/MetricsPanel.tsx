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

interface MetricsPanelProps {
  metrics: MetricsData | null
}

function Gauge({ value, label }: { value: number | null | undefined; label: string }) {
  const pct = value != null ? Math.round(value * 100) : null
  const color = pct == null
    ? 'text-gray-500'
    : pct >= 80
    ? 'text-green-400'
    : pct >= 50
    ? 'text-yellow-400'
    : 'text-red-400'
  const ring = pct == null
    ? 'border-gray-700'
    : pct >= 80
    ? 'border-green-500'
    : pct >= 50
    ? 'border-yellow-500'
    : 'border-red-500'

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`w-16 h-16 rounded-full border-4 ${ring} flex items-center justify-center`}>
        <span className={`text-lg font-bold font-mono ${color}`}>
          {pct != null ? `${pct}%` : '–'}
        </span>
      </div>
      <span className="text-xs text-gray-400 text-center">{label}</span>
    </div>
  )
}

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  if (!metrics) return null

  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-green-400">📈</span> Retrieval Metrics
        {metrics.k && (
          <span className="ml-auto text-xs text-gray-500 font-normal">@K={metrics.k}</span>
        )}
      </h2>

      {!metrics.ground_truth_found ? (
        <p className="text-sm text-gray-500 italic">
          No ground truth found for this query. Add it to ground_truth.json to see metrics.
        </p>
      ) : (
        <>
          <div className="flex justify-around mb-5">
            <Gauge value={metrics.precision_at_k} label="Precision@K" />
            <Gauge value={metrics.recall_at_k} label="Recall@K" />
            <Gauge value={metrics.ndcg_at_k} label="nDCG@K" />
          </div>

          <div className="space-y-2 text-xs">
            {metrics.query_id && (
              <div className="flex gap-2">
                <span className="text-gray-500 w-32 shrink-0">Query ID:</span>
                <span className="text-gray-300 font-mono">{metrics.query_id}</span>
              </div>
            )}
            {metrics.relevant_doc_ids && (
              <div className="flex gap-2">
                <span className="text-gray-500 w-32 shrink-0">Relevant docs:</span>
                <span className="text-green-400 font-mono">{metrics.relevant_doc_ids.join(', ')}</span>
              </div>
            )}
            {metrics.retrieved_doc_ids && (
              <div className="flex gap-2">
                <span className="text-gray-500 w-32 shrink-0">Retrieved docs:</span>
                <div className="flex flex-wrap gap-1">
                  {metrics.retrieved_doc_ids.map(id => (
                    <span
                      key={id}
                      className={`px-2 py-0.5 rounded font-mono ${
                        metrics.relevant_doc_ids?.includes(id)
                          ? 'bg-green-900 text-green-300'
                          : 'bg-gray-800 text-gray-400'
                      }`}
                    >
                      {id}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
