import os
import sys
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

class EmailService:
    """Email service for sending admin statistics and notifications"""
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        if not self.api_key:
            print("Warning: SENDGRID_API_KEY environment variable not set")
            self.sg = None
        else:
            self.sg = SendGridAPIClient(self.api_key)
    
    def send_admin_stats(self, to_email: str, stats: dict, from_email: str = 'noreply@cylinder-tracker.com') -> bool:
        """Send admin statistics email"""
        if not self.sg:
            print("SendGrid not configured")
            return False
        
        try:
            # Create HTML email content
            html_content = self._generate_stats_html(stats)
            
            # Create plain text version
            text_content = self._generate_stats_text(stats)
            
            message = Mail(
                from_email=Email(from_email),
                to_emails=To(to_email),
                subject=f"Cylinder Tracker Statistics - {datetime.now().strftime('%B %d, %Y')}",
                html_content=Content("text/html", html_content)
            )
            
            # Add plain text version
            message.add_content(Content("text/plain", text_content))
            
            response = self.sg.send(message)
            print(f"Email sent successfully. Status code: {response.status_code}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _generate_stats_html(self, stats: dict) -> str:
        """Generate HTML email content for statistics"""
        current_date = datetime.now().strftime('%B %d, %Y')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; }}
                .stat-card {{ background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .stat-label {{ color: #666; font-size: 14px; }}
                .footer {{ background: #f8f9fa; padding: 15px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔧 Oxygen Cylinder Tracker</h1>
                    <p>Daily Statistics Report - {current_date}</p>
                </div>
                
                <div class="content">
                    <h2>System Overview</h2>
                    
                    <div class="stat-card">
                        <div class="stat-number">{stats.get('total_customers', 0)}</div>
                        <div class="stat-label">Total Customers</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-number">{stats.get('total_cylinders', 0)}</div>
                        <div class="stat-label">Total Cylinders</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-number">{stats.get('available_cylinders', 0)}</div>
                        <div class="stat-label">Available Cylinders</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-number">{stats.get('rented_cylinders', 0)}</div>
                        <div class="stat-label">Rented Cylinders</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-number">{stats.get('maintenance_cylinders', 0)}</div>
                        <div class="stat-label">Cylinders in Maintenance</div>
                    </div>
                    
                    <h3>Performance Metrics</h3>
                    
                    <div class="stat-card">
                        <div class="stat-number">{stats.get('utilization_rate', 0)}%</div>
                        <div class="stat-label">Utilization Rate</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-number">{stats.get('efficiency_score', 0)}/10</div>
                        <div class="stat-label">Efficiency Score</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-number">{stats.get('days_active', 0)}</div>
                        <div class="stat-label">Days Active</div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated report from your Oxygen Cylinder Tracker system.</p>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_stats_text(self, stats: dict) -> str:
        """Generate plain text email content for statistics"""
        current_date = datetime.now().strftime('%B %d, %Y')
        
        text = f"""
OXYGEN CYLINDER TRACKER - DAILY STATISTICS REPORT
{current_date}

SYSTEM OVERVIEW
===============
Total Customers: {stats.get('total_customers', 0)}
Total Cylinders: {stats.get('total_cylinders', 0)}
Available Cylinders: {stats.get('available_cylinders', 0)}
Rented Cylinders: {stats.get('rented_cylinders', 0)}
Cylinders in Maintenance: {stats.get('maintenance_cylinders', 0)}

PERFORMANCE METRICS
==================
Utilization Rate: {stats.get('utilization_rate', 0)}%
Efficiency Score: {stats.get('efficiency_score', 0)}/10
Days Active: {stats.get('days_active', 0)}

---
This is an automated report from your Oxygen Cylinder Tracker system.
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return text.strip()
    
    def send_test_email(self, to_email: str, from_email: str = 'noreply@cylinder-tracker.com') -> bool:
        """Send a test email to verify configuration"""
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