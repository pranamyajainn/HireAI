import json
import re
import os
from typing import Dict, List, Any, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception as e:
    print(f"Gemini import failed: {e}")
    GEMINI_AVAILABLE = False

class AIMatcher:
    def __init__(self, api_key: str = None):
        self.ai_available = False
        
        if GEMINI_AVAILABLE:
            # Use provided key or environment variable
            gemini_key = api_key or os.getenv('GEMINI_API_KEY')
            
            if gemini_key:
                try:
                    print(f"🔧 AIMatcher: Configuring Gemini...")
                    genai.configure(api_key=gemini_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash')
                    
                    # Simple test without storing the response
                    self.model.generate_content("Test")
                    self.ai_available = True
                    print("✅ AIMatcher: Gemini working successfully!")
                except Exception as e:
                    print(f"❌ AIMatcher: Gemini failed: {e}")
                    self.ai_available = False
            else:
                print("🔄 AIMatcher: No Gemini API key found - using fallback")
        else:
            print("🔄 AIMatcher: Gemini not available - using fallback")
    
    def parse_natural_language_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language hiring queries into structured criteria"""
        if self.ai_available:
            return self._parse_with_ai(query)
        else:
            return self._parse_with_advanced_regex(query)
    
    def _parse_with_ai(self, query: str) -> Dict[str, Any]:
        """Use AI to parse natural language queries"""
        prompt = f"""
        Parse this hiring query into structured criteria. Return ONLY valid JSON:

        Query: "{query}"

        Extract and return in this exact format:
        {{
            "role": "extracted job title",
            "seniority": "entry/mid/senior/lead",
            "required_skills": ["skill1", "skill2"],
            "preferred_skills": ["skill3", "skill4"],
            "location": ["location1", "location2"],
            "remote_ok": true/false,
            "contract_type": "full-time/contract/either",
            "min_experience": 0,
            "industry": "technology/finance/healthcare/etc"
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
            print(f"AI query parsing failed: {e}")
            return self._parse_with_advanced_regex(query)
    
    def _parse_with_advanced_regex(self, query: str) -> Dict[str, Any]:
        """Enhanced regex-based query parsing"""
        query_lower = query.lower()
        
        # Extract job role
        role_patterns = [
            r'(machine learning|ml|ai)\s+(engineer|scientist|developer)',
            r'(data)\s+(scientist|engineer|analyst)',
            r'(software|backend|frontend|full[- ]?stack)\s+(engineer|developer)',
            r'(devops|sre)\s+(engineer)',
            r'(product)\s+(manager)',
            r'(gen-ai|generative ai)\s+(engineer|developer)'
        ]
        
        role = "Engineer"  # default
        for pattern in role_patterns:
            match = re.search(pattern, query_lower)
            if match:
                role = match.group().title()
                break
        
        # Extract seniority with better patterns
        seniority = "mid"  # default
        if re.search(r'\b(senior|sr\.?|lead|principal|staff|architect)\b', query_lower):
            seniority = "senior"
        elif re.search(r'\b(junior|jr\.?|entry|graduate|intern|associate)\b', query_lower):
            seniority = "entry"
        elif re.search(r'\b(director|vp|head of|chief)\b', query_lower):
            seniority = "lead"
        
        # Enhanced skill extraction
        skill_keywords = {
            'Python': ['python', 'django', 'flask', 'fastapi', 'pytorch'],
            'JavaScript': ['javascript', 'js', 'react', 'angular', 'vue', 'node'],
            'Machine Learning': ['ml', 'machine learning', 'ai', 'tensorflow', 'pytorch', 'scikit-learn'],
            'LangChain': ['langchain', 'lang chain', 'lang-chain'],
            'RAG': ['rag', 'retrieval augmented', 'retrieval-augmented'],
            'Gen-AI': ['gen-ai', 'generative ai', 'llm', 'gpt', 'openai'],
            'Data Science': ['data science', 'data scientist', 'pandas', 'numpy'],
            'AWS': ['aws', 'amazon web services', 'ec2', 's3', 'lambda'],
            'Docker': ['docker', 'kubernetes', 'k8s', 'containers'],
            'SQL': ['sql', 'postgresql', 'mysql', 'database', 'mongodb'],
            'React': ['react', 'reactjs', 'react.js'],
            'Node.js': ['node', 'nodejs', 'node.js'],
            'Java': ['java', 'spring', 'hibernate'],
            'Go': ['go', 'golang'],
            'Rust': ['rust'],
            'C++': ['c++', 'cpp'],
            'TypeScript': ['typescript', 'ts']
        }
        
        required_skills = []
        preferred_skills = []
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                required_skills.append(skill)
        
        # Extract locations with better patterns
        locations = []
        location_patterns = {
            'Europe': ['europe', 'eu', 'european'],
            'USA': ['usa', 'us', 'united states', 'america'],
            'San Francisco': ['san francisco', 'sf', 'bay area'],
            'New York': ['new york', 'ny', 'nyc'],
            'London': ['london', 'uk', 'united kingdom'],
            'Berlin': ['berlin', 'germany'],
            'Toronto': ['toronto', 'canada'],
            'Remote': ['remote', 'anywhere', 'distributed']
        }
        
        for location, keywords in location_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                locations.append(location)
        
        # Contract type detection
        contract_type = "full-time"  # default
        if re.search(r'\b(contract|freelance|contractor|consulting)\b', query_lower):
            contract_type = "contract"
        elif re.search(r'\b(part[- ]?time)\b', query_lower):
            contract_type = "part-time"
        
        # Remote work detection
        remote_ok = bool(re.search(r'\b(remote|distributed|anywhere|wfh|work from home)\b', query_lower))
        
        # Experience extraction with better patterns
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience',
            r'minimum\s*(\d+)\s*years?',
            r'at least\s*(\d+)\s*years?',
            r'(\d+)\+\s*years?'
        ]
        
        min_experience = 0
        for pattern in exp_patterns:
            match = re.search(pattern, query_lower)
            if match:
                min_experience = int(match.group(1))
                break
        
        # Industry detection
        industry = "technology"  # default
        industry_keywords = {
            'finance': ['fintech', 'finance', 'banking', 'trading', 'investment'],
            'healthcare': ['healthcare', 'medical', 'biotech', 'pharma'],
            'retail': ['retail', 'e-commerce', 'ecommerce', 'shopping'],
            'gaming': ['gaming', 'game', 'entertainment'],
            'education': ['education', 'edtech', 'learning']
        }
        
        for ind, keywords in industry_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                industry = ind
                break
        
        return {
            "role": role,
            "seniority": seniority,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "location": locations,
            "remote_ok": remote_ok,
            "contract_type": contract_type,
            "min_experience": min_experience,
            "industry": industry,
            "parsed_query": query  # Keep original for reference
        }
    
    def match_candidates(self, job_description: str, candidates: List[Dict], filters: Dict = None) -> List[Dict]:
        """Enhanced candidate matching with intelligent scoring"""
        if not candidates:
            return []
        
        # Parse the job description into criteria
        criteria = self.parse_natural_language_query(job_description) if job_description.strip() else {}
        
        scored_candidates = []
        for candidate in candidates:
            if self.ai_available:
                score_data = self._ai_score_candidate(candidate, job_description, criteria)
            else:
                score_data = self._advanced_score_candidate(candidate, criteria)
            
            candidate_with_score = candidate.copy()
            candidate_with_score.update(score_data)
            scored_candidates.append(candidate_with_score)
        
        # Sort by match score
        return sorted(scored_candidates, key=lambda x: x.get('match_score', 0), reverse=True)
    
    def _ai_score_candidate(self, candidate: Dict, job_description: str, criteria: Dict) -> Dict:
        """Use AI to score candidate fit"""
        prompt = f"""
        Score this candidate against the job requirements. Return ONLY valid JSON:

        JOB: {job_description}

        CANDIDATE:
        - Name: {candidate.get('name', 'Unknown')}
        - Skills: {', '.join(candidate.get('skills', []))}
        - Experience: {candidate.get('experience_years', 0)} years
        - Location: {candidate.get('location', 'Unknown')}
        - Summary: {candidate.get('summary', 'No summary')[:200]}

        Return scoring in this exact format:
        {{
            "match_score": 85,
            "skill_match": 90,
            "experience_match": 80,
            "location_match": 85,
            "match_reasons": ["Has required Python skills", "5+ years experience matches requirement"],
            "concerns": ["Missing specific framework experience"],
            "overall_fit": "excellent/good/fair/poor"
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
            print(f"AI candidate scoring failed: {e}")
            return self._advanced_score_candidate(candidate, criteria)
    
    def _advanced_score_candidate(self, candidate: Dict, criteria: Dict) -> Dict:
        """Advanced fallback candidate scoring with better logic"""
        total_score = 0
        reasons = []
        concerns = []
        
        # 1. Skill Matching (40% weight)
        candidate_skills = [skill.lower().strip() for skill in candidate.get('skills', [])]
        required_skills = [skill.lower().strip() for skill in criteria.get('required_skills', [])]
        
        if required_skills:
            skill_matches = 0
            matched_skills = []
            
            for req_skill in required_skills:
                for cand_skill in candidate_skills:
                    # Fuzzy matching for skills
                    if (req_skill in cand_skill or cand_skill in req_skill or 
                        self._skills_similar(req_skill, cand_skill)):
                        skill_matches += 1
                        matched_skills.append(req_skill.title())
                        break
            
            skill_score = (skill_matches / len(required_skills)) * 100
            
            if matched_skills:
                reasons.append(f"Strong match in: {', '.join(matched_skills[:3])}")
            else:
                concerns.append("Missing key required skills")
            
            # Bonus for extra relevant skills
            bonus_skills = len(candidate_skills) - len(required_skills)
            if bonus_skills > 0:
                skill_score = min(100, skill_score + (bonus_skills * 5))
                reasons.append(f"Has {len(candidate_skills)} total skills")
        else:
            skill_score = 70  # Default when no requirements specified
        
        total_score += skill_score * 0.4
        
        # 2. Experience Matching (30% weight)
        candidate_exp_raw = candidate.get('experience_years')
        candidate_exp = 0
        if candidate_exp_raw is not None:
            try:
                candidate_exp = int(float(candidate_exp_raw))
            except (ValueError, TypeError):
                candidate_exp = 0 # Default to 0 if conversion fails

        required_exp = criteria.get('min_experience', 0)

        if required_exp == 0:
            exp_score = 80  # No requirement specified
        elif candidate_exp >= required_exp:
            # Bonus for more experience, but diminishing returns
            exp_score = min(100, 80 + (candidate_exp - required_exp) * 5)
            reasons.append(f"{candidate_exp} years experience (required: {required_exp}+)")
        else:
            # Penalty for less experience
            exp_score = max(20, (candidate_exp / required_exp) * 70)
            concerns.append(f"Only {candidate_exp} years (required: {required_exp}+)")

        total_score += exp_score * 0.3
        
        # 3. Location/Remote Matching (20% weight)
        candidate_location = candidate.get('location', '').lower()
        required_locations = [loc.lower() for loc in criteria.get('location', [])]
        remote_ok = criteria.get('remote_ok', False)
        
        if remote_ok or 'remote' in candidate_location:
            location_score = 100
            reasons.append("Remote work compatible")
        elif not required_locations:
            location_score = 80  # No specific location requirement
        elif any(self._location_match(loc, candidate_location) for loc in required_locations):
            location_score = 95
            reasons.append("Located in target region")
        else:
            location_score = 40
            concerns.append("Location may not be ideal")
        
        total_score += location_score * 0.2

        # 4. Seniority Matching (10% weight)
        # Use the already processed integer candidate_exp
        required_seniority = criteria.get('seniority', 'mid')

        seniority_score = self._match_seniority(candidate_exp, required_seniority)
        total_score += seniority_score * 0.1

        # Overall assessment
        final_score = min(100, int(total_score))
        
        if final_score >= 85:
            overall_fit = "excellent"
        elif final_score >= 70:
            overall_fit = "good"
        elif final_score >= 50:
            overall_fit = "fair"
        else:
            overall_fit = "poor"
        
        return {
            "match_score": final_score,
            "skill_match": int(skill_score),
            "experience_match": int(exp_score),
            "location_match": int(location_score),
            "match_reasons": reasons[:4],  # Top 4 reasons
            "concerns": concerns[:3],      # Top 3 concerns
            "overall_fit": overall_fit
        }
    
    def _skills_similar(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are similar"""
        similar_skills = {
            'javascript': ['js', 'node', 'react', 'angular'],
            'python': ['django', 'flask', 'fastapi'],
            'machine learning': ['ml', 'ai', 'tensorflow', 'pytorch'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb']
        }
        
        for base_skill, variants in similar_skills.items():
            if (skill1 in variants and base_skill in skill2) or (skill2 in variants and base_skill in skill1):
                return True
        
        return False
    
    def _location_match(self, required: str, candidate: str) -> bool:
        """Check if locations match"""
        location_groups = {
            'europe': ['london', 'berlin', 'amsterdam', 'paris', 'madrid', 'uk', 'germany', 'france'],
            'usa': ['san francisco', 'new york', 'seattle', 'austin', 'boston', 'sf', 'nyc'],
            'remote': ['remote', 'anywhere', 'distributed']
        }
        
        for group, locations in location_groups.items():
            if required in locations and any(loc in candidate for loc in locations):
                return True
        
        return required in candidate
    
    def _match_seniority(self, experience_years: int, required_seniority: str) -> int:
        """Match candidate experience to required seniority level"""
        seniority_ranges = {
            'entry': (0, 2),
            'mid': (2, 5),
            'senior': (5, 10),
            'lead': (8, 15)
        }
        
        min_exp, max_exp = seniority_ranges.get(required_seniority, (0, 10))
        
        if min_exp <= experience_years <= max_exp:
            return 90
        elif experience_years >= min_exp:
            return 75  # Over-qualified
        else:
            return 50  # Under-qualified
    
    def generate_screening_questions(self, job_description: str, candidate: Dict) -> List[Dict]:
        """Generate pre-screening questions for a candidate"""
        if self.ai_available:
            return self._ai_generate_questions(job_description, candidate)
        else:
            return self._smart_generate_questions(job_description, candidate)
    
    def _ai_generate_questions(self, job_description: str, candidate: Dict) -> List[Dict]:
        """Use AI to generate screening questions"""
        prompt = f"""
        Generate 4 pre-screening questions for this candidate. Return ONLY valid JSON:

        JOB: {job_description}

        CANDIDATE:
        - Skills: {', '.join(candidate.get('skills', []))}
        - Experience: {candidate.get('experience_years', 0)} years

        Return in this exact format:
        {{
            "questions": [
                {{
                    "question": "Can you describe your experience with Python and Django?",
                    "type": "technical",
                    "expected_keywords": ["python", "django", "mvc", "orm"],
                    "difficulty": "medium"
                }}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('questions', [])
            else:
                raise ValueError("No valid JSON in AI response")
                
        except Exception as e:
            print(f"AI question generation failed: {e}")
            return self._smart_generate_questions(job_description, candidate)
    
    def _smart_generate_questions(self, job_description: str, candidate: Dict) -> List[Dict]:
        """Generate smart screening questions based on skills and requirements"""
        questions = []
        candidate_skills = [skill.lower() for skill in candidate.get('skills', [])]
        
        # Technical questions based on specific skills
        skill_questions = {
            'python': {
                "question": "Can you walk me through a recent Python project? What frameworks and libraries did you use?",
                "type": "technical",
                "expected_keywords": ["python", "project", "framework", "library"],
                "difficulty": "medium"
            },
            'machine learning': {
                "question": "Describe a machine learning model you've built. What was the problem, your approach, and the results?",
                "type": "technical", 
                "expected_keywords": ["model", "data", "algorithm", "performance"],
                "difficulty": "hard"
            },
            'langchain': {
                "question": "How have you used LangChain in your projects? Can you explain a specific use case?",
                "type": "technical",
                "expected_keywords": ["langchain", "llm", "chains", "agents"],
                "difficulty": "hard"
            },
            'react': {
                "question": "What's your experience with React? Can you explain how you handle state management?",
                "type": "technical",
                "expected_keywords": ["react", "components", "state", "hooks"],
                "difficulty": "medium"
            },
            'aws': {
                "question": "Which AWS services have you worked with? Can you describe a cloud architecture you've designed?",
                "type": "technical",
                "expected_keywords": ["aws", "cloud", "services", "architecture"],
                "difficulty": "medium"
            }
        }
        
        # Add skill-specific questions
        for skill in candidate_skills:
            for skill_key, question_data in skill_questions.items():
                if skill_key in skill:
                    questions.append(question_data)
                    break
        
        # Experience-based questions
        exp_years = candidate.get('experience_years', 0)
        if exp_years >= 5:
            questions.append({
                "question": f"With {exp_years} years of experience, what's the most complex technical challenge you've solved?",
                "type": "behavioral",
                "expected_keywords": ["challenge", "solution", "technical", "complex"],
                "difficulty": "medium"
            })
        else:
            questions.append({
                "question": "What recent project are you most proud of and why?",
                "type": "behavioral",
                "expected_keywords": ["project", "proud", "accomplishment"],
                "difficulty": "easy"
            })
        
        # Role-specific questions based on job description
        job_lower = job_description.lower()
        if 'remote' in job_lower:
            questions.append({
                "question": "This role offers remote work. How do you stay productive and communicate effectively in a remote environment?",
                "type": "logistics",
                "expected_keywords": ["remote", "communication", "productivity"],
                "difficulty": "easy"
            })
        
        # Availability question
        questions.append({
            "question": "What's your availability for this role? When could you start?",
            "type": "logistics",
            "expected_keywords": ["availability", "start", "notice"],
            "difficulty": "easy"
        })
        
        return questions[:4]  # Return max 4 questions