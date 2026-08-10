import enum
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SQLEnum
from app.core.database import Base

class InvestigationStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    ANALYZING = "ANALYZING"
    REPRODUCING = "REPRODUCING"
    VERIFYING = "VERIFYING"
    FIXED = "FIXED"
    FAILED = "FAILED"

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    fingerprint = Column(String, index=True, nullable=False)
    service = Column(String, index=True, nullable=False)
    environment = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    ingested_at = Column(DateTime, nullable=False)
    status = Column(SQLEnum(InvestigationStatus), default=InvestigationStatus.RECEIVED, nullable=False)
    
    # GitHub Repository Association
    github_owner = Column(String, nullable=True)
    github_repo = Column(String, nullable=True)
    github_branch = Column(String, nullable=True)
    github_commit_sha = Column(String, nullable=True)
    github_repo_url = Column(String, nullable=True)
    
    # Request Information
    request_method = Column(String, nullable=False)
    request_path = Column(String, nullable=False)
    request_query = Column(JSON, nullable=True)
    request_headers = Column(JSON, nullable=True)
    request_body = Column(JSON, nullable=True)

    # Response Information
    response_status_code = Column(Integer, nullable=False)
    response_body = Column(JSON, nullable=True)

    # Error Information
    error_type = Column(String, nullable=False)
    error_message = Column(String, nullable=False)
    error_stack_trace = Column(String, nullable=False)

    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Traceback Analysis Evidence
    traceback_analysis = Column(JSON, nullable=True)
    
    # Competing Hypotheses Evidence
    hypotheses = Column(JSON, nullable=True)
    
    # Reproduction Result
    reproduction_result = Column(JSON, nullable=True)
    
    # Verification Results
    verification_results = Column(JSON, nullable=True)
    
    # Generated Patch Result
    patch_result = Column(JSON, nullable=True)
    
    # Generated Pull Request Result
    pr_result = Column(JSON, nullable=True)






