import { useState } from 'react'
import LandingPage from './components/LandingPage'
import UploadPage from './components/UploadPage'
import CallingAgentPage from './components/CallingAgentPage'
import TrackerPage from './components/TrackerPage'

export default function App() {
  const [page, setPage] = useState('landing')
  const [jobId, setJobId] = useState(null)

  const handleSubmit = (jobId) => {
    setJobId(jobId)
    setPage('calling_agent')
  }

  return (
    <div className="min-h-screen bg-[#0B1426] text-white">
      {page === 'landing' && (
        <LandingPage onUploadClick={() => setPage('upload')} />
      )}
      {page === 'upload' && (
        <UploadPage
          onBack={() => setPage('landing')}
          onSubmit={handleSubmit}
        />
      )}
      {page === 'calling_agent' && (
        <CallingAgentPage
          jobId={jobId}
          onComplete={(id) => {
            setJobId(id)
            setPage('result')
          }}
          onError={() => setPage('upload')}
        />
      )}
      {page === 'result' && (
        <TrackerPage
          jobId={jobId}
          onBack={() => {
            setJobId(null)
            setPage('landing')
          }}
        />
      )}
    </div>
  )
}
