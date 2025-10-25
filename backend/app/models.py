# Pydantic models for data validation and ORM models 

import enum
from sqlalchemy import Column, String, DateTime, Enum as SQLAlchemyEnum, Text, Float, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class JobStatusEnum(str, enum.Enum):
    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(String, primary_key=True, index=True)  # Unique job ID (UUID string)
    topic = Column(String, index=True, nullable=False)  # The research topic
    output_format = Column(String, nullable=False)  # Requested output format ('bullets' or 'full_report')
    
    status = Column(SQLAlchemyEnum(JobStatusEnum), default=JobStatusEnum.queued, nullable=False, index=True)  # Current status of the job
    progress = Column(Float, nullable=True)  # Optional progress of the job (0.0 to 1.0)

    request_payload = Column(JSON, nullable=False)  # The full JSON request payload used to create the job
    result_payload = Column(JSON, nullable=True)  # The JSON payload of the research result when completed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Timestamp when the job was created
    started_at = Column(DateTime, nullable=True)  # Timestamp when the job processing started
    completed_at = Column(DateTime, nullable=True)  # Timestamp when the job processing completed or failed
    deadline = Column(DateTime, nullable=True)  # Optional deadline for the research job

    error_message = Column(Text, nullable=True)  # Error message if the job failed

    # user_id: Optional[str] = None # For future user association

    def __repr__(self):
        return f"<ResearchJob(id='{self.id}', topic='{self.topic}', status='{self.status}')>" 