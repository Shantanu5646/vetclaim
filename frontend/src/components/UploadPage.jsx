import { useState, useRef } from 'react'

// Pure helper — exported for property-based testing (Property 7)
export function filterPdfs(files) {
  return Array.from(files).filter(f => f.type === 'application/pdf')
}

// Recursively collect all PDF File objects from a FileSystemEntry
async function collectPdfsFromEntry(entry) {
  if (entry.isFile) {
    return new Promise((resolve) => {
      entry.file((file) => {
        resolve(file.type === 'application/pdf' ? [file] : [])
      }, () => resolve([]))
    })
  }

  if (entry.isDirectory) {
    const reader = entry.createReader()
    const allFiles = []
    // readEntries may return results in batches; keep reading until empty
    const readBatch = () =>
      new Promise((resolve, reject) => reader.readEntries(resolve, reject))

    let batch
    do {
      batch = await readBatch()
      for (const child of batch) {
        const childFiles = await collectPdfsFromEntry(child)
        allFiles.push(...childFiles)
      }
    } while (batch.length > 0)

    return allFiles
  }

  return []
}

export default function UploadPage({ onBack, onSubmit }) {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef()

  const addPdfs = (newFiles) => {
    const pdfs = filterPdfs(newFiles)
    setFiles(prev => [...prev, ...pdfs])
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    setDragging(false)
    setError(null)

    const items = Array.from(e.dataTransfer.items)
    const pdfs = []

    for (const item of items) {
      if (item.kind !== 'file') continue
      const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null
      if (entry) {
        const collected = await collectPdfsFromEntry(entry)
        pdfs.push(...collected)
      } else {
        // Fallback: no FileSystem API support
        const file = item.getAsFile()
        if (file && file.type === 'application/pdf') pdfs.push(file)
      }
    }

    setFiles(prev => [...prev, ...pdfs])
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    if (files.length === 0 || submitting) return
    setSubmitting(true)
    setError(null)

    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (res.status === 202) {
        const data = await res.json()
        onSubmit(data.job_id)
      } else {
        const data = await res.json().catch(() => ({}))
        setError(data.error || `Upload failed (HTTP ${res.status})`)
      }
    } catch (err) {
      setError('Network error — could not reach the server. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0B1426] flex flex-col">
      {/* Header */}
      <header className="flex items-center gap-4 px-8 py-5 border-b border-[#1E3A6E]/50">
        <button
          onClick={onBack}
          className="text-[#8A9BB5] hover:text-white transition-colors flex items-center gap-2 text-sm"
        >
          ← Back
        </button>
        <span className="text-[#C9A84C] font-black text-lg tracking-widest uppercase">VetClaim</span>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-6 py-12">
        <div className="fade-in-up">
          <h2 className="text-3xl font-bold text-white mb-2">Upload All Required VA Documents</h2>
          <p className="text-[#8A9BB5] mb-10">Upload your C&P Exam, DBQ, Rating Decision, or any other VA documents. PDF files only, max 10MB each.</p>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer mb-6 fade-in-up-2
            ${dragging
              ? 'border-[#C9A84C] bg-[#C9A84C]/10 scale-[1.02]'
              : 'border-[#1E3A6E] hover:border-[#C9A84C]/50 bg-[#142040]/50 hover:bg-[#142040]'
            }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            webkitdirectory=""
            accept="application/pdf"
            className="hidden"
            onChange={(e) => { setError(null); addPdfs(e.target.files) }}
          />
          <div className="text-5xl mb-3">📄</div>
          <p className="text-white font-semibold mb-2">
            {dragging ? 'Drop your folder or files here' : 'Click or drag a folder / files here'}
          </p>
          <p className="text-[#8A9BB5] text-sm">PDF files only — select a folder or individual files</p>
        </div>

        {/* File count summary */}
        {files.length > 0 && (
          <p className="text-[#C9A84C] text-sm font-semibold mb-3 fade-in-up-2">
            {files.length} PDF document{files.length !== 1 ? 's' : ''} selected
          </p>
        )}

        {/* File list */}
        {files.length > 0 && (
          <div className="space-y-3 mb-8 fade-in-up-2">
            {files.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between bg-[#142040] border border-[#C9A84C]/30 rounded-xl p-4"
              >
                <div className="flex items-center gap-3 flex-1">
                  <div className="text-[#C9A84C] text-xl">✓</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-semibold truncate">{file.name}</p>
                    <p className="text-[#8A9BB5] text-xs">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); removeFile(idx) }}
                  className="text-gray-500 hover:text-red-400 text-xl transition-colors ml-4 flex-shrink-0"
                  title="Remove"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Inline error */}
        {error && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-red-900/30 border border-red-500/40 text-red-300 text-sm fade-in-up-2">
            {error}
          </div>
        )}

        {/* Submit button */}
        <div className="fade-in-up-3">
          <button
            disabled={files.length === 0 || submitting}
            onClick={handleSubmit}
            className={`w-full py-4 rounded-xl font-bold text-base transition-all duration-200
              ${files.length > 0 && !submitting
                ? 'bg-[#C9A84C] hover:bg-[#E8C56A] text-[#0B1426] shadow-lg hover:shadow-[#C9A84C]/30 hover:scale-[1.02] active:scale-95'
                : 'bg-[#1E3A6E]/40 text-gray-600 cursor-not-allowed'
              }`}
          >
            {submitting
              ? 'Uploading…'
              : files.length > 0
                ? `Submit (${files.length} document${files.length !== 1 ? 's' : ''})`
                : 'Submit Documents'}
          </button>
          {files.length === 0 && !submitting && (
            <p className="text-center text-[#8A9BB5] text-xs mt-3">Upload at least one document to continue</p>
          )}
        </div>
      </main>
    </div>
  )
}
