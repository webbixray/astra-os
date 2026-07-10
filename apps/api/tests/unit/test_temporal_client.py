from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.infrastructure.temporal.client import TemporalWorkflowClient


class TestInit:
    def test_disabled_when_host_is_localhost(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = "localhost:7233"

            client = TemporalWorkflowClient()

            assert client.enabled is False

    def test_disabled_when_no_host(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = ""

            client = TemporalWorkflowClient()

            assert client.enabled is False

    def test_enabled_with_production_host(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = "temporal.example.com:7233"

            client = TemporalWorkflowClient()

            assert client.enabled is True


class TestGetClient:
    async def test_disabled_returns_none(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = "localhost:7233"

            client = TemporalWorkflowClient()
            result = await client.get_client()

            assert result is None

    async def test_import_error_disables(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = "temporal.example.com:7233"

            client = TemporalWorkflowClient()
            import builtins
            original_import = builtins.__import__
            def fake_import(name, *args, **kwargs):
                if name == "temporalio":
                    raise ImportError("No module temporalio")
                return original_import(name, *args, **kwargs)
            with patch("builtins.__import__", side_effect=fake_import):
                result = await client.get_client()

                assert result is None
                assert client.enabled is False

    async def test_successful_connection(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = "temporal.example.com:7233"

            client = TemporalWorkflowClient()
            mock_conn = MagicMock()
            mock_conn.connect = AsyncMock(return_value=mock_conn)

            mock_module = MagicMock()
            mock_module.Client = mock_conn
            with patch.dict("sys.modules", {"temporalio": mock_module, "temporalio.client": mock_module}):
                result = await client.get_client()

                assert result is not None

    async def test_cached_client_returned(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = "temporal.example.com:7233"

            client = TemporalWorkflowClient()
            mock_conn = MagicMock()
            mock_conn.connect = AsyncMock(return_value=mock_conn)

            with patch.dict("sys.modules", {"temporalio.client": MagicMock()}):
                client._client = mock_conn
                client._imported = True

                result = await client.get_client()

                assert result == mock_conn


class TestExecuteWorkflow:
    async def test_disabled_returns_none(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = "localhost:7233"

            client = TemporalWorkflowClient()
            result = await client.execute_workflow(uuid4(), uuid4(), "test", [], [])

            assert result is None

    async def test_successful_execution(self):
        with patch("app.infrastructure.temporal.client.config") as mock_cfg:
            mock_cfg.temporal_host = "temporal.example.com:7233"

            client = TemporalWorkflowClient()
            mock_client = MagicMock()
            mock_handle = MagicMock()
            mock_handle.result = AsyncMock(return_value={"status": "completed"})
            mock_client.start_workflow = AsyncMock(return_value=mock_handle)
            client._client = mock_client
            client.enabled = True
            client._imported = True

            result = await client.execute_workflow(uuid4(), uuid4(), "test", [], [])

            assert result == {"status": "completed"}
            mock_client.start_workflow.assert_awaited_once()
