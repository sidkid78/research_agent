# Pydantic schemas for API request/response 
from datetime import datetime
from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=255, description="The research topic or question.")
    output_format: Literal["bullets", "full_report"] = Field(..., description="The desired output format.")
    deadline: Optional[datetime] = Field(None, description="Optional deadline for the research job (ISO 8601 format).")
    email: Optional[str] = Field(None, description="Email address for PubMed API access.")
    # user_id: Optional[str] = None # Optional, for history features / authentication.

# Reference schema for the agent (simpler version)
class Reference(BaseModel):
    title: str = Field(..., description="Title of the source.")
    url: str = Field(..., description="URL of the source.")
    accessed_date: datetime = Field(..., description="Date when the source was accessed.")
    snippet: Optional[str] = Field(None, description="Brief snippet or description from the source.")
    source_type: Optional[str] = Field(None, description="Type of source: arxiv, pubmed, or web")

# Legacy reference schema for API compatibility
class ResearchReference(BaseModel):
    title: str = Field(..., description="Title of the source.")
    url: Optional[str] = Field(None, description="URL of the source.")
    author: Optional[str] = Field(None, description="Author(s) of the source.")
    date: Optional[str] = Field(None, description="Publication date of the source.")
    publisher: Optional[str] = Field(None, description="Publisher of the source.")

class ResearchResult(BaseModel):
    topic: str = Field(..., description="The research topic.")
    content: str = Field(..., description="The main research content (formatted according to output_format).")
    references: List[Reference] = Field(default_factory=list, description="List of cited sources.")
    output_format: Literal["bullets", "full_report"] = Field(..., description="The format of the content.")
    generated_at: datetime = Field(..., description="Timestamp when the research was completed.")
    word_count: int = Field(..., description="Word count of the research content.")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score of the research quality.")

# Legacy result schema for API compatibility
class LegacyResearchResult(BaseModel):
    title: str = Field(..., description="Synthetically generated topic title for the research.")
    summary: Union[List[str], str] = Field(..., description="Key findings (list of strings for bullets, single string for full_report).")
    references: List[ResearchReference] = Field(default_factory=list, description="List of cited sources.")
    conclusion: str = Field(..., description="Synthesized, short conclusion of the research.")
    output_format: Literal["bullets", "full_report"] = Field(..., description="Echoes the requested output format.")
    job_id: str = Field(..., description="The ID of the research job.")
    status: str = Field(..., description="The final status of the job (e.g., 'completed').")


class JobSubmitResponse(BaseModel):
    job_id: str = Field(..., description="Unique ID for the submitted research job.")
    status: str = Field(..., description="Initial status of the job (e.g., 'queued').")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes.")

class JobStatusResponse(BaseModel):
    job_id: str = Field(..., description="Unique ID for the research job.")
    status: str = Field(..., description="Current status of the job (e.g., 'queued', 'in_progress', 'completed', 'failed').")
    progress: Optional[float] = Field(None, ge=0, le=1, description="Optional progress of the job (0.0 to 1.0).")
    error_message: Optional[str] = Field(None, description="Error message if job failed.")
    # Optional: add ETA, current step, etc. 