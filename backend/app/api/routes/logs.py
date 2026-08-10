import uuid
import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.api.routes.github_routes import get_resolved_token
from app.models.incident import Incident, InvestigationStatus
from app.schemas.ingestion_schemas import IngestionLogPayload
from app.services.ingestion.scrubber import scrub_headers
from app.services.ingestion.fingerprint import generate_fingerprint
from app.services.analysis.mapper import TracebackMapper
from app.services.analysis.llm_provider import get_llm_provider
from app.services.analysis.hypothesis_generator import HypothesisGenerator
from app.services.reproduction.manager import ReproductionManager
from app.services.verification.verifier import VerificationEngine
from app.services.patch.patch_generator import PatchGenerator
from app.services.github.pr_manager import PullRequestManager
from app.api.routes.github_routes import get_resolved_token
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("app.api.routes.logs")
router = APIRouter()

@router.post("/logs", response_model=None, status_code=status.HTTP_201_CREATED)
def ingest_log(payload: IngestionLogPayload, db: Session = Depends(get_db)):
    """
    Ingests an API failure log, filters sensitive headers, generates
    a fingerprint, and persists it to the database as an Incident.
    """
    logger.info(f"Ingesting failure log for service '{payload.service}' in '{payload.environment}'")
    
    # 1. Scrub sensitive headers
    scrubbed_headers = scrub_headers(payload.request.headers)
    
    # 2. Compute the stable fingerprint
    fingerprint = generate_fingerprint(
        method=payload.request.method,
        path=payload.request.path,
        error_type=payload.error.type,
        error_message=payload.error.message,
        stack_trace=payload.error.stack_trace
    )
    
    # 3. Create unique incident ID
    incident_id = f"inc_{uuid.uuid4().hex[:16]}"
    
    # 4. Construct DB Incident object
    db_incident = Incident(
        id=incident_id,
        fingerprint=fingerprint,
        service=payload.service,
        environment=payload.environment,
        timestamp=payload.timestamp,
        ingested_at=datetime.now(timezone.utc),
        status=InvestigationStatus.RECEIVED,
        request_method=payload.request.method,
        request_path=payload.request.path,
        request_query=payload.request.query,
        request_headers=scrubbed_headers,
        request_body=payload.request.body,
        response_status_code=payload.response.status_code,
        response_body=payload.response.body,
        error_type=payload.error.type,
        error_message=payload.error.message,
        error_stack_trace=payload.error.stack_trace,
        metadata_json={
            "request_id": payload.metadata.request_id,
            "deployment_id": payload.metadata.deployment_id,
            "git_commit": payload.metadata.git_commit,
        }
    )
    
    try:
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        logger.info(f"Successfully created Incident {incident_id} (Fingerprint: {fingerprint})")
        return {
            "incident_id": db_incident.id,
            "fingerprint": db_incident.fingerprint,
            "status": db_incident.status,
            "service": db_incident.service,
            "environment": db_incident.environment,
            "timestamp": db_incident.timestamp,
            "ingested_at": db_incident.ingested_at
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist incident in database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save incident to database"
        )

@router.get("/incidents", response_model=None)
def list_incidents(db: Session = Depends(get_db)):
    """
    Retrieves all ingested incidents.
    """
    logger.info("Listing all incidents")
    incidents = db.query(Incident).order_by(Incident.ingested_at.desc()).all()
    return incidents

