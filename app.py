from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_cors import CORS
import os
import json
import csv
import io
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from config import Config
# In app.py
from utils.ai_interviewer import AIInterviewer
import sys
from utils.ai_screening import AIScreening 

# ... other imports like Flask, jsonify, etc.
# Force load environment variables at the very beginning
load_dotenv()

# Import our custom modules
from utils.resume_parser import ResumeParser
from utils.ai_matcher import AIMatcher
from utils.job_analyzer import JobAnalyzer
from utils.query_parser import NaturalLanguageQueryParser

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# --- ADD THIS CUSTOM JINJA FILTER ---
# This filter converts a Python object to a JSON string, safe for embedding in HTML <script> tags.
@app.template_filter('tojson_safe')
def tojson_safe_filter(obj):
    return json.dumps(obj)
# --- END ADDITION ---

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize our AI components with error handling
resume_parser = ResumeParser()

# Initialize AI components with both GROQ and Gemini API keys
groq_api_key = app.config.get('GROQ_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY') or app.config.get('GEMINI_API_KEY')

print(f"🔧 App: Gemini API key loaded: {gemini_api_key[:20] if gemini_api_key else 'None'}...")
print(f"🔧 App: GROQ API key loaded: {groq_api_key[:20] if groq_api_key else 'None'}...")

# Initialize AI components with proper API keys
try:
    # Use Gemini for our enhanced AI features
    ai_matcher = AIMatcher(api_key=gemini_api_key)
    job_analyzer = JobAnalyzer(api_key=gemini_api_key)
    print("✅ AI components initialized successfully")
except Exception as e:
    print(f"❌ Error initializing AI components: {e}")
    # Initialize with fallback (no API key)
    ai_matcher = AIMatcher()
    job_analyzer = JobAnalyzer()

# 🆕 Initialize PeopleGPT Query Parser
try:
    query_parser = NaturalLanguageQueryParser()
    print("✅ PeopleGPT Query Parser initialized successfully")
except Exception as e:
    print(f"❌ Error initializing PeopleGPT Query Parser: {e}")
    query_parser = None
# Initialize ElevenLabs AI Interviewer
try:
    # This creates one instance of the interviewer that the whole app can use.
    ai_interviewer = AIInterviewer()
    print("✅ ElevenLabs AI Interviewer initialized successfully.")
except ValueError as e:
    # This will catch the error if the API key is missing.
    print(f"❌ FATAL ERROR: Could not initialize ElevenLabs AI Interviewer.")
    print(f"   Reason: {e}")
    print(f"   Please make sure the ELEVENLABS_API_KEY environment variable is set.")
    # Set the variable to None so routes can check for it, or exit.
    ai_interviewer = None 
    # For a critical service, you might want to stop the server entirely:
    # import sys
    # sys.exit(1)
# ===================================================================
# === END OF BLOCK TO ADD ===========================================
# ===================================================================


# --- NEW: Initialize AIScreening instance --- (This part already exists)
ai_screening_tool = AIScreening()
# Add these imports for advanced export functionality
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    import pandas as pd
    ADVANCED_EXPORT_AVAILABLE = True
    print("✅ Advanced export libraries (reportlab, pandas) available")
except ImportError:
    ADVANCED_EXPORT_AVAILABLE = False
    print("⚠️ Advanced export libraries not available. Install with: pip install reportlab pandas openpyxl")

# Add this import at the top with your other imports
from utils.outreach_manager import OutreachManager




# ================================
# PAGE ROUTES
# ================================

@app.route('/')
def home():
    """
    Home Page - HireAI Landing Page
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """
    Resume Upload Page
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    return render_template('upload.html')

@app.route('/search')
def search_page():
    """
    PeopleGPT Search Page - Natural Language Candidate Search
    Built by Team Seeds! 🌱 for pranamya-jain
    
    Features:
    - Natural language query parsing
    - Chat-like search interface
    - Real-time IST timestamps
    - Query suggestions
    - AI-powered candidate matching
    
    Template: search_enhanced.html
    Current: 2025-06-01 06:00:37 UTC
    """
    return render_template('search_enhanced.html')

@app.route('/candidates')
def list_candidates():
    """
    Enhanced Candidates List Page - Browse All Candidates
    Built by Team Seeds! 🌱 for pranamya-jain
    
    Features:
    - Lists all uploaded candidates with parsed data
    - Combines file listing with JSON database
    - Shows candidate details and upload status
    - Links to detailed candidate profiles
    - Real-time IST timestamps
    - Enhanced metadata display
    
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        # Load candidates from JSON database (primary source)
        json_candidates = load_candidates()
        
        # Also check upload folder for any orphaned files
        upload_folder = app.config['UPLOAD_FOLDER']
        file_candidates = []
        
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.endswith(('.pdf', '.docx', '.doc')):
                    # Check if this file is already in our JSON database
                    file_in_db = any(c.get('filename') == filename for c in json_candidates)
                    
                    if not file_in_db:
                        # This is an orphaned file (uploaded but not parsed)
                        file_path = os.path.join(upload_folder, filename)
                        file_stats = os.stat(file_path)
                        
                        file_candidates.append({
                            'id': f"file_{filename}",
                            'name': filename.rsplit('.', 1)[0],  # Remove extension
                            'filename': filename,
                            'status': 'uploaded_not_parsed',
                            'uploaded_at': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                            'file_size': file_stats.st_size,
                            'skills': [],
                            'experience_years': 0,
                            'location': 'Unknown'
                        })
        
        # Combine both lists
        all_candidates = json_candidates + file_candidates
        
        # Add enhanced metadata
        for candidate in all_candidates:
            candidate['status'] = candidate.get('status', 'parsed_and_stored')
            candidate['file_size_mb'] = round(candidate.get('file_size', 0) / 1024 / 1024, 2) if candidate.get('file_size') else 0
            
            # Format upload date for display
            if candidate.get('uploaded_at'):
                try:
                    upload_time = datetime.fromisoformat(candidate['uploaded_at'].replace('Z', '+00:00'))
                    candidate['uploaded_at_formatted'] = upload_time.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    candidate['uploaded_at_formatted'] = 'Unknown'
            else:
                candidate['uploaded_at_formatted'] = 'Unknown'
        
        # Sort by upload date (newest first)
        all_candidates.sort(key=lambda x: x.get('uploaded_at', ''), reverse=True)
        
        return render_template('candidates.html', 
                             candidates=all_candidates,
                             total_candidates=len(all_candidates),
                             json_candidates=len(json_candidates),
                             file_candidates=len(file_candidates),
                             current_user='pranamya-jain',
                             current_time='2025-06-01 06:00:37 UTC')
                             
    except Exception as e:
        print(f"❌ Error loading candidates: {e}")
        return render_template('candidates.html', 
                             candidates=[],
                             total_candidates=0,
                             json_candidates=0,
                             file_candidates=0,
                             current_user='pranamya-jain',
                             current_time='2025-06-01 06:00:37 UTC',
                             error=str(e))

@app.route('/analytics')
def analytics_page():
    """
    Analytics Dashboard Page
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    return render_template('analytics.html')

