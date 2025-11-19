# System-Level Agent Routing Logic

## 🎯 Purpose

This document defines the **mandatory routing rules** that the system must enforce to prevent agent conflicts and ensure proper collaboration between ui-implementer and feature-logic-implementer.

---

## 🔒 Core Enforcement Rules

### Rule #1: UI Agent ALWAYS Runs First

For any feature request that involves both UI and backend:

```
Request Type: Full Feature
Examples: "회원가입 만들어줘", "시간 거래 기능 구현", "프로필 수정"

System Decision:
1. Route to ui-implementer FIRST
2. feature-logic-implementer CANNOT run until UI completes
```

**Why this rule?**
- feature-logic-implementer depends on files created by ui-implementer
- Without types.ts and api.ts, backend has nowhere to integrate
- Prevents duplicate file creation

---

### Rule #2: Logic Agent Must Verify Prerequisites

Before feature-logic-implementer executes:

```python
def can_run_feature_logic_implementer(feature_path: str) -> bool:
    """
    Check if prerequisite files exist
    """
    required_files = [
        f"{feature_path}/types.ts",
        f"{feature_path}/api.ts",
        f"{feature_path}/components/"
    ]
    
    for file in required_files:
        if not exists(file):
            return False
    
    return True
```

**If prerequisites missing:**
```
STOP execution
Show error to user:
  "Cannot run feature-logic-implementer.
   
   Required files missing:
   - app/[feature]/types.ts
   - app/[feature]/api.ts
   - app/[feature]/components/
   
   Please run ui-implementer first."
```

---

### Rule #3: UI Agent Must Complete Mandatory Files

ui-implementer cannot mark task complete without:

```python
def verify_ui_completion(feature_path: str) -> tuple[bool, list[str]]:
    """
    Verify UI agent created all mandatory files
    """
    missing = []
    
    if not exists(f"{feature_path}/types.ts"):
        missing.append("types.ts")
    
    if not exists(f"{feature_path}/api.ts"):
        missing.append("api.ts")
    
    if not exists(f"{feature_path}/components/"):
        missing.append("components/")
    
    # Verify api.ts has TODO markers
    if exists(f"{feature_path}/api.ts"):
        content = read_file(f"{feature_path}/api.ts")
        if "🔌 INTEGRATION POINT" not in content:
            missing.append("api.ts (missing TODO markers)")
    
    return (len(missing) == 0, missing)
```

**If verification fails:**
```
Block task completion
Show error to ui-implementer:
  "Cannot complete task. Missing required files:
   - types.ts
   - api.ts (with TODO markers)
   - components/
   
   You must create all three before completing."
```

---

## 🔀 Routing Decision Tree

### Scenario 1: User Requests Full Feature

```
User input: "시간 거래 기능 만들어줘"

System analysis:
- Contains: feature description
- Requires: UI + Backend
- No existing files mentioned

Routing decision:
1. Route to ui-implementer ✓
2. ui-implementer creates: types.ts, api.ts, components/
3. Verify completion (all 3 files exist)
4. Auto-trigger feature-logic-implementer OR wait for user

User: "이제 실제로 작동하게 해줘"
5. Verify prerequisites (types.ts, api.ts exist)
6. Route to feature-logic-implementer ✓
```

### Scenario 2: User Requests UI Only

```
User input: "로그인 폼 UI만 만들어줘"

System analysis:
- Contains: UI-specific request
- Keyword: "UI만", "디자인만"

Routing decision:
1. Route to ui-implementer ✓
2. ui-implementer creates: types.ts, api.ts, components/
   (Even though user said "UI only", create integration layer)
3. Task complete
4. If user later says "로직 구현해줘":
   - Verify prerequisites exist ✓
   - Route to feature-logic-implementer ✓
```

### Scenario 3: User Requests Backend Only

