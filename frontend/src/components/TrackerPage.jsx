import { useState, useEffect, useRef } from 'react'

// Flag type badge config
const FLAG_BADGE = {
  UNDER_RATED:            { label: 'Under-Rated',            bg: 'bg-amber-500/20',  border: 'border-amber-500/60',  text: 'text-amber-400' },
  WRONG_CODE:             { label: 'Wrong Code',             bg: 'bg-red-500/20',    border: 'border-red-500/60',    text: 'text-red-400' },
  MISSING_NEXUS:          { label: 'Missing Nexus',          bg: 'bg-red-500/20',    border: 'border-red-500/60',    text: 'text-red-400' },
  PACT_ACT_ELIGIBLE:      { label: 'PACT Act Eligible',      bg: 'bg-green-500/20',  border: 'border-green-500/60',  text: 'text-green-400' },
  TDIU_ELIGIBLE:          { label: 'TDIU Eligible',          bg: 'bg-blue-500/20',   border: 'border-blue-500/60',   text: 'text-blue-400' },
  COMBINED_RATING_ERROR:  { label: 'Combined Rating Error',  bg: 'bg-red-500/20',    border: 'border-red-500/60',    text: 'text-red-400' },
  SEPARATE_RATING_MISSED: { label: 'Separate Rating Missed', bg: 'bg-yellow-500/20', border: 'border-yellow-500/60', text: 'text-yellow-400' },
}

function FlagBadge({ flagType }) {
  const cfg = FLAG_BADGE[flagType] || { label: flagType, bg: 'bg-gray-500/20', border: 'border-gray-500/60', text: 'text-gray-400' }
  return (
    <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full border ${cfg.bg} ${cfg.border} ${cfg.text}`}>
      {cfg.label}
    </span>
  )
}

function Spinner() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24">
      <svg className="w-10 h-10 text-[#C9A84C] animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
      </svg>
      <p className="text-[#8A9BB5] text-sm">Loading audit results…</p>
    </div>
  )
}

function SectionHeader({ icon, title }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="text-xl">{icon}</span>
      <h3 className="text-lg font-bold text-white">{title}</h3>
    </div>
  )
}

export default function TrackerPage({ jobId, onBack }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    async function fetchResult() {
      try {
        const res = await fetch(`/api/result/${jobId}`)
        if (cancelled) return

        if (res.status === 202) {
          // Still processing — poll again in 2 seconds
          pollRef.current = setTimeout(fetchResult, 2000)
          return
        }

        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          setError(body.error || `Unexpected error (HTTP ${res.status})`)
          setLoading(false)
          return
        }

        const data = await res.json()
        setResult(data)
        setLoading(false)
      } catch (err) {
        if (!cancelled) {
          setError('Failed to connect to the server. Please try again.')
          setLoading(false)
        }
      }
    }

    fetchResult()

    return () => {
      cancelled = true
      if (pollRef.current) clearTimeout(pollRef.current)
    }
  }, [jobId])

  const auditResult = result?.audit_result ?? {}
  const flags = auditResult.flags ?? []
  const vaFormLinks = result?.va_form_links ?? []
  const missingNexusFlags = flags.filter((f) => f.flag_type === 'MISSING_NEXUS')

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

      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-10">
        {loading && <Spinner />}

        {error && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-6 text-center">
            <p className="text-red-300 font-semibold mb-1">Error Loading Results</p>
            <p className="text-red-200 text-sm mb-4">{error}</p>
            <button
              onClick={onBack}
              className="bg-[#C9A84C] hover:bg-[#E8C56A] text-[#0B1426] font-bold px-6 py-2 rounded-lg text-sm transition-all hover:scale-105 active:scale-95"
            >
              ← Back to Home
            </button>
          </div>
        )}

        {result && (
          <div className="space-y-8">
            {/* ── 1. Veteran Info Header ── */}
            <div className="bg-[#0F1C36] border border-[#1E3A6E] rounded-2xl p-6">
              <div className="flex items-start justify-between flex-wrap gap-4 mb-6">
                <div>
                  <p className="text-[#8A9BB5] text-xs uppercase tracking-widest mb-1">Veteran</p>
                  <h2 className="text-2xl font-bold text-white">
                    {auditResult.veteran_name || 'Unknown Veteran'}
                  </h2>
                </div>
                <span className="text-xs text-[#C9A84C] font-semibold bg-[#C9A84C]/10 border border-[#C9A84C]/30 px-3 py-1 rounded-full">
                  Audit Complete
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <StatCard label="Current Rating" value={`${auditResult.current_combined_rating ?? '—'}%`} />
                <StatCard label="Corrected Rating" value={`${auditResult.corrected_combined_rating ?? '—'}%`} highlight />
                <StatCard label="Current Monthly Pay" value={formatUSD(auditResult.current_monthly_pay_usd)} />
                <StatCard label="Potential Monthly Pay" value={formatUSD(auditResult.potential_monthly_pay_usd)} highlight />
                <StatCard label="Annual Impact" value={formatUSD(auditResult.annual_impact_usd)} highlight />
              </div>
            </div>

            {/* ── 2. Audit Flags ── */}
            <div className="bg-[#0F1C36] border border-[#1E3A6E] rounded-2xl p-6">
              <SectionHeader icon="🚩" title="Audit Flags" />
              {flags.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-3">✅</div>
                  <p className="text-[#C9A84C] font-semibold">No issues found</p>
                  <p className="text-[#8A9BB5] text-sm mt-1">Your current ratings appear to be accurate.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {flags.map((flag, idx) => (
                    <FlagCard key={idx} flag={flag} />
                  ))}
                </div>
              )}
            </div>

            {/* ── 3. Rejection Reasons (MISSING_NEXUS) ── */}
            {missingNexusFlags.length > 0 && (
              <div className="bg-[#0F1C36] border border-red-500/30 rounded-2xl p-6">
                <SectionHeader icon="❌" title="Rejection Reasons" />
                <div className="space-y-3">
                  {missingNexusFlags.map((flag, idx) => (
                    <div key={idx} className="bg-red-900/20 border border-red-500/30 rounded-xl p-4">
                      <p className="font-semibold text-red-300 mb-1">{flag.condition_name}</p>
                      <p className="text-[#8A9BB5] text-sm leading-relaxed">{flag.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── 4. Filled VA Forms ── */}
            {vaFormLinks.length > 0 && (
              <div className="bg-[#0F1C36] border border-[#1E3A6E] rounded-2xl p-6">
                <SectionHeader icon="📄" title="Filled VA Forms" />
                <div className="space-y-3">
                  {vaFormLinks.map((form, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-[#142040] border border-[#1E3A6E] rounded-xl px-4 py-3">
                      <div>
                        <p className="font-semibold text-white text-sm">VA Form {form.form_number}</p>
                        {form.fields_filled != null && (
                          <p className="text-[#8A9BB5] text-xs mt-0.5">
                            {form.fields_filled} of {form.fields_found} fields filled
                          </p>
                        )}
                      </div>
                      <a
                        href={`/api/download?path=${encodeURIComponent(form.filled_path)}`}
                        download
                        className="flex items-center gap-1.5 bg-[#C9A84C] hover:bg-[#E8C56A] text-[#0B1426] font-bold text-xs px-4 py-2 rounded-lg transition-all hover:scale-105 active:scale-95"
                      >
                        ⬇ Download
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── 5. AI Reasoning ── */}
            {auditResult.auditor_notes && (
              <div className="bg-[#0F1C36] border border-[#1E3A6E] rounded-2xl p-6">
                <SectionHeader icon="🤖" title="AI Reasoning" />
                <p className="text-[#C8D8E8] text-sm leading-relaxed whitespace-pre-wrap">
                  {auditResult.auditor_notes}
                </p>
              </div>
            )}

            {/* ── 6. Rule-Based Report ── */}
            {result.rule_based_triggered && result.rule_based_report && (
              <div className="bg-[#0F1C36] border border-[#1E3A6E] rounded-2xl p-6">
                <SectionHeader icon="📋" title="Rule-Based Report" />
                <p className="text-[#C8D8E8] text-sm leading-relaxed whitespace-pre-wrap">
                  {result.rule_based_report}
                </p>
              </div>
            )}

            {/* ── Submit Another Claim ── */}
            <div className="text-center pt-4 pb-8">
              <button
                onClick={onBack}
                className="bg-[#C9A84C] hover:bg-[#E8C56A] text-[#0B1426] font-bold px-10 py-3 rounded-xl transition-all hover:scale-105 active:scale-95"
              >
                Submit Another Claim
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function StatCard({ label, value, highlight }) {
  return (
    <div className={`rounded-xl p-4 border ${highlight ? 'bg-[#C9A84C]/5 border-[#C9A84C]/30' : 'bg-[#142040] border-[#1E3A6E]'}`}>
      <p className="text-[#8A9BB5] text-xs uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-xl font-bold ${highlight ? 'text-[#C9A84C]' : 'text-white'}`}>{value}</p>
    </div>
  )
}

