import { useState, useEffect } from 'react'

const NAV_BLUE = '#1B3A6B'

const STAGES = [
  {
    id: 0,
    title: 'Required Documents Submitted',
    desc: 'Your documents have been received and logged.',
  },
  {
    id: 1,
    title: 'Documents Under Review',
    desc: 'AI is analyzing your C&P Exam, DBQ forms, and Rating Decision for key findings.',
  },
  {
    id: 2,
    title: 'Review Complete',
    desc: 'Your document review is finished. A summary is ready for your next steps.',
  },
]

export default function TrackerPage({ files, onBack, onCallClick }) {
  const [activeStage, setActiveStage] = useState(0)
  const [completedStages, setCompletedStages] = useState(new Set([0]))

  useEffect(() => {
    const timers = [
      setTimeout(() => { setActiveStage(1); setCompletedStages(new Set([0])) }, 800),
      setTimeout(() => { setCompletedStages(new Set([0, 1])); setActiveStage(2) }, 3200),
      setTimeout(() => { setCompletedStages(new Set([0, 1, 2])) }, 5500),
    ]
    return () => timers.forEach(clearTimeout)
  }, [])

  const allDone = completedStages.size === 3
  const fileCount = Array.isArray(files) ? files.length : 0

  return (
    <div className="min-h-screen bg-white flex flex-col">

      {/* Nav */}
      <nav className="border-b border-gray-200 bg-white sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors font-medium"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/>
              </svg>
              Back
            </button>
            <span className="text-gray-300">|</span>
            <span className="font-bold text-base" style={{ color: NAV_BLUE }}>VetClaim AI</span>
          </div>
          <span
            className="text-xs font-semibold px-3 py-1 rounded-full"
            style={allDone
              ? { background: '#F0FDF4', color: '#166534', border: '1px solid #BBF7D0' }
              : { background: '#EFF6FF', color: '#1D4ED8', border: '1px solid #BFDBFE' }}
          >
            {allDone ? 'Review Complete' : 'Processing...'}
          </span>
        </div>
      </nav>

      <main className="flex-1 max-w-2xl mx-auto w-full px-6 py-12">

        {/* Heading */}
        <div className="fade-in-up mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-1">Claim Progress</h1>
          <p className="text-gray-500 text-sm">
            {fileCount} file{fileCount !== 1 ? 's' : ''} submitted
            &nbsp;·&nbsp;
            {allDone ? 'All steps complete' : 'Review in progress'}
          </p>
        </div>

        {/* ── Stepper ── */}
        <div className="fade-in-up-2 mb-10">
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-4 top-8 bottom-8 w-px bg-gray-200" />

            <div className="space-y-4">
              {STAGES.map((stage) => {
                const isDone    = completedStages.has(stage.id)
                const isActive  = activeStage === stage.id && !isDone
                const isPending = !isDone && !isActive

                return (
                  <div
                    key={stage.id}
                    className="relative flex gap-5 items-start transition-opacity duration-500"
                    style={{ opacity: isPending ? 0.35 : 1 }}
                  >
                    {/* Circle */}
                    <div className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-semibold transition-all duration-500 ${
                      isDone    ? 'bg-green-600 text-white' :
                      isActive  ? 'bg-blue-600 text-white' :
                                  'bg-white border-2 border-gray-300 text-gray-400'
                    }`}>
                      {isDone ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                        </svg>
                      ) : isActive ? (
                        <svg className="w-4 h-4 spin-cw" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                        </svg>
                      ) : stage.id + 1}
                    </div>

                    {/* Card */}
                    <div className={`flex-1 rounded-lg px-5 py-4 border transition-all duration-500 ${
                      isDone   ? 'bg-green-50 border-green-200' :
                      isActive ? 'bg-blue-50 border-blue-200' :
                                 'bg-white border-gray-200'
                    }`}>
                      <div className="flex items-center justify-between mb-1">
                        <p className={`font-semibold text-sm ${
                          isDone ? 'text-green-800' : isActive ? 'text-blue-800' : 'text-gray-400'
                        }`}>
                          {stage.title}
                        </p>
                        {isDone   && <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-0.5 rounded-full">Done</span>}
                        {isActive && <span className="text-xs font-medium text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full animate-pulse">In Progress</span>}
                        {isPending && <span className="text-xs text-gray-400">Pending</span>}
                      </div>
                      <p className={`text-xs leading-relaxed ${
                        isDone ? 'text-green-700' : isActive ? 'text-blue-700' : 'text-gray-400'
                      }`}>
                        {stage.desc}
                      </p>
                      {isActive && (
                        <div className="mt-3 h-1 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full tracker-fill" />
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* ── VA Calling Agent ── */}
        <div className="fade-in-up-3 mb-8 border border-gray-200 rounded-xl p-6 bg-white">
          <h2 className="text-base font-bold text-gray-900 mb-1">Call the VA</h2>
          <p className="text-gray-500 text-xs mb-4">
            Our AI agent calls your phone, reads a consent disclosure, then connects to
            1-800-827-1000 and requests a status update on your behalf. Transcript and
            summary are saved automatically.
          </p>
          <button
            onClick={onCallClick}
            className="w-full py-2.5 rounded-lg font-semibold text-sm text-white transition-colors flex items-center justify-center gap-2"
            style={{ background: NAV_BLUE }}
            onMouseEnter={e => e.currentTarget.style.background = '#0F2444'}
            onMouseLeave={e => e.currentTarget.style.background = NAV_BLUE}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
            </svg>
            Open VA Calling Agent
          </button>
        </div>

        {/* All done */}
        {allDone && (
          <div className="fade-in-up bg-green-50 border border-green-200 rounded-xl p-6 text-center mb-6">
            <div className="text-3xl mb-3">🎖️</div>
            <h3 className="text-base font-bold text-green-900 mb-1">Review Complete</h3>
            <p className="text-green-700 text-sm mb-4">
              Your documents have been reviewed. Contact the VA or a VSO for next steps.
            </p>
            <button
              onClick={onBack}
              className="px-6 py-2.5 rounded-lg font-semibold text-sm text-white transition-colors"
              style={{ background: NAV_BLUE }}
              onMouseEnter={e => e.currentTarget.style.background = '#0F2444'}
              onMouseLeave={e => e.currentTarget.style.background = NAV_BLUE}
            >
              Back to Home
            </button>
          </div>
        )}

        {!allDone && (
          <div className="text-center">
            <button
              onClick={onBack}
              className="text-xs text-gray-400 hover:text-gray-700 transition-colors"
            >
              ← Back to Home
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
