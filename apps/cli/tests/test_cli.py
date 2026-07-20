"""Tests for Astra CLI"""

import os
import sys

import pytest
from click.testing import CliRunner

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from astra_cli.config import (
    get_config_value,
    get_default_config,
    set_config_value,
)
from astra_cli.main import cli


class TestCLI:
    """Tests for main CLI entry point"""

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "astra" in result.output.lower()

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Astra OS CLI" in result.output

    def test_config_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0


class TestConfig:
    """Tests for configuration management"""

    def test_default_config(self):
        config = get_default_config()
        assert "api" in config
        assert "auth" in config
        assert "defaults" in config
        assert "monitoring" in config

        assert config["api"]["url"] == "https://api.astra-os.io"
        assert config["auth"]["token"] is None

    def test_get_config_value(self):
        config = get_default_config()
        assert get_config_value("api.url", config) == "https://api.astra-os.io"
        assert get_config_value("auth.token", config) is None
        assert get_config_value("defaults.output_format", config) == "table"
        assert get_config_value("nonexistent.key", config) is None

    def test_set_config_value(self):
        config = get_default_config()
        set_config_value("api.url", "https://custom.api.com", config)
        assert config["api"]["url"] == "https://custom.api.com"

        set_config_value("new.nested.key", "value", config)
        assert config["new"]["nested"]["key"] == "value"

    def test_yaml_serialization(self):
        config = get_default_config()
        import yaml

        yaml_str = yaml.dump(config)
        loaded = yaml.safe_load(yaml_str)
        assert loaded["api"]["url"] == "https://api.astra-os.io"


class TestAuthCommands:
    """Tests for authentication commands"""

    def test_login_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auth", "login", "--help"])
        assert result.exit_code == 0
        assert "email" in result.output.lower()

    def test_logout_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auth", "logout", "--help"])
        assert result.exit_code == 0

    def test_whoami_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auth", "whoami", "--help"])
        assert result.exit_code == 0

    def test_status_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auth", "status", "--help"])
        assert result.exit_code == 0


class TestAgentCommands:
    """Tests for agent commands"""

    def test_agents_list_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["agents", "list", "--help"])
        assert result.exit_code == 0
        assert "limit" in result.output.lower()

    def test_agents_get_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["agents", "get", "--help"])
        assert result.exit_code == 0

    def test_agents_create_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["agents", "create", "--help"])
        assert result.exit_code == 0
        assert "name" in result.output.lower()
        assert "type" in result.output.lower()

    def test_agents_run_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["agents", "run", "--help"])
        assert result.exit_code == 0
        assert "async" in result.output.lower()

    def test_agents_status_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["agents", "status", "--help"])
        assert result.exit_code == 0

    def test_agents_logs_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["agents", "logs", "--help"])
        assert result.exit_code == 0

    def test_agents_delete_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["agents", "delete", "--help"])
        assert result.exit_code == 0


class TestWorkflowCommands:
    """Tests for workflow commands"""

    def test_workflows_list_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["workflows", "list", "--help"])
        assert result.exit_code == 0

    def test_workflows_get_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["workflows", "get", "--help"])
        assert result.exit_code == 0

    def test_workflows_create_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["workflows", "create", "--help"])
        assert result.exit_code == 0

    def test_workflows_run_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["workflows", "run", "--help"])
        assert result.exit_code == 0

    def test_workflows_executions_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["workflows", "executions", "--help"])
        assert result.exit_code == 0

    def test_workflows_delete_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["workflows", "delete", "--help"])
        assert result.exit_code == 0


class TestMonitoringCommands:
    """Tests for monitoring commands"""

    def test_monitor_health_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["monitor", "health", "--help"])
        assert result.exit_code == 0

    def test_monitor_metrics_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["monitor", "metrics", "--help"])
        assert result.exit_code == 0

    def test_monitor_alerts_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["monitor", "alerts", "--help"])
        assert result.exit_code == 0

    def test_monitor_slo_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["monitor", "slo", "--help"])
        assert result.exit_code == 0

    def test_monitor_trace_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["monitor", "trace", "--help"])
        assert result.exit_code == 0

    def test_monitor_circuit_breakers_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["monitor", "circuit-breakers", "--help"])
        assert result.exit_code == 0

    def test_monitor_dlq_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["monitor", "dlq", "--help"])
        assert result.exit_code == 0


class TestCostCommands:
    """Tests for cost commands"""

    def test_cost_report_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["costs", "report", "--help"])
        assert result.exit_code == 0

    def test_cost_forecast_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["costs", "forecast", "--help"])
        assert result.exit_code == 0

    def test_cost_breakdown_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["costs", "breakdown", "--help"])
        assert result.exit_code == 0

    def test_cost_budget_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["costs", "budget", "--help"])
        assert result.exit_code == 0


class TestSchemaCommands:
    """Tests for schema commands"""

    def test_schemas_list_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schemas", "list", "--help"])
        assert result.exit_code == 0

    def test_schemas_get_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schemas", "get", "--help"])
        assert result.exit_code == 0

    def test_schemas_validate_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schemas", "validate", "--help"])
        assert result.exit_code == 0

    def test_schemas_example_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schemas", "example", "--help"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
