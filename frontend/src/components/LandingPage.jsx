import { useState } from 'react'

function EagleMascot() {
  return (
    <svg viewBox="0 0 280 310" xmlns="http://www.w3.org/2000/svg" className="w-56 h-56 md:w-72 md:h-72 drop-shadow-2xl">
      {/* Left wing */}
      <path d="M12,185 C-5,145 8,100 52,80 C72,72 84,90 90,115 L86,170 Q55,182 12,185Z" fill="#142040"/>
      <path d="M18,180 C5,148 14,108 52,88 C68,80 78,95 84,115" fill="none" stroke="#1E3A6E" strokeWidth="2.5"/>
      <path d="M28,175 C18,150 24,118 56,100" fill="none" stroke="#1E3A6E" strokeWidth="1.5" opacity="0.6"/>
      {/* Right wing */}
      <path d="M268,185 C285,145 272,100 228,80 C208,72 196,90 190,115 L194,170 Q225,182 268,185Z" fill="#142040"/>
      <path d="M262,180 C275,148 266,108 228,88 C212,80 202,95 196,115" fill="none" stroke="#1E3A6E" strokeWidth="2.5"/>
      <path d="M252,175 C262,150 256,118 224,100" fill="none" stroke="#1E3A6E" strokeWidth="1.5" opacity="0.6"/>
      {/* Body */}
      <ellipse cx="140" cy="222" rx="54" ry="70" fill="#142040"/>
      {/* Chest shield */}
      <path d="M114,198 L166,198 L166,248 Q140,265 114,248 Z" fill="#C9A84C"/>
      <rect x="114" y="198" width="52" height="20" rx="0" fill="#B22234"/>
      <rect x="114" y="208" width="52" height="5" fill="#B22234" opacity="0.7"/>
      <rect x="114" y="218" width="52" height="5" fill="#B22234" opacity="0.4"/>
      <line x1="114" y1="198" x2="166" y2="198" stroke="#A07830" strokeWidth="1"/>
      <line x1="114" y1="248" x2="140" y2="264" stroke="#A07830" strokeWidth="1"/>
      <line x1="166" y1="248" x2="140" y2="264" stroke="#A07830" strokeWidth="1"/>
      {/* Star on shield */}
      <text x="140" y="244" textAnchor="middle" fontSize="16" fill="#0B1426" fontWeight="bold">★</text>
      {/* Neck */}
      <ellipse cx="140" cy="158" rx="21" ry="27" fill="white"/>
      {/* Head */}
      <ellipse cx="140" cy="118" rx="34" ry="32" fill="white"/>
      {/* Upper beak */}
      <path d="M155,126 Q180,130 172,146 Q162,155 150,146 L154,128 Z" fill="#C9A84C"/>
      {/* Lower beak */}
      <path d="M154,134 Q170,137 164,146 Q158,152 150,146 Z" fill="#A07830"/>
      {/* Beak highlight */}
      <path d="M157,128 Q173,132 168,142" stroke="#E8C56A" strokeWidth="1" fill="none" opacity="0.5"/>
      {/* Nostril */}
      <ellipse cx="167" cy="132" rx="3" ry="2" fill="#8A6520"/>
      {/* Left eye socket */}
      <circle cx="122" cy="112" r="12" fill="#0B1426"/>
      {/* Right eye socket */}
      <circle cx="158" cy="112" r="12" fill="#0B1426"/>
      {/* Left iris */}
      <circle cx="122" cy="112" r="8" fill="#C9A84C"/>
      {/* Right iris */}
      <circle cx="158" cy="112" r="8" fill="#C9A84C"/>
      {/* Left pupil */}
      <circle cx="123" cy="113" r="4.5" fill="#111"/>
      {/* Right pupil */}
      <circle cx="159" cy="113" r="4.5" fill="#111"/>
      {/* Left eye highlight */}
      <circle cx="120" cy="110" r="1.8" fill="white"/>
      {/* Right eye highlight */}
      <circle cx="156" cy="110" r="1.8" fill="white"/>
      {/* Stern left brow */}
      <path d="M108,99 Q118,90 132,96" stroke="#8B7355" strokeWidth="4" fill="none" strokeLinecap="round"/>
      {/* Stern right brow */}
      <path d="M148,96 Q162,90 172,99" stroke="#8B7355" strokeWidth="4" fill="none" strokeLinecap="round"/>
      {/* Head feather detail */}
      <path d="M108,108 Q102,92 114,93" stroke="#ddd" strokeWidth="1.5" fill="none" opacity="0.5"/>
      <path d="M112,102 Q104,85 118,88" stroke="#ddd" strokeWidth="1.5" fill="none" opacity="0.4"/>
      {/* Left leg */}
      <rect x="115" y="272" width="9" height="20" rx="4" fill="#C9A84C"/>
      {/* Right leg */}
      <rect x="156" y="272" width="9" height="20" rx="4" fill="#C9A84C"/>
      {/* Left talons */}
      <path d="M112,290 Q105,300 98,302" stroke="#C9A84C" strokeWidth="3.5" fill="none" strokeLinecap="round"/>
      <path d="M116,292 Q112,303 110,307" stroke="#C9A84C" strokeWidth="3.5" fill="none" strokeLinecap="round"/>
      <path d="M120,291 Q120,303 122,307" stroke="#C9A84C" strokeWidth="3.5" fill="none" strokeLinecap="round"/>
      {/* Right talons */}
      <path d="M168,290 Q175,300 182,302" stroke="#C9A84C" strokeWidth="3.5" fill="none" strokeLinecap="round"/>
      <path d="M164,292 Q168,303 170,307" stroke="#C9A84C" strokeWidth="3.5" fill="none" strokeLinecap="round"/>
      <path d="M160,291 Q160,303 158,307" stroke="#C9A84C" strokeWidth="3.5" fill="none" strokeLinecap="round"/>
    </svg>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#142040] border border-[#1E3A6E] rounded-2xl max-w-lg w-full p-8 shadow-2xl fade-in-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-[#C9A84C]">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl leading-none transition-colors">&times;</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export default function LandingPage({ onUploadClick }) {
  const [modal, setModal] = useState(null)

  return (
    <div className="min-h-screen bg-[#0B1426] flex flex-col">
      {/* Top bar */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-[#1E3A6E]/50">
        <div className="flex items-center gap-2">
          <span className="text-[#C9A84C] font-black text-xl tracking-widest uppercase">VetClaim</span>
        </div>
        <div className="text-xs text-gray-500 hidden md:block">Serving those who served</div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12 text-center">
        {/* Eagle */}
        <div className="fade-in-up mb-2">
          <EagleMascot />
        </div>

        {/* Title */}
        <div className="fade-in-up-2">
          <h1 className="text-5xl md:text-7xl font-black tracking-tight mb-3">
            <span className="text-white">Vet</span>
            <span className="text-[#C9A84C]">Claim</span>
          </h1>
          <p className="text-[#8A9BB5] text-lg md:text-xl max-w-md mx-auto mb-10">
            Your VA benefits, handled with the precision and care you deserve.
          </p>
        </div>

        {/* Buttons */}
        <div className="fade-in-up-3 flex flex-col sm:flex-row gap-4 items-center">
          <button
            onClick={onUploadClick}
            className="w-full sm:w-auto bg-[#C9A84C] hover:bg-[#E8C56A] text-[#0B1426] font-bold px-10 py-4 rounded-xl text-base transition-all duration-200 shadow-lg hover:shadow-[#C9A84C]/30 hover:scale-105 active:scale-95"
          >
            Upload Documents
          </button>
          <button
            onClick={() => setModal('how')}
            className="w-full sm:w-auto border border-[#1E3A6E] hover:border-[#C9A84C] text-[#8A9BB5] hover:text-white font-semibold px-10 py-4 rounded-xl text-base transition-all duration-200 hover:bg-[#142040]"
          >
            How It Works
          </button>
          <button
            onClick={() => setModal('about')}
            className="w-full sm:w-auto border border-[#1E3A6E] hover:border-[#C9A84C] text-[#8A9BB5] hover:text-white font-semibold px-10 py-4 rounded-xl text-base transition-all duration-200 hover:bg-[#142040]"
          >
            About Us
          </button>
        </div>

        {/* Trust badge */}
        <p className="mt-12 text-xs text-gray-600">
          Not affiliated with the U.S. Department of Veterans Affairs &nbsp;·&nbsp; Always consult an accredited VSO
        </p>
      </main>

      {/* How It Works modal */}
      {modal === 'how' && (
        <Modal title="How It Works" onClose={() => setModal(null)}>
          <div className="space-y-5">
            {[
              { step: '01', title: 'Upload Your Documents', desc: 'Submit your C&P Exam, DBQ forms, and VA Rating Decision or Denial Letter.' },
              { step: '02', title: 'We Review Everything', desc: 'Our system analyzes your documents for key findings, gaps, and nexus opportunities.' },
              { step: '03', title: 'Track Your Progress', desc: 'Follow along as your claim moves from submission through review to finalization.' },
            ].map(({ step, title, desc }) => (
              <div key={step} className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-full bg-[#C9A84C]/20 border border-[#C9A84C]/40 flex items-center justify-center flex-shrink-0 text-[#C9A84C] font-bold text-sm">{step}</div>
                <div>
                  <p className="text-white font-semibold mb-1">{title}</p>
                  <p className="text-[#8A9BB5] text-sm leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Modal>
      )}

      {/* About Us modal */}
      {modal === 'about' && (
        <Modal title="About VetClaim" onClose={() => setModal(null)}>
          <div className="space-y-4 text-[#8A9BB5] text-sm leading-relaxed">
            <p>VetClaim was built to help veterans navigate the often confusing VA benefits claims process — so you can focus on your health, not paperwork.</p>
            <p>Our team is dedicated to making sure every veteran gets the benefits they've earned through their service and sacrifice.</p>
            <p className="border-t border-[#1E3A6E] pt-4 text-xs text-gray-600">
              VetClaim is a document preparation tool and does not provide legal or medical advice. For official claims, work with an accredited VSO, attorney, or claims agent.
            </p>
          </div>
        </Modal>
      )}
    </div>
  )
}
