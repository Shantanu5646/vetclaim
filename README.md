# Vetclaim 🇺🇸 (Hackthon Project)

**An AI-powered advocate and multi-agent pipeline for Veterans Affairs (VA) claims**

> Built during **HackUSF** for a Google-sponsored track.

## ✨ What is Vetclaim?

Vetclaim is an intelligent platform designed to make the VA claims process less confusing, less manual, and more veteran-friendly.

Instead of one static workflow, Vetclaim uses a team of specialized AI agents that work together to:

- 📄 read and understand messy claim documents
- ⚖️ audit claims against VA rules and ratings logic
- 🧩 map data into strict government form fields
- 🖨️ generate filing-ready PDFs
- 📞 help with VA customer care calls using voice AI
- 💬 give veterans a live, context-aware support experience

The goal is simple: reduce the paperwork burden and help veterans move through the claims process with more clarity and confidence.

## 🚀 Key Features

### 🧠 Multi-Agent Orchestration
Uses **Google ADK** to coordinate multiple specialized agents, each focused on one part of the workflow.

### 📄 Smart Document Parsing
Extracts structured claim data from unstructured documents such as:

- DBQs
- Decision Letters
- Personal Statements

### ⚖️ Deterministic Legal Auditing
Uses Gemini for reasoning and analysis, while keeping rating calculations and legal checks grounded in deterministic Python tools.

This includes:

- VA combined ratings
- TDIU eligibility
- PACT Act presumptions
- CFR-based comparisons

### ✍️ Automated Form Filling
Maps user data into rigid VA PDF forms and prepares them for filing.

### 📞 Voice AI Advocacy
Integrates with **Vapi AI** to place outbound calls to VA customer care and return transcripts + summaries to the user.

### 💬 Context-Aware Chat Assistant
Provides a live assistant interface that can respond using:

- claim audit results
- active CFR references
- benefit impact calculations

## 🏗️ Architecture Overview

Vetclaim is built around a strict separation of concerns:

- **LLMs** handle language understanding, extraction, and routing
- **Python tools** handle calculations, validation, and legal logic
- **Agents** coordinate the full workflow end-to-end

### Pipeline

**1. Parser Agent**  
Reads PDFs and extracts relevant claim details into a validated schema.

**2. Auditor Agent**  
Checks the claim against VA rules and flags possible issues such as under-ratings or missing service connections.

**3. Mapping Agent**  
Matches logical claim data to the field names used in legacy VA forms.

**4. Filer Agent**  
Fetches blank forms, fills them, and prepares completed PDFs for submission.


## 🛠️ Tech Stack

### Backend
- Python 3.10+
- Flask
- Google Agent Development Kit (ADK)
- Google GenAI SDK (Gemini 2.5 Flash)
- Pydantic
- pdfplumber
- pypdf

### Frontend
- React
- Vite
- TypeScript

### Integrations
- VA Lighthouse API
- Vapi AI
- ElevenLabs


## ⚙️ Getting Started

### Prerequisites
Make sure you have:

- Python 3.10 or higher
- Node.js and npm
- API keys for:
  - Google Gemini
  - Vapi AI
  - VA Lighthouse sandbox
  - ElevenLabs


### 
1) Clone the repository

bash
git clone https://github.com/yourusername/vetclaim.git
cd vetclaim

2) Backend setup

Create and activate a virtual environment:

python -m venv venv
venv\Scripts\activate   # Windows

Install dependencies:

pip install -r requirements.txt

Create a .env file in the backend directory or root directory, depending on your project structure:

GOOGLE_API_KEY=your_gemini_key_here

VAPI_PRIVATE_KEY=your_vapi_key_here

VA_FORMS_API_KEY=your_va_sandbox_key_here

ELEVENLABS_API_KEY=your_elevenlabs_key_here

VA_API_KEY=your_va_benefits_key_here

VITE_API_BASE_URL=http://localhost:5001

Start the backend server:

python server.py

The backend runs on:

http://localhost:5001

3) Frontend setup

Open a new terminal, then run:

cd frontend
npm install
npm run dev

The frontend runs on:

http://localhost:5173
🧪 Running Tests

Vetclaim includes testing for pipeline stability and streaming behavior.

Run the test suite:

pytest backend/test_server_properties.py
python backend/test_auditor_tools.py

🤝 Contributing

This project was originally built as a hackathon project, so active development may be limited.

Still, contributions are welcome for:

architecture improvements
better VA form support
additional agent workflows
new integrations
UI/UX enhancements

📌 Notes
This project is designed to assist with the claims process, not replace official VA guidance.
Legal and rating logic should always be validated carefully.
Replace placeholder links and keys before deployment.
