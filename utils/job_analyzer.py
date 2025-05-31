import json
import re
import os
from typing import Dict, List, Any

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Gemini not available, using fallback analysis")

class JobAnalyzer:
    def __init__(self, api_key: str = None):
        self.ai_available = False
        
        if GEMINI_AVAILABLE:
            # Use provided key or environment variable
            gemini_key = api_key or os.getenv('GEMINI_API_KEY')
            
            if gemini_key:
                try:
                    print(f"🔧 JobAnalyzer: Configuring Gemini...")
                    genai.configure(api_key=gemini_key)
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Simple test without storing the response
                    self.model.generate_content("Test")
                    self.ai_available = True
                    print("✅ JobAnalyzer: Gemini working successfully!")
                except Exception as e:
                    print(f"❌ JobAnalyzer: Gemini failed: {e}")
                    self.ai_available = False
            else:
                print("🔄 JobAnalyzer: No Gemini API key found - using fallback")
        else:
            print("🔄 JobAnalyzer: Gemini not available - using fallback")
    
    def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """Comprehensive analysis of a job description"""
        if not job_description or len(job_description.strip()) < 10:
            return {
                "error": "Job description too short or empty",
                "requirements": {},
                "analysis": {},
                "recommendations": []
            }
        
        try:
            if self.ai_available:
                # Try AI analysis first
                analysis = self._get_ai_analysis(job_description)
            else:
                # Use enhanced fallback analysis
                analysis = self._get_enhanced_fallback_analysis(job_description)
            
            # Add some basic metrics
            analysis['metrics'] = self._calculate_metrics(job_description)
            analysis['ai_powered'] = self.ai_available
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing job description: {e}")
            # Always fallback to basic analysis
            fallback = self._get_enhanced_fallback_analysis(job_description)
            fallback['error'] = f"AI analysis failed: {str(e)}"
            fallback['metrics'] = self._calculate_metrics(job_description)
            fallback['ai_powered'] = False
            return fallback
    
    def _get_ai_analysis(self, job_description: str) -> Dict[str, Any]:
        """Get AI analysis using Gemini"""
        prompt = f"""
        Analyze this job description and extract key information in JSON format:

        JOB DESCRIPTION:
        {job_description}

        Please provide analysis in this exact JSON format:
        {{
            "requirements": {{
                "required_skills": ["skill1", "skill2"],
                "min_experience_years": 0,
                "education_level": "bachelor",
                "job_level": "mid"
            }},
            "analysis": {{
                "job_type": "full-time",
                "industry": "technology",
                "remote_work": "hybrid"
            }},
            "key_responsibilities": ["resp1", "resp2"],
            "recommendations": {{
                "for_candidates": ["tip1", "tip2"],
                "for_recruiters": ["tip1", "tip2"]
            }}
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in AI response")
                
        except Exception as e:
            print(f"AI analysis error: {e}")
            raise e
    
    def _get_enhanced_fallback_analysis(self, job_description: str) -> Dict[str, Any]:
        """Enhanced fallback analysis when AI is not available"""
        text_lower = job_description.lower()
        
        # Extract skills using enhanced keyword matching
        tech_skills = []
        skill_keywords = {
            'Python': ['python', 'django', 'flask', 'fastapi', 'pytorch'],
            'JavaScript': ['javascript', 'js', 'node.js', 'react', 'angular', 'vue', 'typescript'],
            'Java': ['java', 'spring', 'hibernate', 'maven'],
            'Machine Learning': ['machine learning', 'ml', 'ai', 'artificial intelligence', 'tensorflow', 'pytorch', 'scikit-learn', 'keras'],
            'Data Science': ['data science', 'data analysis', 'pandas', 'numpy', 'matplotlib', 'seaborn'],
            'LangChain': ['langchain', 'lang chain', 'lang-chain'],
            'RAG': ['rag', 'retrieval augmented', 'retrieval-augmented'],
            'Gen-AI': ['gen-ai', 'generative ai', 'llm', 'gpt', 'openai', 'large language model'],
            'SQL': ['sql', 'mysql', 'postgresql', 'database', 'mongodb'],
            'AWS': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'cloud'],
            'Docker': ['docker', 'kubernetes', 'containers', 'k8s'],
            'Git': ['git', 'github', 'version control', 'gitlab'],
            'React': ['react', 'reactjs', 'react.js'],
            'Node.js': ['node', 'nodejs', 'node.js', 'express'],
            'Go': ['golang', 'go'],
            'Rust': ['rust'],
            'C++': ['c++', 'cpp'],
            'DevOps': ['devops', 'ci/cd', 'jenkins', 'terraform']
        }
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tech_skills.append(skill)
        
        # Extract experience requirement with better patterns
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience',
            r'minimum\s*(\d+)\s*years?',
            r'at least\s*(\d+)\s*years?',
            r'(\d+)\s*to\s*(\d+)\s*years?'
        ]
        
        min_experience = 0
        for pattern in exp_patterns:
            match = re.search(pattern, text_lower)
            if match:
                min_experience = int(match.group(1))
                break
        
        # Determine job level with enhanced logic
        job_level = "mid"
        if any(term in text_lower for term in ['senior', 'sr.', 'lead', 'principal', 'architect', 'staff']):
            job_level = "senior"
        elif any(term in text_lower for term in ['junior', 'jr.', 'entry', 'graduate', 'intern', 'associate']):
            job_level = "entry"
        elif any(term in text_lower for term in ['director', 'manager', 'head of', 'vp', 'chief']):
            job_level = "management"
        
        # Determine industry with expanded keywords
        industry = "technology"
        industry_keywords = {
            'finance': ['fintech', 'finance', 'banking', 'trading', 'investment', 'financial'],
            'healthcare': ['healthcare', 'medical', 'biotech', 'pharma', 'health'],
            'retail': ['retail', 'e-commerce', 'ecommerce', 'shopping', 'marketplace'],
            'gaming': ['gaming', 'game', 'entertainment', 'media'],
            'education': ['education', 'edtech', 'learning', 'academic'],
            'consulting': ['consulting', 'advisory', 'consulting'],
            'startup': ['startup', 'early-stage', 'seed', 'series a']
        }
        
        for ind, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                industry = ind
                break
        
        # Enhanced work type detection
        job_type = "full-time"
        if any(term in text_lower for term in ['contract', 'contractor', 'freelance', 'consulting']):
            job_type = "contract"
        elif any(term in text_lower for term in ['part-time', 'part time']):
            job_type = "part-time"
        elif any(term in text_lower for term in ['intern', 'internship']):
            job_type = "internship"
        
        # Remote work detection
        remote_work = "on-site"
        if any(term in text_lower for term in ['remote', 'work from home', 'wfh', 'distributed']):
            if any(term in text_lower for term in ['hybrid', 'flexible']):
                remote_work = "hybrid"
            else:
                remote_work = "remote"
        elif any(term in text_lower for term in ['hybrid', 'flexible']):
            remote_work = "hybrid"
        
        # Extract key responsibilities with better patterns
        responsibilities = []
        responsibility_patterns = [
            (r'\b(?:develop|build|create|implement)\b', "Software development and implementation"),
            (r'\b(?:design|architect|plan)\b', "System design and architecture"),
            (r'\b(?:test|qa|quality)\b', "Testing and quality assurance"),
            (r'\b(?:collaborate|team|work with)\b', "Team collaboration and communication"),
            (r'\b(?:maintain|support|monitor)\b', "System maintenance and support"),
            (r'\b(?:lead|manage|mentor)\b', "Team leadership and mentoring"),
            (r'\b(?:research|analyze|investigate)\b', "Research and analysis"),
            (r'\b(?:deploy|devops|infrastructure)\b', "Deployment and infrastructure")
        ]
        
        for pattern, responsibility in responsibility_patterns:
            if re.search(pattern, text_lower):
                responsibilities.append(responsibility)
        
        # Generate enhanced recommendations
        candidate_tips = []
        recruiter_tips = []
        
        if tech_skills:
            candidate_tips.append(f"Highlight experience with {', '.join(tech_skills[:3])} in your resume")
            candidate_tips.append("Include specific project examples demonstrating these skills")
        
        if min_experience > 0:
            candidate_tips.append(f"Emphasize your {min_experience}+ years of relevant experience")
        else:
            candidate_tips.append("Focus on relevant projects and learning experiences")
        
        candidate_tips.append(f"Position yourself for a {job_level}-level role with appropriate examples")
        
        # Recruiter recommendations
        recruiter_tips.append("Consider adding salary range to attract quality candidates")
        recruiter_tips.append("Specify remote work policy and collaboration tools")
        recruiter_tips.append("Include team size and reporting structure details")
        
        if len(tech_skills) > 5:
            recruiter_tips.append("Consider prioritizing must-have vs nice-to-have skills")
        
        return {
            "requirements": {
                "required_skills": tech_skills,
                "min_experience_years": min_experience,
                "education_level": "bachelor" if any(term in text_lower for term in ['degree', 'bachelor', 'bs', 'ba']) else "not specified",
                "job_level": job_level
            },
            "analysis": {
                "job_type": job_type,
                "industry": industry,
                "remote_work": remote_work
            },
            "key_responsibilities": responsibilities[:5],
            "recommendations": {
                "for_candidates": candidate_tips,
                "for_recruiters": recruiter_tips
            },
            "note": "Analysis based on enhanced pattern matching - add Gemini API key for full AI features"
        }
    
    def _calculate_metrics(self, job_description: str) -> Dict[str, Any]:
        """Calculate enhanced metrics about the job description"""
        words = job_description.split()
        sentences = [s.strip() for s in job_description.split('.') if s.strip()]
        
        # Calculate complexity score
        complex_words = len([w for w in words if len(w) > 7])
        complexity = min(100, (complex_words / len(words)) * 200) if words else 0
        
        # Calculate completeness based on key sections
        completeness_factors = [
            'responsibilities' in job_description.lower(),
            'requirements' in job_description.lower(),
            'experience' in job_description.lower(),
            'skills' in job_description.lower(),
            any(benefit in job_description.lower() for benefit in ['benefits', 'salary', 'compensation']),
            len(words) > 100
        ]
        
        completeness_score = (sum(completeness_factors) / len(completeness_factors)) * 100
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'reading_level': 'complex' if complexity > 60 else 'medium' if complexity > 30 else 'simple',
            'completeness_score': int(completeness_score),
            'complexity_score': int(complexity)
        }
    
    def generate_job_requirements(self, role: str, skills: List[str], experience_level: str) -> Dict[str, Any]:
        """Generate job requirements based on role and skills"""
        if self.ai_available:
            return self._ai_generate_requirements(role, skills, experience_level)
        else:
            return self._basic_generate_requirements(role, skills, experience_level)
    
    def _ai_generate_requirements(self, role: str, skills: List[str], experience_level: str) -> Dict[str, Any]:
        """Use AI to generate comprehensive job requirements"""
        prompt = f"""
        Generate a comprehensive job description for this role. Return ONLY valid JSON:

        ROLE: {role}
        REQUIRED SKILLS: {', '.join(skills)}
        EXPERIENCE LEVEL: {experience_level}

        Generate in this exact format:
        {{
            "job_title": "Generated job title",
            "job_summary": "Brief role description",
            "key_responsibilities": ["responsibility1", "responsibility2"],
            "required_qualifications": ["qualification1", "qualification2"],
            "preferred_qualifications": ["preferred1", "preferred2"],
            "benefits": ["benefit1", "benefit2"]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON in AI response")
                
        except Exception as e:
            print(f"AI job generation failed: {e}")
            return self._basic_generate_requirements(role, skills, experience_level)
    
    def _basic_generate_requirements(self, role: str, skills: List[str], experience_level: str) -> Dict[str, Any]:
        """Generate basic job requirements"""
        exp_mapping = {
            'entry': '0-2 years',
            'mid': '3-5 years', 
            'senior': '5+ years',
            'lead': '8+ years'
        }
        
        return {
            "job_title": f"{experience_level.title()} {role}",
            "job_summary": f"We are seeking a {experience_level} {role} to join our team.",
            "key_responsibilities": [
                f"Develop and maintain applications using {', '.join(skills[:3])}",
                "Collaborate with cross-functional teams",
                "Write clean, maintainable code",
                "Participate in code reviews and technical discussions"
            ],
            "required_qualifications": [
                f"{exp_mapping.get(experience_level, '3+ years')} of experience",
                f"Proficiency in {', '.join(skills[:3])}",
                "Strong problem-solving skills",
                "Bachelor's degree in Computer Science or related field"
            ],
            "preferred_qualifications": [
                f"Experience with {', '.join(skills[3:6])}",
                "Previous experience in agile development",
                "Open source contributions"
            ],
            "benefits": [
                "Competitive salary and equity",
                "Health, dental, and vision insurance",
                "Flexible working hours and remote options",
                "Professional development opportunities"
            ]
        }