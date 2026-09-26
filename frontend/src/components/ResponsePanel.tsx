interface ResponsePanelProps {
  response: string
  isStreaming: boolean
}

export default function ResponsePanel({ response, isStreaming }: ResponsePanelProps) {
  if (!response && !isStreaming) return null

  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-pink-400">🤖</span> LLM Response
        {isStreaming && (
          <span className="ml-auto flex items-center gap-1.5 text-xs text-pink-400">
            <span className="animate-pulse w-2 h-2 rounded-full bg-pink-400 inline-block" />
            Streaming
          </span>
        )}
      </h2>

      <div className="bg-gray-950 rounded-lg p-4 border border-gray-800 min-h-[80px]">
        {response ? (
          <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
            {response}
            {isStreaming && <span className="animate-pulse text-pink-400">▋</span>}
          </p>
        ) : (
          <div className="flex items-center gap-2 text-gray-600 text-sm">
            <span className="animate-spin">⟳</span>
            Waiting for LLM...
          </div>
        )}
      </div>
    </div>
  )
}