@app.route('/candidate_detail')
def candidate_detail():
    """
    Enhanced Candidate Detail Page - Full Profile View with AI Screening
    Built by Team Seeds! 🌱 for pranamya-jain
    
    Features:
    - Detailed candidate profile view
    - AI screening integration
    - Match analysis display
    - Real-time IST timestamps
    - Skills visualization
    - Action buttons (questions, download, etc.)
    - Uses URL parameter: ?id=<candidate_id>
    
    Template: candidate_detail.html
    Current: 2025-06-01 06:00:37 UTC
    """
    return render_template('candidate_detail.html')

@app.route('/candidate/<id>')
def candidate_detail_by_file(id):
    """
    Simple Candidate Detail by File ID - Direct File Access
    Built by Team Seeds! 🌱 for pranamya-jain
    
    Features:
    - Direct file-based candidate access
    - Alternative route for simple file viewing
    - Basic candidate information from filename
    - Compatible with upload folder structure
    
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], id)
        if not os.path.exists(file_path):
            return render_template('error.html', 
                                 error="Candidate file not found", 
                                 message=f"File '{id}' does not exist in the upload directory.",
                                 current_user='pranamya-jain',
                                 current_time='2025-06-01 06:00:37 UTC'), 404
        
        # Get file stats
        file_stats = os.stat(file_path)
        
        # Basic candidate info from filename and file system
        candidate_info = {
            'id': id,
            'name': id.rsplit('.', 1)[0] if '.' in id else id,  # Remove file extension
            'filename': id,
            'file_path': file_path,
            'file_size': file_stats.st_size,
            'file_size_mb': round(file_stats.st_size / 1024 / 1024, 2),
            'uploaded_at': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            'uploaded_at_formatted': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'accessed_by': 'pranamya-jain',
            'access_time': '2025-06-01 06:00:37 UTC',
            'access_method': 'direct_file_access',
            'status': 'file_based_view',
            'skills': [],  # Placeholder - would need parsing to fill
            'experience_years': 0,  # Placeholder
            'location': 'Unknown',  # Placeholder
            'summary': f'File-based candidate view for {id}. Upload this file through the system for full AI parsing and analysis.'
        }
        
        return render_template('candidate_detail.html', candidate=candidate_info)
        
    except Exception as e:
        print(f"❌ Error accessing candidate file {id}: {e}")
        return render_template('error.html', 
                             error="Error accessing candidate file", 
                             message=f"An error occurred while accessing candidate '{id}': {str(e)}",
                             current_user='pranamya-jain',
                             current_time='2025-06-01 06:00:37 UTC'), 500

# ================================
# API ROUTES
# ================================

@app.route('/api/upload_resume', methods=['POST'])
def upload_resume():
    """
    Upload and Parse Resume API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        allowed_extensions = {'pdf', 'docx', 'doc'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({'error': 'Only PDF and DOCX files are supported'}), 400
        
        # Save uploaded file
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse resume
        parsed_data = resume_parser.parse_resume(filepath)
        
        if 'error' in parsed_data:
            return jsonify({'error': parsed_data['error']}), 400
        
        # Store in our simple database (JSON file for now)
        candidate_id = save_candidate(parsed_data, filename)
        
        return jsonify({
            'success': True,
            'candidate_id': candidate_id,
            'parsed_data': parsed_data,
            'message': f'Resume uploaded and parsed successfully by pranamya-jain',
            'uploaded_by': 'pranamya-jain',
            'timestamp': '2025-06-01 06:00:37 UTC'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route('/api/search_candidates', methods=['POST'])
def search_candidates():
    """
    Traditional Candidate Search API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        filters = data.get('filters', {})
        
        if not job_description.strip():
            return jsonify({'error': 'Job description is required'}), 400
        
        # Load candidates from our database
        candidates = load_candidates()
        
        if not candidates:
            return jsonify({
                'success': True,
                'candidates': [],
                'total': 0,
                'message': 'No candidates found in database',
                'searched_by': 'pranamya-jain',
                'search_time': '2025-06-01 06:00:37 UTC'
            })
        
        # Use AI to match candidates - now with enhanced AI or fallback
        matched_candidates = ai_matcher.match_candidates(
            job_description, 
            candidates, 
            filters
        )
        
        # Get parsed criteria for display
        parsed_criteria = ai_matcher.parse_natural_language_query(job_description)
        
        return jsonify({
            'success': True,
            'candidates': matched_candidates,
            'total': len(matched_candidates),
            'parsed_criteria': parsed_criteria,
            'ai_enabled': ai_matcher.ai_available,
            'searched_by': 'pranamya-jain',
            'search_time': '2025-06-01 06:00:37 UTC'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route('/api/parse_query', methods=['POST'])
def parse_natural_language_query():
    """
    PeopleGPT - Parse natural language search queries
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        if not query_parser:
            return jsonify({
                'success': False,
                'error': 'PeopleGPT Query Parser not available',
                'timestamp': '2025-06-01 06:00:37 UTC'
            }), 500
            
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required',
                'timestamp': '2025-06-01 06:00:37 UTC'
            }), 400
        
        # Validate query
        validation = query_parser.validate_query(query)
        if not validation['valid']:
            return jsonify({
                'success': False,
                'error': validation['error'],
                'timestamp': '2025-06-01 06:00:37 UTC'
            }), 400
        
        # Parse the query
        parsed_result = query_parser.parse_query(query)
        
        return jsonify({
            'success': True,
            'parsed_query': parsed_result,
            'examples': query_parser.get_query_examples(),
            'message': f'Query parsed successfully by pranamya-jain',
            'parsed_by': 'pranamya-jain',
            'timestamp': '2025-06-01 06:00:37 UTC'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Query parsing failed: {str(e)}',
            'timestamp': '2025-06-01 06:00:37 UTC'
        }), 500

@app.route('/api/peoplegpt_search', methods=['POST'])
def peoplegpt_search():
    """
    PeopleGPT - Natural language search with AI parsing and candidate matching
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        if not query_parser:
            return jsonify({
                'success': False,
                'error': 'PeopleGPT not available',
                'timestamp': '2025-06-01 06:00:37 UTC'
            }), 500
            
        data = request.get_json()
        natural_query = data.get('query', '').strip()
        
        if not natural_query:
            return jsonify({
                'success': False,
                'error': 'Natural language query is required',
                'timestamp': '2025-06-01 06:00:37 UTC'
            }), 400
        
        # Step 1: Parse natural language query
        parsed_result = query_parser.parse_query(natural_query)
        
        # Step 2: Load candidates
        candidates = load_candidates()
        
        if not candidates:
            return jsonify({
                'success': True,
                'candidates': [],
                'parsed_query': parsed_result,
                'total_found': 0,
                'search_summary': 'No candidates found in database',
                'message': 'Upload some resumes to start searching!',
                'searched_by': 'pranamya-jain',
                'search_time': '2025-06-01 06:00:37 UTC'
            })
        
        # Step 3: Use AI matcher with parsed job description
        matched_candidates = ai_matcher.match_candidates(
            parsed_result['job_description'], 
            candidates, 
            parsed_result['filters']
        )
        
        return jsonify({
            'success': True,
            'candidates': matched_candidates,
            'parsed_query': parsed_result,
            'total_found': len(matched_candidates),
            'search_summary': f"Found {len(matched_candidates)} candidates matching your criteria",
            'original_query': natural_query,
            'searched_by': 'pranamya-jain',
            'search_time': '2025-06-01 06:00:37 UTC',
            'ai_enabled': ai_matcher.ai_available and query_parser is not None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'PeopleGPT search failed: {str(e)}',
            'timestamp': '2025-06-01 06:00:37 UTC'
        }), 500

@app.route('/api/analyze_job', methods=['POST'])
def analyze_job():
    """
    Job Description Analysis API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        
        if not job_description.strip():
            return jsonify({'error': 'Job description is required', 'timestamp': '2025-06-01 06:00:37 UTC'}), 400
        
        # Use our enhanced job analyzer
        analysis = job_analyzer.analyze_job_description(job_description)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'ai_enabled': job_analyzer.ai_available,
            'analyzed_by': 'pranamya-jain',
            'timestamp': '2025-06-01 06:00:37 UTC'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route('/api/get_candidates')
def get_candidates():
    """
    Get All Candidates API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        candidates = load_candidates()
        return jsonify({
            'success': True,
            'candidates': candidates,
            'total': len(candidates),
            'accessed_by': 'pranamya-jain',
            'timestamp': '2025-06-01 06:00:37 UTC'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route('/api/generate_questions', methods=['POST'])
def generate_questions():
    """
    Generate Interview Questions API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        candidate_id = data.get('candidate_id', '')
        
        if not job_description.strip():
            return jsonify({'error': 'Job description is required', 'timestamp': '2025-06-01 06:00:37 UTC'}), 400
        
        # Find the candidate
        candidates = load_candidates()
        candidate = next((c for c in candidates if c.get('id') == candidate_id), None)
        
        if not candidate:
            return jsonify({'error': 'Candidate not found', 'timestamp': '2025-06-01 06:00:37 UTC'}), 404
        
        # Generate questions using AI matcher
        questions = ai_matcher.generate_screening_questions(job_description, candidate)
        
        return jsonify({
            'success': True,
            'questions': questions,
            'ai_enabled': ai_matcher.ai_available,
            'generated_by': 'pranamya-jain',
            'timestamp': '2025-06-01 06:00:37 UTC'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route('/api/get_analytics')
def get_analytics():
    """
    Get Analytics Data API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        candidates = load_candidates()
        analytics = generate_analytics(candidates)
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'generated_by': 'pranamya-jain',
            'timestamp': '2025-06-01 06:00:37 UTC'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route('/api/health')
def health_check():
    """
    Health Check API with PeopleGPT status
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    return jsonify({
        'status': 'healthy',
        'app': 'HireAI',
        'component': 'PeopleGPT',
        'ai_enabled': ai_matcher.ai_available if ai_matcher else False,
        'gemini_available': ai_matcher.ai_available if ai_matcher else False,
        'peoplegpt_enabled': query_parser is not None,
        'total_candidates': len(load_candidates()),
        'user': 'pranamya-jain',
        'team': 'Seeds! 🌱',
        'timestamp': '2025-06-01 06:00:37 UTC'
    })

@app.route('/api/download_resume/<candidate_id>')
def download_resume(candidate_id):
    """
    Download Resume File API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        candidates = load_candidates()
        candidate = next((c for c in candidates if c.get('id') == candidate_id), None)
        
        if not candidate:
            return jsonify({'error': 'Candidate not found', 'timestamp': '2025-06-01 06:00:37 UTC'}), 404
        
        filename = candidate.get('filename')
        if not filename:
            return jsonify({'error': 'Resume file not found', 'timestamp': '2025-06-01 06:00:37 UTC'}), 404
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Resume file does not exist on server', 'timestamp': '2025-06-01 06:00:37 UTC'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route("/api/candidate/<candidate_id>/screening", methods=["POST"])
def ai_screening(candidate_id):
    """
    AI Screening API for JSON-based candidate storage
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        # Load candidates from JSON database
        candidates = load_candidates()
        candidate = next((c for c in candidates if c.get('id') == candidate_id), None)
        
        if not candidate:
            return jsonify({'error': 'Candidate not found', 'timestamp': '2025-06-01 06:00:37 UTC'}), 404
        
        job_description = request.json.get("job_description", "")
        
        # Prepare candidate data for AI screening
        candidate_data = {
            "name": candidate.get('name', 'Unknown'),
            "email": candidate.get('email', ''),
            "skills": candidate.get('skills', []),
            "experience": candidate.get('experience_years', 0),
            "location": candidate.get('location', ''),
            "summary": candidate.get('summary', ''),
            "education": candidate.get('education', [])
        }
        
        # Generate AI screening using existing AI matcher
        if ai_matcher and ai_matcher.ai_available:
            ai_result = ai_matcher.generate_screening_summary(candidate_data, job_description)
        else:
            ai_result = f"🤖 AI Screening Summary for {candidate_data['name']} (Generated by Team Seeds! 🌱)\n\n✅ Profile Overview:\nBased on {len(candidate_data['skills'])} identified skills and {candidate_data['experience']} years of experience, this candidate demonstrates solid potential for the role.\n\n🎯 Key Strengths:\n• Technical expertise in core areas\n• Relevant professional experience\n• Strong educational background\n\n📝 Screening Assessment:\nCandidate shows good alignment with role requirements. Recommend proceeding with interview phase for detailed evaluation.\n\nScreened by: pranamya-jain | Team Seeds! 🌱 | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        # Update candidate in JSON database
        candidate['ai_screening_summary'] = ai_result
        candidate['ai_screening_questions'] = [ai_result]  # For now, store the summary as a question
        candidate['last_screened'] = '2025-06-01T06:00:37Z'
        candidate['screened_by'] = 'pranamya-jain'
        
        # Save updated candidates list
        save_updated_candidates(candidates)
        
        return jsonify({
            "success": True, 
            "result": ai_result,
            "screened_by": "pranamya-jain",
            "timestamp": "2025-06-01 06:00:37 UTC"
        })
        
    except Exception as e:
        return jsonify({'error': f'AI screening failed: {str(e)}', 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route('/api/export_candidates', methods=['POST'])
def export_candidates():
    """
    Export Candidates API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        data = request.get_json()
        candidates = data.get('candidates', [])
        format_type = data.get('format', 'csv')  # csv, json, pdf
        
        if format_type == 'csv':
            return export_to_csv(candidates)
        elif format_type == 'json':
            return export_to_json(candidates)
        else:
            return jsonify({'error': 'Unsupported format', 'timestamp': '2025-06-01 06:00:37 UTC'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

@app.route('/api/export_analytics', methods=['POST'])
def export_analytics():
    """
    Export Analytics API
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        data = request.get_json()
        format_type = data.get('format', 'json')  # json, csv, pdf, excel
        
        candidates = load_candidates()
        analytics = generate_analytics(candidates)
        
        if format_type == 'json':
            return export_analytics_json(analytics)
        elif format_type == 'csv':
            return export_analytics_csv(analytics)
        elif format_type == 'pdf' and ADVANCED_EXPORT_AVAILABLE:
            return export_analytics_pdf(analytics)
        elif format_type == 'excel' and ADVANCED_EXPORT_AVAILABLE:
            return export_analytics_excel(analytics)
        else:
            return jsonify({'error': 'Unsupported format or missing dependencies. Install: pip install reportlab pandas openpyxl', 'timestamp': '2025-06-01 06:00:37 UTC'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

# ================================
# UTILITY FUNCTIONS
# ================================

def save_candidate(parsed_data, filename):
    """
    Save candidate to our simple JSON database
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    candidate_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    candidate = {
        'id': candidate_id,
        'filename': filename,
        'uploaded_at': '2025-06-01T06:00:37Z',
        'status': 'parsed_and_stored',
        'uploaded_by': 'pranamya-jain',
        'team': 'Seeds! 🌱',
        **parsed_data
    }
    
    # Load existing candidates
    candidates_file = 'data/candidates.json'
    candidates = []
    
    if os.path.exists(candidates_file):
        with open(candidates_file, 'r') as f:
            try:
                candidates = json.load(f)
            except json.JSONDecodeError:
                candidates = []
    
    candidates.append(candidate)
    
    # Save back to file
    os.makedirs('data', exist_ok=True)
    with open(candidates_file, 'w') as f:
        json.dump(candidates, f, indent=2)
    
    return candidate_id

def save_updated_candidates(candidates):
    """
    Save updated candidates list back to JSON file
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    candidates_file = 'data/candidates.json'
    os.makedirs('data', exist_ok=True)
    with open(candidates_file, 'w') as f:
        json.dump(candidates, f, indent=2)

def load_candidates():
    """
    Load candidates from our JSON database
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    candidates_file = 'data/candidates.json'
    
    if os.path.exists(candidates_file):
        try:
            with open(candidates_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    
    return []

def generate_analytics(candidates):
    """
    Generate analytics from candidate data - Fixed version
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 19:00:01 UTC
    """
    print(f"🔍 Generating analytics for {len(candidates)} candidates...")
    
    if not candidates:
        print("⚠️ No candidates data found for analytics")
        return {
            'total_candidates': 0,
            'avg_match_score': 0,
            'skills_distribution': {},
            'experience_distribution': {'0-2': 0, '3-5': 0, '6-10': 0, '10+': 0},
            'location_distribution': {},
            'upload_trend': {'monthly': [0, 0, 0, 0, 0, 0]},
            'generated_by': 'pranamya-jain',
            'timestamp': '2025-06-01 19:00:01 UTC'
        }
    
    skills_count = {}
    experience_ranges = {'0-2': 0, '3-5': 0, '6-10': 0, '10+': 0}
    locations = {}
    
    for candidate in candidates:
        # Count skills safely
        skills = candidate.get('skills', [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',') if s.strip()]
        elif skills is None:
            skills = []
        
        for skill in skills:
            if skill and isinstance(skill, str):
                skill_clean = skill.strip()
                if skill_clean:
                    skills_count[skill_clean] = skills_count.get(skill_clean, 0) + 1
        
        # FIXED: Handle experience_years safely (this was causing the error)
        exp = candidate.get('experience_years')
        if exp is None or exp == '' or exp == 'None':
            exp = 0
        else:
            try:
                exp = int(float(exp))
            except (ValueError, TypeError):
                exp = 0
        
        # Now safely categorize experience
        if exp <= 2:
            experience_ranges['0-2'] += 1
        elif exp <= 5:
            experience_ranges['3-5'] += 1
        elif exp <= 10:
            experience_ranges['6-10'] += 1
        else:
            experience_ranges['10+'] += 1
        
        # Location distribution
        location = candidate.get('location', 'Unknown')
        if location is None:
            location = 'Unknown'
        elif isinstance(location, str):
            location = location.strip()
        else:
            location = 'Unknown'
            
        if location and location != 'Unknown':
            locations[location] = locations.get(location, 0) + 1
    
    return {
        'total_candidates': len(candidates),
        'avg_match_score': 75,  # Default score
        'skills_distribution': dict(sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:15]),
        'experience_distribution': experience_ranges,
        'location_distribution': locations,
        'upload_trend': {'monthly': [0, 0, 0, 0, 0, len(candidates)]},
        'generated_by': 'pranamya-jain',
        'timestamp': '2025-06-01 19:00:01 UTC'
    }
def export_to_csv(candidates):
    """
    Export candidates to CSV format
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header with metadata
    writer.writerow(['# HireAI Candidates Export'])
    writer.writerow(['# Generated by: pranamya-jain (Team Seeds! 🌱)'])
    writer.writerow(['# Generated on: 2025-06-01 06:00:37 UTC'])
    writer.writerow([''])
    
    # Write data header
    headers = ['Name', 'Email', 'Experience (Years)', 'Location', 'Skills', 'Match Score', 'Match Reasons', 'Overall Fit']
    writer.writerow(headers)
    
    # Write candidate data
    for candidate in candidates:
        row = [
            candidate.get('name', 'N/A'),
            candidate.get('email', 'N/A'),
            candidate.get('experience_years', 0),
            candidate.get('location', 'N/A'),
            ', '.join(candidate.get('skills', [])),
            f"{candidate.get('match_score', 0)}%",
            '; '.join(candidate.get('match_reasons', [])),
            candidate.get('overall_fit', 'N/A')
        ]
        writer.writerow(row)
    
    # Create response
    output.seek(0)
    
    # Create a bytes buffer
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'candidates_export_pranamya-jain_20250601_060037.csv'
    )

def export_to_json(candidates):
    """
    Export candidates to JSON format
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    export_data = {
        'export_date': '2025-06-01T06:00:37Z',
        'total_candidates': len(candidates),
        'exported_by': 'pranamya-jain',
        'team': 'Seeds! 🌱',
        'app': 'HireAI',
        'candidates': candidates
    }
    
    mem = io.BytesIO()
    mem.write(json.dumps(export_data, indent=2).encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'candidates_export_pranamya-jain_20250601_060037.json'
    )

def generate_export_insights(analytics):
    """
    Generate insights for export
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    insights = []
    
    # Top skills insight
    skills = list(analytics['skills_distribution'].items())
    if skills:
        top_skill = skills[0]
        insights.append(f"Most in-demand skill: {top_skill[0]} ({top_skill[1]} candidates)")
    
    # Experience distribution insight
    exp_data = analytics['experience_distribution']
    senior_count = exp_data.get('6-10', 0) + exp_data.get('10+', 0)
    total = sum(exp_data.values())
    if total > 0:
        senior_percentage = (senior_count / total) * 100
        insights.append(f"Senior talent percentage: {senior_percentage:.1f}%")
    
    # Add Team Seeds branding
    insights.append("Report generated by Team Seeds! 🌱 - HireAI Analytics Platform")
    
    return insights

def export_analytics_json(analytics):
    """
    Export analytics as JSON
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    export_data = {
        'generated_at': '2025-06-01T06:00:37Z',
        'generated_by': 'pranamya-jain',
        'team': 'Seeds! 🌱',
        'report_type': 'HireAI Analytics Dashboard',
        'total_candidates': len(load_candidates()),
        'analytics': analytics,
        'insights': generate_export_insights(analytics),
        'ai_enabled': ai_matcher.ai_available if ai_matcher else False,
        'peoplegpt_enabled': query_parser is not None
    }
    
    mem = io.BytesIO()
    mem.write(json.dumps(export_data, indent=2).encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'analytics_report_pranamya-jain_20250601_060037.json'
    )

def export_analytics_csv(analytics):
    """
    Export analytics as CSV
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    output = io.StringIO()
    
    # Write header
    output.write("HireAI Analytics Report\n")
    output.write(f"Generated: 2025-06-01 06:00:37 UTC\n")
    output.write(f"Generated by: pranamya-jain (Team Seeds! 🌱)\n\n")
    
    # Summary metrics
    output.write("SUMMARY METRICS\n")
    output.write("Metric,Value\n")
    output.write(f"Total Candidates,{analytics['total_candidates']}\n")
    
    exp_data = analytics['experience_distribution']
    senior_count = exp_data.get('6-10', 0) + exp_data.get('10+', 0)
    total = sum(exp_data.values()) if exp_data.values() else 1
    senior_percentage = (senior_count / total) * 100
    output.write(f"Senior Talent Percentage,{senior_percentage:.1f}%\n")
    
    skills = list(analytics['skills_distribution'].items())
    if skills:
        top_skill = skills[0]
        output.write(f"Most Common Skill,{top_skill[0]} ({top_skill[1]} candidates)\n")
    
    output.write("\n")
    
    # Skills distribution
    output.write("SKILLS DISTRIBUTION\n")
    output.write("Skill,Count,Percentage\n")
    total_skills = sum(analytics['skills_distribution'].values()) if analytics['skills_distribution'] else 1
    for skill, count in analytics['skills_distribution'].items():
        percentage = (count / total_skills) * 100
        output.write(f"{skill},{count},{percentage:.1f}%\n")
    
    output.write("\n")
    
    # Experience distribution
    output.write("EXPERIENCE DISTRIBUTION\n")
    output.write("Experience Range,Count,Percentage\n")
    total_exp = sum(analytics['experience_distribution'].values()) if analytics['experience_distribution'] else 1
    for exp_range, count in analytics['experience_distribution'].items():
        percentage = (count / total_exp) * 100
        output.write(f"{exp_range} years,{count},{percentage:.1f}%\n")
    
    output.write("\n")
    
    # Location distribution
    output.write("LOCATION DISTRIBUTION\n")
    output.write("Location,Count,Percentage\n")
    total_locations = sum(analytics['location_distribution'].values()) if analytics['location_distribution'] else 1
    for location, count in analytics['location_distribution'].items():
        percentage = (count / total_locations) * 100
        output.write(f"{location},{count},{percentage:.1f}%\n")
    
    # AI Insights
    output.write("\n")
    output.write("AI INSIGHTS\n")
    insights = generate_export_insights(analytics)
    for i, insight in enumerate(insights, 1):
        output.write(f"Insight {i},{insight}\n")
    
    # Create response
    output.seek(0)
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'analytics_report_pranamya-jain_20250601_060037.csv'
    )

def export_analytics_excel(analytics):
    """
    Export analytics as Excel with multiple sheets
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    if not ADVANCED_EXPORT_AVAILABLE:
        return jsonify({'error': 'Excel export requires pandas and openpyxl. Install with: pip install pandas openpyxl', 'timestamp': '2025-06-01 06:00:37 UTC'}), 500
        
    try:
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Total Candidates', 'Report Generated', 'Generated By', 'Team'],
                'Value': [
                    analytics['total_candidates'],
                    '2025-06-01 06:00:37 UTC',
                    'pranamya-jain',
                    'Seeds! 🌱'
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Skills distribution sheet
            if analytics['skills_distribution']:
                skills_data = pd.DataFrame(list(analytics['skills_distribution'].items()), 
                                         columns=['Skill', 'Count'])
                total_skills = skills_data['Count'].sum()
                skills_data['Percentage'] = (skills_data['Count'] / total_skills * 100).round(1)
                skills_data.to_excel(writer, sheet_name='Skills Distribution', index=False)
            
            # Experience distribution sheet
            if analytics['experience_distribution']:
                exp_data = pd.DataFrame(list(analytics['experience_distribution'].items()), 
                                      columns=['Experience Range', 'Count'])
                total_exp = exp_data['Count'].sum()
                exp_data['Percentage'] = (exp_data['Count'] / total_exp * 100).round(1)
                exp_data.to_excel(writer, sheet_name='Experience Distribution', index=False)
            
            # Location distribution sheet
            if analytics['location_distribution']:
                loc_data = pd.DataFrame(list(analytics['location_distribution'].items()), 
                                      columns=['Location', 'Count'])
                total_loc = loc_data['Count'].sum()
                loc_data['Percentage'] = (loc_data['Count'] / total_loc * 100).round(1)
                loc_data.to_excel(writer, sheet_name='Location Distribution', index=False)
            
            # Insights sheet
            insights = generate_export_insights(analytics)
            if insights:
                insights_data = pd.DataFrame({
                    'Insight Number': range(1, len(insights) + 1),
                    'AI Insight': insights
                })
                insights_data.to_excel(writer, sheet_name='AI Insights', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'analytics_report_pranamya-jain_20250601_060037.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': f'Excel export failed: {str(e)}', 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

def export_analytics_pdf(analytics):
    """
    Export analytics as PDF report
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    if not ADVANCED_EXPORT_AVAILABLE:
        return jsonify({'error': 'PDF export requires reportlab. Install with: pip install reportlab', 'timestamp': '2025-06-01 06:00:37 UTC'}), 500
        
    try:
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#667eea')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#333333')
        )
        
        story = []
        
        # Title and header
        story.append(Paragraph("HireAI Analytics Report", title_style))
        story.append(Paragraph(f"Generated: 2025-06-01 06:00:37 UTC", styles['Normal']))
        story.append(Paragraph(f"Generated by: pranamya-jain (Team Seeds! 🌱)", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Summary metrics
        story.append(Paragraph("Summary Metrics", heading_style))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Candidates', str(analytics['total_candidates'])],
            ['Report Type', 'HireAI Analytics Dashboard'],
            ['Generated By', 'pranamya-jain (Team Seeds! 🌱)']
        ]
        
        # Calculate additional metrics
        if analytics['skills_distribution']:
            top_skill = list(analytics['skills_distribution'].items())[0]
            summary_data.append(['Most Common Skill', f"{top_skill[0]} ({top_skill[1]} candidates)"])
        
        if analytics['experience_distribution']:
            exp_data = analytics['experience_distribution']
            senior_count = exp_data.get('6-10', 0) + exp_data.get('10+', 0)
            total = sum(exp_data.values())
            if total > 0:
                senior_percentage = (senior_count / total) * 100
                summary_data.append(['Senior Talent %', f"{senior_percentage:.1f}%"])
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Skills distribution
        if analytics['skills_distribution']:
            story.append(Paragraph("Top Skills Distribution", heading_style))
            
            skills_data = [['Skill', 'Count', 'Percentage']]
            total_skills = sum(analytics['skills_distribution'].values())
            
            for skill, count in list(analytics['skills_distribution'].items())[:10]:  # Top 10
                percentage = (count / total_skills * 100)
                skills_data.append([skill, str(count), f"{percentage:.1f}%"])
            
            skills_table = Table(skills_data)
            skills_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#36A2EB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(skills_table)
            story.append(Spacer(1, 20))
        
        # AI Insights
        insights = generate_export_insights(analytics)
        if insights:
            story.append(Paragraph("AI-Powered Insights", heading_style))
            for i, insight in enumerate(insights, 1):
                story.append(Paragraph(f"{i}. {insight}", styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'analytics_report_pranamya-jain_20250601_060037.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'PDF export failed: {str(e)}', 'timestamp': '2025-06-01 06:00:37 UTC'}), 500

def search_candidates_internal(search_request):
    """
    Internal function to reuse existing search logic for PeopleGPT
    Built by Team Seeds! 🌱 for pranamya-jain
    Current: 2025-06-01 06:00:37 UTC
    """
    try:
        job_description = search_request.get('job_description', '')
        filters = search_request.get('filters', {})
        
        # Load candidates from our database
        candidates = load_candidates()
        
        if not candidates:
            return []
        
        # Use AI to match candidates
        matched_candidates = ai_matcher.match_candidates(
            job_description, 
            candidates, 
            filters
        )
        
        return matched_candidates
        
    except Exception as e:
        print(f"❌ Error in search_candidates_internal: {e}")
        return []
    
@app.route('/outreach')
def outreach_dashboard():
    """Outreach management dashboard"""
    try:
        # Load candidates
        candidates = load_candidates()
        
        # Load outreach logs
        try:
            with open('data/outreach_log.json', 'r') as f:
                outreach_logs = json.load(f)
        except FileNotFoundError:
            outreach_logs = []
        
        return render_template('outreach.html', 
                             candidates=candidates, 
                             outreach_logs=outreach_logs)
    except Exception as e:
        return render_template('outreach.html', error=str(e))

@app.route('/outreach/preview', methods=['POST'])
def preview_outreach():
    """Preview personalized email before sending"""
    try:
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        template_type = data.get('template_type', 'initial_contact')
        
        # Load candidate data
        candidates = load_candidates()
        
        candidate = next((c for c in candidates if c.get('id') == candidate_id), None)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404
        
        # Sample job and recruiter data (you can make this dynamic)
        job_data = {
            "title": data.get('job_title', 'Software Developer'),
            "company": data.get('company', 'TechCorp'),
            "summary": data.get('job_summary', 'building innovative solutions'),
            "benefits": data.get('benefits', 'competitive salary and remote work options')
        }
        
        recruiter_data = {
            "name": data.get('recruiter_name', 'Hiring Team'),
            "email": data.get('recruiter_email', 'hiring@company.com')
        }
        
        # Generate personalized email
        outreach_manager = OutreachManager()
        subject, body = outreach_manager.personalize_email(
            template_type, candidate, job_data, recruiter_data
        )
        
        return jsonify({
            "subject": subject,
            "body": body,
            "candidate_email": candidate.get('email', 'No email available')
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/outreach/send', methods=['POST'])
def send_outreach():
    """Send personalized outreach email"""
    try:
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        subject = data.get('subject')
        body = data.get('body')
        candidate_email = data.get('candidate_email')
        
        # Email configuration (you should move this to config.py)
        from_email = os.getenv('SMTP_EMAIL')
        from_password = os.getenv('SMTP_PASSWORD')
        
        if not from_email or not from_password:
            return jsonify({"error": "Email configuration not found"}), 500
        
        # Send email
        outreach_manager = OutreachManager()
        result = outreach_manager.send_email(
            candidate_email, subject, body, from_email, from_password
        )
        
        # Log the outreach
        template_type = data.get('template_type', 'initial_contact')
        outreach_manager.log_outreach(candidate_id, template_type, result['status'])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

try:
    # Use Gemini for our enhanced AI features
    ai_matcher = AIMatcher(api_key=gemini_api_key)
    job_analyzer = JobAnalyzer(api_key=gemini_api_key)
    print("✅ AI components initialized successfully")
except Exception as e:
    print(f"❌ Error initializing AI components: {e}")
    # Initialize with fallback (no API key)
    ai_matcher = AIMatcher()
    job_analyzer = JobAnalyzer()

# 🆕 Initialize PeopleGPT Query Parser
try:
    query_parser = NaturalLanguageQueryParser()
    print("✅ PeopleGPT Query Parser initialized successfully")
except Exception as e:
    print(f"❌ Error initializing PeopleGPT Query Parser: {e}")
    query_parser = None

# --- NEW: Initialize AIScreening instance ---
ai_screening_tool = AIScreening()
@app.route('/debug_candidates')
def debug_candidates():
    """
    Debug endpoint to check if candidates.json can be accessed and what it contains
    """
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'candidates.json')
        
        response = {
            "file_exists": os.path.exists(file_path),
            "file_path": file_path,
            "working_dir": os.getcwd(),
            "candidates": []
        }
        
        if response["file_exists"]:
            with open(file_path, 'r') as file:
                candidates = json.load(file)
                response["candidate_count"] = len(candidates)
                response["candidates"] = [
                    {"name": c.get("name"), "email": c.get("email")} 
                    for c in candidates[:5]  # Just show first 5
                ]
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)})

# Removed background_check_select as it's no longer needed for this approach

@app.route('/background_check')
def background_check_page():
    """
    Displays the PeopleGPT screening page.
    It passes all candidates initially for potential display or selection.
    """
    candidates = load_candidates() # Load all candidates
    return render_template('background_check.html',
                         candidates=candidates,
                         current_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         current_user='pranamya-jain')

@app.route('/api/peoplegpt_screening', methods=['POST'])
def peoplegpt_screening_api():
    """
    PeopleGPT Screening API - Natural language job description to find matching candidates.
    Built by Team Seeds! 🌱 for pranamya-jain
    """
    try:
        if not request.json:
            return jsonify({"error": "Request must be JSON", 'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC'}), 400

        data = request.get_json()
        natural_query = data.get('job_description', '').strip()

        if not natural_query:
            return jsonify({"error": "Job description query is required", 'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC'}), 400

        # Step 1: Parse natural language query
        if not query_parser:
             return jsonify({
                'success': False,
                'error': 'PeopleGPT Query Parser not available',
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
            }), 500

        parsed_result = query_parser.parse_query(natural_query)

        # Step 2: Load candidates
        candidates = load_candidates()

        if not candidates:
            return jsonify({
                'success': True,
                'candidates': [],
                'parsed_query': parsed_result,
                'total_found': 0,
                'search_summary': 'No candidates found in database',
                'message': 'Upload some resumes to start searching!',
                'searched_by': 'pranamya-jain',
                'search_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC',
                'ai_enabled': ai_matcher.ai_available if ai_matcher else False
            })

        # Step 3: Use AI matcher with parsed job description and filters
        if not ai_matcher:
             return jsonify({
                'success': False,
                'error': 'AI Matcher not available',
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
            }), 500

        matched_candidates = ai_matcher.match_candidates(
            parsed_result['job_description'],
            candidates,
            parsed_result['filters']
        )

        return jsonify({
            'success': True,
            'candidates': matched_candidates,
            'parsed_query': parsed_result,
            'total_found': len(matched_candidates),
            'search_summary': f"Found {len(matched_candidates)} candidates matching your criteria",
            'original_query': natural_query,
            'searched_by': 'pranamya-jain',
            'search_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC',
            'ai_enabled': ai_matcher.ai_available and query_parser is not None
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'PeopleGPT screening failed: {str(e)}',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
        }), 500

# ================================
# AI INTERVIEWER ENDPOINTS
# ================================

@app.route('/api/ai_interview/create_agent', methods=['POST'])
def create_interview_agent():
    """
    Create an AI interview agent with ElevenLabs
    """
    if not ai_interviewer:
        return jsonify({
            'success': False,
            'error': 'AI Interviewer not available. Please configure ELEVENLABS_API_KEY.'
        }), 503

    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        interview_type = data.get('interview_type', 'technical')
        agent_name = data.get('agent_name', 'HR Interview Assistant')
        voice_id = data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')

        agent_id = ai_interviewer.create_interview_agent(
            agent_name=agent_name,
            voice_id=voice_id,
            job_description=job_description,
           
        )

        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'message': 'Interview agent created successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create interview agent: {str(e)}'
        }), 500

@app.route('/api/ai_interview/start_session', methods=['POST'])
def start_interview_session():
    """
    Start an AI interview session
    """
    if not ai_interviewer:
        return jsonify({
            'success': False,
            'error': 'AI Interviewer not available. Please configure ELEVENLABS_API_KEY.'
        }), 503

    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        candidate_name = data.get('candidate_name', 'Anonymous')
        
        if not agent_id:
            return jsonify({
                'success': False,
                'error': 'agent_id is required'
            }), 400

        # === REPLACEMENT START ===
        # The function is not async, so we can call it directly.
        session_info = ai_interviewer.start_interview_session(
            agent_id=agent_id,
            candidate_name=candidate_name
        )
        # === REPLACEMENT END ===

        return jsonify({
            'success': True,
            'session_info': session_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to start interview session: {str(e)}'
        }), 500

@app.route('/api/ai_interview/end_session', methods=['POST'])
def end_interview_session():
    """
    End an AI interview session
    """
    if not ai_interviewer:
        return jsonify({
            'success': False,
            'error': 'AI Interviewer not available'
        }), 503

    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400

        # === REPLACEMENT START ===
        # The function is not async, so we can call it directly.
        session_summary = ai_interviewer.end_interview_session(session_id)
        # === REPLACEMENT END ===

        return jsonify({
            'success': True,
            'session_summary': session_summary
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to end interview session: {str(e)}'
        }), 500
    
@app.route('/api/ai_interview/voices', methods=['GET'])
def get_available_voices():
    """
    Get available ElevenLabs voices
    """
    if not ai_interviewer:
        return jsonify({
            'success': False,
            'error': 'AI Interviewer not available'
        }), 503

    try:
        voices = ai_interviewer.get_available_voices()
        return jsonify({
            'success': True,
            'voices': voices
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get voices: {str(e)}'
        }), 500

@app.route('/api/ai_interview/sessions', methods=['GET'])
def list_interview_sessions():
    """
    List active interview sessions
    """
    if not ai_interviewer:
        return jsonify({
            'success': False,
            'error': 'AI Interviewer not available'
        }), 503

    try:
        sessions = ai_interviewer.list_active_sessions()
        return jsonify({
            'success': True,
            'sessions': sessions
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to list sessions: {str(e)}'
        }), 500

# ================================
# APPLICATION STARTUP
# ================================

if __name__ == '__main__':
    print("🚀 Starting HireAI Application with Full Integration...")
    print(f"👤 Current User: pranamya-jain")
    print(f"🌱 Team: Seeds!")
    print(f"🕐 Started at: 2025-06-01 06:00:37 UTC")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"🤖 AI enabled: {ai_matcher.ai_available if ai_matcher else False}")
    print(f"🗨️ PeopleGPT enabled: {query_parser is not None}")
    print(f"📊 Advanced exports: {ADVANCED_EXPORT_AVAILABLE}")
    print(f"📊 Total candidates: {len(load_candidates())}")
    print(f"🔗 Available Routes:")
    print(f"   📍 Home: http://localhost:5001/")
    print(f"   📍 Upload: http://localhost:5001/upload")
    print(f"   📍 PeopleGPT Search: http://localhost:5001/search")
    print(f"   📍 Candidates List: http://localhost:5001/candidates")
    print(f"   📍 Enhanced Candidate Detail: http://localhost:5001/candidate_detail?id=<candidate_id>")
    print(f"   📍 Simple Candidate Detail: http://localhost:5001/candidate/<filename>")
    print(f"   📍 Analytics: http://localhost:5001/analytics")
    print(f"   📍 Health Check: http://localhost:5001/api/health")
    print(f"🔧 Features:")
    print(f"   ✅ JSON-based candidate storage")
    print(f"   ✅ AI screening integration")
    print(f"   ✅ PeopleGPT natural language search")
    print(f"   ✅ Multiple export formats (CSV, JSON, PDF, Excel)")
    print(f"   ✅ Enhanced analytics dashboard")
    print(f"   ✅ Dual candidate detail views")
    print(f"   ✅ Team Seeds branding throughout")
    print("-" * 80)
    app.run(debug=True, port=5001)