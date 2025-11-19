"""
API Interface for Agent Orchestration System

Provides REST API endpoints for agent routing and execution.

Installation:
    pip install fastapi uvicorn pydantic

Usage:
    uvicorn api_interface:app --reload --port 8000

API Documentation:
    http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from pathlib import Path
import logging

from main import AgentOrchestrator, ExecutionResult, AgentStatus


# Pydantic models for request/response
class ProcessRequest(BaseModel):
    """Request to process user message"""
    message: str = Field(..., description="User's request message")
    context: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional context (e.g., current_path)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "시간 거래 기능 만들어줘",
                "context": {"current_path": "app/time-slots"}
            }
        }


class VerifyCompletionRequest(BaseModel):
    """Request to verify agent completion"""
    agent: str = Field(..., description="Agent name (ui-implementer or feature-logic-implementer)")
    feature_path: str = Field(..., description="Path to feature directory")

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "ui-implementer",
                "feature_path": "app/time-slots"
            }
        }


class CheckFileOperationRequest(BaseModel):
    """Request to check if file operation is allowed"""
    agent: str = Field(..., description="Agent name")
    operation: str = Field(..., description="Operation type: 'create' or 'modify'")
    file_path: str = Field(..., description="Path to file")

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "feature-logic-implementer",
                "operation": "create",
                "file_path": "app/time-slots/api.ts"
            }
        }


class ExecutionResponse(BaseModel):
    """Response with execution result"""
    agent: str
    status: str
    message: str
    files_created: List[str] = []
    files_modified: List[str] = []
    error: Optional[str] = None
    timestamp: str


class MetricsResponse(BaseModel):
    """Response with system metrics"""
    metrics: Dict[str, int]
    success_rate: float
    total_executions: int
    history: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    orchestrator_ready: bool


class FileOperationResponse(BaseModel):
    """Response for file operation check"""
    allowed: bool
    error: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title="Agent Orchestration API",
    description="API for routing and managing UI and Logic implementation agents",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator: Optional[AgentOrchestrator] = None


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup"""
    global orchestrator
    orchestrator = AgentOrchestrator(
        base_path=".",
        log_level=logging.INFO,
    )
    logging.info("Agent Orchestrator initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global orchestrator
    if orchestrator:
        # Export history before shutdown
        history_file = Path("agent_history.json")
        orchestrator.export_history(history_file)
        logging.info(f"History exported to {history_file}")


@app.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns:
        System health status
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        orchestrator_ready=orchestrator is not None,
    )


@app.post("/process", response_model=ExecutionResponse)
async def process_request(request: ProcessRequest):
    """
    Process user request and route to appropriate agent

    Args:
        request: ProcessRequest with user message and context

    Returns:
        ExecutionResponse with routing decision and execution plan

    Raises:
        HTTPException: If processing fails
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        result = orchestrator.process_request(
            request.message,
            request.context,
        )

        return ExecutionResponse(
            agent=result.agent,
            status=result.status.value,
            message=result.message,
            files_created=result.files_created,
            files_modified=result.files_modified,
            error=result.error,
            timestamp=result.timestamp,
        )

    except Exception as e:
        logging.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/verify-completion", response_model=ExecutionResponse)
async def verify_completion(request: VerifyCompletionRequest):
    """
    Verify that agent completed all required tasks

    Args:
        request: VerifyCompletionRequest with agent and feature path

    Returns:
        ExecutionResponse with verification result

    Raises:
        HTTPException: If verification fails
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        feature_path = Path(request.feature_path)

        result = orchestrator.verify_agent_completion(
            request.agent,
            feature_path,
        )

        return ExecutionResponse(
            agent=result.agent,
            status=result.status.value,
            message=result.message,
            files_created=result.files_created,
            files_modified=result.files_modified,
            error=result.error,
            timestamp=result.timestamp,
        )

    except Exception as e:
        logging.error(f"Error verifying completion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/check-file-operation", response_model=FileOperationResponse)
async def check_file_operation(request: CheckFileOperationRequest):
    """
    Check if file operation is allowed for agent

    Args:
        request: CheckFileOperationRequest with agent, operation, and file path

    Returns:
        FileOperationResponse indicating if operation is allowed

    Raises:
        HTTPException: If check fails
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        file_path = Path(request.file_path)

        error = orchestrator.check_file_operation(
            request.agent,
            request.operation,
            file_path,
        )

        return FileOperationResponse(
            allowed=error is None,
            error=error,
        )

    except Exception as e:
        logging.error(f"Error checking file operation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get system metrics

    Returns:
        MetricsResponse with current metrics and statistics

    Raises:
        HTTPException: If retrieval fails
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        metrics_data = orchestrator.get_metrics()

        return MetricsResponse(
            metrics=metrics_data["metrics"],
            success_rate=metrics_data["success_rate"],
            total_executions=metrics_data["total_executions"],
            history=metrics_data["history"],
        )

    except Exception as e:
        logging.error(f"Error getting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/history")
async def get_history():
    """
    Get execution history

    Returns:
        JSON string of execution history

    Raises:
        HTTPException: If retrieval fails
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        history = orchestrator.export_history()
        return {"history": history}

    except Exception as e:
        logging.error(f"Error getting history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Example usage and testing endpoints
@app.post("/examples/ui-request", response_model=ExecutionResponse)
async def example_ui_request():
    """
    Example: Request UI creation

    Returns:
        Execution result for UI creation request
    """
    return await process_request(ProcessRequest(
        message="시간 거래 목록 페이지 만들어줘",
        context=None,
    ))


@app.post("/examples/backend-request", response_model=ExecutionResponse)
async def example_backend_request():
    """
    Example: Request backend implementation

    Returns:
        Execution result for backend implementation request
    """
    return await process_request(ProcessRequest(
        message="Supabase 연결해서 실제로 작동하게 해줘",
        context={"current_path": "app/time-slots"},
    ))


@app.post("/examples/full-feature", response_model=ExecutionResponse)
async def example_full_feature():
    """
    Example: Request full feature implementation

    Returns:
        Execution result for full feature request
    """
    return await process_request(ProcessRequest(
        message="회원가입 기능 만들어줘",
        context=None,
    ))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_interface:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
