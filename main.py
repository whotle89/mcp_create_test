"""
Agent Orchestrator - Main Coordination System

This module orchestrates the collaboration between ui-implementer and
feature-logic-implementer agents, ensuring proper sequencing and preventing conflicts.

Usage:
    from main import AgentOrchestrator

    orchestrator = AgentOrchestrator()
    result = orchestrator.process_request("시간 거래 기능 만들어줘")
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from agent_router import (
    AgentRouter,
    RoutingMetrics,
    AgentRouterError,
    MissingPrerequisitesError,
    IncompleteDeliveryError,
    ForbiddenOperationError,
)


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ExecutionResult:
    """Result of agent execution"""

    def __init__(
        self,
        agent: str,
        status: AgentStatus,
        message: str,
        files_created: Optional[List[str]] = None,
        files_modified: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        self.agent = agent
        self.status = status
        self.message = message
        self.files_created = files_created or []
        self.files_modified = files_modified or []
        self.error = error
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "agent": self.agent,
            "status": self.status.value,
            "message": self.message,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class AgentOrchestrator:
    """
    Orchestrates multi-agent workflow for feature development

    Responsibilities:
    1. Route requests to appropriate agents
    2. Verify prerequisites before execution
    3. Validate completeness after execution
    4. Prevent conflicts between agents
    5. Track metrics and logging
    """

    def __init__(
        self,
        base_path: str = ".",
        log_level: int = logging.INFO,
    ):
        self.base_path = Path(base_path)
        self.router = AgentRouter(base_path)
        self.metrics = RoutingMetrics()

        # Setup logging
        self.logger = self._setup_logging(log_level)

        # Execution history
        self.history: List[ExecutionResult] = []

        # Current state
        self.current_agent: Optional[str] = None
        self.current_feature_path: Optional[Path] = None

    def _setup_logging(self, log_level: int) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("AgentOrchestrator")
        logger.setLevel(log_level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        # File handler
        log_file = self.base_path / "agent_orchestrator.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def process_request(
        self,
        user_message: str,
        context: Optional[Dict] = None,
    ) -> ExecutionResult:
        """
        Process user request and route to appropriate agent

        Args:
            user_message: User's request message
            context: Additional context (current_path, etc.)

        Returns:
            ExecutionResult with outcome
        """
        self.logger.info(f"Processing request: {user_message}")

        try:
            # Step 1: Route the request
            agent = self.router.route_request(user_message, context)
            self.logger.info(f"Routing decision: {agent}")

            # Step 2: Handle routing result
            if agent.startswith("error:"):
                return self._handle_routing_error(agent, user_message, context)

            # Step 3: Extract feature path
            feature_path = self.router.extract_feature_path(user_message, context or {})
            self.current_feature_path = feature_path
            self.logger.info(f"Feature path: {feature_path}")

            # Step 4: Verify prerequisites
            can_run, error_msg = self.router.verify_prerequisites(agent, feature_path)
            if not can_run:
                self.logger.warning(f"Prerequisites check failed: {error_msg}")
                self.metrics.record_block("missing_prerequisites")

                return ExecutionResult(
                    agent=agent,
                    status=AgentStatus.BLOCKED,
                    message=error_msg,
                    error="MissingPrerequisitesError",
                )

            # Step 5: Record routing decision
            self.metrics.record_route(agent)

            # Step 6: Return execution plan
            return self._create_execution_plan(agent, user_message, feature_path)

        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            return ExecutionResult(
                agent="error",
                status=AgentStatus.FAILED,
                message=str(e),
                error=type(e).__name__,
            )

    def _handle_routing_error(
        self,
        error_code: str,
        user_message: str,
        context: Optional[Dict],
    ) -> ExecutionResult:
        """
        Handle routing errors

        Args:
            error_code: Error code from router
            user_message: User's request
            context: Request context

        Returns:
            ExecutionResult with error details
        """
        if error_code == "error:missing_ui_foundation":
            feature_path = self.router.extract_feature_path(user_message, context or {})

            error_msg = (
                f"❌ Cannot proceed with backend implementation\n\n"
                f"UI foundation not found at: {feature_path}\n\n"
                f"Required files:\n"
                f"- types.ts (TypeScript interfaces)\n"
                f"- api.ts (integration layer)\n"
                f"- components/ (UI components)\n\n"
                f"Next steps:\n"
                f"1. First, run ui-implementer to create the UI structure\n"
                f"2. Then, run feature-logic-implementer to add backend logic\n\n"
                f"Example: 'Create UI for time slots feature first'"
            )

            self.metrics.record_block("missing_prerequisites")

            return ExecutionResult(
                agent="feature-logic-implementer",
                status=AgentStatus.BLOCKED,
                message=error_msg,
                error="MissingUIFoundation",
            )

        return ExecutionResult(
            agent="error",
            status=AgentStatus.FAILED,
            message=f"Unknown routing error: {error_code}",
            error="UnknownRoutingError",
        )

    def _create_execution_plan(
        self,
        agent: str,
        user_message: str,
        feature_path: Path,
    ) -> ExecutionResult:
        """
        Create execution plan for agent

        Args:
            agent: Agent to execute
            user_message: User's request
            feature_path: Feature directory path

        Returns:
            ExecutionResult with execution plan
        """
        if agent == "ui-implementer":
            message = (
                f"✅ Routing to ui-implementer\n\n"
                f"Task: Create UI foundation for feature\n"
                f"Location: {feature_path}\n\n"
                f"Required deliverables:\n"
                f"1. types.ts - TypeScript interfaces\n"
                f"2. api.ts - Integration layer with TODO markers\n"
                f"3. components/ - UI components\n\n"
                f"After completion, feature-logic-implementer can implement backend logic."
            )

            return ExecutionResult(
                agent=agent,
                status=AgentStatus.RUNNING,
                message=message,
            )

        elif agent == "feature-logic-implementer":
            files_exist = self.router.check_existing_files(feature_path)

            message = (
                f"✅ Routing to feature-logic-implementer\n\n"
                f"Task: Implement backend logic\n"
                f"Location: {feature_path}\n\n"
                f"Found UI foundation:\n"
                f"- types.ts: {'✓' if files_exist['types_exists'] else '✗'}\n"
                f"- api.ts: {'✓' if files_exist['api_exists'] else '✗'}\n"
                f"- components/: {'✓' if files_exist['components_exist'] else '✗'}\n\n"
                f"Tasks:\n"
                f"1. Read api.ts to understand function signatures\n"
                f"2. Implement TODOs in api.ts\n"
                f"3. Create domain/ and services/ layers\n"
                f"4. Setup Supabase integration\n\n"
                f"Restrictions:\n"
                f"- DO NOT modify UI components\n"
                f"- DO NOT change function signatures in api.ts\n"
                f"- DO NOT create new types.ts or api.ts files"
            )

            return ExecutionResult(
                agent=agent,
                status=AgentStatus.RUNNING,
                message=message,
            )

        return ExecutionResult(
            agent=agent,
            status=AgentStatus.FAILED,
            message=f"Unknown agent: {agent}",
            error="UnknownAgent",
        )

    def verify_agent_completion(
        self,
        agent: str,
        feature_path: Path,
    ) -> ExecutionResult:
        """
        Verify agent completed all required tasks

        Args:
            agent: Agent that completed work
            feature_path: Feature directory path

        Returns:
            ExecutionResult with verification result
        """
        self.logger.info(f"Verifying completion for {agent} at {feature_path}")

        try:
            is_complete, error_msg = self.router.verify_completion(agent, feature_path)

            if not is_complete:
                self.logger.warning(f"Completion check failed: {error_msg}")
                self.metrics.record_block("incomplete_ui")

                return ExecutionResult(
                    agent=agent,
                    status=AgentStatus.BLOCKED,
                    message=error_msg,
                    error="IncompleteDeliveryError",
                )

            # Success
            self.metrics.record_success()

            message = (
                f"✅ {agent} completed successfully\n\n"
                f"All required files created at: {feature_path}\n\n"
            )

            if agent == "ui-implementer":
                message += (
                    f"Next step:\n"
                    f"Run feature-logic-implementer to implement backend logic."
                )

            return ExecutionResult(
                agent=agent,
                status=AgentStatus.COMPLETED,
                message=message,
            )

        except Exception as e:
            self.logger.error(f"Error verifying completion: {e}", exc_info=True)
            return ExecutionResult(
                agent=agent,
                status=AgentStatus.FAILED,
                message=str(e),
                error=type(e).__name__,
            )

    def check_file_operation(
        self,
        agent: str,
        operation: str,
        file_path: Path,
    ) -> Optional[str]:
        """
        Check if file operation is allowed

        Args:
            agent: Agent performing operation
            operation: "create" or "modify"
            file_path: Path to file

        Returns:
            Error message if forbidden, None if allowed
        """
        try:
            if operation == "create":
                self.router.before_create_file(agent, file_path)
            elif operation == "modify":
                self.router.before_modify_file(agent, file_path)

            return None

        except ForbiddenOperationError as e:
            self.logger.warning(f"Forbidden operation: {e}")
            self.metrics.record_block("file_conflicts")
            return str(e)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics

        Returns:
            Dictionary with metrics and statistics
        """
        metrics = self.metrics.get_metrics()

        return {
            "metrics": metrics,
            "success_rate": self.metrics.get_success_rate(),
            "total_executions": len(self.history),
            "history": [r.to_dict() for r in self.history[-10:]],  # Last 10
        }

    def export_history(self, output_file: Optional[Path] = None) -> str:
        """
        Export execution history to JSON

        Args:
            output_file: Optional output file path

        Returns:
            JSON string of history
        """
        history_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.get_metrics(),
            "history": [r.to_dict() for r in self.history],
        }

        json_str = json.dumps(history_data, indent=2)

        if output_file:
            output_file.write_text(json_str)
            self.logger.info(f"History exported to {output_file}")

        return json_str


