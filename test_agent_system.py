"""
Test Suite for Agent Orchestration System

Tests routing logic, prerequisite checks, completion verification,
and conflict prevention.

Installation:
    pip install pytest pytest-cov

Usage:
    pytest test_agent_system.py -v
    pytest test_agent_system.py -v --cov=. --cov-report=html
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from agent_router import (
    AgentRouter,
    RoutingMetrics,
    ForbiddenOperationError,
)
from main import AgentOrchestrator, AgentStatus


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def router(temp_dir):
    """Create AgentRouter instance"""
    return AgentRouter(base_path=str(temp_dir))


@pytest.fixture
def orchestrator(temp_dir):
    """Create AgentOrchestrator instance"""
    return AgentOrchestrator(base_path=str(temp_dir))


class TestRequestClassification:
    """Test request classification logic"""

    def test_full_feature_request(self, router):
        """Test classification of full feature request"""
        result = router.classify_request("시간 거래 기능 만들어줘")
        assert result == "full_feature"

    def test_ui_only_request(self, router):
        """Test classification of UI-only request"""
        result = router.classify_request("로그인 폼 UI만 만들어줘")
        assert result == "ui_only"

    def test_backend_only_request(self, router):
        """Test classification of backend-only request"""
        result = router.classify_request("Supabase 쿼리 구현해줘")
        assert result == "backend_only"

    def test_modify_existing_request(self, router):
        """Test classification of modification request"""
        result = router.classify_request("시간 거래 수정 기능 추가해줘")
        assert result == "modify_existing"


class TestRouting:
    """Test routing decision logic"""

    def test_first_feature_request_routes_to_ui(self, router, temp_dir):
        """Test that first feature request routes to UI agent"""
        result = router.route_request(
            "회원가입 기능 만들어줘",
            {"current_path": str(temp_dir / "app" / "auth")}
        )
        assert result == "ui-implementer"

    def test_backend_request_without_ui_blocked(self, router, temp_dir):
        """Test that backend request without UI is blocked"""
        result = router.route_request(
            "Supabase 인증 로직 구현해줘",
            {"current_path": str(temp_dir / "app" / "auth")}
        )
        assert result == "error:missing_ui_foundation"

    def test_backend_request_with_ui_routes_to_backend(self, router, temp_dir):
        """Test that backend request with UI routes to backend agent"""
        # Create UI foundation
        feature_path = temp_dir / "app" / "auth"
        feature_path.mkdir(parents=True)
        (feature_path / "types.ts").write_text("export interface User {}")
        (feature_path / "api.ts").write_text("export async function login() {}")
        (feature_path / "components").mkdir()

        result = router.route_request(
            "Supabase 연결해줘",
            {"current_path": str(feature_path)}
        )
        assert result == "feature-logic-implementer"


class TestPrerequisiteChecks:
    """Test prerequisite verification"""

    def test_ui_agent_no_prerequisites(self, router, temp_dir):
        """Test that UI agent has no prerequisites"""
        feature_path = temp_dir / "app" / "new-feature"
        can_run, error = router.verify_prerequisites("ui-implementer", feature_path)

        assert can_run is True
        assert error == ""

    def test_backend_agent_requires_ui_foundation(self, router, temp_dir):
        """Test that backend agent requires UI foundation"""
        feature_path = temp_dir / "app" / "new-feature"
        can_run, error = router.verify_prerequisites("feature-logic-implementer", feature_path)

        assert can_run is False
        assert "Cannot run feature-logic-implementer" in error
        assert "types.ts" in error

    def test_backend_agent_with_ui_foundation(self, router, temp_dir):
        """Test that backend agent can run with UI foundation"""
        # Create UI foundation
        feature_path = temp_dir / "app" / "feature"
        feature_path.mkdir(parents=True)
        (feature_path / "types.ts").write_text("export interface Data {}")
        (feature_path / "api.ts").write_text("🔌 INTEGRATION POINT\nexport async function getData() {}")
        (feature_path / "components").mkdir()

        can_run, error = router.verify_prerequisites("feature-logic-implementer", feature_path)

        assert can_run is True
        assert error == ""


class TestCompletionVerification:
    """Test completion verification"""

    def test_ui_agent_incomplete_without_types(self, router, temp_dir):
        """Test that UI agent cannot complete without types.ts"""
        feature_path = temp_dir / "app" / "feature"
        feature_path.mkdir(parents=True)
        (feature_path / "components").mkdir()

        is_complete, error = router.verify_completion("ui-implementer", feature_path)

        assert is_complete is False
        assert "types.ts" in error

    def test_ui_agent_incomplete_without_api(self, router, temp_dir):
        """Test that UI agent cannot complete without api.ts"""
        feature_path = temp_dir / "app" / "feature"
        feature_path.mkdir(parents=True)
        (feature_path / "types.ts").write_text("export interface Data {}")
        (feature_path / "components").mkdir()

        is_complete, error = router.verify_completion("ui-implementer", feature_path)

        assert is_complete is False
        assert "api.ts" in error

    def test_ui_agent_incomplete_without_todo_markers(self, router, temp_dir):
        """Test that UI agent cannot complete without TODO markers in api.ts"""
        feature_path = temp_dir / "app" / "feature"
        feature_path.mkdir(parents=True)
        (feature_path / "types.ts").write_text("export interface Data {}")
        (feature_path / "api.ts").write_text("export async function getData() {}")
        (feature_path / "components").mkdir()

        is_complete, error = router.verify_completion("ui-implementer", feature_path)

        assert is_complete is False
        assert "missing TODO markers" in error

    def test_ui_agent_complete_with_all_files(self, router, temp_dir):
        """Test that UI agent can complete with all required files"""
        feature_path = temp_dir / "app" / "feature"
        feature_path.mkdir(parents=True)
        (feature_path / "types.ts").write_text("export interface Data {}")
        (feature_path / "api.ts").write_text("🔌 INTEGRATION POINT\nexport async function getData() {}")
        (feature_path / "components").mkdir()

        is_complete, error = router.verify_completion("ui-implementer", feature_path)

        assert is_complete is True


class TestConflictPrevention:
    """Test conflict prevention rules"""

    def test_backend_cannot_create_api_ts(self, router, temp_dir):
        """Test that backend agent cannot create api.ts"""
        feature_path = temp_dir / "app" / "feature"
        feature_path.mkdir(parents=True)
        api_file = feature_path / "api.ts"
        api_file.write_text("existing content")

        with pytest.raises(ForbiddenOperationError):
            router.before_create_file("feature-logic-implementer", api_file)

    def test_backend_can_create_service_files(self, router, temp_dir):
        """Test that backend agent can create service files"""
        service_file = temp_dir / "lib" / "services" / "timeSlotService.ts"

        # Should not raise
        router.before_create_file("feature-logic-implementer", service_file)

    def test_backend_cannot_modify_components(self, router, temp_dir):
        """Test that backend agent cannot modify components"""
        component_file = temp_dir / "app" / "feature" / "components" / "Form.tsx"

        with pytest.raises(ForbiddenOperationError):
            router.before_modify_file("feature-logic-implementer", component_file)

    def test_backend_cannot_modify_page_tsx(self, router, temp_dir):
        """Test that backend agent cannot modify page.tsx"""
        page_file = temp_dir / "app" / "feature" / "page.tsx"

        with pytest.raises(ForbiddenOperationError):
            router.before_modify_file("feature-logic-implementer", page_file)

    def test_ui_can_modify_components(self, router, temp_dir):
        """Test that UI agent can modify components"""
        component_file = temp_dir / "app" / "feature" / "components" / "Form.tsx"

        # Should not raise
        router.before_modify_file("ui-implementer", component_file)


class TestFunctionSignatureVerification:
    """Test function signature verification"""

    def test_signatures_unchanged(self, router):
        """Test that unchanged signatures pass verification"""
        original = """
