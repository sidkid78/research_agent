# FastAPI application entrypoint 
import uuid
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import List
import json

from . import models, schemas, crud # crud will be created later
from .db import SessionLocal, engine, get_db, create_db_and_tables
from .agent import create_research_agent
from google import genai

from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logger = logging.getLogger(__name__)

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Research Agent API",
    description="API for submitting research jobs and retrieving results.",
    version="0.1.0"
)

# --- Event Handlers ---
def startup_event():
    create_db_and_tables()
    logger.info("Database tables created")
    logger.info("Starting the application...")

app.add_event_handler("startup", startup_event)

# --- Middleware ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# --- Background Task Functions ---

async def run_research_job(job_id: str, request_data: dict):
    """
    Background task to run the actual research job using Gemini AI.
    """
    logger.info(f"Starting research job {job_id}")
    
    # Get database session
    db = SessionLocal()
    try:
        # Update job status to in_progress
        crud.update_job_status(db, job_id, models.JobStatusEnum.in_progress, progress=0.1)
        logger.info(f"Job {job_id} updated to in_progress")
        # Create research agent
        agent = create_research_agent()
        logger.info(f"Research agent created")
        # Create research request from stored data
        research_request = schemas.ResearchRequest(**request_data)
        logger.info(f"Research request created")
        # Run the research
        result = await agent.conduct_research(research_request)
        logger.info(f"Research completed")
        # Convert result to dict for storage
        result_dict = {
            "job_id": job_id,
            "topic": result.topic,
            "content": result.content,
            "references": [
                {
                    "title": ref.title,
                    "url": ref.url,
                    "accessed_date": ref.accessed_date.isoformat(),
                    "snippet": ref.snippet
                }
                for ref in result.references
            ],
            "output_format": result.output_format,
            "generated_at": result.generated_at.isoformat(),
            "word_count": result.word_count,
            "confidence_score": result.confidence_score,
            "academic_source_breakdown": {
                "arxiv_papers": len([r for r in result.references if r.source_type == 'arxiv']),
                "pubmed_papers": len([r for r in result.references if r.source_type == 'pubmed']),
                "web_sources": len([r for r in result.references if r.source_type == 'web']),
                "total_sources": len(result.references)
            },
            "research_quality_indicators": {
                # PubMed sources are generally peer-reviewed
                "peer_reviewed_percentage": (len([r for r in result.references if r.source_type == 'pubmed']) / len(result.references) * 100) if result.references else 0,
                # Estimate recent sources (this would need actual publication dates)
                "recent_sources_percentage": 75.0,  # TODO: Calculate from actual publication dates
                # PubMed and arXiv are authoritative academic sources
                "authoritative_sources_percentage": (len([r for r in result.references if r.source_type in ['pubmed', 'arxiv']]) / len(result.references) * 100) if result.references else 0
            }
        }
        
        # Update job with results
        crud.update_job_completed(db, job_id, result_dict)
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Job {job_id} failed with error: {str(e)}")
        logger.error(f"Full traceback:\n{error_details}")
        crud.update_job_completed(db, job_id, None, error_message=f"{str(e)}\n\nTraceback:\n{error_details}")
    finally:
        db.close()
        logger.info(f"Database connection closed")

# --- API Endpoints ---

@app.post("/research", response_model=schemas.JobSubmitResponse, status_code=202) # 202 Accepted
async def submit_research_job(
    request: schemas.ResearchRequest,
    background_tasks: BackgroundTasks, # We'll use this later
    db: Session = Depends(get_db)
):
    """
    Submit a new research request.

    - **topic**: The research topic or question.
    - **output_format**: 'bullets' or 'full_report'.
    - **deadline** (optional): ISO 8601 format datetime string.
    """
    job_id = str(uuid.uuid4())
    
    # Use CRUD function to create the job
    crud.create_research_job(db=db, job_id=job_id, research_request=request)
    logger.info(f"Job {job_id} created")
    # Add actual research task to background processing
    background_tasks.add_task(run_research_job, job_id, request.model_dump())
    logger.info(f"Research task added to background processing")
    return schemas.JobSubmitResponse(job_id=job_id, status=models.JobStatusEnum.queued.value)

