import os
import re
import PyPDF2
import docx
from typing import Dict, List, Any
import spacy

class ResumeParser:
    def __init__(self):
        # Try to load spaCy model, fallback to simple parsing if not available
        try:
            self.nlp = spacy.load('en_core_web_sm')
            self.spacy_available = True
        except OSError:
            print("spaCy model not available, using simple text parsing")
            self.spacy_available = False
            self.nlp = None
    
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Main function to parse a resume file"""
        # Extract text based on file type
        text = self._extract_text(file_path)
        
        if not text:
            return {"error": "Could not extract text from file"}
        
        # Parse the extracted text
        parsed_data = self._parse_text(text)
        parsed_data['raw_text'] = text
        parsed_data['file_path'] = file_path
        
        return parsed_data
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX files"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX: {e}")
        return text
    
    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse the extracted text to extract structured information"""
        parsed_data = {
            'name': self._extract_name(text),
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'location': self._extract_location(text),
            'skills': self._extract_skills(text),
            'experience': self._extract_experience(text),
            'education': self._extract_education(text),
            'experience_years': self._calculate_experience_years(text),
            'summary': self._extract_summary(text)
        }
        
        return parsed_data
    
    def _extract_name(self, text: str) -> str:
        """Extract candidate name from resume text"""
        lines = text.strip().split('\n')
        
        # Usually the name is in the first few lines
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 2 and len(line.split()) <= 4:
                # Skip common headers
                skip_words = ['resume', 'cv', 'curriculum', 'vitae', 'profile', 'contact', 'email', 'phone']
                if not any(word in line.lower() for word in skip_words):
                    # Check if it looks like a name (contains letters, minimal numbers)
                    if re.match(r'^[A-Za-z\s\.-]+$', line) and len(line) > 5:
                        return line.title()
        
        return "Name not found"
    
    def _extract_email(self, text: str) -> str:
        """Extract email address from resume text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else "Email not found"
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from resume text"""
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?\d{1,3}[-.\s]?\d{10}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]
        
        return "Phone not found"
    
    def _extract_location(self, text: str) -> str:
        """Extract location/address from resume text"""
        # Look for common location patterns
        location_patterns = [
            r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}',  # City, ST 12345
            r'[A-Za-z\s]+,\s*[A-Z]{2}',  # City, ST
            r'[A-Za-z\s]+,\s*[A-Za-z\s]+',  # City, Country/State
        ]
        
        for pattern in location_patterns:
            locations = re.findall(pattern, text)
            if locations:
                return locations[0]
        
        return "Location not found"
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        # Common technical skills (you can expand this list)
        common_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js', 'express',
            'django', 'flask', 'fastapi', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
            'data analysis', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'tableau',
            'html', 'css', 'bootstrap', 'sass', 'typescript', 'jquery', 'webpack',
            'microservices', 'rest api', 'graphql', 'agile', 'scrum', 'devops',
            'linux', 'windows', 'macos', 'bash', 'powershell', 'c++', 'c#', 'go',
            'rust', 'swift', 'kotlin', 'php', 'ruby', 'scala', 'r', 'matlab'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Remove duplicates and return
        return list(set(found_skills))
    
    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience from resume text"""
        # This is a simplified version - you can make it more sophisticated
        experience = []
        
        # Look for common experience section headers
        experience_sections = re.split(r'(?i)(experience|work\s+experience|employment|professional\s+experience)', text)
        
        if len(experience_sections) > 1:
            exp_text = experience_sections[-1][:1000]  # Take first 1000 chars after experience header
            
            # Look for job titles and companies (simplified pattern)
            job_patterns = [
                r'([A-Za-z\s]+(?:Engineer|Developer|Manager|Analyst|Specialist|Coordinator|Director|Lead))[^\n]*\n[^\n]*([A-Za-z\s&,\.]+)(?:Inc|LLC|Corp|Company|Ltd)?',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)[^\n]*\n[^\n]*([A-Z][a-z\s&,\.]+)'
            ]
            
            for pattern in job_patterns:
                matches = re.findall(pattern, exp_text)
                for match in matches[:3]:  # Limit to first 3 matches
                    experience.append({
                        'title': match[0].strip(),
                        'company': match[1].strip(),
                        'description': 'Details extracted from resume'
                    })
                if matches:
                    break
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from resume text"""
        education = []
        
        # Look for common degree patterns
        degree_patterns = [
            r'(Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|MBA)[^\n]*([A-Za-z\s]+(?:University|College|Institute))',
            r'(B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|MBA|PhD)[^\n]*([A-Za-z\s]+(?:University|College|Institute))'
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                education.append({
                    'degree': match[0].strip(),
                    'institution': match[1].strip(),
                    'year': 'Not specified'
                })
        
        return education
    
    def _calculate_experience_years(self, text: str) -> int:
        """Calculate total years of experience"""
        # Look for experience mentions
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience',
            r'experience[:\s]*(\d+)\+?\s*years?'
        ]
        
        years = []
        for pattern in exp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            years.extend([int(match) for match in matches])
        
        return max(years) if years else 0
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary or objective"""
        # Look for summary/objective sections
        summary_patterns = [
            r'(?i)(summary|objective|profile)[:\s]*([^\n]*(?:\n[^\n]*){0,3})',
            r'(?i)(about\s+me|professional\s+summary)[:\s]*([^\n]*(?:\n[^\n]*){0,3})'
        ]
        
        for pattern in summary_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0][1].strip()[:200]  # First 200 chars
        
        # If no summary section, take first paragraph as summary
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
        if paragraphs:
            return paragraphs[0][:200]
        
        return "No summary available"