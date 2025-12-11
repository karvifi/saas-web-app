"""
Email and SMS notification service for AI Agent Platform
Handles user communications, alerts, and marketing emails
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import asyncio
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import os
import json
from pathlib import Path
import aiosmtplib
from jinja2 import Template
import requests

logger = logging.getLogger(__name__)

class EmailService:
    """SMTP-based email service"""

    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587,
                 username: Optional[str] = None, password: Optional[str] = None,
                 use_tls: bool = True, from_email: str = "noreply@aiagentplatform.com"):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username or os.getenv("SMTP_USERNAME")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.use_tls = use_tls
        self.from_email = from_email
        self.templates_dir = Path(__file__).parent / "templates" / "emails"

        # Create templates directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Email templates
        self._load_templates()

    def _load_templates(self):
        """Load email templates"""
        self.templates = {}

        # Welcome email template
        self.templates['welcome'] = """
        <html>
        <body>
            <h1>Welcome to AI Agent Platform, {{ user_name }}!</h1>
            <p>Thank you for joining our AI-powered agent ecosystem. Your account has been successfully created.</p>
            <p>Here's what you can do:</p>
            <ul>
                <li>Execute tasks with our 11 specialized AI agents</li>
                <li>Access real-time updates via WebSocket</li>
                <li>Manage your subscription and billing</li>
                <li>Monitor your task history and analytics</li>
            </ul>
            <p>Get started by logging into your dashboard: <a href="{{ dashboard_url }}">Dashboard</a></p>
            <p>Best regards,<br>The AI Agent Platform Team</p>
        </body>
        </html>
        """

        # Task completion template
        self.templates['task_complete'] = """
        <html>
        <body>
            <h2>Task Completed Successfully</h2>
            <p>Hello {{ user_name }},</p>
            <p>Your task "{{ task_name }}" has been completed successfully.</p>
            <p><strong>Task ID:</strong> {{ task_id }}</p>
            <p><strong>Agent:</strong> {{ agent_name }}</p>
            <p><strong>Completed at:</strong> {{ completed_at }}</p>
            {% if result_summary %}
            <p><strong>Summary:</strong> {{ result_summary }}</p>
            {% endif %}
            <p>View full results in your dashboard: <a href="{{ dashboard_url }}">View Results</a></p>
        </body>
        </html>
        """

        # Payment confirmation template
        self.templates['payment_success'] = """
        <html>
        <body>
            <h2>Payment Successful</h2>
            <p>Hello {{ user_name }},</p>
            <p>Your payment of ${{ amount }} has been processed successfully.</p>
            <p><strong>Transaction ID:</strong> {{ transaction_id }}</p>
            <p><strong>Plan:</strong> {{ plan_name }}</p>
            <p><strong>Next billing date:</strong> {{ next_billing }}</p>
            <p>Thank you for your continued support!</p>
        </body>
        </html>
        """

        # System alert template
        self.templates['system_alert'] = """
        <html>
        <body>
            <h2>System Alert</h2>
            <p>{{ message }}</p>
            <p><strong>Time:</strong> {{ timestamp }}</p>
            <p><strong>Level:</strong> {{ level|upper }}</p>
            {% if action_required %}
            <p><strong>Action Required:</strong> {{ action_required }}</p>
            {% endif %}
        </body>
        </html>
        """

    async def send_email(self, to_email: str, subject: str, html_content: str,
                        text_content: Optional[str] = None, attachments: List[str] = None) -> bool:
        """Send an email asynchronously"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, "rb") as f:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header("Content-Disposition",
                                          f"attachment; filename={os.path.basename(attachment_path)}")
                            message.attach(part)

            # Send email
            if self.use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            if self.username and self.password:
                server.login(self.username, self.password)

            server.sendmail(self.from_email, to_email, message.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_template_email(self, template_name: str, to_email: str,
                                subject: str, template_vars: Dict[str, Any],
                                attachments: List[str] = None) -> bool:
        """Send email using a template"""
        if template_name not in self.templates:
            logger.error(f"Template {template_name} not found")
            return False

        template = Template(self.templates[template_name])
        html_content = template.render(**template_vars)

        # Generate text version from HTML (simple version)
        text_content = html_content.replace('<br>', '\n').replace('</p>', '\n\n')
        text_content = ''.join(c for c in text_content if c not in '<>')

        return await self.send_email(to_email, subject, html_content,
                                   text_content, attachments)

    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user"""
        template_vars = {
            'user_name': user_name,
            'dashboard_url': 'https://aiagentplatform.com/dashboard'
        }

        return await self.send_template_email(
            'welcome', user_email,
            'Welcome to AI Agent Platform!',
            template_vars
        )

    async def send_task_completion_email(self, user_email: str, user_name: str,
                                       task_id: str, task_name: str, agent_name: str,
                                       result_summary: Optional[str] = None) -> bool:
        """Send task completion notification"""
        template_vars = {
            'user_name': user_name,
            'task_id': task_id,
            'task_name': task_name,
            'agent_name': agent_name,
            'completed_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'result_summary': result_summary,
            'dashboard_url': f'https://aiagentplatform.com/dashboard/tasks/{task_id}'
        }

        return await self.send_template_email(
            'task_complete', user_email,
            f'Task Completed: {task_name}',
            template_vars
        )

    async def send_payment_confirmation(self, user_email: str, user_name: str,
                                      amount: float, transaction_id: str,
                                      plan_name: str, next_billing: str) -> bool:
        """Send payment confirmation email"""
        template_vars = {
            'user_name': user_name,
            'amount': f"{amount:.2f}",
            'transaction_id': transaction_id,
            'plan_name': plan_name,
            'next_billing': next_billing
        }

        return await self.send_template_email(
            'payment_success', user_email,
            'Payment Confirmation',
            template_vars
        )

    async def send_system_alert(self, to_emails: List[str], message: str,
                              level: str = "info", action_required: Optional[str] = None) -> bool:
        """Send system alert to administrators"""
        template_vars = {
            'message': message,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'level': level,
            'action_required': action_required
        }

        success = True
        for email in to_emails:
            result = await self.send_template_email(
                'system_alert', email,
                f'System Alert - {level.upper()}',
                template_vars
            )
            if not result:
                success = False

        return success

    async def send_bulk_email(self, emails: List[str], subject: str,
                            html_content: str, text_content: Optional[str] = None) -> Dict[str, bool]:
        """Send email to multiple recipients"""
        results = {}
        for email in emails:
            results[email] = await self.send_email(email, subject, html_content, text_content)
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        return results

class SMSService:
    """SMS notification service using Twilio or similar"""

    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None,
                 from_number: Optional[str] = None):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER")

        # Fallback to mock mode if credentials not provided
        self.mock_mode = not all([self.account_sid, self.auth_token, self.from_number])

        if self.mock_mode:
            logger.warning("SMS service running in mock mode - no real SMS will be sent")

    async def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS message"""
        if self.mock_mode:
            logger.info(f"MOCK SMS to {to_number}: {message}")
            return True

        try:
            # Using requests for simplicity (in production, use twilio library)
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            data = {
                'From': self.from_number,
                'To': to_number,
                'Body': message
            }

            response = requests.post(url, data=data, auth=(self.account_sid, self.auth_token))

            if response.status_code == 201:
                logger.info(f"SMS sent successfully to {to_number}")
                return True
            else:
                logger.error(f"Failed to send SMS: {response.text}")
                return False

        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            return False

    async def send_task_alert(self, phone_number: str, task_name: str, status: str) -> bool:
        """Send task status alert via SMS"""
        message = f"AI Agent: Task '{task_name}' is now {status}"
        return await self.send_sms(phone_number, message)

    async def send_security_alert(self, phone_number: str, alert_type: str) -> bool:
        """Send security alert via SMS"""
        message = f"AI Agent Security: {alert_type}. Please check your account."
        return await self.send_sms(phone_number, message)

class NotificationManager:
    """Unified notification manager for email and SMS"""

    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()

        # Notification preferences storage (in production, this would be in database)
        self.user_preferences = {}

    async def notify_user(self, user_id: str, notification_type: str,
                         email: Optional[str] = None, phone: Optional[str] = None,
                         **kwargs) -> Dict[str, bool]:
        """Send notification to user based on preferences"""
        results = {"email": False, "sms": False}

        # Get user preferences (mock implementation)
        prefs = self.user_preferences.get(user_id, {"email": True, "sms": False})

        if prefs.get("email") and email:
            if notification_type == "welcome":
                results["email"] = await self.email_service.send_welcome_email(
                    email, kwargs.get("user_name", "User")
                )
            elif notification_type == "task_complete":
                results["email"] = await self.email_service.send_task_completion_email(
                    email, kwargs.get("user_name", "User"), kwargs.get("task_id"),
                    kwargs.get("task_name"), kwargs.get("agent_name"), kwargs.get("result_summary")
                )
            elif notification_type == "payment":
                results["email"] = await self.email_service.send_payment_confirmation(
                    email, kwargs.get("user_name", "User"), kwargs.get("amount", 0),
                    kwargs.get("transaction_id"), kwargs.get("plan_name"), kwargs.get("next_billing")
                )

        if prefs.get("sms") and phone:
            if notification_type == "task_complete":
                results["sms"] = await self.sms_service.send_task_alert(
                    phone, kwargs.get("task_name"), "completed"
                )
            elif notification_type == "security":
                results["sms"] = await self.sms_service.send_security_alert(
                    phone, kwargs.get("alert_type", "Security Alert")
                )

        return results

    async def set_user_preferences(self, user_id: str, email: bool = True, sms: bool = False):
        """Set notification preferences for a user"""
        self.user_preferences[user_id] = {"email": email, "sms": sms}

    async def broadcast_system_alert(self, message: str, level: str = "info",
                                   admin_emails: List[str] = None):
        """Broadcast system alert to administrators"""
        if not admin_emails:
            admin_emails = ["admin@aiagentplatform.com"]  # Default admin email

        return await self.email_service.send_system_alert(admin_emails, message, level)

# Global notification manager
notification_manager = NotificationManager()

# Helper functions for easy access
async def send_welcome_notification(user_email: str, user_name: str):
    """Send welcome notification"""
    return await notification_manager.email_service.send_welcome_email(user_email, user_name)

async def send_task_completion_notification(user_id: str, user_email: str, user_name: str,
                                         task_id: str, task_name: str, agent_name: str,
                                         result_summary: Optional[str] = None):
    """Send task completion notification"""
    return await notification_manager.notify_user(
        user_id, "task_complete", email=user_email,
        user_name=user_name, task_id=task_id, task_name=task_name,
        agent_name=agent_name, result_summary=result_summary
    )

async def send_payment_notification(user_id: str, user_email: str, user_name: str,
                                  amount: float, transaction_id: str, plan_name: str, next_billing: str):
    """Send payment confirmation notification"""
    return await notification_manager.notify_user(
        user_id, "payment", email=user_email,
        user_name=user_name, amount=amount, transaction_id=transaction_id,
        plan_name=plan_name, next_billing=next_billing
    )

async def send_system_alert(message: str, level: str = "info", admin_emails: List[str] = None):
    """Send system alert"""
    return await notification_manager.broadcast_system_alert(message, level, admin_emails)