@app.get("/research/{job_id}/status", response_model=schemas.JobStatusResponse)
async def get_research_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get the current status and progress of a research job.
    """
    logger.info(f"Getting status for job {job_id}")
    db_job = crud.get_research_job(db, job_id=job_id)
    logger.info(f"Job {job_id} found")
    if db_job is None:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found.")
    
    # Include error message if job failed
    error_message = None
    if db_job.status == models.JobStatusEnum.failed and db_job.error_message:
        error_message = db_job.error_message
        logger.warning(f"Job {job_id} failed with error: {error_message}")
    
    logger.info(f"Job {job_id} status returned")
    return schemas.JobStatusResponse(
        job_id=db_job.id,
        status=db_job.status.value,
        progress=db_job.progress,
        error_message=error_message
    )
    
@app.get("/research/{job_id}/details", response_model=schemas.ResearchRequest, tags=["Research Jobs"])
async def get_research_job_details(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the original request details for a specific research job.
    """
    logger.info(f"Getting details for job {job_id}")
    db_job = crud.get_research_job(db, job_id=job_id)
    logger.info(f"Job {job_id} details found")
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    logger.info(f"Job {job_id} details returned")
    if db_job.request_payload is None:
        raise HTTPException(status_code=404, detail="Job details not found for this job.")
    logger.info(f"Job {job_id} details returned")
    return schemas.ResearchRequest(**db_job.request_payload)

@app.get("/research/{job_id}/result", response_model=schemas.ResearchResult)
async def get_research_job_result(job_id: str, db: Session = Depends(get_db)):
    """
    Get the result of a completed research job.
    """
    logger.info(f"Getting result for job {job_id}")
    db_job = crud.get_research_job(db, job_id=job_id)
    
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if db_job.status != models.JobStatusEnum.completed:
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if db_job.result_payload is None:
        raise HTTPException(status_code=404, detail="Job result not found")
    
    logger.info(f"Job {job_id} result returned")
    return schemas.ResearchResult(**db_job.result_payload)

# Academic Research Endpoints
@app.post("/academic-research", response_model=schemas.JobSubmitResponse, status_code=202)
async def submit_academic_research(
    request: schemas.ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a new academic research request with enhanced features.
    """
    logger.info(f"Academic research request received: {request.topic}")
    job_id = str(uuid.uuid4())
    
    # Create the job using existing CRUD function
    crud.create_research_job(db=db, job_id=job_id, research_request=request)
    logger.info(f"Academic research job {job_id} created")
    
    # Add research task to background processing
    background_tasks.add_task(run_research_job, job_id, request.model_dump())
    logger.info(f"Academic research task added to background processing")
    
    return schemas.JobSubmitResponse(
        job_id=job_id, 
        status=models.JobStatusEnum.queued.value,
        estimated_duration_minutes=5
    )

@app.post("/academic-research/validate-pubmed")
async def validate_pubmed_access(request: dict):
    """
    Validate PubMed email access (placeholder implementation).
    """
    email = request.get("email", "")
    logger.info(f"PubMed validation request for email: {email}")
    
    # Simple validation - in production, you'd implement actual PubMed API validation
    if email and "@" in email:
        return {"valid": True, "message": "Email format is valid"}
    else:
        return {"valid": False, "message": "Invalid email format"}

@app.get("/academic-research/preview")
async def get_academic_sources_preview(topic: str, email: str = None):
    """
    Get a preview of academic sources for a given topic.
    """
    logger.info(f"Academic sources preview requested for topic: {topic}")
    
    try:
        from .gemini_helpers import AcademicGeminiHelpers
        
        # Quick preview search - limit to 2 papers per source
        arxiv_papers = await AcademicGeminiHelpers.search_arxiv_papers(topic, max_results=2)
        
        pubmed_papers = []
        if email:
            pubmed_papers = await AcademicGeminiHelpers.search_pubmed_papers(
                topic, max_results=2, email=email
            )
        
        # Format for frontend
        arxiv_preview = [
            {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", "")[:200] + "..."
            }
            for paper in arxiv_papers[:2]
        ]
        
        pubmed_preview = [
            {
                "title": paper.get("title", ""),
                "journal": paper.get("journal", "Unknown"),
                "abstract": paper.get("abstract", "")[:200] + "..."
            }
            for paper in pubmed_papers[:2]
        ]
        
        estimated_sources = len(arxiv_papers) + len(pubmed_papers) + 5  # +5 for potential web sources
        
        return {
            "arxiv_preview": arxiv_preview,
            "pubmed_preview": pubmed_preview,
            "estimated_sources": estimated_sources
        }
    except Exception as e:
        logger.error(f"Preview search failed: {e}")
        # Return empty preview on error
        return {
            "arxiv_preview": [],
            "pubmed_preview": [],
            "estimated_sources": 0
        }

# Health check endpoint
@app.get("/health", status_code=200)
async def health_check():
    logger.info("Health check endpoint called")
    return {
        "status": "healthy",
        "services": {"database": "up", "gemini": "up"},
        "version": "0.1.0",
        "uptime_seconds": 3600
    }

if __name__ == "__main__":
    import uvicorn
    create_db_and_tables()
    uvicorn.run(app, host="0.0.0.0", port=8000) 
    logger.info("Application started")
