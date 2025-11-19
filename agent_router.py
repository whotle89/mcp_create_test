"""
Agent Router - System-Level Agent Routing Logic

This module implements mandatory routing rules to prevent agent conflicts
and ensure proper collaboration between ui-implementer and feature-logic-implementer.

Based on: SYSTEM-ROUTING-LOGIC.md
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Literal
import re


RequestType = Literal["full_feature", "ui_only", "backend_only", "modify_existing"]
AgentType = Literal["ui-implementer", "feature-logic-implementer", "error"]


class AgentRouterError(Exception):
    """Base exception for agent routing errors"""
    pass


class MissingPrerequisitesError(AgentRouterError):
    """Raised when required files are missing"""
    pass


class IncompleteDeliveryError(AgentRouterError):
    """Raised when agent hasn't completed required files"""
    pass


class ForbiddenOperationError(AgentRouterError):
    """Raised when agent tries to perform forbidden operation"""
    pass


class AgentRouter:
    """
    Routes requests to appropriate agents and enforces collaboration rules
    """

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.config = {
            "enforce_ui_first": True,
            "verify_prerequisites": True,
            "verify_completion": True,
            "prevent_file_conflicts": True,
            "allow_manual_override": False,  # For debugging only
        }

    def route_request(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        Determine which agent should handle the request

        Args:
            user_message: The user's request message
            context: Additional context (current_path, etc.)

        Returns:
            "ui-implementer" | "feature-logic-implementer" | "error:*"
        """
        context = context or {}

        # Step 1: Analyze request type
        request_type = self.classify_request(user_message)

        # Step 2: Check existing files
        feature_path = self.extract_feature_path(user_message, context)
        files_exist = self.check_existing_files(feature_path)

        # Step 3: Route based on rules
        if request_type == "full_feature":
            # Full feature needs UI first
            if not files_exist["ui_complete"]:
                return "ui-implementer"
            else:
                # UI exists, now add backend
                return "feature-logic-implementer"

        elif request_type == "ui_only":
            # Always UI agent for UI requests
            return "ui-implementer"

        elif request_type == "backend_only":
            # Backend needs UI foundation
            if not files_exist["ui_complete"]:
                return "error:missing_ui_foundation"
            else:
                return "feature-logic-implementer"

        elif request_type == "modify_existing":
            # Check what needs modification
            if self.needs_ui_changes(user_message):
                return "ui-implementer"
            else:
                if not files_exist["ui_complete"]:
                    return "error:missing_ui_foundation"
                return "feature-logic-implementer"

        else:
            # Ambiguous, default to UI first
            return "ui-implementer"

    def classify_request(self, message: str) -> RequestType:
        """
        Classify user request type

        Args:
            message: User's request message

        Returns:
            Request type classification
        """
        ui_keywords = ["UI", "디자인", "레이아웃", "컴포넌트", "화면", "폼", "페이지"]
        backend_keywords = [
            "Supabase", "API", "로직", "데이터베이스", "쿼리",
            "작동", "연결", "구현", "인증", "서버"
        ]
        modify_keywords = ["수정", "추가", "변경", "업데이트"]

        has_ui = any(kw in message for kw in ui_keywords)
        has_backend = any(kw in message for kw in backend_keywords)
        has_modify = any(kw in message for kw in modify_keywords)

        if has_ui and not has_backend and "만" in message:
            # Explicit "UI만" request
            return "ui_only"
        elif has_backend and not has_ui:
            return "backend_only"
        elif has_modify:
            return "modify_existing"
        else:
            return "full_feature"

    def extract_feature_path(self, message: str, context: Dict) -> Path:
        """
        Extract feature path from message and context

        Args:
            message: User's request message
            context: Additional context

        Returns:
            Path to feature directory
        """
        # Try to get from context first
        if "current_path" in context:
            return Path(context["current_path"])

        # Try to extract from message
        # Look for patterns like "app/[feature]" or feature names
        feature_patterns = [
            r"app/([a-z-]+)",
            r"(시간\s*거래)",
            r"(로그인|회원가입|인증)",
            r"(프로필|설정)",
        ]

        for pattern in feature_patterns:
            match = re.search(pattern, message)
            if match:
                feature = match.group(1)
                # Convert Korean to path-friendly name
                feature_map = {
                    "시간 거래": "time-slots",
                    "로그인": "auth",
                    "회원가입": "auth",
                    "인증": "auth",
                    "프로필": "profile",
                    "설정": "settings",
                }
                feature_name = feature_map.get(feature, feature.replace(" ", "-"))
                return self.base_path / "app" / feature_name

        # Default to app root
        return self.base_path / "app"

    def check_existing_files(self, feature_path: Path) -> Dict[str, bool]:
        """
        Check what files already exist

        Args:
            feature_path: Path to feature directory

        Returns:
            Dictionary with existence flags
        """
        types_exists = (feature_path / "types.ts").exists()
        api_exists = (feature_path / "api.ts").exists()
        components_exist = (feature_path / "components").exists()

        return {
            "types_exists": types_exists,
            "api_exists": api_exists,
            "components_exist": components_exist,
            "ui_complete": types_exists and api_exists and components_exist,
        }

    def needs_ui_changes(self, message: str) -> bool:
        """
        Determine if message implies UI changes are needed

        Args:
            message: User's request message

        Returns:
            True if UI changes needed
        """
        ui_change_keywords = [
            "폼", "화면", "디자인", "레이아웃", "버튼",
            "입력", "표시", "보여", "UI", "컴포넌트"
        ]

        return any(kw in message for kw in ui_change_keywords)

    def verify_prerequisites(self, agent: str, feature_path: Path) -> Tuple[bool, str]:
        """
        Verify agent can run

        Args:
            agent: Agent name
            feature_path: Path to feature directory

        Returns:
            (can_run, error_message)
        """
        if not self.config["verify_prerequisites"]:
            return (True, "")

        if agent == "feature-logic-implementer":
            files = self.check_existing_files(feature_path)
            if not files["ui_complete"]:
                missing = []
                if not files["types_exists"]:
                    missing.append("types.ts")
                if not files["api_exists"]:
                    missing.append("api.ts")
                if not files["components_exist"]:
                    missing.append("components/")

                error_msg = (
                    f"❌ Cannot run feature-logic-implementer\n\n"
                    f"Required files not found:\n"
                    f"{chr(10).join('- ' + str(feature_path / m) for m in missing)}\n\n"
                    f"These files must be created by ui-implementer first.\n\n"
                    f"Next step:\n"
                    f"1. Run ui-implementer to create the UI foundation\n"
                    f"2. Then run feature-logic-implementer to add backend logic"
                )
                return (False, error_msg)

        return (True, "")

    def verify_completion(self, agent: str, feature_path: Path) -> Tuple[bool, str]:
        """
        Verify agent completed required tasks

        Args:
            agent: Agent name
            feature_path: Path to feature directory

        Returns:
            (is_complete, error_message)
        """
        if not self.config["verify_completion"]:
            return (True, "")

        if agent == "ui-implementer":
            is_complete, missing = self._verify_ui_completion(feature_path)
            if not is_complete:
                error_msg = (
                    f"❌ Cannot complete ui-implementer task\n\n"
                    f"Missing required files:\n"
                    f"{chr(10).join('- ' + m for m in missing)}\n\n"
                    f"You must create ALL mandatory files:\n"
                    f"1. types.ts {'✓' if (feature_path / 'types.ts').exists() else '✗ (MISSING)'}\n"
                    f"2. api.ts {'✓' if (feature_path / 'api.ts').exists() else '✗ (MISSING)'}\n"
                    f"3. components/ {'✓' if (feature_path / 'components').exists() else '✗ (MISSING)'}\n\n"
                    f"Please create all files before completing."
                )
                return (False, error_msg)

        return (True, "")

    def _verify_ui_completion(self, feature_path: Path) -> Tuple[bool, List[str]]:
        """
        Verify UI agent created all mandatory files

        Args:
            feature_path: Path to feature directory

        Returns:
            (is_complete, missing_files)
        """
        missing = []

        if not (feature_path / "types.ts").exists():
            missing.append("types.ts")

        if not (feature_path / "api.ts").exists():
            missing.append("api.ts")
        else:
            # Verify api.ts has TODO markers
            content = (feature_path / "api.ts").read_text(encoding='utf-8')
            if "🔌 INTEGRATION POINT" not in content:
                missing.append("api.ts (missing TODO markers)")

        if not (feature_path / "components").exists():
            missing.append("components/")

        return (len(missing) == 0, missing)

    def before_create_file(self, agent: str, file_path: Path) -> None:
        """
        Prevent duplicate file creation

        Args:
            agent: Agent name
            file_path: Path to file being created

        Raises:
            ForbiddenOperationError: If operation is forbidden
        """
        if not self.config["prevent_file_conflicts"]:
            return

        if str(file_path).endswith("api.ts"):
            if file_path.exists():
                if agent == "feature-logic-implementer":
                    raise ForbiddenOperationError(
                        f"FORBIDDEN: feature-logic-implementer cannot create {file_path}. "
                        f"This file already exists and should only be modified, not replaced."
                    )

        if str(file_path).endswith("types.ts"):
            if file_path.exists():
                if agent == "feature-logic-implementer":
                    # Allow extending, but warn
                    print(f"⚠️  WARNING: Extending existing {file_path}. Do not delete existing types.")

    def before_modify_file(self, agent: str, file_path: Path) -> None:
        """
        Prevent backend agent from touching UI files

        Args:
            agent: Agent name
            file_path: Path to file being modified

        Raises:
            ForbiddenOperationError: If operation is forbidden
        """
        if not self.config["prevent_file_conflicts"]:
            return

        ui_directories = ["/components/", "/page.tsx", "/layout.tsx"]

        if agent == "feature-logic-implementer":
            for ui_dir in ui_directories:
                if ui_dir in str(file_path).replace("\\", "/"):
                    raise ForbiddenOperationError(
                        f"FORBIDDEN: feature-logic-implementer cannot modify {file_path}. "
                        f"This is UI territory. Request ui-implementer to make changes."
                    )

    def verify_api_signature_unchanged(
        self,
        original_api: str,
        modified_api: str
    ) -> None:
        """
        Ensure feature-logic-implementer didn't change function signatures

        Args:
            original_api: Original api.ts content
            modified_api: Modified api.ts content

        Raises:
            ForbiddenOperationError: If signatures were changed
        """
        if not self.config["prevent_file_conflicts"]:
            return

        original_sigs = self._extract_function_signatures(original_api)
        modified_sigs = self._extract_function_signatures(modified_api)

        for func_name in original_sigs:
            if func_name not in modified_sigs:
                raise ForbiddenOperationError(
                    f"Function {func_name} was removed from api.ts"
                )

            if original_sigs[func_name] != modified_sigs[func_name]:
                raise ForbiddenOperationError(
                    f"Function signature changed: {func_name}\n"
                    f"Original: {original_sigs[func_name]}\n"
                    f"Modified: {modified_sigs[func_name]}\n"
                    f"FORBIDDEN: You must keep the exact signature that UI expects."
                )

    def _extract_function_signatures(self, content: str) -> Dict[str, str]:
        """
        Extract function signatures from TypeScript code

        Args:
            content: TypeScript file content

        Returns:
            Dictionary of function_name -> signature
        """
        signatures = {}

        # Match export async function declarations
        pattern = r'export\s+async\s+function\s+(\w+)\s*\([^)]*\)\s*:\s*Promise<[^>]+>'

        for match in re.finditer(pattern, content):
            func_name = match.group(1)
            signature = match.group(0)
            signatures[func_name] = signature

        return signatures


class RoutingMetrics:
    """
    Track routing metrics for monitoring
    """

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "routed_to_ui": 0,
            "routed_to_backend": 0,
            "blocked_missing_prerequisites": 0,
            "blocked_incomplete_ui": 0,
            "blocked_file_conflicts": 0,
            "successful_collaborations": 0,
        }

    def record_route(self, agent: str) -> None:
        """Record successful routing"""
        self.metrics["total_requests"] += 1
        if agent == "ui-implementer":
            self.metrics["routed_to_ui"] += 1
        elif agent == "feature-logic-implementer":
            self.metrics["routed_to_backend"] += 1

    def record_block(self, reason: str) -> None:
        """Record blocked operation"""
        if reason == "missing_prerequisites":
            self.metrics["blocked_missing_prerequisites"] += 1
        elif reason == "incomplete_ui":
            self.metrics["blocked_incomplete_ui"] += 1
        elif reason == "file_conflicts":
            self.metrics["blocked_file_conflicts"] += 1

    def record_success(self) -> None:
        """Record successful collaboration"""
        self.metrics["successful_collaborations"] += 1

    def get_metrics(self) -> Dict[str, int]:
        """Get current metrics"""
        return self.metrics.copy()

    def get_success_rate(self) -> float:
        """Calculate success rate (blocked should be near zero)"""
        total_blocked = (
            self.metrics["blocked_missing_prerequisites"] +
            self.metrics["blocked_incomplete_ui"] +
            self.metrics["blocked_file_conflicts"]
        )
        total = self.metrics["total_requests"]

        if total == 0:
            return 1.0

        return 1.0 - (total_blocked / total)
