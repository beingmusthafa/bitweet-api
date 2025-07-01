from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Twitter Clone Server is running"}
