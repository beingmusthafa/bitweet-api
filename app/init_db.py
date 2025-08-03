import asyncio
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
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(init_database())