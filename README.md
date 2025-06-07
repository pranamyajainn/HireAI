# HireAI

**HireAI** is an intelligent resume management and candidate pre-screening platform powered by AI. Upload resumes, parse candidate data automatically, and generate instant pre-screening summaries and interview questions to supercharge your hiring process.

---

## 🚀 Features

- **Resume Upload:** Supports PDF and DOCX formats
- **Automatic Parsing:** Extracts candidate name, skills, experience, and contact info
- **Candidate Database:** Browse, search, and filter uploaded resumes
- **AI Pre-Screening:** One-click summary and custom Q&A for every candidate using LLMs (e.g., OpenAI, Gemini)
- **Modern UI:** Responsive design with enhanced navigation and candidate cards
- **Export:** Download candidate data as CSV for further analysis

---

## 🖥️ Screenshots

<!-- Add your screenshots here -->
<!-- ![Screenshot of candidate list](static/screenshots/candidates.png) -->

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML/CSS/JS (Jinja2 templates, Font Awesome, Google Fonts)
- **Parsing:** `pdfplumber` / `PyPDF2` for PDF, `python-docx` for DOCX (customizable)
- **AI Integration:** OpenAI GPT / Gemini (Google) for pre-screening (easy to swap)

---

## ⚡ Quickstart

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/hireai.git
   cd hireai
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API keys (for AI):**
   - Create a `.env` file or export `OPENAI_API_KEY`/`GEMINI_API_KEY` as environment variables.

5. **Run the app:**
   ```bash
   flask run
   ```

6. **Open your browser:**  
   Visit [http://localhost:5000](http://localhost:5000)

---

## 📝 Usage

- **Upload Resume:** Go to the "Upload Resume" tab, select a file, and submit.
- **View Candidates:** Click "View Candidates" to see the database. Use filters & search as needed.
- **Candidate Details:** Click a candidate card to view their profile.
- **AI Pre-Screening:** On a candidate’s page, click "Run AI Screening" to generate a summary and pre-screening questions.

---

## 🤖 AI Screening

HireAI connects to LLMs (like OpenAI or Gemini) to:
- Summarize candidate profiles
- Generate relevant pre-screening/interview questions

> *You can customize the AI prompt and swap out providers easily in `app.py`.*

---

## 📦 Directory Structure

```
hireai/
│
├── app.py
├── requirements.txt
├── uploads/                 # Uploaded resumes (PDF, DOCX)
├── templates/
│   ├── index.html
│   ├── candidates.html
│   ├── candidate_detail.html
│   └── error.html
├── static/
│   ├── css/
│   └── screenshots/
└── README.md
```

---

## 🙌 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

[MIT](LICENSE)

---

## 💡 Credits

Built with ❤️ by Team Seeds 🌱
