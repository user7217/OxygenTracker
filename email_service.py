import os
import sys
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

class EmailService:

    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        if not self.api_key:
            print("Warning: SENDGRID_API_KEY environment variable not set")
            self.sg = None
        else:
            self.sg = SendGridAPIClient(self.api_key)
    
    def send_admin_stats(self, to_email: str, stats: dict, from_email: str = 'noreply@cylinder-tracker.com') -> bool:
        
        if not self.sg:
            print("SendGrid not configured")
            return False
        
        try:
            html_content = self._generate_stats_html(stats)
            
            text_content = self._generate_stats_text(stats)
            
            message = Mail(
                from_email=Email(from_email),
                to_emails=To(to_email),
                subject=f"Cylinder Tracker Statistics - {datetime.now().strftime('%B %d, %Y')}",
                html_content=Content("text/html", html_content)
            )
            
            message.add_content(Content("text/plain", text_content))
            
            response = self.sg.send(message)
            print(f"Email sent successfully. Status code: {response.status_code}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _generate_stats_html(self, stats: dict) -> str:
        
        current_date = datetime.now().strftime('%B %d, %Y')
        
        html = f
        return html
    
    def _generate_stats_text(self, stats: dict) -> str:
        
        current_date = datetime.now().strftime('%B %d, %Y')
        
        text = f
        return text.strip()
    
    def send_test_email(self, to_email: str, from_email: str = 'noreply@cylinder-tracker.com') -> bool:
        
        if not self.sg:
            print("SendGrid not configured")
            return False
        
        try:
            message = Mail(
                from_email=Email(from_email),
                to_emails=To(to_email),
                subject="Cylinder Tracker - Email Test",
                html_content=Content("text/html", "<h1>Test Email</h1><p>Your email configuration is working correctly!</p>")
            )
            
            response = self.sg.send(message)
            print(f"Test email sent successfully. Status code: {response.status_code}")
            return True
            
        except Exception as e:
            print(f"Error sending test email: {e}")
            return False