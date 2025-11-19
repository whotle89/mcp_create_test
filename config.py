"""
Configuration Management for Agent Orchestration System

Centralized configuration for routing rules, file paths, and system behavior.

Usage:
    from config import Config

    config = Config.load()
    if config.ENFORCE_UI_FIRST:
        # Apply routing rules
"""

from pathlib import Path
from typing import Dict, List, Optional
import os
import json


class Config:
    """
    System configuration
    """

    # ==================== ROUTING RULES ====================

    # Core enforcement
    ENFORCE_UI_FIRST = True
    """UI agent must always run before backend agent"""

    REQUIRE_UI_FOUNDATION = True
    """Backend agent requires UI foundation files"""

    VERIFY_PREREQUISITES = True
    """Check prerequisites before allowing agent execution"""

    VERIFY_COMPLETION = True
    """Verify agent completed all required deliverables"""

    PREVENT_FILE_CONFLICTS = True
    """Prevent agents from modifying each other's files"""

    ALLOW_MANUAL_OVERRIDE = False
    """Allow manual override of routing rules (debugging only)"""

    # ==================== FILE STRUCTURE ====================

    # Required UI files
    UI_REQUIRED_FILES = [
        "types.ts",
        "api.ts",
        "components/",
    ]
    """Files that ui-implementer must create"""

    # UI file patterns that backend cannot modify
    UI_PROTECTED_PATTERNS = [
        "/components/",
        "/page.tsx",
        "/layout.tsx",
        ".tsx",
    ]
    """File patterns that feature-logic-implementer cannot modify"""

    # Backend file territory
    BACKEND_FILE_PATTERNS = [
        "lib/domain/",
        "lib/services/",
        "lib/supabase/",
        "lib/utils/",
        "/actions.ts",
    ]
    """File patterns that feature-logic-implementer can create"""

    # ==================== VALIDATION ====================

    # API.ts validation
    API_TODO_MARKER = "🔌 INTEGRATION POINT"
    """Required marker in api.ts for TODOs"""

    API_STATUS_TAG = "@status TODO"
    """Required status tag in api.ts comments"""

    # ==================== METRICS & MONITORING ====================

    # Metrics
    METRICS_ENABLED = True
    """Enable metrics collection"""

    METRICS_HISTORY_SIZE = 1000
    """Number of events to keep in history"""

    # Logging
    LOG_LEVEL = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR"""

    LOG_FILE = "agent_orchestrator.log"
    """Log file path"""

    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    """Log message format"""

    # Alert thresholds
    ALERT_ERROR_RATE_THRESHOLD = 0.1
    """Alert if error rate exceeds 10%"""

    ALERT_BLOCK_RATE_THRESHOLD = 0.2
    """Alert if block rate exceeds 20%"""

    ALERT_SUCCESS_RATE_THRESHOLD = 0.8
    """Alert if success rate falls below 80%"""

    # ==================== API INTERFACE ====================

    # API server
    API_HOST = "0.0.0.0"
    """API server host"""

    API_PORT = 8000
    """API server port"""

    API_RELOAD = True
    """Enable API auto-reload (development)"""

    # CORS
    API_CORS_ORIGINS = ["*"]
    """Allowed CORS origins"""

    # ==================== PATHS ====================

    BASE_PATH = Path(".")
    """Base directory for the project"""

    APP_PATH = BASE_PATH / "app"
    """Next.js app directory"""

    LIB_PATH = BASE_PATH / "lib"
    """Library directory for services/domain/utils"""

    SUPABASE_PATH = BASE_PATH / "supabase"
    """Supabase directory for migrations"""

    # ==================== FEATURE DETECTION ====================

    # Keywords for request classification
    UI_KEYWORDS = [
        "UI", "디자인", "레이아웃", "컴포넌트", "화면",
        "폼", "페이지", "버튼", "입력", "표시"
    ]
    """Keywords indicating UI-focused request"""

    BACKEND_KEYWORDS = [
        "Supabase", "API", "로직", "데이터베이스", "쿼리",
        "작동", "연결", "구현", "인증", "서버", "저장"
    ]
    """Keywords indicating backend-focused request"""

    MODIFY_KEYWORDS = [
        "수정", "추가", "변경", "업데이트", "개선"
    ]
    """Keywords indicating modification of existing feature"""

    # Feature name mapping (Korean -> path)
    FEATURE_NAME_MAP = {
        "시간 거래": "time-slots",
        "로그인": "auth",
        "회원가입": "auth",
        "인증": "auth",
        "프로필": "profile",
        "설정": "settings",
        "대시보드": "dashboard",
        "알림": "notifications",
    }
    """Mapping of Korean feature names to directory names"""

    # ==================== CLAUDE CODE INTEGRATION ====================

    # Agent paths
    CLAUDE_AGENTS_PATH = Path(".claude") / "agents"
    """Path to Claude Code agent definitions"""

    UI_AGENT_FILE = CLAUDE_AGENTS_PATH / "ui-implementer.md"
    """Path to ui-implementer agent definition"""

    LOGIC_AGENT_FILE = CLAUDE_AGENTS_PATH / "feature-logic-implementer.md"
    """Path to feature-logic-implementer agent definition"""

    # ==================== METHODS ====================

    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> "Config":
        """
        Load configuration from file

        Args:
            config_file: Optional JSON config file

        Returns:
            Config instance
        """
        config = cls()

        if config_file and config_file.exists():
            data = json.loads(config_file.read_text())

            # Override defaults with file values
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        # Override with environment variables
        config._load_from_env()

        return config

    def _load_from_env(self):
        """Load configuration from environment variables"""

        # Routing rules
        if "STRICT_AGENT_ROUTING" in os.environ:
            self.ENFORCE_UI_FIRST = os.environ["STRICT_AGENT_ROUTING"].lower() == "true"

        if "REQUIRE_UI_FIRST" in os.environ:
            self.REQUIRE_UI_FOUNDATION = os.environ["REQUIRE_UI_FIRST"].lower() == "true"

        if "VERIFY_UI_MANDATORY_FILES" in os.environ:
            self.VERIFY_COMPLETION = os.environ["VERIFY_UI_MANDATORY_FILES"].lower() == "true"

        if "PROTECT_UI_FILES" in os.environ:
            self.PREVENT_FILE_CONFLICTS = os.environ["PROTECT_UI_FILES"].lower() == "true"

        # Logging
        if "LOG_LEVEL" in os.environ:
            self.LOG_LEVEL = os.environ["LOG_LEVEL"]

        # API
        if "API_PORT" in os.environ:
            self.API_PORT = int(os.environ["API_PORT"])

    def save(self, config_file: Path):
        """
        Save configuration to file

        Args:
            config_file: Path to save config
        """
        # Get all uppercase attributes (config values)
        config_data = {
            key: getattr(self, key)
            for key in dir(self)
            if key.isupper() and not key.startswith("_")
        }

        # Convert Path objects to strings
        for key, value in config_data.items():
            if isinstance(value, Path):
                config_data[key] = str(value)
            elif isinstance(value, list) and value and isinstance(value[0], Path):
                config_data[key] = [str(p) for p in value]

        config_file.write_text(json.dumps(config_data, indent=2))

    def to_dict(self) -> Dict:
        """
        Convert config to dictionary

        Returns:
            Dictionary with config values
        """
        return {
            key: getattr(self, key)
            for key in dir(self)
            if key.isupper() and not key.startswith("_")
        }

    def display(self):
        """Display current configuration"""
        print("\n" + "=" * 80)
        print("AGENT ORCHESTRATION SYSTEM - CONFIGURATION")
        print("=" * 80)

        print("\n🔒 ROUTING RULES:")
        print(f"  Enforce UI First: {self.ENFORCE_UI_FIRST}")
        print(f"  Require UI Foundation: {self.REQUIRE_UI_FOUNDATION}")
        print(f"  Verify Prerequisites: {self.VERIFY_PREREQUISITES}")
        print(f"  Verify Completion: {self.VERIFY_COMPLETION}")
        print(f"  Prevent File Conflicts: {self.PREVENT_FILE_CONFLICTS}")

        print("\n📁 FILE STRUCTURE:")
        print(f"  UI Required Files: {', '.join(self.UI_REQUIRED_FILES)}")
        print(f"  UI Protected Patterns: {len(self.UI_PROTECTED_PATTERNS)} patterns")
        print(f"  Backend File Patterns: {len(self.BACKEND_FILE_PATTERNS)} patterns")

        print("\n📊 METRICS & MONITORING:")
        print(f"  Metrics Enabled: {self.METRICS_ENABLED}")
        print(f"  History Size: {self.METRICS_HISTORY_SIZE}")
        print(f"  Log Level: {self.LOG_LEVEL}")

        print("\n🌐 API INTERFACE:")
        print(f"  Host: {self.API_HOST}")
        print(f"  Port: {self.API_PORT}")
        print(f"  Auto-reload: {self.API_RELOAD}")

        print("\n" + "=" * 80 + "\n")


# Global config instance
config = Config.load()


if __name__ == "__main__":
    # Display configuration
    config = Config.load()
    config.display()

    # Save to file
    config.save(Path("config.json"))
    print("✅ Configuration saved to config.json")
