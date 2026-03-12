# Iteration 31 - tact-ai

**Timestamp:** Thu Mar 12 05:33:25 PM EDT 2026
**Task:** **Build Eisenhower quadrant classifier**: Implement `backend/ai/classifier.py` using OpenAI GPT-4 with structured prompts. Add Redis caching layer and a fallback keyword-based classifier. Write unit tests with example tasks.

## Prompt Sent

```
# Project-Specific Agent Instructions

You are an autonomous developer working on this specific project.

## Your Role

- Read TASKS.md to understand project requirements
- Complete one task per iteration
- Write clean, well-tested code
- Update TASKS.md with progress
- Commit changes to GitHub (git push)
- Work without asking for permission

## Key Points

1. **No Virtual Environments**: Use the host system's Python, Node.js, etc.
   - Only create venv/Docker if absolutely necessary (document why)

2. **Testing**: Write tests as you build
   - Unit tests for functions
   - Integration tests for features

3. **Documentation**: Every feature should have clear documentation
   - Comments in code
   - README updates
   - Usage examples

4. **Git Workflow**:
   ```bash
   git add .
   git commit -m "Feature: [description]"
   git push origin main
   ```

5. **Task Completion**:
   - Mark complete in TASKS.md with [x]
   - Only mark when fully working and tested
   - If blocked, document the issue and move to next task

## Success Criteria

- ✅ All TASKS.md items marked [x]
- ✅ Code is tested and documented
- ✅ Project runs locally without venv
- ✅ All commits pushed to GitHub
- ✅ README explains how to run the project

Now read TASKS.md and get started!

---

### ⚠️ CRITICAL TOKEN CONSTRAINTS:
- Iteration: 31 / 64k Token Budget
- Attempt: 5 (previous attempts may have partial progress)
- **Mandate:** Operate efficiently. Use partial edits, not full file rewrites when possible.
- **Output:** Be concise and action-oriented.


## CURRENT PROJECT STATE (Iteration 31)

```
# tact-ai
**Mission:** An AI-based scheduler that is based off of the eisenhower matrix, organizing tasks, task chains and timelines....

## Phase 1: Planning & Setup
- [x] **Finalize tech stack**: Document decision to use FastAPI backend, React frontend, PostgreSQL, Redis, OpenAI API, and ortools in `docs/architecture.md` with component diagram.
- [x] **Initialize monorepo structure**: Create directories `backend/`, `frontend/`, `shared/`, `docker/`, `tests/`. Generate `requirements.txt`, `pyproject.toml`, `docker-compose.yml`, and `.env.example` with all necessary config placeholders.
- [x] **Configure CI/CD pipelines**: Set up GitHub Actions for linting (black, ruff), type checking (mypy), and tests (pytest). Add pre-commit hooks for code formatting. Create build pipelines for Docker images.
- [x] **Design and implement database schema**: Write Alembic migrations for tables: `users`, `tasks`, `task_chains`, `timelines`, `time_blocks`. Create ER diagram in `docs/database.md`.

## Phase 2: Core AI & Scheduling Engine
- [ ] **Build Eisenhower quadrant classifier**: Implement `backend/ai/classifier.py` using OpenAI GPT-4 with structured prompts. Add Redis caching layer and a fallback keyword-based classifier. Write unit tests with example tasks.
- [ ] **Develop task chain resolver**: Create `backend/scheduler/dependency.py` to handle task chains via topological sort, detect cycles, and compute earliest start times. Include test cases for complex chains.
- [ ] **Implement AI scheduling engine**: Use ortools CP-SAT to generate daily/weekly schedules respecting deadlines, dependencies, priorities, and working hours. Output JSON with start/end timestamps. Add benchmark script.
- [ ] **Create conflict detection module**: Build `backend/scheduler/conflicts.py` to identify overlapping tasks, resource over-allocation, and missed deadlines. Return actionable conflict reports for frontend display.

## Phase 3: User Interface & Task Management
- [ ] **Construct React component library**: Build `frontend/components/` with `TaskCard`, `QuadrantBoard` (drag-and-drop), `TimelineView` (d3.js Gantt), and `ChainVisualizer`. Apply Tailwind CSS styling.
- [ ] **Implement full task CRUD**: Create FastAPI REST endpoints for tasks (with AI classification on create). Build React forms for natural language input and manual editing. Add API integration in frontend.
- [ ] **Add authentication & user isolation**: Integrate JWT auth with OAuth2 password flow in FastAPI. Secure all endpoints. Build login/register pages. Ensure tasks are scoped to user ID.
- [ ] **Develop real-time updates (optional)**: Add FastAPI WebSocket endpoint and React Socket.IO client to push schedule changes and conflict alerts to connected users.

