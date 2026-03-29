import { useState } from 'react'
import LandingPage from './components/LandingPage'
import UploadPage from './components/UploadPage'
import LoadingScreen from './components/LoadingScreen'
import TrackerPage from './components/TrackerPage'

export default function App() {
  const [page, setPage] = useState('landing')
  const [uploadedFiles, setUploadedFiles] = useState([])

  const handleSubmit = (files) => {
    setUploadedFiles(files)
    setPage('loading')
    setTimeout(() => setPage('tracker'), 3500)
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
      {page === 'loading' && <LoadingScreen />}
      {page === 'tracker' && (
        <TrackerPage
          files={uploadedFiles}
          onBack={() => setPage('landing')}
        />
      )}
    </div>
  )
}
