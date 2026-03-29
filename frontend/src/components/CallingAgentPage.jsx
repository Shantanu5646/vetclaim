import { useState, useEffect } from 'react'
import { Phone, PhoneOff, Mic, MicOff, Loader, CheckCircle } from 'lucide-react'

const CALLING_AGENT_BASE_URL = import.meta.env.VITE_CALLING_AGENT_URL || 'http://localhost:8000'

export default function CallingAgentPage({ onBack }) {
  const [callStatus, setCallStatus] = useState('idle') // idle, calling, ringing, connected, ended, success
  const [recipientPhone, setRecipientPhone] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [callDuration, setCallDuration] = useState(0)
  const [isMuted, setIsMuted] = useState(false)
  const [callHistory, setCallHistory] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentCallSid, setCurrentCallSid] = useState(null)
  const [callStartTime, setCallStartTime] = useState(null)

  // Timer for call duration
  useEffect(() => {
    let timer
    if (callStatus === 'connected') {
      timer = setInterval(() => {
        setCallDuration(prev => prev + 1)
      }, 1000)
    }
    return () => clearInterval(timer)
  }, [callStatus])

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const formatPhoneDisplay = (phone) => {
    const cleaned = phone.replace(/\D/g, '')
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`
    } else if (cleaned.length > 10) {
      return `+${cleaned.slice(-11, -10)} (${cleaned.slice(-10, -7)}) ${cleaned.slice(-7, -4)}-${cleaned.slice(-4)}`
    }
    return phone
  }

  const validatePhone = (phone) => {
    const cleaned = phone.replace(/\D/g, '')
    return cleaned.length >= 10
  }

  const initializeCall = async () => {
    setError('')
    setSuccess('')
    
    if (!recipientPhone.trim()) {
      setError('Please enter a phone number')
      return
    }

    if (!validatePhone(recipientPhone)) {
      setError('Please enter a valid phone number (10+ digits, e.g., +1-555-123-4567 or 555-123-4567)')
      return
    }

    setIsLoading(true)
    setCallStatus('calling')
    setCallDuration(0)
    setCallStartTime(new Date())

    try {
      const response = await fetch(`${CALLING_AGENT_BASE_URL}/call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to: recipientPhone,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Failed to initiate call')
      }

      const data = await response.json()
      setCurrentCallSid(data.call_sid)
      setSuccess(`Call initiated! SID: ${data.call_sid}`)
      
      // Simulate call progression
      setTimeout(() => setCallStatus('ringing'), 800)
      setTimeout(() => setCallStatus('connected'), 2500)

      // Add to call history
      const newCall = {
        id: data.call_sid,
        number: recipientPhone,
        displayNumber: formatPhoneDisplay(recipientPhone),
        timestamp: new Date().toLocaleTimeString(),
        date: new Date().toLocaleDateString(),
        duration: 0,
        status: 'connected'
      }
      setCallHistory([newCall, ...callHistory])

    } catch (err) {
      console.error('Call error:', err)
      setError(`Failed to make call: ${err.message}. Make sure the calling agent server is running on port 8000 and ngrok is configured with Twilio credentials.`)
      setCallStatus('idle')
      setCurrentCallSid(null)
    } finally {
      setIsLoading(false)
    }
  }

  const endCall = () => {
    if (callStatus === 'connected' || callStatus === 'ringing') {
      setCallStatus('ended')
      
      // Update call history with final duration
      if (callHistory.length > 0) {
        const updatedHistory = [...callHistory]
        updatedHistory[0].duration = callDuration
        updatedHistory[0].status = 'completed'
        setCallHistory(updatedHistory)
      }

      setTimeout(() => {
        setCallStatus('success')
        setTimeout(() => {
          setCallStatus('idle')
          setCallDuration(0)
          setCurrentCallSid(null)
          setRecipientPhone('')
        }, 2000)
      }, 500)
    }
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
  }

  const handlePhoneInput = (e) => {
    let value = e.target.value.trim()
    // Auto-format as user types
    setRecipientPhone(value)
  }

  return (
    <div className="min-h-screen bg-[#0B1426] flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-[#1E3A6E]/50 bg-[#0D1B32]">
        <h1 className="text-[#C9A84C] font-black text-xl tracking-widest uppercase">Calling Agent</h1>
        <button
          onClick={onBack}
          className="px-6 py-2 rounded-lg border border-[#1E3A6E] text-white hover:bg-[#1E3A6E]/20 transition-colors"
        >
          ← Back
        </button>
      </header>

      {/* Main Content Area - Call Status Display */}
      <div className="flex-1 flex flex-col p-8 overflow-y-auto">
        
        {/* Call Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* Current Status */}
          <div className="p-6 rounded-xl border-2 border-[#1E3A6E] bg-[#0D1B32]">
            <p className="text-gray-400 text-sm mb-2">Current Status</p>
            <p className="text-2xl font-bold text-[#C9A84C] capitalize">
              {callStatus === 'success' ? '✅ Success' : callStatus}
            </p>
          </div>

          {/* Call Duration */}
          <div className="p-6 rounded-xl border-2 border-[#1E3A6E] bg-[#0D1B32]">
            <p className="text-gray-400 text-sm mb-2">Call Duration</p>
            <p className={`text-2xl font-bold font-mono ${
              callStatus === 'connected' ? 'text-green-400' : 
              callStatus === 'success' ? 'text-green-400' :
              'text-[#C9A84C]'
            }`}>
              {formatDuration(callDuration)}
            </p>
          </div>

          {/* Current Call SID */}
          <div className="p-6 rounded-xl border-2 border-[#1E3A6E] bg-[#0D1B32]">
            <p className="text-gray-400 text-sm mb-2">Call SID</p>
            {currentCallSid ? (
              <p className="text-xs font-mono text-[#C9A84C] truncate" title={currentCallSid}>
                {currentCallSid.slice(0, 20)}...
              </p>
            ) : (
              <p className="text-gray-500 text-sm">None</p>
            )}
          </div>
        </div>

        {/* Status Indicator */}
        {callStatus !== 'idle' && (
          <div className={`mb-8 p-8 rounded-2xl border-2 text-center transition-all ${
            callStatus === 'calling' ? 'border-[#FFA500] bg-[#1a1410]/50 animate-pulse' :
            callStatus === 'ringing' ? 'border-[#FF6B6B] bg-[#2a1410]/50 animate-pulse' :
            callStatus === 'connected' ? 'border-[#4CAF50] bg-[#1a2a10]/50' :
            callStatus === 'ended' ? 'border-[#666] bg-[#1a1a1a]/50' :
            'border-[#4CAF50] bg-[#1a2a10]/50'
          }`}>
            <div>
              {callStatus === 'calling' && (
                <>
                  <Loader className="w-12 h-12 text-[#FFA500] mx-auto mb-2 animate-spin" />
                  <p className="text-sm text-[#FFA500] font-semibold">Initiating call...</p>
                </>
              )}
              {callStatus === 'ringing' && (
                <>
                  <Phone className="w-12 h-12 text-[#FF6B6B] mx-auto mb-2 animate-pulse" />
                  <p className="text-sm text-[#FF6B6B] font-semibold">Ringing...</p>
                </>
              )}
              {callStatus === 'connected' && (
                <>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <div className="w-3 h-3 bg-[#4CAF50] rounded-full animate-pulse"></div>
                    <p className="text-sm text-[#4CAF50] font-semibold">Call Connected</p>
                  </div>
                  {callHistory.length > 0 && (
                    <p className="text-xs text-gray-400">to {callHistory[0].displayNumber}</p>
                  )}
                </>
              )}
              {callStatus === 'ended' && (
                <>
                  <PhoneOff className="w-12 h-12 text-gray-500 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">Call ended</p>
                </>
              )}
              {callStatus === 'success' && (
                <>
                  <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-2" />
                  <p className="text-sm text-green-400 font-semibold">Call completed successfully!</p>
                </>
              )}
            </div>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="mb-6 p-4 bg-green-900/30 border border-green-700 rounded-lg">
            <p className="text-green-200 text-sm">{success}</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {/* Call History */}
        {callHistory.length > 0 && (
          <div className="mb-8">
            <h3 className="text-[#C9A84C] font-bold mb-4">Call History</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {callHistory.map((call, idx) => (
                <div key={idx} className="flex justify-between items-center p-4 bg-[#142040] rounded-lg border border-[#1E3A6E]/30 hover:border-[#1E3A6E] transition-colors">
                  <div>
                    <p className="text-white font-semibold">{call.displayNumber}</p>
                    <p className="text-gray-400 text-xs">{call.date} at {call.timestamp}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[#C9A84C] text-sm font-mono font-semibold">{formatDuration(call.duration)}</p>
                    <p className={`text-xs ${call.status === 'completed' ? 'text-green-400' : 'text-gray-400'}`}>
                      {call.status}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Phone Controls at Bottom - THIS IS THE LAST PART */}
      <div className="border-t border-[#1E3A6E]/50 bg-[#0D1B32] p-8">
        <div className="max-w-md mx-auto">
          {callStatus === 'idle' || callStatus === 'success' ? (
            <>
              {/* Phone Number Input */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-[#C9A84C] mb-3">
                  📞 Recipient Phone Number
                </label>
                <div className="relative">
                  <input
                    type="tel"
                    placeholder="+1 (555) 123-4567 or 555-123-4567"
                    value={recipientPhone}
                    onChange={handlePhoneInput}
                    disabled={isLoading || callStatus === 'success'}
                    className="w-full px-4 py-3 bg-[#142040] border border-[#1E3A6E] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#C9A84C] transition-all disabled:opacity-50"
                  />
                  {recipientPhone && validatePhone(recipientPhone) && (
                    <span className="absolute right-4 top-3.5 text-green-400 text-lg">✓</span>
                  )}
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  Enter 10+ digits. US format: (555) 123-4567 or international: +1-555-123-4567
                </p>
              </div>

              {/* Call Button */}
              <button
                onClick={initializeCall}
                disabled={isLoading || !recipientPhone.trim() || !validatePhone(recipientPhone)}
                className="w-full py-3 bg-gradient-to-r from-[#C9A84C] to-[#E8C56A] text-[#0B1426] font-bold rounded-lg hover:shadow-lg hover:shadow-[#C9A84C]/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-base"
              >
                {isLoading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Calling...
                  </>
                ) : (
                  <>
                    <Phone className="w-5 h-5" />
                    Make Call
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              {/* Call Active Controls */}
              <div className="flex gap-4">
                <button
                  onClick={toggleMute}
                  className={`flex-1 py-3 rounded-lg font-bold transition-all flex items-center justify-center gap-2 ${
                    isMuted
                      ? 'bg-red-900/50 border border-red-700 text-red-300 hover:bg-red-900/70'
                      : 'bg-[#142040] border border-[#1E3A6E] text-white hover:bg-[#1E3A6E]/50'
                  }`}
                >
                  {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                  {isMuted ? 'Muted' : 'Unmuted'}
                </button>
                <button
                  onClick={endCall}
                  disabled={callStatus === 'ended' || callStatus === 'success'}
                  className="flex-1 py-3 bg-red-900/50 border border-red-700 text-red-300 rounded-lg font-bold hover:bg-red-900/70 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <PhoneOff className="w-5 h-5" />
                  End Call
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-[#1E3A6E]/50 px-8 py-3 text-center text-xs text-gray-600 bg-[#0B1426]">
        <p>Twilio Calling Agent • Requires valid Twilio credentials and ngrok for live calls</p>
      </div>
    </div>
  )
}