export async function createData(data: CreateDTO): Promise<Data> {
    throw new Error('Not implemented');
}
"""
        modified = """
export async function createData(data: CreateDTO): Promise<Data> {
    const result = await service.create(data);
    return result;
}
"""
        # Should not raise
        router.verify_api_signature_unchanged(original, modified)

    def test_signature_changed_detected(self, router):
        """Test that changed signatures are detected"""
        original = """
export async function createData(data: CreateDTO): Promise<Data> {
    throw new Error('Not implemented');
}
"""
        modified = """
export async function createData(title: string, value: number): Promise<Data> {
    return service.create({ title, value });
}
"""
        with pytest.raises(ForbiddenOperationError):
            router.verify_api_signature_unchanged(original, modified)

    def test_function_removed_detected(self, router):
        """Test that removed functions are detected"""
        original = """
export async function createData(data: CreateDTO): Promise<Data> {
    throw new Error('Not implemented');
}
export async function updateData(id: string, data: UpdateDTO): Promise<Data> {
    throw new Error('Not implemented');
}
"""
        modified = """
export async function createData(data: CreateDTO): Promise<Data> {
    return service.create(data);
}
"""
        with pytest.raises(ForbiddenOperationError):
            router.verify_api_signature_unchanged(original, modified)


class TestMetrics:
    """Test metrics tracking"""

    def test_metrics_initialization(self):
        """Test that metrics are initialized correctly"""
        metrics = RoutingMetrics()

        assert metrics.metrics['total_requests'] == 0
        assert metrics.metrics['routed_to_ui'] == 0
        assert metrics.metrics['routed_to_backend'] == 0

    def test_record_route(self):
        """Test recording routing decisions"""
        metrics = RoutingMetrics()

        metrics.record_route("ui-implementer")
        assert metrics.metrics['total_requests'] == 1
        assert metrics.metrics['routed_to_ui'] == 1

        metrics.record_route("feature-logic-implementer")
        assert metrics.metrics['total_requests'] == 2
        assert metrics.metrics['routed_to_backend'] == 1

    def test_record_block(self):
        """Test recording blocked operations"""
        metrics = RoutingMetrics()

        metrics.record_block("missing_prerequisites")
        assert metrics.metrics['blocked_missing_prerequisites'] == 1

        metrics.record_block("file_conflicts")
        assert metrics.metrics['blocked_file_conflicts'] == 1

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        metrics = RoutingMetrics()

        # 8 successful, 2 blocked
        for _ in range(8):
            metrics.record_route("ui-implementer")

        for _ in range(2):
            metrics.record_route("ui-implementer")
            metrics.record_block("missing_prerequisites")

        success_rate = metrics.get_success_rate()
        assert success_rate == 0.8  # 8/10


class TestOrchestrator:
    """Test orchestrator functionality"""

    def test_process_ui_request(self, orchestrator):
        """Test processing UI request"""
        result = orchestrator.process_request("시간 거래 UI 만들어줘")

        assert result.agent == "ui-implementer"
        assert result.status == AgentStatus.RUNNING

    def test_process_backend_without_ui_blocked(self, orchestrator):
        """Test processing backend request without UI"""
        result = orchestrator.process_request("Supabase 구현해줘")

        assert result.status == AgentStatus.BLOCKED
        assert "UI foundation not found" in result.message

    def test_verify_completion_success(self, orchestrator, temp_dir):
        """Test successful completion verification"""
        # Create complete UI foundation
        feature_path = temp_dir / "app" / "feature"
        feature_path.mkdir(parents=True)
        (feature_path / "types.ts").write_text("export interface Data {}")
        (feature_path / "api.ts").write_text("🔌 INTEGRATION POINT\nexport async function getData() {}")
        (feature_path / "components").mkdir()

        result = orchestrator.verify_agent_completion("ui-implementer", feature_path)

        assert result.status == AgentStatus.COMPLETED

    def test_verify_completion_failure(self, orchestrator, temp_dir):
        """Test failed completion verification"""
        # Incomplete foundation
        feature_path = temp_dir / "app" / "feature"
        feature_path.mkdir(parents=True)
        (feature_path / "types.ts").write_text("export interface Data {}")

        result = orchestrator.verify_agent_completion("ui-implementer", feature_path)

        assert result.status == AgentStatus.BLOCKED

    def test_check_file_operation_allowed(self, orchestrator, temp_dir):
        """Test allowed file operation"""
        service_file = temp_dir / "lib" / "services" / "service.ts"

        error = orchestrator.check_file_operation(
            "feature-logic-implementer",
            "create",
            service_file
        )

        assert error is None

    def test_check_file_operation_forbidden(self, orchestrator, temp_dir):
        """Test forbidden file operation"""
        component_file = temp_dir / "app" / "feature" / "components" / "Form.tsx"

        error = orchestrator.check_file_operation(
            "feature-logic-implementer",
            "modify",
            component_file
        )

        assert error is not None
        assert "FORBIDDEN" in error


class TestIntegrationScenarios:
    """Test complete workflow scenarios"""

    def test_full_feature_workflow(self, orchestrator, temp_dir):
        """Test complete feature workflow: UI -> Backend"""

        # Step 1: User requests full feature
        result1 = orchestrator.process_request("시간 거래 기능 만들어줘")
        assert result1.agent == "ui-implementer"
        assert result1.status == AgentStatus.RUNNING

        # Step 2: UI agent creates foundation
        feature_path = temp_dir / "app" / "time-slots"
        feature_path.mkdir(parents=True)
        (feature_path / "types.ts").write_text("export interface TimeSlot {}")
        (feature_path / "api.ts").write_text("🔌 INTEGRATION POINT\nexport async function getSlots() {}")
        (feature_path / "components").mkdir()

        # Step 3: Verify UI completion
        result2 = orchestrator.verify_agent_completion("ui-implementer", feature_path)
        assert result2.status == AgentStatus.COMPLETED

        # Step 4: User requests backend
        result3 = orchestrator.process_request(
            "이제 실제로 작동하게 해줘",
            {"current_path": str(feature_path)}
        )
        assert result3.agent == "feature-logic-implementer"
        assert result3.status == AgentStatus.RUNNING

    def test_backend_first_blocked(self, orchestrator):
        """Test that backend-first approach is blocked"""

        result = orchestrator.process_request("Supabase 인증 로직 구현해줘")

        assert result.status == AgentStatus.BLOCKED
        assert "UI foundation not found" in result.message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])
