"""Test configuration for the backend test suite.

Sets up sys.path and pre-mocks modules that would cause circular import
issues when unit-testing lightweight config/registry code in isolation.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Make 'app' and 'medrix_flow' importable from any working directory
sys.path.insert(0, str(Path(__file__).parent.parent))

# Break the circular import chain that exists in production code:
#   medrix_flow.subagents.__init__
#     -> .executor (SubagentExecutor, SubagentResult)
#       -> medrix_flow.agents.thread_state
#         -> medrix_flow.agents.__init__
#           -> lead_agent.agent
#             -> subagent_limit_middleware
#               -> medrix_flow.subagents.executor  <-- circular!
#
# By injecting a mock for medrix_flow.subagents.executor *before* any test module
# triggers the import, __init__.py's "from .executor import ..." succeeds
# immediately without running the real executor module.
_executor_mock = MagicMock()
_executor_mock.SubagentExecutor = MagicMock
_executor_mock.SubagentResult = MagicMock
_executor_mock.SubagentStatus = MagicMock
_executor_mock.MAX_CONCURRENT_SUBAGENTS = 3
_executor_mock.get_background_task_result = MagicMock()

sys.modules["medrix_flow.subagents.executor"] = _executor_mock