```
User input: "Supabase 쿼리 구현해줘"

System analysis:
- Contains: Backend-specific request
- Keywords: "Supabase", "API", "로직"

Routing decision:
1. Check if UI files exist:
   - If YES → Route to feature-logic-implementer ✓
   - If NO → BLOCK and inform user:
     "UI structure not found. Please create UI first with ui-implementer,
      then I can implement the backend logic."
```

### Scenario 4: User Modifies Existing Feature

```
User input: "시간 거래 수정 기능 추가해줘"
(시간 거래 create already exists)

System analysis:
- Feature path exists: app/time-slots/
- Files exist: types.ts ✓, api.ts ✓, components/ ✓

Routing decision:
1. Check if new UI components needed:
   - If YES → Route to ui-implementer first
     (add updateTimeSlot to api.ts, create EditForm component)
   - If NO → Route directly to feature-logic-implementer
2. feature-logic-implementer modifies existing api.ts
```

---

## 🛡️ Conflict Prevention Rules

### Prevention #1: Duplicate File Creation

```python
def before_create_file(agent: str, file_path: str):
    """
    Prevent duplicate file creation
    """
    if file_path.endswith("api.ts"):
        if exists(file_path):
            if agent == "feature-logic-implementer":
                raise Error(
                    "FORBIDDEN: feature-logic-implementer cannot create api.ts. "
                    "This file already exists and should only be modified, not replaced."
                )
    
    if file_path.endswith("types.ts"):
        if exists(file_path):
            if agent == "feature-logic-implementer":
                # Allow extending, but warn
                print("WARNING: Extending existing types.ts. Do not delete existing types.")
```

### Prevention #2: Function Signature Changes

```python
def verify_api_signature_unchanged(original_api: str, modified_api: str):
    """
    Ensure feature-logic-implementer didn't change function signatures
    """
    original_signatures = extract_function_signatures(original_api)
    modified_signatures = extract_function_signatures(modified_api)
    
    for func_name in original_signatures:
        if func_name not in modified_signatures:
            raise Error(f"Function {func_name} was removed from api.ts")
        
        if original_signatures[func_name] != modified_signatures[func_name]:
            raise Error(
                f"Function signature changed: {func_name}\n"
                f"Original: {original_signatures[func_name]}\n"
                f"Modified: {modified_signatures[func_name]}\n"
                f"FORBIDDEN: You must keep the exact signature that UI expects."
            )
```

### Prevention #3: UI File Modification

```python
def before_modify_file(agent: str, file_path: str):
    """
    Prevent backend agent from touching UI files
    """
    ui_directories = ["/components/", "/page.tsx", "/layout.tsx"]
    
    if agent == "feature-logic-implementer":
        for ui_dir in ui_directories:
            if ui_dir in file_path:
                raise Error(
                    f"FORBIDDEN: feature-logic-implementer cannot modify {file_path}. "
                    f"This is UI territory. Request ui-implementer to make changes."
                )
```

---

## 📊 Routing Logic Implementation

### Pseudo-code for System Router

