from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import database

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

class ExecuteRequest(BaseModel):
    sistemas: List[str]
    dry_run: bool = False
    limpar: bool = False
    data_inicial: str | None = None
    data_final: str | None = None
    opcoes: Dict[str, Dict[str, bool]] = {}

@router.post("/api/execute")
def execute_job(request: ExecuteRequest):
    """
    Queues an ETL job in the database.
    """
    try:
        # Check if any job is pending or running (optional restriction)
        # pending_job = database.get_pending_job()
        # if pending_job:
        #     return {"status": "error", "message": "A job is already pending"}
        
        job_id = database.add_job("etl_execution", request.dict())
        logger.info(f"Job queued: {job_id}")
        
        return {
            "status": "started", 
            "message": "ETL Job queued successfully",
            "job_id": job_id
        }
    except Exception as e:
        logger.error(f"Error queuing job: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/api/jobs/{job_id}")
def get_job_status(job_id: int):
    job = database.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
