import asyncio
import subprocess
import sys
import time
import socket

def wait_for_postgres():
    print("Waiting for PostgreSQL...")
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('postgres', 5432))
            sock.close()
            if result == 0:
                print("PostgreSQL is ready!")
                break
        except:
            pass
        time.sleep(1)

async def init_database():
    try:
        wait_for_postgres()
        
        # Generate Prisma client
        subprocess.run([sys.executable, "-m", "prisma", "generate"], check=True)
        
        # Push schema to database
        subprocess.run([sys.executable, "-m", "prisma", "db", "push"], check=True)
        
        print("Database initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_database())