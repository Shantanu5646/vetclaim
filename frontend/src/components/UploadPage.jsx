import { useState, useRef } from 'react'

export default function UploadPage({ onBack, onSubmit }) {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const fileInputRef = useRef()

  const handleFile = (newFiles) => {
    const pdfFiles = Array.from(newFiles).filter(f => f.type === 'application/pdf')
    setFiles(prev => [...prev, ...pdfFiles])
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files)
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
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
            accept="application/pdf"
            className="hidden"
            onChange={(e) => handleFile(e.target.files)}
          />
          <div className="text-5xl mb-3">📄</div>
          <p className="text-white font-semibold mb-2">
            {dragging ? 'Drop your files here' : 'Click or drag documents here'}
          </p>
          <p className="text-[#8A9BB5] text-sm">PDF files up to 10MB each</p>
        </div>

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
                  onClick={() => removeFile(idx)}
                  className="text-gray-500 hover:text-red-400 text-xl transition-colors ml-4 flex-shrink-0"
                  title="Remove"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Submit button */}
        <div className="fade-in-up-3">
          <button
            disabled={files.length === 0}
            onClick={() => onSubmit(files)}
            className={`w-full py-4 rounded-xl font-bold text-base transition-all duration-200
              ${files.length > 0
                ? 'bg-[#C9A84C] hover:bg-[#E8C56A] text-[#0B1426] shadow-lg hover:shadow-[#C9A84C]/30 hover:scale-[1.02] active:scale-95'
                : 'bg-[#1E3A6E]/40 text-gray-600 cursor-not-allowed'
              }`}
          >
            Submit {files.length > 0 ? `(${files.length} document${files.length !== 1 ? 's' : ''})` : 'Documents'}
          </button>
          {files.length === 0 && (
            <p className="text-center text-[#8A9BB5] text-xs mt-3">Upload at least one document to continue</p>
          )}
        </div>
      </main>
    </div>
  )
}