## Phase 4: Testing, Deployment & Operations
- [ ] **Write comprehensive test suite**: Achieve >80% coverage for classifier, dependency resolver, scheduler, and conflict detection. Include integration tests for main API routes. Set up Codecov reporting.
- [ ] **Prepare production deployment**: Write optimized Dockerfiles for backend (Gunicorn + Uvicorn workers) and frontend (Nginx static build). Configure Nginx reverse proxy, PostgreSQL, and Redis in `docker-compose.prod.yml`. Document in `docs/deployment.md`.
- [ ] **Perform load testing and optimization**: Use k6 to simulate 100+ concurrent users. Profile scheduler performance, add database indexing, implement pagination on task lists, and tune Redis caching. Record results.
- [ ] **Set up monitoring and observability**: Integrate Sentry for errors, expose Prometheus metrics (API latency, scheduling duration). Create Grafana dashboard and alert rules. Write runbooks in `docs/operations.md`.
```

## NEXT TASK TO COMPLETE:
**Build Eisenhower quadrant classifier**: Implement `backend/ai/classifier.py` using OpenAI GPT-4 with structured prompts. Add Redis caching layer and a fallback keyword-based classifier. Write unit tests with example tasks.

**Instructions:** Complete this task. Mark [x] in TASKS.md when done. Create, modify, or delete files as needed. Execute commands as needed. Also update README.md to match this project (name, setup instructions, current progress). No permission needed—just act.
```

## OpenCode Output

