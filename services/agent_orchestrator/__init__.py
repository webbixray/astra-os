"""Agent Orchestrator submodule for services package - redirects to astra_agent_orchestrator."""

from astra_agent_orchestrator import *  # noqa: F403,F401
from astra_agent_orchestrator.agent import *  # noqa: F403,F401
from astra_agent_orchestrator.comms import *  # noqa: F403,F401
from astra_agent_orchestrator.events import *  # noqa: F403,F401
from astra_agent_orchestrator.hierarchy import *  # noqa: F403,F401
from astra_agent_orchestrator.memory import *  # noqa: F403,F401
from astra_agent_orchestrator.router import *  # noqa: F403,F401
from astra_agent_orchestrator.resilience import *  # noqa: F403,F401
from astra_agent_orchestrator.tools import *  # noqa: F403,F401
from astra_agent_orchestrator.agents import *  # noqa: F403,F401

# Expose submodules
import astra_agent_orchestrator.agent as agent
import astra_agent_orchestrator.comms as comms
import astra_agent_orchestrator.events as events
import astra_agent_orchestrator.hierarchy as hierarchy
import astra_agent_orchestrator.memory as memory
import astra_agent_orchestrator.router as router
import astra_agent_orchestrator.resilience as resilience
import astra_agent_orchestrator.tools as tools
import astra_agent_orchestrator.agents as agents