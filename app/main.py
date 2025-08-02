from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from controllers.auth_controller import router as auth_router
from controllers.connections_controller import router as connections_router
from controllers.tweet_controller import router as tweet_router
from controllers.user_controller import router as user_router
from controllers.notification_controller import router as notification_router
from database.connection import connect_db, disconnect_db
from init_db import init_database
from services.websocket_manager import websocket_manager
from starlette.middleware.cors import CORSMiddleware
from utils.security_middleware import SecurityMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()
    await connect_db()
    await websocket_manager.init_redis()
    yield
    # Shutdown
    await disconnect_db()

app = FastAPI(lifespan=lifespan)

app.add_middleware(SecurityMiddleware)

# Configure CORS
client_url = os.getenv("CLIENT_URL")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[client_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(connections_router)
app.include_router(tweet_router)
app.include_router(user_router)
app.include_router(notification_router)

@app.get("/")
def root():
    return {"message": "Twitter Clone Server is running"}
