from celery import Celery
import os
from utils.email_utils import send_brevo_email

celery = Celery(
    "app",
    broker=f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}/0",
    backend=f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}/0",
    include=['worker']  # Include this module for task discovery
)

# Configure Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        'worker.print_otp_to_console': {'queue': 'celery'},
        'worker.add': {'queue': 'celery'},
        'worker.send_otp_email': {'queue': 'celery'},
    }
)

@celery.task
def add(x, y):
    return x + y

@celery.task
def print_otp_to_console(otp, user_id):
    """Task to print OTP to console after a delay"""
    print(f"OTP for user {user_id}: {otp}")
    return True

@celery.task
def send_otp_email(email: str, otp: str):
    """Task to send OTP email"""
    subject = "Your OTP for Password Reset"
    html_content = f"<p>Your OTP for password reset is: <strong>{otp}</strong></p>"
    send_brevo_email(to_email=email, subject=subject, html_content=html_content)
    return True
