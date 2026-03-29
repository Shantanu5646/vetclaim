import { useState } from 'react'
import LandingPage from './components/LandingPage'
import UploadPage from './components/UploadPage'
import LoadingScreen from './components/LoadingScreen'
import TrackerPage from './components/TrackerPage'
import CallingAgentPage from './components/CallingAgentPage'
import AuditResultsPage from './components/AuditResultsPage'

export default function App() {
  const [page, setPage] = useState('landing')
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [jobId, setJobId] = useState(null)
  const [auditResult, setAuditResult] = useState(null)
  const [uploadError, setUploadError] = useState(null)

  const handleSubmit = async (files) => {
    setUploadedFiles(files)
    setUploadError(null)
    setPage('loading')

    const formData = new FormData()
    files.forEach(f => formData.append('files', f))

    try {
      const res = await fetch('/api/upload', { method: 'POST', body: formData })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error || `Upload failed (${res.status})`)
      }
      const { job_id } = await res.json()
      setJobId(job_id)
      setPage('tracker')
    } catch (err) {
      setUploadError(err.message)
      setPage('upload')
    }
  }

  const handleViewAudit = (result) => {
    setAuditResult(result)
    setPage('results')
  }

  return (
    <div className="min-h-screen bg-white text-gray-900">
      {page === 'landing' && (
        <LandingPage
          onUploadClick={() => setPage('upload')}
          onCallClick={() => setPage('caller')}
        />
      )}
      {page === 'upload' && (
        <UploadPage
          onBack={() => setPage('landing')}
          onSubmit={handleSubmit}
          error={uploadError}
        />
      )}
      {page === 'loading' && <LoadingScreen />}
      {page === 'tracker' && (
        <TrackerPage
          files={uploadedFiles}
          jobId={jobId}
          onBack={() => setPage('landing')}
          onCallClick={() => setPage('caller')}
          onViewAudit={handleViewAudit}
        />
      )}
      {page === 'results' && (
        <AuditResultsPage
          result={auditResult}
          jobId={jobId}
          onBack={() => setPage('landing')}
          onCallClick={() => setPage('caller')}
        />
      )}
      {page === 'caller' && (
        <CallingAgentPage onBack={() => setPage('tracker')} />
      )}
    </div>
  )
}
