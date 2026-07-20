"""Tests for the supervisor module."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from astra_agent_orchestrator.supervisor import (
    Supervisor,
    SupervisorConfig,
)


class TestSupervisor:
    """Tests for Supervisor class."""

    @pytest.fixture
    def config(self):
        return SupervisorConfig(
            max_restarts=3,
            restart_window_seconds=60,
            base_backoff_seconds=0.1,
            max_backoff_seconds=1.0,
            backoff_multiplier=2.0,
        )

    @pytest.mark.asyncio
    async def test_clean_exit_no_restart(self, config):
        """SystemExit(0) should stop supervisor without restart."""
        supervisor = Supervisor(config)
        mock_run = AsyncMock(side_effect=SystemExit(0))

        await supervisor.run(mock_run)

        assert mock_run.call_count == 1
        assert supervisor._restart_count == 0

    @pytest.mark.asyncio
    async def test_nonzero_systemexit_no_restart(self, config):
        """SystemExit(non-zero) = deterministic failure, no restart."""
        supervisor = Supervisor(config)
        mock_run = AsyncMock(side_effect=SystemExit(1))

        with pytest.raises(SystemExit) as exc:
            await supervisor.run(mock_run)

        assert exc.value.code == 1
        assert mock_run.call_count == 1

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_clean_exit(self, config):
        """KeyboardInterrupt should exit cleanly without restart."""
        supervisor = Supervisor(config)
        mock_run = AsyncMock(side_effect=KeyboardInterrupt())

        await supervisor.run(mock_run)

        assert mock_run.call_count == 1

    @pytest.mark.asyncio
    async def test_unhandled_exception_triggers_restart(self, config):
        """Any other exception triggers restart with exponential backoff."""
        supervisor = Supervisor(config)
        call_count = 0

        async def flaky_run():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("transient failure")
            return "success"

        result = await supervisor.run(flaky_run)

        assert result == "success"
        assert call_count == 3
        assert supervisor._restart_count == 2

    @pytest.mark.asyncio
    async def test_crash_loop_guard_exits_after_max_restarts(self, config):
        """More than max_restarts within window -> exit 1."""
        config.max_restarts = 2
        config.restart_window_seconds = 300
        supervisor = Supervisor(config)

        async def always_fails():
            raise RuntimeError("permanent failure")

        with pytest.raises(SystemExit) as exc:
            await supervisor.run(always_fails)

        assert exc.value.code == 1
        # max_restarts=2 allows 2 restarts, the 3rd attempt triggers crash-loop guard
        assert supervisor._restart_count == 3

    @pytest.mark.asyncio
    async def test_disable_via_env_var(self, config, monkeypatch):
        """HERMES_ORCHESTRATOR_NO_SUPERVISE=1 disables supervisor."""
        monkeypatch.setenv("HERMES_ORCHESTRATOR_NO_SUPERVISE", "1")
        supervisor = Supervisor(config)
        mock_run = AsyncMock(return_value="done")

        result = await supervisor.run(mock_run)

        assert result == "done"
        assert mock_run.call_count == 1

    @pytest.mark.asyncio
    async def test_backoff_increases_exponentially(self, config):
        """Backoff should increase exponentially up to max."""
        config.base_backoff_seconds = 0.05
        config.max_backoff_seconds = 0.5
        config.backoff_multiplier = 2.0
        supervisor = Supervisor(config)

        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise RuntimeError("fail")
            return "ok"

        with patch("asyncio.sleep") as mock_sleep:
            await supervisor.run(flaky)

        # Verify backoff progression: 0.05, 0.1, 0.2 (capped at 0.5)
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls[0] == pytest.approx(0.05, rel=0.2)
        assert sleep_calls[1] == pytest.approx(0.1, rel=0.2)
        assert sleep_calls[2] == pytest.approx(0.2, rel=0.2)

    @pytest.mark.asyncio
    async def test_sleep_in_small_slices(self, config):
        """Backoff sleep should be in small slices for signal responsiveness."""
        config.base_backoff_seconds = 0.1
        supervisor = Supervisor(config)

        async def fails_twice():
            raise RuntimeError("fail")

        with patch("asyncio.sleep") as mock_sleep:
            try:
                await supervisor.run(fails_twice)
            except SystemExit:
                pass

        # Each sleep should be <= 0.25s
        for call in mock_sleep.call_args_list:
            assert call.args[0] <= 0.25

    @pytest.mark.asyncio
    async def test_restart_window_cleanup(self, config):
        """Old restart timestamps outside window should be cleaned up."""
        config.max_restarts = 2
        config.restart_window_seconds = 1
        supervisor = Supervisor(config)

        async def fail():
            raise RuntimeError("fail")

        # First failure
        with pytest.raises(SystemExit):
            await supervisor.run(fail)

        # Wait for window to expire
        await asyncio.sleep(1.5)

        # Should be able to restart again (old timestamps cleaned)
        with pytest.raises(SystemExit):
            await supervisor.run(fail)

        assert supervisor._restart_count == 2  # Total across both windows

    @pytest.mark.asyncio
    async def test_disable_method(self, config):
        """disable() method should bypass supervisor."""
        supervisor = Supervisor(config).disable()
        mock_run = AsyncMock(return_value="disabled")

        result = await supervisor.run(mock_run)

        assert result == "disabled"
        assert mock_run.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])