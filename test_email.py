import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append('.')

# Load environment variables
load_dotenv()

# Import your outreach manager
from utils.outreach_manager import OutreachManager

def test_email_config():
    """Test email configuration with your Gmail App Password"""
    
    # Get email credentials from environment
    from_email = os.getenv('SMTP_EMAIL')
    from_password = os.getenv('SMTP_PASSWORD')
    
    print(f"Testing email configuration...")
    print(f"From email: {from_email}")
    print(f"App password length: {len(from_password) if from_password else 'Not found'}")
    
    if not from_email or not from_password:
        print("❌ ERROR: Email credentials not found in .env file")
        return False
    
    # Test email sending
    outreach_manager = OutreachManager()
    result = outreach_manager.send_email(
        to_email=from_email,  # Send test email to yourself
        subject="HireAI Email Test - " + "2025-06-01 14:36:06",
        body=f"""Hello pranamya-jain,

This is a test email from your HireAI outreach system.

If you receive this email, your email configuration is working correctly!

Test sent at: 2025-06-01 14:36:06 UTC

Best regards,
HireAI System""",
        from_email=from_email,
        from_password=from_password
    )
    
    print(f"Test result: {result}")
    
    if result['status'] == 'success':
        print("✅ SUCCESS: Email configuration is working!")
        return True
    else:
        print(f"❌ ERROR: {result['message']}")
        return False

if __name__ == "__main__":
    test_email_config()