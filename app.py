from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_cors import CORS
import os
import json
from datetime import datetime
from dotenv import load_dotenv  # Add this import
from config import Config

# Force load environment variables at the very beginning
load_dotenv()

# Import our custom modules
from utils.resume_parser import ResumeParser
from utils.ai_matcher import AIMatcher
from utils.job_analyzer import JobAnalyzer

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/search')
def search_page():
    return render_template('search.html')

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')

@app.route('/api/upload_resume', methods=['POST'])
def upload_resume():
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
            'parsed_data': parsed_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_candidates', methods=['POST'])
def search_candidates():
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
                'message': 'No candidates found in database'
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
            'ai_enabled': ai_matcher.ai_available
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze_job', methods=['POST'])
def analyze_job():
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        
        if not job_description.strip():
            return jsonify({'error': 'Job description is required'}), 400
        
        # Use our enhanced job analyzer
        analysis = job_analyzer.analyze_job_description(job_description)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'ai_enabled': job_analyzer.ai_available
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_candidates')
def get_candidates():
    """Get all candidates for the search interface"""
    try:
        candidates = load_candidates()
        return jsonify({
            'success': True,
            'candidates': candidates,
            'total': len(candidates)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_questions', methods=['POST'])
def generate_questions():
    """Generate screening questions for a candidate"""
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        candidate_id = data.get('candidate_id', '')
        
        if not job_description.strip():
            return jsonify({'error': 'Job description is required'}), 400
        
        # Find the candidate
        candidates = load_candidates()
        candidate = next((c for c in candidates if c.get('id') == candidate_id), None)
        
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Generate questions using AI matcher
        questions = ai_matcher.generate_screening_questions(job_description, candidate)
        
        return jsonify({
            'success': True,
            'questions': questions,
            'ai_enabled': ai_matcher.ai_available
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_analytics')
def get_analytics():
    try:
        candidates = load_candidates()
        analytics = generate_analytics(candidates)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ai_enabled': ai_matcher.ai_available if ai_matcher else False,
        'gemini_available': ai_matcher.ai_available if ai_matcher else False,
        'total_candidates': len(load_candidates())
    })

def save_candidate(parsed_data, filename):
    """Save candidate to our simple JSON database"""
    candidate_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    candidate = {
        'id': candidate_id,
        'filename': filename,
        'uploaded_at': datetime.now().isoformat(),
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

def load_candidates():
    """Load candidates from our JSON database"""
    candidates_file = 'data/candidates.json'
    
    if os.path.exists(candidates_file):
        try:
            with open(candidates_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    
    return []

def generate_analytics(candidates):
    """Generate analytics from candidate data"""
    if not candidates:
        return {
            'total_candidates': 0,
            'skills_distribution': {},
            'experience_distribution': {},
            'location_distribution': {}
        }
    
    skills_count = {}
    experience_ranges = {'0-2': 0, '3-5': 0, '6-10': 0, '10+': 0}
    locations = {}
    
    for candidate in candidates:
        # Count skills
        for skill in candidate.get('skills', []):
            skills_count[skill] = skills_count.get(skill, 0) + 1
        
        # Experience distribution
        exp = candidate.get('experience_years', 0)
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
        locations[location] = locations.get(location, 0) + 1
    
    return {
        'total_candidates': len(candidates),
        'skills_distribution': dict(sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:10]),
        'experience_distribution': experience_ranges,
        'location_distribution': locations
    }

if __name__ == '__main__':
    print("🚀 Starting HireAI Application...")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"🤖 AI enabled: {ai_matcher.ai_available if ai_matcher else False}")
    app.run(debug=True, port=5001)  # Changed to port 5001 to avoid conflict