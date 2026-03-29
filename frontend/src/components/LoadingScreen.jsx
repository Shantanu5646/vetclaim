export default function LoadingScreen() {
  return (
    <div className="min-h-screen bg-[#0B1426] flex flex-col items-center justify-center gap-10 px-6">
      {/* Eagle icon */}
      <div className="text-[#C9A84C]/30 text-8xl select-none">🦅</div>

      {/* Message */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">Processing Your Documents</h2>
        <p className="text-[#8A9BB5] text-sm">Please wait while we review your submission...</p>
      </div>

      {/* 3-dot conveyor animation */}
      <div className="relative w-24 h-5 overflow-hidden">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="loading-dot absolute top-0 w-4 h-4 rounded-full bg-[#C9A84C]"
            style={{ left: 0, top: '2px' }}
          />
        ))}
      </div>

      {/* Disclaimer */}
      <div className="max-w-md bg-[#142040]/80 border border-[#1E3A6E] rounded-xl p-4 text-center">
        <p className="text-[#8A9BB5] text-xs leading-relaxed">
          Results are AI-generated and may miss or misinterpret details. Always verify with official VA sources or a qualified representative.
        </p>
      </div>
    </div>
  )
}