def main():
    """
    CLI entry point for testing
    """
    import sys

    orchestrator = AgentOrchestrator()

    if len(sys.argv) < 2:
        print("Usage: python main.py '<user message>' [feature_path]")
        print("\nExamples:")
        print('  python main.py "시간 거래 기능 만들어줘"')
        print('  python main.py "Supabase 연결해줘" app/time-slots')
        sys.exit(1)

    user_message = sys.argv[1]
    context = {}

    if len(sys.argv) >= 3:
        context["current_path"] = sys.argv[2]

    # Process request
    result = orchestrator.process_request(user_message, context)

    # Print result
    print("\n" + "=" * 60)
    print(result.message)
    print("=" * 60)
    print(f"\nAgent: {result.agent}")
    print(f"Status: {result.status.value}")

    if result.error:
        print(f"Error: {result.error}")

    # Print metrics
    print("\n" + "-" * 60)
    print("Metrics:")
    metrics = orchestrator.get_metrics()
    print(f"  Total Requests: {metrics['metrics']['total_requests']}")
    print(f"  Success Rate: {metrics['success_rate']:.2%}")
    print(f"  Blocked (Prerequisites): {metrics['metrics']['blocked_missing_prerequisites']}")
    print(f"  Blocked (Incomplete UI): {metrics['metrics']['blocked_incomplete_ui']}")
    print(f"  Blocked (File Conflicts): {metrics['metrics']['blocked_file_conflicts']}")
    print("-" * 60)


if __name__ == "__main__":
    main()
