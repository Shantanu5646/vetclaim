import { useEffect, useRef, useState } from 'react'

const STEP_LABELS = {
  parsing_documents: 'Parsing Documents',
  running_audit: 'Running Audit',
  filling_forms: 'Filling Forms',
  complete: 'Complete',
  error: 'Error',
}

function PulsingDots() {
  return (
    <span className="inline-flex items-center gap-1 ml-2">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-[#C9A84C]"
          style={{ animation: `pulse-dot 1.2s ease-in-out ${i * 0.2}s infinite` }}
        />
      ))}
    </span>
  )
}

export default function CallingAgentPage({ jobId, onComplete, onError }) {
  const [logs, setLogs] = useState([])
  const [errorMsg, setErrorMsg] = useState(null)
  const [done, setDone] = useState(false)
  const logEndRef = useRef(null)
  const esRef = useRef(null)

  useEffect(() => {
    const es = new EventSource('/api/stream/' + jobId)
    esRef.current = es

    es.onmessage = (event) => {
      let parsed
      try {
        parsed = JSON.parse(event.data)
      } catch {
        return
      }

      const { status, step } = parsed
      const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false })

      setLogs((prev) => [...prev, { timestamp, status, step }])

      if (step === 'complete') {
        es.close()
        setDone(true)
        onComplete(jobId)
      } else if (step === 'error') {
        es.close()
        setErrorMsg(status)
      }
    }

    es.onerror = () => {
      es.close()
      setErrorMsg('Connection to server lost. Please try again.')
    }

    return () => {
      es.close()
    }
  }, [jobId])

  // Auto-scroll to bottom on new log entries
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  const isProcessing = !done && !errorMsg

  return (
    <div className="min-h-screen bg-[#0B1426] flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-[#1E3A6E]/50">
        <div className="flex items-center gap-2">
          <span className="text-[#C9A84C] font-black text-xl tracking-widest uppercase">VetClaim</span>
        </div>
        <div className="text-xs text-gray-500 hidden md:block">Serving those who served</div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center px-6 py-10 max-w-3xl mx-auto w-full">
        {/* Status heading */}
        <div className="w-full mb-6 text-center">
          {isProcessing ? (
            <div className="flex items-center justify-center gap-3">
              {/* Spinning icon */}
              <svg
                className="w-6 h-6 text-[#C9A84C] animate-spin"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              <h1 className="text-2xl font-bold text-white">
                Processing your claim
                <PulsingDots />
              </h1>
            </div>
          ) : errorMsg ? (
            <h1 className="text-2xl font-bold text-red-400">Processing Failed</h1>
          ) : (
            <h1 className="text-2xl font-bold text-[#C9A84C]">Processing Complete</h1>
          )}
          <p className="text-[#8A9BB5] text-sm mt-2">
            Job ID: <span className="font-mono text-[#C9A84C]/70">{jobId}</span>
          </p>
        </div>

        {/* Error banner */}
        {errorMsg && (
          <div className="w-full mb-6 bg-red-900/30 border border-red-500/50 rounded-xl p-5">
            <p className="text-red-300 font-semibold mb-1">Error</p>
            <p className="text-red-200 text-sm">{errorMsg}</p>
            <button
              onClick={onError}
              className="mt-4 bg-[#C9A84C] hover:bg-[#E8C56A] text-[#0B1426] font-bold px-6 py-2 rounded-lg text-sm transition-all duration-200 hover:scale-105 active:scale-95"
            >
              ← Back to Upload
            </button>
          </div>
        )}

        {/* Terminal log */}
        <div className="w-full flex-1 bg-[#060D1A] border border-[#1E3A6E] rounded-xl overflow-hidden shadow-2xl">
          {/* Terminal title bar */}
          <div className="flex items-center gap-2 px-4 py-3 bg-[#0D1B33] border-b border-[#1E3A6E]">
            <span className="w-3 h-3 rounded-full bg-red-500/70" />
            <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <span className="w-3 h-3 rounded-full bg-green-500/70" />
            <span className="ml-3 text-xs text-[#8A9BB5] font-mono">vetclaim — agent pipeline</span>
          </div>

          {/* Log lines */}
          <div className="p-4 h-96 overflow-y-auto font-mono text-sm space-y-1">
            {logs.length === 0 && (
              <p className="text-[#3A5070] italic">Waiting for agent output...</p>
            )}
            {logs.map((entry, idx) => (
              <div key={idx} className="flex items-start gap-2 leading-relaxed">
                <span className="text-[#3A5070] flex-shrink-0 select-none">{entry.timestamp}</span>
                <span className="text-[#C9A84C] flex-shrink-0 select-none">›</span>
                {entry.step && STEP_LABELS[entry.step] && (
                  <span className="text-[#4A7AB5] flex-shrink-0 text-xs bg-[#0D1B33] border border-[#1E3A6E] rounded px-1.5 py-0.5 leading-none self-center">
                    {STEP_LABELS[entry.step]}
                  </span>
                )}
                <span className={
                  entry.step === 'error'
                    ? 'text-red-400'
                    : entry.step === 'complete'
                    ? 'text-green-400'
                    : 'text-[#C8D8E8]'
                }>
                  {entry.status}
                </span>
              </div>
            ))}
            {isProcessing && (
              <div className="flex items-center gap-2 text-[#3A5070]">
                <span className="select-none">{'>'}</span>
                <span className="animate-pulse">█</span>
              </div>
            )}
            <div ref={logEndRef} />
          </div>
        </div>

        {/* Step progress pills */}
        {logs.length > 0 && (
          <div className="w-full mt-5 flex flex-wrap gap-2 justify-center">
            {['parsing_documents', 'running_audit', 'filling_forms', 'complete'].map((step) => {
              const reached = logs.some((l) => l.step === step)
              return (
                <span
                  key={step}
                  className={`text-xs px-3 py-1 rounded-full border font-medium transition-all duration-300 ${
                    reached
                      ? 'bg-[#C9A84C]/20 border-[#C9A84C]/60 text-[#C9A84C]'
                      : 'bg-transparent border-[#1E3A6E] text-[#3A5070]'
                  }`}
                >
                  {STEP_LABELS[step]}
                </span>
              )
            })}
          </div>
        )}
      </main>

      <style>{`
        @keyframes pulse-dot {
          0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
          40% { opacity: 1; transform: scale(1.2); }
        }
      `}</style>
    </div>
  )
}
