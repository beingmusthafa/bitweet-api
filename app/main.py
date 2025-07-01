from fastapi import FastAPI
from contextlib import asynccontextmanager
from controllers.auth_controller import router as auth_router
from database.connection import connect_db, disconnect_db
from init_db import init_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()
    await connect_db()
    yield
    # Shutdown
    await disconnect_db()

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Twitter Clone Server is running"}
