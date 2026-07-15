"""Agent Orchestrator Tests Package."""
import sys
import os
import types

# Make this a proper namespace package
__path__ = [os.path.dirname(__file__)]

# Ensure parent module has tests attribute
parent = sys.modules.get('services.agent_orchestrator')
if parent is not None:
    parent.tests = sys.modules['services.agent_orchestrator.tests']

# Import and expose conftest
import importlib.util
spec = importlib.util.spec_from_file_location(
    'services.agent_orchestrator.tests.conftest',
    os.path.join(os.path.dirname(__file__), 'conftest.py')
)
conftest = importlib.util.module_from_spec(spec)
sys.modules['services.agent_orchestrator.tests.conftest'] = conftest
spec.loader.exec_module(conftest)

# Also register in sys.modules with full path
sys.modules['services.agent_orchestrator.tests.conftest'] = conftest
