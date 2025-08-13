import uvicorn
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from celery.result import AsyncResult
from .worker import process_media, celery_app
from .settings import settings
import base64

app = FastAPI(title="Defect Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(settings.DATA_DIR)
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    jobs = []
    for f in files:
        # Limit size (streaming validation would be better for truly huge files)
        contents = await f.read()
        mb = len(contents) / (1024 * 1024)
        if mb > settings.MAX_CONTENT_LENGTH_MB:
            raise HTTPException(status_code=413, detail=f"{f.filename} exceeds {settings.MAX_CONTENT_LENGTH_MB}MB")

        dest = UPLOADS_DIR / f.filename
        with open(dest, "wb") as out:
            out.write(contents)

        task = process_media.delay(str(dest))
        jobs.append({"job_id": task.id, "filename": f.filename})
        
        print(jobs)

    return {"jobs": jobs}

@app.get("/api/status/{job_id}")
def status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    resp = {"job_id": job_id, "state": result.state}
    if result.state == "PENDING":
        resp["progress"] = 0
    elif result.state == "STARTED":
        resp["progress"] = 10
    elif result.state == "SUCCESS":
        resp["progress"] = 100
        resp["result"] = result.result
    elif result.state == "FAILURE":
        resp["error"] = str(result.info)
    return JSONResponse(resp)

@app.get("/api/result/{job_id}")
def get_result(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    if not result.ready():
        return JSONResponse({"job_id": job_id, "ready": False, "state": result.state})
    if result.failed():
        return JSONResponse({"job_id": job_id, "ready": True, "error": str(result.info)}, status_code=500)
    return JSONResponse({"job_id": job_id, "ready": True, "result": result.result})
