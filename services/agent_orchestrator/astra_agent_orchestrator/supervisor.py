"""Process-level supervisor for Agent Orchestrator with bounded restart logic."""

import asyncio
import os
import signal
import sys
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExitReason(Enum):
    """Reason for supervisor exit."""

    CLEAN = "clean"
    DETERMINISTIC_FAILURE = "deterministic_failure"
    CRASH_LOOP = "crash_loop"
    EXCEPTION = "exception"
    SIGNAL = "signal"
    DISABLED = "disabled"


@dataclass
class SupervisorConfig:
    """Configuration for the supervisor."""

    max_restarts: int = 10
    restart_window_seconds: int = 600
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    disable_env_var: str = "HERMES_ORCHESTRATOR_NO_SUPERVISE"
    enable_signal_handling: bool = True


@dataclass
class Supervisor:
    """In-process supervisor with bounded auto-restart and crash-loop protection.
    
    Rules:
    - Clean exit (SystemExit(0), KeyboardInterrupt/SIGINT) -> stop, no restart
    - Non-zero SystemExit -> deterministic failure, no restart
    - Any other exception -> restart with exponential backoff
    - Crash-loop guard: max_restarts within restart_window_seconds -> exit 1
    - Escape hatch: disable_env_var or supervise=False bypasses supervisor
    """

    config: SupervisorConfig
    _orchestrator: Any = field(default=None, repr=False)
    _supervise: bool = field(default=True, repr=False)
    _restart_count: int = field(default=0, repr=False)
    _restart_timestamps: list[float] = field(default_factory=list, repr=False)
    _backoff: float = field(default=0.0, repr=False)
    _shutdown_requested: bool = field(default=False, repr=False)

    def __post_init__(self):
        if os.getenv(self.config.disable_env_var) == "1":
            self._supervise = False
        self._backoff = self.config.base_backoff_seconds

    def set_orchestrator(self, orchestrator: Any) -> "Supervisor":
        """Set the orchestrator instance to supervise."""
        self._orchestrator = orchestrator
        return self

    def disable(self) -> "Supervisor":
        """Disable supervisor (for testing or external management)."""
        self._supervise = False
        return self

    async def run(self, coro_factory: Callable[[], Awaitable[Any]] | None = None) -> Any:
        """Run the orchestrator with supervision.
        
        Args:
            coro_factory: Optional async callable to run. If not provided,
                         uses self._orchestrator.run()
        
        Returns:
            Result from the successful run, or None on clean exit.
        
        """
        if not self._supervise:
            return await self._run_once(coro_factory)

        self._setup_signal_handlers()

        while True:
            try:
                return await self._run_once(coro_factory)
            except SystemExit as e:
                return await self._handle_system_exit(e)
            except KeyboardInterrupt:
                return await self._handle_keyboard_interrupt()
            except Exception as e:
                await self._handle_exception(e)

    async def _run_once(self, coro_factory: Callable[[], Awaitable[Any]] | None) -> Any:
        """Run the orchestrator once."""
        if coro_factory:
            return await coro_factory()
        if self._orchestrator:
            return await self._orchestrator.run()
        raise RuntimeError("No orchestrator or coroutine factory provided")

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        if not self.config.enable_signal_handling:
            return

        loop = asyncio.get_event_loop()

        def handle_signal(sig: int, frame: Any) -> None:
            if not self._shutdown_requested:
                self._shutdown_requested = True
                # Schedule shutdown
                asyncio.create_task(self._orchestrator.shutdown() if self._orchestrator else asyncio.sleep(0))

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, handle_signal, sig, None)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                pass

    async def _handle_system_exit(self, exc: SystemExit) -> Any:
        """Handle SystemExit - clean exit (0) or deterministic failure (non-zero)."""
        if exc.code == 0:
            return None  # Clean exit
        # Non-zero = deterministic failure, don't restart
        raise

    async def _handle_keyboard_interrupt(self) -> Any:
        """Handle KeyboardInterrupt (SIGINT) as clean exit."""
        return None

    async def _handle_exception(self, error: Exception) -> None:
        """Handle unhandled exception - trigger restart with backoff."""
        now = time.monotonic()

        # Clean old timestamps outside the window
        self._restart_timestamps = [
            ts for ts in self._restart_timestamps
            if now - ts < self.config.restart_window_seconds
        ]

        self._restart_timestamps.append(now)
        self._restart_count += 1

        # Crash-loop guard
        if len(self._restart_timestamps) > self.config.max_restarts:
            print(
                f"Crash-loop detected: {len(self._restart_timestamps)} restarts "
                f"within {self.config.restart_window_seconds}s. Exiting.",
                file=sys.stderr
            )
            sys.exit(1)

        # Sleep in small slices for signal responsiveness
        remaining = self._backoff
        while remaining > 0 and not self._shutdown_requested:
            slice_ms = min(0.25, remaining)
            await asyncio.sleep(slice_ms)
            remaining -= slice_ms

        # Increase backoff for next crash
        self._backoff = min(
            self._backoff * self.config.backoff_multiplier,
            self.config.max_backoff_seconds
        )