function FlagCard({ flag }) {
  return (
    <div className="bg-[#142040] border border-[#1E3A6E] rounded-xl p-4">
      <div className="flex items-start justify-between gap-3 flex-wrap mb-2">
        <p className="font-semibold text-white">{flag.condition_name}</p>
        <FlagBadge flagType={flag.flag_type} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 text-xs">
        {flag.assigned_rating != null && (
          <div>
            <span className="text-[#8A9BB5]">Assigned: </span>
            <span className="text-white font-medium">{flag.assigned_rating}%</span>
          </div>
        )}
        {flag.eligible_rating != null && (
          <div>
            <span className="text-[#8A9BB5]">Eligible: </span>
            <span className="text-[#C9A84C] font-medium">{flag.eligible_rating}%</span>
          </div>
        )}
        {flag.cfr_citation && (
          <div className="col-span-2">
            <span className="text-[#8A9BB5]">CFR: </span>
            <span className="text-white font-medium">{flag.cfr_citation}</span>
          </div>
        )}
      </div>

      <p className="text-[#C8D8E8] text-sm leading-relaxed mb-2">{flag.explanation}</p>

      {flag.confidence != null && (
        <div className="flex items-center gap-2 mt-2">
          <span className="text-[#8A9BB5] text-xs">Confidence:</span>
          <div className="flex-1 h-1.5 bg-[#1E3A6E] rounded-full overflow-hidden max-w-[120px]">
            <div
              className="h-full bg-[#C9A84C] rounded-full"
              style={{ width: `${Math.round(flag.confidence * 100)}%` }}
            />
          </div>
          <span className="text-[#C9A84C] text-xs font-medium">{Math.round(flag.confidence * 100)}%</span>
        </div>
      )}
    </div>
  )
}

function formatUSD(value) {
  if (value == null) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
}
