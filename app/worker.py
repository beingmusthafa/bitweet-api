from celery import Celery
import os

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
