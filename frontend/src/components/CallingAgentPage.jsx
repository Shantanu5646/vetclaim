import { useState } from 'react'

const BACKEND_URL = import.meta.env.VITE_CALLING_AGENT_URL || 'http://localhost:8000'
const NAV_BLUE = '#1B3A6B'

const CLAIM_TYPES = [
  'disability',
  'disability increase',
  'new claim',
  'appeal',
  'supplemental claim',
]

export default function CallingAgentPage({ onBack }) {
  const [form, setForm] = useState({
    customer_number: '',
    full_name: '',
    last_four_ssn: '',
    va_file_number: '',
    claim_date: '',
    claim_type: 'disability',
  })
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [callId, setCallId] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [callRecord, setCallRecord] = useState(null)

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleCall = async () => {
    if (!form.customer_number.trim()) {
      setErrorMsg('Phone number is required.')
      return
    }
    setStatus('loading')
    setErrorMsg('')
    setCallRecord(null)

    try {
      const res = await fetch(`${BACKEND_URL}/start-va-call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.error || data.message || 'Failed to start call')
      }

      setCallId(data.call_id)
      setStatus('success')
    } catch (err) {
      setErrorMsg(err.message)
      setStatus('error')
    }
  }

  const fetchRecord = async () => {
    if (!callId) return
    try {
      const res = await fetch(`${BACKEND_URL}/calls/${callId}`)
      if (res.ok) setCallRecord(await res.json())
    } catch (_) {}
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">

      {/* Nav */}
      <nav className="border-b border-gray-200 bg-white sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-4">
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
          <span className="font-bold text-base" style={{ color: NAV_BLUE }}>VetClaim AI — VA Caller</span>
        </div>
      </nav>

      <main className="flex-1 max-w-xl mx-auto w-full px-6 py-12">

        {/* Heading */}
        <div className="fade-in-up mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Initiate VA Call</h1>
          <p className="text-gray-500 text-sm leading-relaxed">
            Our AI agent will call <strong>your phone</strong> first, read a consent disclosure,
            then connect to the VA and request a status update on your behalf.
          </p>
        </div>

        {/* Consent notice */}
        <div className="mb-8 p-4 bg-amber-50 border border-amber-200 rounded-lg flex gap-3">
          <svg className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p className="text-xs text-amber-700 leading-relaxed">
            This call will be recorded for documentation purposes. The AI agent will announce
            this disclosure before any recording begins. Florida is an all-party consent state —
            you must stay on the line to confirm consent.
          </p>
        </div>

        {/* Form */}
        <div className="fade-in-up-2 space-y-5 mb-8">
          {/* Phone */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1.5">
              Your Phone Number <span className="text-red-500">*</span>
            </label>
            <input
              type="tel"
              placeholder="+1 (555) 123-4567"
              value={form.customer_number}
              onChange={e => update('customer_number', e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 outline-none focus:border-blue-400 transition-colors"
            />
            <p className="text-xs text-gray-400 mt-1">Vapi will call this number first</p>
          </div>

          {/* Name */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1.5">Full Name</label>
            <input
              type="text"
              placeholder="John Smith"
              value={form.full_name}
              onChange={e => update('full_name', e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 outline-none focus:border-blue-400 transition-colors"
            />
          </div>

          {/* SSN + File number row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Last 4 of SSN</label>
              <input
                type="text"
                placeholder="1234"
                maxLength={4}
                value={form.last_four_ssn}
                onChange={e => update('last_four_ssn', e.target.value.replace(/\D/g, '').slice(0, 4))}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 outline-none focus:border-blue-400 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">VA File Number</label>
              <input
                type="text"
                placeholder="Optional"
                value={form.va_file_number}
                onChange={e => update('va_file_number', e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 outline-none focus:border-blue-400 transition-colors"
              />
            </div>
          </div>

          {/* Claim date + type row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Claim Submitted Date</label>
              <input
                type="date"
                value={form.claim_date}
                onChange={e => update('claim_date', e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 outline-none focus:border-blue-400 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Claim Type</label>
              <select
                value={form.claim_type}
                onChange={e => update('claim_type', e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 outline-none focus:border-blue-400 transition-colors bg-white"
              >
                {CLAIM_TYPES.map(t => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Error */}
        {errorMsg && (
          <div className="mb-6 px-4 py-3 rounded-lg text-xs text-red-700 bg-red-50 border border-red-200">
            {errorMsg}
          </div>
        )}

        {/* Success */}
        {status === 'success' && (
          <div className="mb-6 px-4 py-3 rounded-lg text-xs text-green-700 bg-green-50 border border-green-200 space-y-1">
            <p className="font-semibold">Call initiated successfully!</p>
            <p>Call ID: <span className="font-mono">{callId}</span></p>
            <p>Vapi is calling your phone now. Answer it to begin.</p>
          </div>
        )}

        {/* Submit button */}
        <div className="fade-in-up-3">
          <button
            onClick={handleCall}
            disabled={status === 'loading'}
            className="w-full py-3 rounded-lg font-semibold text-sm text-white transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ background: NAV_BLUE }}
            onMouseEnter={e => { if (status !== 'loading') e.currentTarget.style.background = '#0F2444' }}
            onMouseLeave={e => { e.currentTarget.style.background = NAV_BLUE }}
          >
            {status === 'loading' ? (
              <>
                <svg className="w-4 h-4 spin-cw" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                Starting Call...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
                </svg>
                Initiate VA Call
              </>
            )}
          </button>
        </div>

        {/* Post-call record fetch */}
        {callId && status === 'success' && (
          <div className="mt-8">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-gray-700">Call Record</p>
              <button
                onClick={fetchRecord}
                className="text-xs font-medium underline transition-colors"
                style={{ color: NAV_BLUE }}
              >
                Refresh
              </button>
            </div>

            {callRecord ? (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3 text-xs">
                {/* Status */}
                <div>
                  <p className="font-semibold text-gray-700 mb-0.5">Status</p>
                  <p className="text-gray-600">{callRecord.status || '—'}</p>
                </div>

                {/* Claim status from summary */}
                {callRecord.summary?.claim_status && (
                  <div>
                    <p className="font-semibold text-gray-700 mb-0.5">Claim Status</p>
                    <p className="text-gray-600">{callRecord.summary.claim_status}</p>
                  </div>
                )}

                {/* Evidence needed */}
                {callRecord.summary?.evidence_needed?.length > 0 && (
                  <div>
                    <p className="font-semibold text-gray-700 mb-0.5">Evidence Needed</p>
                    <ul className="list-disc list-inside text-gray-600 space-y-0.5">
                      {callRecord.summary.evidence_needed.map((e, i) => <li key={i}>{e}</li>)}
                    </ul>
                  </div>
                )}

                {/* Next steps */}
                {callRecord.summary?.next_steps && (
                  <div>
                    <p className="font-semibold text-gray-700 mb-0.5">Next Steps</p>
                    <p className="text-gray-600">{callRecord.summary.next_steps}</p>
                  </div>
                )}

                {/* Transcript */}
                {callRecord.transcript && (
                  <div>
                    <p className="font-semibold text-gray-700 mb-0.5">Transcript</p>
                    <pre className="text-gray-600 whitespace-pre-wrap leading-relaxed font-sans">
                      {callRecord.transcript}
                    </pre>
                  </div>
                )}

                {/* Recording */}
                {callRecord.recording_url && (
                  <div>
                    <p className="font-semibold text-gray-700 mb-1">Recording</p>
                    <audio controls src={callRecord.recording_url} className="w-full" />
                  </div>
                )}

                {(!callRecord.summary && !callRecord.transcript) && (
                  <p className="text-gray-400 italic">
                    Call may still be in progress. Click Refresh after the call ends.
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-400">Click Refresh after the call ends to see the transcript and summary.</p>
            )}
          </div>
        )}

        <p className="text-center text-xs text-gray-400 mt-8">
          Powered by Vapi · Requires VAPI_API_KEY and VAPI_PHONE_NUMBER_ID in .env
        </p>
      </main>
    </div>
  )
}
