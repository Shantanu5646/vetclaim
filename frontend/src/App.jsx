import { useState } from 'react'
import LandingPage from './components/LandingPage'
import UploadPage from './components/UploadPage'
import LoadingScreen from './components/LoadingScreen'
import TrackerPage from './components/TrackerPage'
import CallingAgentPage from './components/CallingAgentPage'

export default function App() {
  const [page, setPage] = useState('landing')
  const [uploadedFiles, setUploadedFiles] = useState([])

  const handleSubmit = (files) => {
    setUploadedFiles(files)
    setPage('loading')
    setTimeout(() => setPage('tracker'), 3500)
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
        />
      )}
      {page === 'loading' && <LoadingScreen />}
      {page === 'tracker' && (
        <TrackerPage
          files={uploadedFiles}
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