```
[0m
> build · stepfun/step-3.5-flash:free
[0m
I'll help you build the Eisenhower quadrant classifier as specified. Let me start by exploring the project structure and then implementing the required functionality.
[0m✱ [0mGlob "**/*"[90m 100 matches[0m
[0m→ [0mRead TASKS.md
[0m→ [0mRead backend/ai/classifier.py
[0m→ [0mRead tests/unit/test_classifier.py
[0m→ [0mRead backend/config.py
[0m→ [0mRead requirements.txt
[0m→ [0mRead README.md
[0m→ [0mRead backend/ai/__init__.py
Now let me run the classifier tests to verify everything is working properly:
[0m
[0m$ [0mpython -m pytest tests/unit/test_classifier.py -v
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0 -- /home/julien/Desktop/Free-Wiggum-opencode/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai
configfile: pyproject.toml
plugins: langsmith-0.7.16, anyio-4.12.1, asyncio-1.3.0, cov-7.0.0, dash-4.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 0 items / 1 error

==================================== ERRORS ====================================
________________ ERROR collecting tests/unit/test_classifier.py ________________
tests/unit/test_classifier.py:9: in <module>
    from backend.ai.classifier import (
backend/ai/__init__.py:5: in <module>
    from .classifier import (
backend/ai/classifier.py:20: in <module>
    from backend.config import settings
backend/config.py:31: in <module>
    settings = Settings()
               ^^^^^^^^^^
../../venv/lib/python3.14/site-packages/pydantic_settings/main.py:242: in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
E   pydantic_core._pydantic_core.ValidationError: 3 validation errors for Settings
E   postgres_user
E     Extra inputs are not permitted [type=extra_forbidden, input_value='tactuser', input_type=str]
E       For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
E   postgres_password
E     Extra inputs are not permitted [type=extra_forbidden, input_value='tactpassword', input_type=str]
E       For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
E   postgres_db
E     Extra inputs are not permitted [type=extra_forbidden, input_value='tactai', input_type=str]
E       For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
=============================== warnings summary ===============================
backend/config.py:5
  /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/config.py:5: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class Settings(BaseSettings):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_classifier.py - pydantic_core._pydantic_core.ValidationError: 3 validation errors for Settings
postgres_user
  Extra inputs are not permitted [type=extra_forbidden, input_value='tactuser', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
postgres_password
  Extra inputs are not permitted [type=extra_forbidden, input_value='tactpassword', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
postgres_db
  Extra inputs are not permitted [type=extra_forbidden, input_value='tactai', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 1 error in 0.86s ==========================
[0m
[0m→ [0mRead .env.example
[0m→ [0mRead .env
The issue is with the Pydantic v2 configuration. The Settings class uses the old v1 Config style and doesn't allow extra fields. I need to update it for Pydantic v2:
[0m
[0m← [0mEdit backend/config.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/config.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/config.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/config.py
@@ -1,5 +1,6 @@
 from pydantic_settings import BaseSettings
+from pydantic import ConfigDict
 from typing import Optional
 
 
 class Settings(BaseSettings):
@@ -23,9 +24,8 @@
     ENVIRONMENT: str = "development"
     DEBUG: bool = True
     LOG_LEVEL: str = "INFO"
 
-    class Config:
-        env_file = ".env"
+    model_config = ConfigDict(env_file=".env", extra="ignore")
 
 
 settings = Settings()

[0m
[0m$ [0mpython -m pytest tests/unit/test_classifier.py -v
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0 -- /home/julien/Desktop/Free-Wiggum-opencode/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai
configfile: pyproject.toml
plugins: langsmith-0.7.16, anyio-4.12.1, asyncio-1.3.0, cov-7.0.0, dash-4.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 21 items

tests/unit/test_classifier.py::TestQuadrantClassification::test_create_valid PASSED [  4%]
tests/unit/test_classifier.py::TestQuadrantClassification::test_invalid_quadrant FAILED [  9%]
tests/unit/test_classifier.py::TestQuadrantClassification::test_confidence_bounds PASSED [ 14%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_quadrant_constants PASSED [ 19%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_quadrants_list PASSED [ 23%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_cache_key_generation PASSED [ 28%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_classify_important_urgent PASSED [ 33%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_classify_important_not_urgent PASSED [ 38%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_classify_not_important_urgent PASSED [ 42%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_classify_not_important_not_urgent PASSED [ 47%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_classification_is_cached PASSED [ 52%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_openai_failure_uses_fallback PASSED [ 57%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_fallback_classifier_important_urgent FAILED [ 61%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_fallback_classifier_important_not_urgent PASSED [ 66%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_fallback_classifier_not_important_urgent PASSED [ 71%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_fallback_classifier_not_important_not_urgent PASSED [ 76%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_fallback_classifier_default FAILED [ 80%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_redis_unavailable_uses_memory PASSED [ 85%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_sync_classification PASSED [ 90%]
tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_bulk_classify PASSED [ 95%]
tests/unit/test_classifier.py::TestRealWorldTasks::test_real_world_examples PASSED [100%]

=================================== FAILURES ===================================
_______________ TestQuadrantClassification.test_invalid_quadrant _______________

self = <unit.test_classifier.TestQuadrantClassification object at 0x7fe64103dbd0>

    def test_invalid_quadrant(self):
        """Test that invalid quadrant raises validation error"""
>       with pytest.raises(Exception):
             ^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE <class 'Exception'>

tests/unit/test_classifier.py:37: Failed
__ TestEisenhowerQuadrantClassifier.test_fallback_classifier_important_urgent __

self = <unit.test_classifier.TestEisenhowerQuadrantClassifier object at 0x7fe640e3c320>
classifier = <backend.ai.classifier.EisenhowerQuadrantClassifier object at 0x7fe6402708d0>

    def test_fallback_classifier_important_urgent(self, classifier):
        """Test fallback classifier with important urgent keywords"""
        result = classifier._classify_with_keywords(
            "Fix critical server outage immediately", "Emergency: Production is down"
        )
        assert result.quadrant == IMPORTANT_URGENT
        assert result.confidence > 0.5
>       assert (
            "emergency" in result.keywords
            or "critical" in result.keywords
            or "outage" in result.keywords
        )
E       AssertionError: assert ('emergency' in ['important_urgent'] or 'critical' in ['important_urgent'] or 'outage' in ['important_urgent'])
E        +  where ['important_urgent'] = QuadrantClassification(quadrant='important_urgent', confidence=0.7, reasoning='Keyword-based classification: important_urgent', keywords=['important_urgent']).keywords
E        +  and   ['important_urgent'] = QuadrantClassification(quadrant='important_urgent', confidence=0.7, reasoning='Keyword-based classification: important_urgent', keywords=['important_urgent']).keywords
E        +  and   ['important_urgent'] = QuadrantClassification(quadrant='important_urgent', confidence=0.7, reasoning='Keyword-based classification: important_urgent', keywords=['important_urgent']).keywords

tests/unit/test_classifier.py:251: AssertionError
______ TestEisenhowerQuadrantClassifier.test_fallback_classifier_default _______

self = <unit.test_classifier.TestEisenhowerQuadrantClassifier object at 0x7fe64205ab60>
classifier = <backend.ai.classifier.EisenhowerQuadrantClassifier object at 0x7fe6403c23f0>

    def test_fallback_classifier_default(self, classifier):
        """Test fallback classifier default when no keywords match"""
        result = classifier._classify_with_keywords(
            "Task without clear keywords", "Ambiguous description"
        )
>       assert result.quadrant == NOT_IMPORTANT_NOT_URGENT
E       AssertionError: assert 'not_important_urgent' == 'not_important_not_urgent'
E         
E         - not_important_not_urgent
E         ?               ----
E         + not_important_urgent

tests/unit/test_classifier.py:287: AssertionError
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.14.3-final-0 ________________

Name                              Stmts   Miss  Cover
-----------------------------------------------------
backend/__init__.py                   0      0   100%
backend/ai/__init__.py                2      0   100%
backend/ai/classifier.py            118     10    92%
backend/config.py                    14      0   100%
backend/database/__init__.py         13     13     0%
backend/main.py                      12     12     0%
backend/models/__init__.py            7      7     0%
backend/models/task.py               32     32     0%
backend/models/task_chain.py         16     16     0%
backend/models/time_block.py         20     20     0%
backend/models/timeline.py           15     15     0%
backend/models/timeline_task.py      15     15     0%
backend/models/user.py               14     14     0%
-----------------------------------------------------
TOTAL                               278    154    45%
Coverage HTML written to dir htmlcov
=========================== short test summary info ============================
FAILED tests/unit/test_classifier.py::TestQuadrantClassification::test_invalid_quadrant - Failed: DID NOT RAISE <class 'Exception'>
FAILED tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_fallback_classifier_important_urgent - AssertionError: assert ('emergency' in ['important_urgent'] or 'critical' in ['important_urgent'] or 'outage' in ['important_urgent'])
 +  where ['important_urgent'] = QuadrantClassification(quadrant='important_urgent', confidence=0.7, reasoning='Keyword-based classification: important_urgent', keywords=['important_urgent']).keywords
 +  and   ['important_urgent'] = QuadrantClassification(quadrant='important_urgent', confidence=0.7, reasoning='Keyword-based classification: important_urgent', keywords=['important_urgent']).keywords
 +  and   ['important_urgent'] = QuadrantClassification(quadrant='important_urgent', confidence=0.7, reasoning='Keyword-based classification: important_urgent', keywords=['important_urgent']).keywords
FAILED tests/unit/test_classifier.py::TestEisenhowerQuadrantClassifier::test_fallback_classifier_default - AssertionError: assert 'not_important_urgent' == 'not_important_not_urgent'
  
  - not_important_not_urgent
  ?               ----
  + not_important_urgent
========================= 3 failed, 18 passed in 3.21s =========================
[0m
Good progress! 18/21 tests pass. There are 3 issues to fix:

1. `test_invalid_quadrant` expects strict validation of the quadrant field
2. `test_fallback_classifier_important_urgent` expects actual keywords, not quadrant names
3. `test_fallback_classifier_default` expects correct default behavior

Let me fix these issues in the classifier:
[0m← [0mEdit backend/ai/classifier.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/ai/classifier.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/ai/classifier.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/ai/classifier.py
@@ -7,16 +7,14 @@
 - not_important_urgent: Urgent but not important (can delegate)
 - not_important_not_urgent: Neither important nor urgent (eliminate/decrease)
 """
 
-import json
-import logging
-from typing import Optional, Dict, Any
+from typing import Optional, Dict, Any, Literal
 from datetime import datetime
 
 import redis
 from openai import AsyncOpenAI
-from pydantic import BaseModel, Field
+from pydantic import BaseModel, Field, field_validator
 
 from backend.config import settings
 
 logger = logging.getLogger(__name__)
@@ -30,9 +28,14 @@
 
 class QuadrantClassification(BaseModel):
     """Structured output from GPT-4 for task classification"""
 
-    quadrant: str = Field(
+    quadrant: Literal[
+        "important_urgent",
+        "important_not_urgent",
+        "not_important_urgent",
+        "not_important_not_urgent",
+    ] = Field(
         ...,
         description="One of: important_urgent, important_not_urgent, not_important_urgent, not_important_not_urgent",
     )
     confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")

[0m
I need to fix the LSP errors. Let me add back the missing imports and fix the type issues:
[0m← [0mEdit backend/ai/classifier.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/ai/classifier.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/ai/classifier.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend/ai/classifier.py
@@ -7,8 +7,10 @@
 - not_important_urgent: Urgent but not important (can delegate)
 - not_important_not_urgent: Neither important nor urgent (eliminate/decrease)
 """
 
+import json
+import logging
 from typing import Optional, Dict, Any, Literal
 from datetime import datetime
 
 import redis

[0m
```

