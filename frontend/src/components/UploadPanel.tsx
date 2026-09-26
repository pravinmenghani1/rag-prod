import { useState } from 'react'

interface UploadPanelProps {
  onPreload: () => void
}

export default function UploadPanel({ onPreload }: UploadPanelProps) {
  const [uploading, setUploading] = useState(false)
  const [preloading, setPreloading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const [status, setStatus] = useState('')

  async function handlePreload() {
    setPreloading(true)
    setStatus('Loading synthetic documents into Qdrant...')
    try {
      const res = await fetch('/api/ingest/preload', { method: 'POST' })
      const data = await res.json()
      const names = data.documents?.map((d: { filename: string }) => d.filename) ?? []
      setUploadedFiles(names)
      setStatus(`✓ Loaded ${names.length} documents into vector DB`)
      onPreload()
    } catch (e) {
      setStatus(`✗ Error: ${e}`)
    } finally {
      setPreloading(false)
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    const results: string[] = []
    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      try {
        const res = await fetch('/api/ingest', { method: 'POST', body: formData })
        const data = await res.json()
        results.push(`✓ ${data.filename} (${data.chunks} chunks)`)
      } catch {
        results.push(`✗ ${file.name} failed`)
      }
    }
    setUploadedFiles(prev => [...prev, ...results])
    setStatus(`Uploaded ${results.length} file(s)`)
    setUploading(false)
    onPreload()
    e.target.value = ''
  }

  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-blue-400">📄</span> Documents
      </h2>

      {/* Preload button */}
      <button
        onClick={handlePreload}
        disabled={preloading}
        className="w-full mb-3 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg font-medium transition-colors text-sm"
      >
        {preloading ? '⏳ Loading...' : '🚀 Load Synthetic Docs'}
      </button>

      {/* File upload */}
      <label className="block w-full cursor-pointer">
        <div className="border-2 border-dashed border-gray-700 hover:border-blue-500 rounded-lg p-4 text-center transition-colors">
          <p className="text-sm text-gray-400">
            {uploading ? '⏳ Uploading...' : 'Drop .txt files here or click to upload'}
          </p>
        </div>
        <input
          type="file"
          accept=".txt"
          multiple
          className="hidden"
          onChange={handleFileUpload}
          disabled={uploading}
        />
      </label>

      {/* Status */}
      {status && (
        <p className="mt-3 text-xs text-green-400">{status}</p>
      )}

      {/* File list */}
      {uploadedFiles.length > 0 && (
        <ul className="mt-3 space-y-1">
          {uploadedFiles.map((f, i) => (
            <li key={i} className="text-xs text-gray-400 bg-gray-800 rounded px-3 py-1.5 truncate">
              {f}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