@router.get("/incidents/{incident_id}", response_model=None)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a single incident by its ID.
    """
    logger.info(f"Retrieving incident details for {incident_id}")
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found"
        )
    return incident

class AnalyzeRequest(BaseModel):
    workspace_id: str

@router.post("/incidents/{incident_id}/analyze", response_model=None)
def analyze_incident(
    incident_id: str,
    payload: AnalyzeRequest,
    token: str = Depends(get_resolved_token),
    db: Session = Depends(get_db)
):
    """
    Analyzes the stack trace of an incident against the source files
    present in the cloned repository workspace. Saves evidence to the database.
    """
    logger.info(f"Endpoint request to analyze traceback for incident {incident_id}")
    mapper = TracebackMapper()
    try:
        evidence = mapper.analyze_incident_traceback(db, incident_id, payload.workspace_id, token=token)
        return evidence
    except ValueError as e:
        logger.warning(f"Failed to analyze incident traceback: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during traceback analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal analysis failure: {e}"
        )

class HypothesesRequest(BaseModel):
    workspace_id: str
    provider: Optional[str] = None

@router.post("/incidents/{incident_id}/hypotheses", response_model=None)
async def generate_incident_hypotheses(
    incident_id: str,
    payload: HypothesesRequest,
    db: Session = Depends(get_db)
):
    """
    Generates competing root-cause hypotheses for an incident based on parsed
    evidence, context files, and call graphs. Stores results in the database.
    """
    logger.info(f"Endpoint request to generate hypotheses for incident {incident_id}")
    
    settings = get_settings()
    provider_name = payload.provider or settings.LLM_PROVIDER
    
    if not settings.LLM_API_KEY and provider_name != "mock":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API key is not configured in settings."
        )
        
    try:
        provider = get_llm_provider(provider_name, settings.LLM_API_KEY)
        generator = HypothesisGenerator()
        
        hypotheses = await generator.generate_hypotheses(
            db=db,
            incident_id=incident_id,
            workspace_id=payload.workspace_id,
            provider=provider
        )
        return hypotheses
    except ValueError as e:
        logger.warning(f"Failed to generate hypotheses: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected failure during hypothesis generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hypothesis generation error: {e}"
        )

class ReproduceRequest(BaseModel):
    workspace_id: str
    provider: Optional[str] = None

@router.post("/incidents/{incident_id}/reproduce", response_model=None)
async def reproduce_incident_endpoint(
    incident_id: str,
    payload: ReproduceRequest,
    token: str = Depends(get_resolved_token),
    db: Session = Depends(get_db)
):
    """
    Kicks off failure reproduction inside an isolated sandbox by compiling logs
    into a targeted reproducer script and asserting the observed exception.
    """
    logger.info(f"Endpoint request to reproduce incident {incident_id}")
    
    settings = get_settings()
    provider_name = payload.provider or settings.LLM_PROVIDER
    
    if not settings.LLM_API_KEY and provider_name != "mock":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API key is not configured in settings."
        )
        
    try:
        provider = get_llm_provider(provider_name, settings.LLM_API_KEY)
        manager = ReproductionManager()
        
        result = await manager.reproduce_incident(
            db=db,
            incident_id=incident_id,
            workspace_id=payload.workspace_id,
            provider=provider,
            token=token
        )
        return result
    except ValueError as e:
        logger.warning(f"Reproduction request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected failure during reproduction flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reproduction processing error: {e}"
        )

class VerifyRequest(BaseModel):
    hypothesis_id: str
    patch_content: str

@router.post("/incidents/{incident_id}/verify", response_model=None)
async def verify_patch_endpoint(
    incident_id: str,
    payload: VerifyRequest,
    token: str = Depends(get_resolved_token),
    db: Session = Depends(get_db)
):
    """
    Tests a candidate patch for a hypothesis experimentally inside a clean sandbox,
    checking if the target exception was resolved without symptom suppression.
    """
    logger.info(f"Endpoint request to verify patch for incident {incident_id}, hypothesis {payload.hypothesis_id}")
    
    try:
        verifier = VerificationEngine()
        result = await verifier.verify_hypothesis_patch(
            db=db,
            incident_id=incident_id,
            hypothesis_id=payload.hypothesis_id,
            patch_content=payload.patch_content,
            token=token
        )
        return result
    except ValueError as e:
        logger.warning(f"Verification request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected failure during verification flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification execution error: {e}"
        )

class PatchRequest(BaseModel):
    hypothesis_id: str
    provider: Optional[str] = None

@router.post("/incidents/{incident_id}/patch", response_model=None)
async def generate_patch_endpoint(
    incident_id: str,
    payload: PatchRequest,
    token: str = Depends(get_resolved_token),
    db: Session = Depends(get_db)
):
    """
    Generates the smallest safe production patch for a validated root-cause hypothesis,
    validates safety filters, and executes verification runs inside an isolated sandbox.
    """
    logger.info(f"Endpoint request to generate patch for incident {incident_id}, hypothesis {payload.hypothesis_id}")
    
    settings = get_settings()
    provider_name = payload.provider or settings.LLM_PROVIDER
    
    if not settings.LLM_API_KEY and provider_name != "mock":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API key is not configured in settings."
        )
        
    try:
        provider = get_llm_provider(provider_name, settings.LLM_API_KEY)
        generator = PatchGenerator()
        
        result = await generator.generate_and_verify_patch(
            db=db,
            incident_id=incident_id,
            hypothesis_id=payload.hypothesis_id,
            token=token,
            provider=provider
        )
        return result
    except ValueError as e:
        logger.warning(f"Patch generation request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected failure during patch generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patch generation execution error: {e}"
        )

class PullRequestRequest(BaseModel):
    connection_id: Optional[str] = None

@router.post("/incidents/{incident_id}/pull-request", response_model=None)
async def create_pull_request_endpoint(
    incident_id: str,
    payload: PullRequestRequest,
    token: str = Depends(get_resolved_token),
    db: Session = Depends(get_db)
):
    """
    Creates a pull request on GitHub for a verified fix, documenting findings,
    evidence, and experimental results. Marks the incident as FIXED.
    """
    logger.info(f"Endpoint request to create pull request for incident {incident_id}")
    
    try:
        manager = PullRequestManager()
        result = await manager.create_pull_request(
            db=db,
            incident_id=incident_id,
            token=token
        )
        return result
    except ValueError as e:
        logger.warning(f"Pull request creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected failure during pull request pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pull request execution error: {e}"
        )
