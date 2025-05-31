from groq import Groq
import json
from typing import List, Dict, Any
import re

class AIMatcher:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "mixtral-8x7b-32768"  # Fast and capable model
    
    def match_candidates(self, job_description: str, candidates: List[Dict], filters: Dict = None) -> List[Dict]:
        """Match candidates to a job description using AI"""
        if not candidates:
            return []
        
        # Apply basic filters first
        filtered_candidates = self._apply_filters(candidates, filters or {})
        
        # Score each candidate using AI
        scored_candidates = []
        for candidate in filtered_candidates:
            try:
                score_data = self._score_candidate(job_description, candidate)
                candidate_with_score = candidate.copy()
                candidate_with_score.update(score_data)
                scored_candidates.append(candidate_with_score)
            except Exception as e:
                print(f"Error scoring candidate {candidate.get('id', 'unknown')}: {e}")
                # Add candidate with default score
                candidate_with_score = candidate.copy()
                candidate_with_score.update({
                    'match_score': 0,
                    'match_reasons': ['Error in AI analysis'],
                    'skill_match': 0,
                    'experience_match': 0
                })
                scored_candidates.append(candidate_with_score)
        
        # Sort by match score (highest first)
        scored_candidates.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return scored_candidates
    
    def _apply_filters(self, candidates: List[Dict], filters: Dict) -> List[Dict]:
        """Apply basic filters to candidates"""
        filtered = candidates.copy()
        
        # Filter by minimum experience
        if filters.get('min_experience'):
            min_exp = int(filters['min_experience'])
            filtered = [c for c in filtered if c.get('experience_years', 0) >= min_exp]
        
        # Filter by required skills
        if filters.get('required_skills'):
            required_skills = [skill.lower().strip() for skill in filters['required_skills']]
            filtered = [
                c for c in filtered 
                if any(
                    req_skill in [skill.lower() for skill in c.get('skills', [])]
                    for req_skill in required_skills
                )
            ]
        
        # Filter by location
        if filters.get('location'):
            location_filter = filters['location'].lower()
            filtered = [
                c for c in filtered 
                if location_filter in c.get('location', '').lower()
            ]
        
        return filtered
    
    def _score_candidate(self, job_description: str, candidate: Dict) -> Dict:
        """Score a single candidate against the job description using AI"""
        
        # Prepare candidate summary for AI
        candidate_summary = self._prepare_candidate_summary(candidate)
        
        prompt = f"""
        You are an expert HR recruiter. Analyze how well this candidate matches the job requirements.

        JOB DESCRIPTION:
        {job_description}

        CANDIDATE PROFILE:
        {candidate_summary}

        Please provide your analysis in the following JSON format:
        {{
            "match_score": <integer from 0-100>,
            "skill_match": <integer from 0-100>,
            "experience_match": <integer from 0-100>,
            "match_reasons": [
                "reason 1 why this candidate is a good/poor match",
                "reason 2",
                "reason 3"
            ],
            "missing_skills": [
                "skill 1 that the candidate lacks",
                "skill 2"
            ],
            "strengths": [
                "strength 1 of this candidate",
                "strength 2"
            ]
        }}

        Be objective and thorough in your assessment. Focus on technical skills, experience level, and relevant background.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert HR recruiter analyzing candidate-job fit. Always respond with valid JSON."},
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
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Error in AI scoring: {e}")
            # Return default scoring
            return {
                "match_score": 50,
                "skill_match": 50,
                "experience_match": 50,
                "match_reasons": ["AI analysis unavailable"],
                "missing_skills": [],
                "strengths": ["Unable to analyze"]
            }
    
    def _prepare_candidate_summary(self, candidate: Dict) -> str:
        """Prepare a concise candidate summary for AI analysis"""
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"Name: {candidate.get('name', 'Unknown')}")
        
        # Experience
        exp_years = candidate.get('experience_years', 0)
        summary_parts.append(f"Years of Experience: {exp_years}")
        
        # Skills
        skills = candidate.get('skills', [])
        if skills:
            summary_parts.append(f"Skills: {', '.join(skills)}")
        
        # Work Experience
        experience = candidate.get('experience', [])
        if experience:
            exp_text = "Work Experience:\n"
            for exp in experience[:3]:  # Limit to top 3 experiences
                exp_text += f"- {exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')}\n"
            summary_parts.append(exp_text)
        
        # Education
        education = candidate.get('education', [])
        if education:
            edu_text = "Education:\n"
            for edu in education[:2]:  # Limit to top 2 education entries
                edu_text += f"- {edu.get('degree', 'Unknown')} from {edu.get('institution', 'Unknown')}\n"
            summary_parts.append(edu_text)
        
        # Professional Summary
        if candidate.get('summary'):
            summary_parts.append(f"Summary: {candidate.get('summary')}")
        
        return "\n\n".join(summary_parts)
    
    def get_job_requirements(self, job_description: str) -> Dict:
        """Extract key requirements from job description using AI"""
        prompt = f"""
        Analyze this job description and extract the key requirements in JSON format:

        JOB DESCRIPTION:
        {job_description}

        Please extract:
        {{
            "required_skills": ["skill1", "skill2", "skill3"],
            "preferred_skills": ["skill1", "skill2"],
            "min_experience_years": <number>,
            "education_requirements": ["requirement1", "requirement2"],
            "job_level": "entry/mid/senior",
            "key_responsibilities": ["resp1", "resp2", "resp3"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing job descriptions. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Error analyzing job description: {e}")
            return {
                "required_skills": [],
                "preferred_skills": [],
                "min_experience_years": 0,
                "education_requirements": [],
                "job_level": "unknown",
                "key_responsibilities": []
            }