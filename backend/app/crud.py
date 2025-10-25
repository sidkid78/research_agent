# CRUD (Create, Read, Update, Delete) operations for the database 

from sqlalchemy.orm import Session
from datetime import datetime
import uuid # For job ID generation if not passed
import logging

logger = logging.getLogger(__name__)

from . import models, schemas

def get_research_job(db: Session, job_id: str) -> models.ResearchJob | None:
    """Retrieve a research job by its ID."""
    logger.info(f"Getting research job {job_id}") 
    db_job = db.query(models.ResearchJob).filter(models.ResearchJob.id == job_id).first()
    logger.info(f"Research job {job_id} found") 
    return db_job

def create_research_job(db: Session, job_id: str, research_request: schemas.ResearchRequest) -> models.ResearchJob:
    """
    Create a new research job in the database.
    The job_id should be pre-generated.
    """
    logger.info(f"Creating research job {job_id}") 
    db_job = models.ResearchJob(
        id=job_id,
        topic=research_request.topic,
        output_format=research_request.output_format,
        request_payload=research_request.model_dump(mode='json'), # Pydantic v2
        deadline=research_request.deadline,
        status=models.JobStatusEnum.queued,
        created_at=datetime.utcnow()
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    logger.info(f"Research job {job_id} created") 
    return db_job

def update_job_status(
    db: Session, 
    job_id: str, 
    status: models.JobStatusEnum, 
    progress: float | None = None
) -> models.ResearchJob | None:
    """Update the status and optionally the progress of a research job."""
    logger.info(f"Updating job status {status} for job {job_id}") 
    db_job = get_research_job(db, job_id)
    if db_job:
        logger.info(f"Job {job_id} found and updated to {status}") 
        db_job.status = status
        if progress is not None:
            db_job.progress = progress
        if status == models.JobStatusEnum.in_progress and db_job.started_at is None:
            db_job.started_at = datetime.utcnow()
            logger.info(f"Job {job_id} started at {db_job.started_at}") 
        # If moving to a terminal state (completed/failed), set completed_at
        if status in [models.JobStatusEnum.completed, models.JobStatusEnum.failed] and db_job.completed_at is None:
            db_job.completed_at = datetime.utcnow()
            logger.info(f"Job {job_id} completed at {db_job.completed_at}") 
            if status == models.JobStatusEnum.completed : # Ensure progress is 100% if completed
                 db_job.progress = 1.0
                 logger.info(f"Job {job_id} progress set to 100%") 

        db.commit()
        db.refresh(db_job)
        logger.info(f"Job {job_id} refreshed") 
    return db_job

def update_job_completed(
    db: Session, 
    job_id: str, 
    result_payload: dict | None, # Can be None if job failed without partial results
    error_message: str | None = None
) -> models.ResearchJob | None:
    """
    Mark a research job as completed or failed, storing the result payload or error.
    """
    logger.info(f"Updating job completed for job {job_id}") 
    db_job = get_research_job(db, job_id)
    if db_job:
        if error_message:
            db_job.status = models.JobStatusEnum.failed
            db_job.error_message = error_message
            db_job.progress = db_job.progress if db_job.progress is not None else 0.0 # Keep progress or set to 0 if None
            logger.info(f"Job {job_id} failed with error message {error_message}") 
        else:
            db_job.status = models.JobStatusEnum.completed
            db_job.result_payload = result_payload
            db_job.progress = 1.0 # Mark as 100% complete
            db_job.error_message = None # Clear any previous error if it's now completed successfully

        db_job.completed_at = datetime.utcnow()
        logger.info(f"Job {job_id} completed at {db_job.completed_at}") 
        db.commit()
        db.refresh(db_job)
        logger.info(f"Job {job_id} refreshed") 
    return db_job

# Optional: A function to list jobs (e.g., for an admin panel or user history)
# def get_research_jobs(db: Session, skip: int = 0, limit: int = 100) -> list[models.ResearchJob]:
#     return db.query(models.ResearchJob).offset(skip).limit(limit).all()

# Optional: A function to update a job with partial results during in_progress state
# def update_job_partial_result(db: Session, job_id: str, partial_result: dict, progress: float) -> models.ResearchJob | None:
#     db_job = get_research_job(db, job_id)
#     if db_job and db_job.status == models.JobStatusEnum.in_progress:
#         # This assumes you have a way to store/merge partial results.
#         # For simplicity, we might just update the result_payload directly if it's designed to hold intermediates.
#         # Or add a new field for it.
#         # db_job.partial_result_payload = partial_result 
#         db_job.progress = progress
#         db.commit()
#         db.refresh(db_job)
#     return db_job 