```python
class AgentRouter:
    def route_request(self, user_message: str, context: dict) -> str:
        """
        Determine which agent should handle the request
        
        Returns: "ui-implementer" | "feature-logic-implementer" | "error"
        """
        
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
                return "feature-logic-implementer"
        
        else:
            # Ambiguous, default to UI first
            return "ui-implementer"
    
    def classify_request(self, message: str) -> str:
        """
        Classify user request type
        """
        ui_keywords = ["UI", "디자인", "레이아웃", "컴포넌트", "화면"]
        backend_keywords = ["Supabase", "API", "로직", "데이터베이스", "쿼리"]
        
        has_ui = any(kw in message for kw in ui_keywords)
        has_backend = any(kw in message for kw in backend_keywords)
        
        if has_ui and not has_backend:
            return "ui_only"
        elif has_backend and not has_ui:
            return "backend_only"
        elif "수정" in message or "추가" in message:
            return "modify_existing"
        else:
            return "full_feature"
    
    def check_existing_files(self, feature_path: str) -> dict:
        """
        Check what files already exist
        """
        return {
            "types_exists": exists(f"{feature_path}/types.ts"),
            "api_exists": exists(f"{feature_path}/api.ts"),
            "components_exist": exists(f"{feature_path}/components/"),
            "ui_complete": (
                exists(f"{feature_path}/types.ts") and
                exists(f"{feature_path}/api.ts") and
                exists(f"{feature_path}/components/")
            )
        }
    
    def verify_prerequisites(self, agent: str, feature_path: str) -> tuple[bool, str]:
        """
        Verify agent can run
        """
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
                    f"Cannot run feature-logic-implementer. Missing files:\n"
                    f"{', '.join(missing)}\n\n"
                    f"Please run ui-implementer first to create the foundation."
                )
                return (False, error_msg)
        
        return (True, "")
    
    def verify_completion(self, agent: str, feature_path: str) -> tuple[bool, str]:
        """
        Verify agent completed required tasks
        """
        if agent == "ui-implementer":
            is_complete, missing = verify_ui_completion(feature_path)
            if not is_complete:
                error_msg = (
                    f"Cannot complete task. Missing required files:\n"
                    f"{', '.join(missing)}\n\n"
                    f"You must create all mandatory files before completing."
                )
                return (False, error_msg)
        
        return (True, "")
```

---

## 🧪 Test Cases

### Test Case 1: First Feature Request

```python
def test_first_feature_request():
    router = AgentRouter()
    
    # User requests new feature
    result = router.route_request(
        user_message="회원가입 기능 만들어줘",
        context={"current_path": "app/auth"}
    )
    
    assert result == "ui-implementer"
    
    # Simulate UI completion
    create_file("app/auth/types.ts")
    create_file("app/auth/api.ts")
    create_file("app/auth/components/SignupForm.tsx")
    
    # User requests backend
    result = router.route_request(
        user_message="이제 Supabase 연결해줘",
        context={"current_path": "app/auth"}
    )
    
    assert result == "feature-logic-implementer"
```

### Test Case 2: Backend First (Should Fail)

```python
def test_backend_first_blocked():
    router = AgentRouter()
    
    # User requests backend without UI
    result = router.route_request(
        user_message="Supabase 인증 로직 구현해줘",
        context={"current_path": "app/auth"}
    )
    
    # Should detect missing UI
    can_run, error = router.verify_prerequisites(
        agent="feature-logic-implementer",
        feature_path="app/auth"
    )
    
    assert can_run == False
    assert "Missing files" in error
```

### Test Case 3: UI Without Mandatory Files (Should Fail)

```python
def test_ui_incomplete():
    router = AgentRouter()
    
    # Simulate UI agent trying to complete without all files
    create_file("app/auth/types.ts")
    # Missing: api.ts, components/
    
    can_complete, error = router.verify_completion(
        agent="ui-implementer",
        feature_path="app/auth"
    )
    
    assert can_complete == False
    assert "api.ts" in error
    assert "components/" in error
```

---

## 🎯 Implementation Checklist

When integrating this routing logic into your system:

### Phase 1: Basic Routing
- [ ] Implement `AgentRouter.route_request()`
- [ ] Implement `classify_request()`
- [ ] Implement `check_existing_files()`
- [ ] Test with basic scenarios

### Phase 2: Prerequisite Checks
- [ ] Implement `verify_prerequisites()`
- [ ] Block feature-logic-implementer if files missing
- [ ] Show clear error messages to user
- [ ] Test blocking behavior

### Phase 3: Completion Verification
- [ ] Implement `verify_completion()`
- [ ] Block ui-implementer if files missing
- [ ] Verify api.ts has TODO markers
- [ ] Test with incomplete deliveries

### Phase 4: Conflict Prevention
- [ ] Implement `before_create_file()` hook
- [ ] Implement `before_modify_file()` hook
- [ ] Implement `verify_api_signature_unchanged()`
- [ ] Test with intentional violations

