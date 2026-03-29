import { useState, useEffect } from 'react'

const STAGES = [
  {
    id: 0,
    title: 'Documents Submitted',
    desc: 'Your documents have been received and logged in our system.',
    icon: '📥',
    completeAfter: 0,
  },
  {
    id: 1,
    title: 'Documents Being Reviewed',
    desc: 'Our system is analyzing your C&P Exam, DBQs, and Rating Decision for key findings.',
    icon: '🔍',
    completeAfter: 2500,
  },
  {
    id: 2,
    title: 'Documents Being Finalized',
    desc: 'Your document review is complete. A summary report is being prepared for you.',
    icon: '✅',
    completeAfter: 5000,
  },
]

export default function TrackerPage({ files, onBack }) {
  const [activeStage, setActiveStage] = useState(0)
  const [completedStages, setCompletedStages] = useState(new Set([0]))

  useEffect(() => {
    const timers = []
    timers.push(setTimeout(() => {
      setActiveStage(1)
      setCompletedStages(new Set([0]))
    }, 800))
    timers.push(setTimeout(() => {
      setCompletedStages(new Set([0, 1]))
      setActiveStage(2)
    }, 3200))
    timers.push(setTimeout(() => {
      setCompletedStages(new Set([0, 1, 2]))
    }, 5500))
    return () => timers.forEach(clearTimeout)
  }, [])

  const allDone = completedStages.size === 3
  const fileCount = Array.isArray(files) ? files.length : 0

  return (
    <div className="min-h-screen bg-[#0B1426] flex flex-col">
      {/* Header */}
      <header className="flex items-center gap-4 px-8 py-5 border-b border-[#1E3A6E]/50">
        <button onClick={onBack} className="text-[#8A9BB5] hover:text-white transition-colors flex items-center gap-2 text-sm">
          ← Back
        </button>
        <span className="text-[#C9A84C] font-black text-lg tracking-widest uppercase">VetClaim</span>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-6 py-12">
        <div className="fade-in-up mb-10">
          <h2 className="text-3xl font-bold text-white mb-2">Claim Progress</h2>
          <p className="text-[#8A9BB5] text-sm">
            {fileCount} document{fileCount !== 1 ? 's' : ''} submitted &nbsp;·&nbsp;
            {allDone ? 'Review complete' : 'Processing...'}
          </p>
        </div>

        {/* Timeline */}
        <div className="relative fade-in-up-2">
          {/* Vertical line */}
          <div className="absolute left-5 top-5 w-0.5 bg-[#1E3A6E]" style={{ height: 'calc(100% - 40px)' }} />

          <div className="space-y-6">
            {STAGES.map((stage) => {
              const isDone = completedStages.has(stage.id)
              const isActive = activeStage === stage.id && !isDone
              return (
                <div key={stage.id} className={`relative flex gap-6 items-start transition-all duration-500
                  ${stage.id > activeStage && !isDone ? 'opacity-30' : 'opacity-100'}`}>
                  {/* Circle */}
                  <div className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-base transition-all duration-500 border-2
                    ${isDone
                      ? 'bg-[#C9A84C] border-[#C9A84C] text-[#0B1426]'
                      : isActive
                      ? 'bg-[#142040] border-[#C9A84C] text-[#C9A84C] pulse-gold'
                      : 'bg-[#142040] border-[#1E3A6E] text-[#8A9BB5]'
                    }`}>
                    {isDone ? '✓' : stage.icon}
                  </div>

                  {/* Content card */}
                  <div className={`flex-1 rounded-xl p-5 border transition-all duration-500
                    ${isDone
                      ? 'bg-[#C9A84C]/5 border-[#C9A84C]/30'
                      : isActive
                      ? 'bg-[#142040] border-[#1E3A6E]'
                      : 'bg-[#0F1C36] border-[#1E3A6E]/50'
                    }`}>
                    <div className="flex items-center justify-between mb-1">
                      <p className={`font-bold ${isDone ? 'text-[#C9A84C]' : isActive ? 'text-white' : 'text-[#8A9BB5]'}`}>
                        {stage.title}
                      </p>
                      {isDone && <span className="text-xs text-[#C9A84C] font-semibold bg-[#C9A84C]/10 px-2 py-0.5 rounded-full">Complete</span>}
                      {isActive && <span className="text-xs text-blue-400 font-semibold bg-blue-400/10 px-2 py-0.5 rounded-full animate-pulse">In Progress</span>}
                    </div>
                    <p className="text-[#8A9BB5] text-sm leading-relaxed">{stage.desc}</p>

                    {/* Progress bar for active stage */}
                    {isActive && (
                      <div className="mt-3 h-1 bg-[#1E3A6E] rounded-full overflow-hidden">
                        <div className="h-full bg-[#C9A84C] rounded-full tracker-fill" />
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Final message */}
        {allDone && (
          <div className="mt-10 bg-[#C9A84C]/10 border border-[#C9A84C]/30 rounded-2xl p-6 text-center fade-in-up">
            <div className="text-4xl mb-3">🎖️</div>
            <h3 className="text-xl font-bold text-[#C9A84C] mb-2">Review Complete</h3>
            <p className="text-[#8A9BB5] text-sm max-w-sm mx-auto mb-6">
              Your documents have been reviewed. Contact the VA for any questions about your claim.
            </p>
            <button
              onClick={onBack}
              className="bg-[#C9A84C] hover:bg-[#E8C56A] text-[#0B1426] font-bold px-8 py-3 rounded-xl transition-all hover:scale-105 active:scale-95"
            >
              Submit Another Claim
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
