# 🚀 AI Placement Co-Pilot

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ai-placement-copilot.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Powered by Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


An end-to-end, AI-powered career enablement platform designed to bridge the gap between job seekers and Applicant Tracking Systems (ATS). Features hybrid semantic resume scanning, automated STAR-framework tailoring, dynamic LLM-driven mock interviews with real-time scoring, and candidate readiness analytics.

---

## 🌐 Live Deployment

Try the live application: **[AI Placement Co-Pilot](https://ai-placement-copilot.streamlit.app)**

---

## 📌 Key Features

### 1. 🎯 Hybrid ATS Resume Scanner
* **Dual-Layer Matching**: Combines dense semantic similarity via Sentence-Transformers (`all-MiniLM-L6-v2`) with sparse Jaccard keyword matching.
* **Granular Extraction**: Extracts raw text directly from PDF resumes using `PyMuPDF` (`fitz`).
* **Visual Diagnostics**: Interactive Plotly radar charts mapping technical overlap, experience alignment, and missing keyword breakdowns.

### 2. ✍️ Resume Optimizer & DOCX Exporter
* **STAR Methodology**: Automatically rewrites candidate bullet points into measurable **Situation-Task-Action-Result** formats.
* **One-Click Export**: Generates clean, ATS-compliant `.docx` resumes formatted with standard margins and typographic hierarchy using `python-docx`.

### 3. 🎙️ Adaptive AI Mock Interviewer
* **Dynamic Entropy Engine**: Generates non-repetitive, situational scenario questions for specific roles using `gemini-1.5-flash` with randomized session seeds.
* **Strict Rubric Evaluation**: Evaluates candidate responses on technical depth, methodology, and clarity (1.0–10.0 scale) while detecting gibberish or empty submissions.
* **Actionable Feedback**: Delivers immediate breakdowns of key strengths, missed concepts, and exemplar model answers.

### 4. 📊 Readiness Roadmap & Telemetry
* **Session Persistence**: SQLite database integration to securely track user accounts, scan history, and mock interview performance over time.
* **Placement Readiness Score**: Aggregated readiness index combining ATS compatibility scores and mock interview averages.

---

## 🛠️ Architecture & Tech Stack

```text
AI-PLACEMENT-COPILOT/
├── app.py # Streamlit UI controller & multi-tab navigation
├── ats_scanner.py # SBERT embeddings & hybrid semantic matching
├── mock_interviewer.py # Gemini LLM interview generation & evaluation
├── resume_generator.py # STAR optimization & dynamic tailoring logic
├── docx_exporter.py # ATS-compliant DOCX document builder
├── database.py # SQLite persistence layer & schema migrations
├── requirements.txt # Production dependencies
├── .gitignore # Environment & artifact exclusions
└── README.md # Project documentation
```



* **Frontend**: Streamlit, Streamlit Option Menu, Plotly
* **AI & NLP**: Google Gemini API (`gemini-1.5-flash`), Sentence-Transformers (`all-MiniLM-L6-v2`), Scikit-Learn
* **Document Processing**: PyMuPDF (`fitz`), Python-Docx, PyPDF
* **Validation & Storage**: Pydantic v2, SQLite3
* **Deployment**: Streamlit Community Cloud, GitHub Actions

---

## 🚀 Local Installation & Setup

### Prerequisites
* Python 3.10 or 3.11 installed
* Gemini API Key 

### 1. Clone the Repository
```bash
git clone [https://github.com/Mudasir287/AI-PLACEMENT-COPILOT.git](https://github.com/Mudasir287/AI-PLACEMENT-COPILOT.git)
cd AI-PLACEMENT-COPILOT

2. Create and Activate a Virtual Environment
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root directory:
GEMINI_API_KEY=your_google_gemini_api_key_here

5. Launch the Application
streamlit run app.py

Open your browser and navigate to http://localhost:8501.
☁️ Deployment Guide (Streamlit Community Cloud)
 * Push your repository to GitHub.
 * Navigate to Streamlit Community Cloud and click New App.
 * Select your repository, set the branch to main, and specify app.py as the Main file path.
 * Under Advanced Settings -> Secrets, add:
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"

 * Click Deploy.
📄 License
This project is licensed under the MIT License 

---