## TASKS.md After Iteration

```markdown
# tact-ai
**Mission:** An AI-based scheduler that is based off of the eisenhower matrix, organizing tasks, task chains and timelines....

## Phase 1: Planning & Setup
- [x] **Finalize tech stack**: Document decision to use FastAPI backend, React frontend, PostgreSQL, Redis, OpenAI API, and ortools in `docs/architecture.md` with component diagram.
- [x] **Initialize monorepo structure**: Create directories `backend/`, `frontend/`, `shared/`, `docker/`, `tests/`. Generate `requirements.txt`, `pyproject.toml`, `docker-compose.yml`, and `.env.example` with all necessary config placeholders.
- [x] **Configure CI/CD pipelines**: Set up GitHub Actions for linting (black, ruff), type checking (mypy), and tests (pytest). Add pre-commit hooks for code formatting. Create build pipelines for Docker images.
- [x] **Design and implement database schema**: Write Alembic migrations for tables: `users`, `tasks`, `task_chains`, `timelines`, `time_blocks`. Create ER diagram in `docs/database.md`.

## Phase 2: Core AI & Scheduling Engine
- [ ] **Build Eisenhower quadrant classifier**: Implement `backend/ai/classifier.py` using OpenAI GPT-4 with structured prompts. Add Redis caching layer and a fallback keyword-based classifier. Write unit tests with example tasks.
- [ ] **Develop task chain resolver**: Create `backend/scheduler/dependency.py` to handle task chains via topological sort, detect cycles, and compute earliest start times. Include test cases for complex chains.
- [ ] **Implement AI scheduling engine**: Use ortools CP-SAT to generate daily/weekly schedules respecting deadlines, dependencies, priorities, and working hours. Output JSON with start/end timestamps. Add benchmark script.
- [ ] **Create conflict detection module**: Build `backend/scheduler/conflicts.py` to identify overlapping tasks, resource over-allocation, and missed deadlines. Return actionable conflict reports for frontend display.

## Phase 3: User Interface & Task Management
- [ ] **Construct React component library**: Build `frontend/components/` with `TaskCard`, `QuadrantBoard` (drag-and-drop), `TimelineView` (d3.js Gantt), and `ChainVisualizer`. Apply Tailwind CSS styling.
- [ ] **Implement full task CRUD**: Create FastAPI REST endpoints for tasks (with AI classification on create). Build React forms for natural language input and manual editing. Add API integration in frontend.
- [ ] **Add authentication & user isolation**: Integrate JWT auth with OAuth2 password flow in FastAPI. Secure all endpoints. Build login/register pages. Ensure tasks are scoped to user ID.
- [ ] **Develop real-time updates (optional)**: Add FastAPI WebSocket endpoint and React Socket.IO client to push schedule changes and conflict alerts to connected users.

## Phase 4: Testing, Deployment & Operations
- [ ] **Write comprehensive test suite**: Achieve >80% coverage for classifier, dependency resolver, scheduler, and conflict detection. Include integration tests for main API routes. Set up Codecov reporting.
- [ ] **Prepare production deployment**: Write optimized Dockerfiles for backend (Gunicorn + Uvicorn workers) and frontend (Nginx static build). Configure Nginx reverse proxy, PostgreSQL, and Redis in `docker-compose.prod.yml`. Document in `docs/deployment.md`.
- [ ] **Perform load testing and optimization**: Use k6 to simulate 100+ concurrent users. Profile scheduler performance, add database indexing, implement pagination on task lists, and tune Redis caching. Record results.
- [ ] **Set up monitoring and observability**: Integrate Sentry for errors, expose Prometheus metrics (API latency, scheduling duration). Create Grafana dashboard and alert rules. Write runbooks in `docs/operations.md`.
```

**Completed at:** Thu Mar 12 05:34:48 PM EDT 2026
