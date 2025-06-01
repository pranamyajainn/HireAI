import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from typing import Dict, List

class OutreachManager:
    def __init__(self):
        self.templates = self.load_templates()
    
    def load_templates(self):
        """Load email templates from JSON file"""
        try:
            with open('data/email_templates.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_templates()
    
    def get_default_templates(self):
        """Default email templates"""
        return {
            "initial_contact": {
                "subject": "Exciting {job_title} Opportunity at {company_name}",
                "body": """Hi {candidate_name},

I hope this email finds you well. I came across your profile and was impressed by your experience in {top_skills}.

We have an exciting {job_title} opportunity at {company_name} that I believe would be a great fit for your background. The role involves {job_summary} and offers {benefits}.

Based on your experience with {relevant_experience}, I think you'd excel in this position. The match score for your profile is {match_score}%.

Would you be interested in learning more about this opportunity? I'd love to schedule a brief call to discuss the details.

Best regards,
{recruiter_name}
{recruiter_email}
{company_name}"""
            },
            "follow_up": {
                "subject": "Following up on {job_title} opportunity",
                "body": """Hi {candidate_name},

I wanted to follow up on the {job_title} position I shared with you last week. 

This role is still available and I believe your skills in {top_skills} make you an ideal candidate. The hiring manager is actively reviewing profiles and I'd hate for you to miss this opportunity.

Are you available for a quick 15-minute call this week to discuss?

Best regards,
{recruiter_name}"""
            }
        }
    
    def personalize_email(self, template_type: str, candidate_data: Dict, job_data: Dict, recruiter_data: Dict):
        """Generate personalized email content"""
        template = self.templates.get(template_type, self.templates["initial_contact"])
        
        # Extract top skills (first 3)
        skills = candidate_data.get('skills', [])
        top_skills = ', '.join(skills[:3]) if skills else "your technical skills"
        
        # Personalization variables
        variables = {
            'candidate_name': candidate_data.get('name', 'there'),
            'job_title': job_data.get('title', 'Software Developer'),
            'company_name': job_data.get('company', 'our company'),
            'top_skills': top_skills,
            'relevant_experience': candidate_data.get('experience_summary', 'your background'),
            'job_summary': job_data.get('summary', 'exciting challenges'),
            'benefits': job_data.get('benefits', 'competitive compensation and growth opportunities'),
            'match_score': candidate_data.get('match_score', 85),
            'recruiter_name': recruiter_data.get('name', 'Hiring Team'),
            'recruiter_email': recruiter_data.get('email', ''),
        }
        
        # Replace placeholders
        subject = template['subject'].format(**variables)
        body = template['body'].format(**variables)
        
        return subject, body
    
    def send_email(self, to_email: str, subject: str, body: str, from_email: str, from_password: str):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # SMTP server setup (Gmail example)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_email, from_password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return {"status": "success", "message": "Email sent successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def log_outreach(self, candidate_id: str, template_type: str, status: str):
        """Log outreach activity"""
        log_entry = {
            "candidate_id": candidate_id,
            "template_type": template_type,
            "timestamp": datetime.now().isoformat(),
            "status": status
        }
        
        # Append to outreach log
        try:
            with open('data/outreach_log.json', 'r') as f:
                logs = json.load(f)
        except FileNotFoundError:
            logs = []
        
        logs.append(log_entry)
        
        with open('data/outreach_log.json', 'w') as f:
            json.dump(logs, f, indent=2)