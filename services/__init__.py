"""Services package - lazy-loading compatibility layer for astra_agent_orchestrator."""

import sys
import types
from types import ModuleType


class _ServicesModule(ModuleType):
    """Lazy-loading module that delegates to astra_agent_orchestrator."""
    
    _loaded = False
    _delegated_module = None
    
    def __init__(self, name):
        super().__init__(name)
        self.__path__ = []  # Makes it a package
    
    def _ensure_loaded(self):
        if not self._loaded:
            try:
                import astra_agent_orchestrator as _delegated
                self._delegated_module = _delegated
                
                # Import all public attributes
                for attr in dir(_delegated):
                    if not attr.startswith('_'):
                        setattr(self, attr, getattr(_delegated, attr))
                
                # Import submodules
                from astra_agent_orchestrator import (
                    agent, comms, events, hierarchy, memory, router, resilience, tools
                )
                self.agent = agent
                self.comms = comms
                self.events = events
                self.hierarchy = hierarchy
                self.memory = memory
                self.router = router
                self.resilience = resilience
                self.tools = tools
                
                # Try to import agents
                try:
                    from astra_agent_orchestrator import agents
                    self.agents = agents
                except ImportError:
                    pass
                    
                self._loaded = True
            except ImportError:
                # Fallback for development
                pass
    
    def __getattr__(self, name):
        self._ensure_loaded()
        if self._delegated_module and hasattr(self._delegated_module, name):
            return getattr(self._delegated_module, name)
        raise AttributeError(f"module 'services' has no attribute '{name}'")
    
    def __dir__(self):
        self._ensure_loaded()
        if self._delegated_module:
            return dir(self._delegated_module)
        return super().__dir__()


# Replace this module with our lazy loader
sys.modules[__name__] = _ServicesModule(__name__)


class _LazySubModule(ModuleType):
    """Lazy-loading submodule that delegates to astra_agent_orchestrator submodule."""
    
    def __init__(self, name, target_name):
        super().__init__(name)
        self._target_name = target_name
        self._target = None
    
    def _ensure_loaded(self):
        if self._target is None:
            import astra_agent_orchestrator
            self._target = getattr(astra_agent_orchestrator, self._target_name)
            # Copy all public attributes
            for attr in dir(self._target):
                if not attr.startswith('_'):
                    setattr(self, attr, getattr(self._target, attr))
    
    def __getattr__(self, name):
        self._ensure_loaded()
        if self._target and hasattr(self._target, name):
            return getattr(self._target, name)
        raise AttributeError(f"module '{self.__name__}' has no attribute '{name}'")
    
    def __dir__(self):
        self._ensure_loaded()
        if self._target:
            return dir(self._target)
        return super().__dir__()


# Create lazy submodules
for _submod, _target in [
    ('agent', 'agent'),
    ('agents', 'agents'),
    ('comms', 'comms'),
    ('events', 'events'),
    ('hierarchy', 'hierarchy'),
    ('memory', 'memory'),
    ('router', 'router'),
    ('resilience', 'resilience'),
    ('tools', 'tools'),
    ('governance', 'governance'),
    ('telemetry', 'telemetry'),
    ('tests', 'tests'),
    ('base', 'agents.base'),
    ('dlq', 'dlq'),
    ('metrics', 'metrics'),
    ('supervisor', 'supervisor'),
]:
    sys.modules[f'services.{_submod}'] = _LazySubModule(f'services.{_submod}', _target)

# agent_orchestrator is the main package - alias it directly
import astra_agent_orchestrator
sys.modules['services.agent_orchestrator'] = astra_agent_orchestrator

# Also ensure agent_orchestrator.tests is available
tests_module = types.ModuleType('services.agent_orchestrator.tests')
# Import all test modules into the tests namespace
try:
    from astra_agent_orchestrator.tests import (
        test_agent,
        test_agent_governance,
        test_agent_rag,
        test_agent_semantic_conventions,
        test_budget_pacing,
        test_circuit_breaker,
        test_concrete_agents,
        test_creative_use_cases,
        test_dlq,
        test_events,
        test_governance,
        test_hierarchy,
        test_integration,
        test_lifecycle_use_cases,
        test_m2_integration,
        test_metrics,
        test_router,
        test_supervisor,
        test_telemetry,
        test_tools,
    )
    # Export them
    tests_module.test_agent = test_agent
    tests_module.test_agent_governance = test_agent_governance
    tests_module.test_agent_rag = test_agent_rag
    tests_module.test_agent_semantic_conventions = test_agent_semantic_conventions
    tests_module.test_budget_pacing = test_budget_pacing
    tests_module.test_circuit_breaker = test_circuit_breaker
    tests_module.test_concrete_agents = test_concrete_agents
    tests_module.test_creative_use_cases = test_creative_use_cases
    tests_module.test_dlq = test_dlq
    tests_module.test_events = test_events
    tests_module.test_governance = test_governance
    tests_module.test_hierarchy = test_hierarchy
    tests_module.test_integration = test_integration
    tests_module.test_lifecycle_use_cases = test_lifecycle_use_cases
    tests_module.test_m2_integration = test_m2_integration
    tests_module.test_metrics = test_metrics
    tests_module.test_router = test_router
    tests_module.test_supervisor = test_supervisor
    tests_module.test_telemetry = test_telemetry
    tests_module.test_tools = test_tools
except ImportError:
    # Fallback - create empty module
    pass

sys.modules['services.agent_orchestrator.tests'] = tests_module

# Also ensure agent_orchestrator is available as attribute of services
_ServicesModule.agent_orchestrator = astra_agent_orchestrator