### Phase 5: Production Hardening
- [ ] Add logging for routing decisions
- [ ] Add metrics for agent conflicts
- [ ] Add override mechanism (for debugging)
- [ ] Document edge cases

---

## 📝 Configuration

### Environment Variables

```bash
# Enable strict routing enforcement
STRICT_AGENT_ROUTING=true

# Block feature-logic without UI
REQUIRE_UI_FIRST=true

# Verify UI completion
VERIFY_UI_MANDATORY_FILES=true

# Prevent UI modification by backend agent
PROTECT_UI_FILES=true
```

### Feature Flags

```python
ROUTING_CONFIG = {
    "enforce_ui_first": True,
    "verify_prerequisites": True,
    "verify_completion": True,
    "prevent_file_conflicts": True,
    "allow_manual_override": False,  # For debugging only
}
```

---

## 🚨 Error Messages

### Error: Missing Prerequisites

```
❌ Cannot run feature-logic-implementer

Required files not found:
- app/time-slots/types.ts
- app/time-slots/api.ts
- app/time-slots/components/

These files must be created by ui-implementer first.

Next step:
1. Run ui-implementer to create the UI foundation
2. Then run feature-logic-implementer to add backend logic
```

### Error: Incomplete UI Delivery

```
❌ Cannot complete ui-implementer task

Missing required files:
- api.ts (integration layer)

You must create ALL mandatory files:
1. types.ts ✓
2. api.ts ✗ (MISSING)
3. components/ ✓

Please create api.ts with TODO markers before completing.
```

### Error: Forbidden File Modification

```
❌ Cannot modify app/time-slots/components/TimeSlotForm.tsx

feature-logic-implementer is not allowed to modify UI components.

If UI changes are needed:
1. Document the required changes
2. Request ui-implementer to make the modifications
3. Continue with backend implementation
```

---

## 🎓 Best Practices

### For System Developers

1. **Fail Fast**: Block invalid operations immediately
2. **Clear Errors**: Explain WHY something is blocked
3. **Logging**: Log all routing decisions for debugging
4. **Testing**: Test conflict scenarios extensively
5. **Monitoring**: Track agent conflict rates in production

### For Agent Developers

1. **Trust the System**: Let routing logic decide order
2. **Verify Prerequisites**: Check files before starting
3. **Document Assumptions**: Make routing easier
4. **Error Handling**: Gracefully handle blocked operations
5. **Communication**: Clear messages when blocked

---

## 📊 Metrics to Track

```python
METRICS = {
    "total_requests": 0,
    "routed_to_ui": 0,
    "routed_to_backend": 0,
    "blocked_missing_prerequisites": 0,
    "blocked_incomplete_ui": 0,
    "blocked_file_conflicts": 0,
    "successful_collaborations": 0,
}
```

**Success metric:** `blocked_*` metrics should be near zero in production.

---

## 🔧 Maintenance

### When to Update Routing Logic

1. **New agent added**: Update routing tree
2. **File structure changes**: Update verification logic
3. **New conflict patterns**: Add prevention rules
4. **Performance issues**: Optimize file checks

### Versioning

```python
ROUTING_LOGIC_VERSION = "1.0.0"

# Track compatibility
COMPATIBLE_AGENTS = {
    "ui-implementer": ">=1.0.0",
    "feature-logic-implementer": ">=1.0.0",
}
```

---

## 🎯 Summary

**This routing logic ensures:**
1. ✅ UI agent ALWAYS runs first
2. ✅ Backend agent CANNOT run without UI foundation
3. ✅ No duplicate file creation
4. ✅ No function signature changes
5. ✅ No unauthorized file modifications
6. ✅ Clear error messages when blocked
7. ✅ Successful agent collaboration

**Without this logic:** Chaos, conflicts, broken features  
**With this logic:** Smooth collaboration, predictable behavior
