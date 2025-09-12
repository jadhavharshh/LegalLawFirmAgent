from fastapi import FastAPI

app = FastAPI(title="Law Agent API")

@app.get("/health")
def health():
    return {"status": "ok"}
