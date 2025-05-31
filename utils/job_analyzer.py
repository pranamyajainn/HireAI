import json
import re
from typing import Dict, List, Any

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Groq not available, using fallback analysis")

class JobAnalyzer:
    def __init__(self, api_key: str = None):
        self.groq_available = GROQ_AVAILABLE and api_key
        if self.groq_available:
            try:
                self.client = Groq(api_key=api_key)
                self.model = "mixtral-8x7b-32768"
                print("✅ JobAnalyzer: Groq client initialized successfully")
            except Exception as e:
                print(f"❌ JobAnalyzer: Failed to initialize Groq client: {e}")
                self.groq_available = False
        
        if not self.groq_available:
            print("🔄 JobAnalyzer: Using fallback analysis mode")
    
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
            if self.groq_available:
                # Try AI analysis first
                analysis = self._get_ai_analysis(job_description)
            else:
                # Use fallback analysis
                analysis = self._get_fallback_analysis(job_description)
            
            # Add some basic metrics
            analysis['metrics'] = self._calculate_metrics(job_description)
            analysis['ai_powered'] = self.groq_available
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing job description: {e}")
            # Always fallback to basic analysis
            fallback = self._get_fallback_analysis(job_description)
            fallback['error'] = f"AI analysis failed: {str(e)}"
            fallback['metrics'] = self._calculate_metrics(job_description)
            fallback['ai_powered'] = False
            return fallback
    
    def _get_ai_analysis(self, job_description: str) -> Dict[str, Any]:
        """Get AI analysis using Groq"""
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in AI response")
                
        except Exception as e:
            print(f"AI analysis error: {e}")
            raise e
    
    def _get_fallback_analysis(self, job_description: str) -> Dict[str, Any]:
        """Enhanced fallback analysis when AI is not available"""
        text_lower = job_description.lower()
        
        # Extract skills using keyword matching
        tech_skills = []
        skill_keywords = {
            'python': ['python', 'django', 'flask', 'fastapi'],
            'javascript': ['javascript', 'js', 'node.js', 'react', 'angular', 'vue'],
            'java': ['java', 'spring', 'hibernate'],
            'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence', 'tensorflow', 'pytorch', 'scikit-learn'],
            'data science': ['data science', 'data analysis', 'pandas', 'numpy', 'matplotlib'],
            'sql': ['sql', 'mysql', 'postgresql', 'database'],
            'aws': ['aws', 'amazon web services', 'ec2', 's3'],
            'docker': ['docker', 'kubernetes', 'containers'],
            'git': ['git', 'github', 'version control']
        }
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tech_skills.append(skill.title())
        
        # Extract experience requirement
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience',
            r'minimum\s*(\d+)\s*years?'
        ]
        
        min_experience = 0
        for pattern in exp_patterns:
            match = re.search(pattern, text_lower)
            if match:
                min_experience = int(match.group(1))
                break
        
        # Determine job level
        job_level = "mid"
        if any(term in text_lower for term in ['senior', 'lead', 'principal', 'architect', 'staff']):
            job_level = "senior"
        elif any(term in text_lower for term in ['junior', 'entry', 'graduate', 'intern', 'associate']):
            job_level = "entry"
        elif any(term in text_lower for term in ['director', 'manager', 'head of']):
            job_level = "management"
        
        # Determine industry
        industry = "technology"
        if any(term in text_lower for term in ['finance', 'banking', 'fintech']):
            industry = "finance"
        elif any(term in text_lower for term in ['healthcare', 'medical', 'biotech']):
            industry = "healthcare"
        elif any(term in text_lower for term in ['retail', 'e-commerce', 'shopping']):
            industry = "retail"
        
        # Extract key responsibilities
        responsibilities = []
        if 'develop' in text_lower or 'build' in text_lower:
            responsibilities.append("Software development and implementation")
        if 'design' in text_lower:
            responsibilities.append("System design and architecture")
        if 'test' in text_lower or 'qa' in text_lower:
            responsibilities.append("Testing and quality assurance")
        if 'collaborate' in text_lower or 'team' in text_lower:
            responsibilities.append("Team collaboration and communication")
        if 'maintain' in text_lower:
            responsibilities.append("System maintenance and support")
        
        # Generate recommendations
        candidate_tips = [
            f"Highlight experience with {', '.join(tech_skills[:3])} in your resume" if tech_skills else "Focus on relevant technical skills",
            f"Emphasize {min_experience}+ years of experience" if min_experience > 0 else "Highlight relevant project experience",
            f"Position yourself for a {job_level}-level role" if job_level else "Match your experience level to the role"
        ]
        
        recruiter_tips = [
            "Consider adding salary range to attract more candidates",
            "Specify remote work policy clearly",
            "Include specific project examples in the job description"
        ]
        
        return {
            "requirements": {
                "required_skills": tech_skills,
                "min_experience_years": min_experience,
                "education_level": "bachelor" if 'degree' in text_lower or 'bachelor' in text_lower else "not specified",
                "job_level": job_level
            },
            "analysis": {
                "job_type": "remote" if 'remote' in text_lower else "full-time",
                "industry": industry,
                "remote_work": "remote" if 'remote' in text_lower else "hybrid" if 'hybrid' in text_lower else "on-site"
            },
            "key_responsibilities": responsibilities[:4],  # Limit to 4
            "recommendations": {
                "for_candidates": candidate_tips,
                "for_recruiters": recruiter_tips
            },
            "note": "Analysis based on keyword matching - AI features limited"
        }
    
    def _calculate_metrics(self, job_description: str) -> Dict[str, Any]:
        """Calculate basic metrics about the job description"""
        words = job_description.split()
        sentences = job_description.split('.')
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'reading_level': 'medium',
            'completeness_score': min(len(words) // 2, 100)  # Simple completeness based on length
        }