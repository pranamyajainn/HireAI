# 🎯 HireAI - AI-Powered Recruitment Platform

<div align="center">
  
  **Revolutionizing recruitment with artificial intelligence**
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
  [![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
  [![AI Powered](https://img.shields.io/badge/AI-Powered-purple.svg)](https://github.com)
  [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  
</div>

---

## 🌟 Overview

**HireAI** is a comprehensive AI-powered recruitment and candidate screening platform that transforms how companies discover, evaluate, and engage with talent. Built with cutting-edge LLMs (Large Language Models), HireAI combines the power of Google Gemini, ElevenLabs Conversational AI, and advanced parsing algorithms to deliver an unparalleled hiring experience.

---

## ✨ Key Features

### 🔍 **PeopleGPT - Intelligent Candidate Matching**
- **Natural Language Queries**: Search candidates using plain English (e.g., "Senior Python developer in Bangalore with ML experience")
- **AI-Powered Scoring**: Get match scores (0-100%) with detailed reasoning for each candidate
- **Smart Filtering**: Advanced filtering based on skills, experience, location, and more
- **Real-time Results**: Instant candidate recommendations with AI-generated explanations

### 📄 **Resume Intelligence**
- **Multi-format Support**: Upload PDF and DOCX resumes with automatic parsing
- **Smart Extraction**: AI-powered extraction of skills, experience, education, and contact information
- **Structured Profiles**: Convert unstructured resumes into organized candidate profiles
- **Bulk Processing**: Handle multiple resume uploads efficiently

### 🎤 **AI Interviewer (ElevenLabs Integration)**
- **Voice-Based Interviews**: Conduct realistic, conversational interviews using ElevenLabs AI
- **Dynamic Question Generation**: AI creates personalized questions based on candidate responses
- **Professional Conversations**: Natural, engaging interviews under 1 minute
- **Session Logging**: Complete interview tracking with timestamps and recordings

### 🔍 **AI Screening & Background Checks**
- **Instant Verification**: Generate comprehensive background assessments using Gemini AI
- **Pre-screening Questions**: Create tailored interview questions for each candidate
- **Risk Assessment**: Identify potential concerns and red flags automatically
- **Detailed Reports**: Get comprehensive screening reports with actionable insights

### 📧 **Smart Outreach Management**
- **Personalized Templates**: AI-generated, customizable email templates
- **Engagement Tracking**: Monitor email opens, responses, and candidate interactions
- **Automated Follow-ups**: Schedule and manage candidate communication workflows
- **Activity Logging**: Complete history of all outreach activities

### 📊 **Advanced Analytics Dashboard**
- **Hiring Funnel Visualization**: Track candidates through every stage of recruitment
- **Performance Metrics**: Monitor screening efficiency and success rates
- **Candidate Analytics**: Deep insights into your talent pool
- **Interactive Charts**: Beautiful, responsive data visualizations

---

## 🏗️ Architecture & Tech Stack

### **Backend**
- **Framework**: Flask (Python 3.8+)
- **AI/ML**: Google Gemini API, ElevenLabs Conversational AI
- **Data Processing**: Pandas, NumPy
- **PDF Parsing**: pdfplumber, PyPDF2
- **Document Processing**: python-docx, mammoth

### **Frontend**
- **Templates**: Jinja2 with modern HTML5/CSS3
- **Styling**: Custom CSS with dark mode support
- **Icons**: Font Awesome, Lucide React
- **Animations**: Smooth transitions and micro-interactions
- **Responsive**: Mobile-first design approach

### **Storage & Data**
- **File Storage**: Local filesystem with organized structure
- **Data Format**: JSON-based candidate profiles
- **Logging**: Comprehensive activity and error logging
- **Export**: CSV and JSON export capabilities

---

## 📁 Project Structure

```
HireAI/
│
├── 📱 app.py                      # Main Flask application & API endpoints
├── ⚙️  config.py                   # Configuration & environment settings
├── 📋 requirements.txt            # Python dependencies
├── 📖 README.md                   # This comprehensive guide
│
├── 📊 data/
│   ├── candidates.json         # Parsed candidate profiles database
│   ├── email_templates.json    # Outreach email templates
│   ├── outreach_log.json       # Communication activity log
│   └── uploads/                # Uploaded resume files (PDF/DOCX)
│
├── 🎨 static/
│   ├── css/
│   │   ├── styles.css          # Main application styles
│   │   └── ai-overlay.css      # AI overlay widget styles
│   ├── js/
│   │   └── ai-overlay.js       # Interactive JavaScript components
│   └── images/                 # Screenshots, logos, and assets
│
├── 🖼️  templates/
│   ├── index.html              # Landing page & dashboard
│   ├── upload.html             # Resume upload interface
│   ├── candidates.html         # Candidate listing & search
│   ├── candidate_detail.html   # Individual candidate profiles
│   ├── search.html             # Basic search functionality
│   ├── search_enhanced.html    # PeopleGPT enhanced search
│   ├── background_check.html   # AI screening & background checks
│   ├── outreach.html           # Outreach management dashboard
│   ├── analytics.html          # Analytics & reporting
│   └── error.html              # Error handling pages
│
├── 🔧 utils/
│   ├── ai_interviewer.py       # ElevenLabs AI interview integration
│   ├── ai_matcher.py           # PeopleGPT candidate matching engine
│   ├── ai_screening.py         # Gemini-powered screening & background checks
│   ├── job_analyzer.py         # Job description analysis & parsing
│   ├── outreach_manager.py     # Email outreach & template management
│   ├── query_parser.py         # Natural language query processing
│   └── resume_parser.py        # Resume PDF/DOCX parsing & extraction
│
└── 🧪 test_email.py               # Email functionality testing
```

---

## 🚀 Quick Start Guide

### 1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/hireai.git
cd hireai
```

### 2. **Set Up Python Environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Configure Environment Variables**
Create a `.env` file in the root directory:

```env
# Required: Google Gemini API Key
GEMINI_API_KEY=your_google_gemini_api_key_here

# Optional: ElevenLabs API Key (for AI Interviewer)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional: OpenAI API Key (alternative to Gemini)
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
FLASK_ENV=development
DEBUG=True
```

### 5. **Launch the Application**
```bash
python app.py
```

### 6. **Access HireAI**
Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)

---

## 💡 How to Use HireAI

### **Step 1: Upload Resumes**
1. Navigate to **"Upload Resume"** from the main dashboard
2. Select PDF or DOCX files (supports multiple uploads)
3. Click **"Upload"** - AI will automatically parse and extract candidate data
4. View parsed information and make any necessary corrections

### **Step 2: PeopleGPT Candidate Search**
1. Go to **"AI Screening"** or **"Enhanced Search"**
2. Enter your job requirements in natural language:
   - *"Senior Full-Stack Developer with React and Node.js experience in San Francisco"*
   - *"Data Scientist with Python, ML, and 3+ years experience"*
   - *"Marketing Manager with digital marketing and social media expertise"*
3. Click **"Search Candidates"**
4. Review AI-matched candidates with scores and detailed reasoning

### **Step 3: AI Screening & Background Checks**
1. Select any candidate from your search results
2. Click **"Generate Background Check"** or **"AI Screening"**
3. Review comprehensive screening reports including:
   - Background verification assessment
   - Customized pre-screening questions
   - Risk analysis and recommendations
   - Interview talking points

### **Step 4: AI-Powered Interviews** 🎤
1. Navigate to the candidate's profile
2. Click **"Start AI Interview"**
3. Configure interview settings (voice, duration, focus areas)
4. The ElevenLabs AI interviewer will:
   - Greet the candidate professionally
   - Ask tailored questions based on their background
   - Conduct a natural, conversational interview
   - Provide interview summary and recommendations

### **Step 5: Outreach Management**
1. Go to **"Outreach"** dashboard
2. Select candidates for outreach campaigns
3. Choose from AI-generated email templates or create custom ones
4. Send personalized emails and track engagement
5. Monitor responses and schedule follow-ups

### **Step 6: Analytics & Insights**
1. Visit the **"Analytics"** dashboard
2. Monitor hiring funnel metrics
3. Track candidate engagement and conversion rates
4. Generate reports for stakeholders
5. Identify optimization opportunities

---

## 🎤 AI Interviewer Deep Dive

### **Revolutionary Voice-Based Screening**

The AI Interviewer feature represents a breakthrough in automated candidate screening, leveraging ElevenLabs' state-of-the-art conversational AI technology.

#### **Key Capabilities:**
- **Natural Conversations**: Human-like dialogue that puts candidates at ease
- **Dynamic Questioning**: AI adapts questions based on candidate responses
- **Professional Assessment**: Evaluates communication skills, technical knowledge, and cultural fit
- **Efficient Screening**: Conducts meaningful interviews in under 5 minutes

#### **Technical Implementation:**
```python
# Example: Creating an AI Interview Session
interviewer = AIInterviewer()
session = interviewer.create_interview_session(
    candidate_name="John Doe",
    job_description="Senior Python Developer",
    interview_duration="3 minutes",
    focus_areas=["technical_skills", "problem_solving", "communication"]
)
```

#### **Interview Flow:**
1. **Greeting & Introduction**: Professional welcome and candidate introduction
2. **Background Discussion**: Questions about experience and skills
3. **Technical Assessment**: Role-specific technical questions
4. **Situational Queries**: Problem-solving and behavioral questions
5. **Wrap-up**: Opportunity for candidate questions and next steps

---

## 🔧 Configuration & Customization

### **AI Model Configuration**
```python
# In config.py - Switch between AI providers
AI_PROVIDER = "gemini"  # Options: "gemini", "openai", "local"
GEMINI_MODEL = "gemini-1.5-flash"
TEMPERATURE = 0.7
MAX_TOKENS = 1000
```

### **Screening Parameters**
```python
# Customize screening criteria
SCREENING_CONFIG = {
    "min_experience_years": 2,
    "required_skills_match": 0.7,
    "location_preference": True,
    "salary_range_consideration": True
}
```

### **UI Customization**
- Modify `static/css/styles.css` for visual customization
- Update templates in `templates/` for layout changes
- Configure color schemes, fonts, and animations
- Add custom logos and branding elements

---

## 📈 Advanced Features

### **Batch Processing**
- Upload and process multiple resumes simultaneously
- Bulk candidate screening and scoring
- Mass outreach campaigns with personalization

### **Integration Capabilities**
- REST API endpoints for third-party integrations
- Webhook support for real-time notifications
- Export capabilities (CSV, JSON, PDF reports)

### **Security & Privacy**
- Secure file handling and storage
- Data encryption for sensitive information
- GDPR compliance considerations
- Audit trails for all activities

---

## 🐛 Troubleshooting

### **Common Issues & Solutions**

#### **Import Errors**
```bash
# Ensure correct Python interpreter
python --version
pip list

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### **API Key Issues**
```bash
# Verify environment variables
echo $GEMINI_API_KEY
echo $ELEVENLABS_API_KEY

# Check .env file format (no spaces around =)
GEMINI_API_KEY=your_key_here
```

#### **Resume Parsing Issues**
- Ensure PDF files are text-based (not scanned images)
- Check file permissions and storage space
- Verify supported file formats (PDF, DOCX)

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### **Getting Started**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### **Contribution Guidelines**
- Follow PEP 8 style guidelines for Python code
- Add comprehensive tests for new features
- Update documentation for any API changes
- Ensure backward compatibility when possible

### **Areas for Contribution**
- 🔍 Additional AI model integrations
- 🎨 UI/UX improvements and themes
- 📊 Advanced analytics and reporting
- 🔌 Third-party integrations (ATS, CRM)
- 🌐 Internationalization and localization

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 HireAI Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 Acknowledgments

- **Google Gemini AI** - For powerful natural language processing capabilities
- **ElevenLabs** - For revolutionary conversational AI technology
- **Flask Community** - For the robust web framework
- **Open Source Contributors** - For the amazing libraries and tools

---

<div align="center">
  
  **Built with ❤️ by Team Seeds! 🌱**
  
  *Revolutionizing recruitment with artificial intelligence*
  
  ⭐ **Star this repo if you found it helpful!** ⭐
  
</div>

---


*Last updated: June 2025*
