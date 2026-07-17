# Contributing to Astra OS

Thank you for your interest in contributing to Astra OS! This document provides guidelines for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Pull Request Process](#pull-request-process)
5. [Code Style](#code-style)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Security](#security)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+ (for web dashboard)
- pnpm 9+ (for monorepo management)
- Docker & Docker Compose
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/astra-os/astra-os.git
cd astra-os

# Install Python dependencies
pip install -e ".[dev]"

# Install Node.js dependencies (uses pnpm workspaces)
pnpm install

# Start local infrastructure
docker compose -f docker/dev/docker-compose.yml up -d

# Run database migrations
alembic upgrade head

# Run tests
pytest
```

## Development Workflow

### Branch Naming

| Type | Prefix | Example |
|------|--------|---------|
| Feature | `feat/` | `feat/add-agent-scheduling` |
| Bug Fix | `fix/` | `fix/circuit-breaker-timeout` |
| Documentation | `docs/` | `docs/update-api-docs` |
| Refactor | `refactor/` | `refactor/agent-registry` |
| Chore | `chore/` | `chore/update-dependencies` |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert`

Examples:
```
feat(agents): add scheduling support for CEO agent
fix(api): handle rate limit exceeded gracefully
docs: update CLI installation instructions
refactor(shadow-mode): simplify session creation logic
```

### Pull Request Process

1. **Create a feature branch** from `main`
2. **Write tests** for new functionality
3. **Ensure all tests pass** locally
4. **Run pre-commit hooks**: `pre-commit run --all-files`
5. **Submit PR** with clear description and linked issue
6. **Address review feedback** promptly
7. **Squash and merge** after approval

### PR Requirements

- [ ] All CI checks pass (tests, linting, security)
- [ ] Code coverage maintained or improved
- [ ] Documentation updated for user-facing changes
- [ ] CHANGELOG.md entry added
- [ ] No merge conflicts with `main`
- [ ] At least 1 approval from code owners

## Code Style

### Python

- **Formatter**: Ruff (configured in `pyproject.toml`)
- **Type Checker**: mypy (strict mode)
- **Import Sorting**: Ruff (isort compatible)
- **Line Length**: 100 characters
- **Target Version**: Python 3.11

```bash
# Format code
ruff format .

# Lint code
ruff check . --fix

# Type check
mypy .
```

### TypeScript/JavaScript

- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checker**: TypeScript (strict mode)

```bash
# Format code
pnpm format

# Lint code
pnpm lint

# Type check
pnpm typecheck
```

### Docker

- Use multi-stage builds
- Run as non-root user
- Use distroless/base images where possible
- Pin base image digests
- Scan with hadolint

## Testing

### Python Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agents.py

# Run with coverage
pytest --cov=apps/api --cov=services --cov-report=html

# Run integration tests
pytest tests/integration -v
```

### Test Categories

| Marker | Description | Command |
|--------|-------------|---------|
| `unit` | Fast, isolated tests | `pytest -m unit` |
| `integration` | Tests with external deps | `pytest -m integration` |
| `e2e` | Full end-to-end tests | `pytest -m e2e` |
| `slow` | Tests > 10 seconds | `pytest -m slow` |

### Test Standards

- **Unit tests**: Mock all external dependencies
- **Integration tests**: Use testcontainers for DB/Redis
- **Naming**: `test_<function>_<scenario>_<expected>`
- **Assertions**: Use `assert` with clear messages
- **Fixtures**: Shared fixtures in `conftest.py`

## Documentation

### Types

- **API Docs**: OpenAPI/Swagger (auto-generated from FastAPI)
- **Architecture**: ADRs in `docs/adr/`
- **User Guides**: `docs/user-guide/`
- **Developer Docs**: `docs/developer/`
- **CLI Help**: Built into `astra --help`

### Updating Docs

1. Update relevant `.md` files in `docs/`
2. Update docstrings for public APIs
3. Run `pnpm docs:build` to verify
4. Include screenshots for UI changes

## Security

### Reporting Vulnerabilities

See [SECURITY.md](SECURITY.md) for responsible disclosure process.

### Security Practices

- Never commit secrets, API keys, or credentials
- Use `.env.example` for configuration templates
- Run `trufflehog` and `bandit` before committing
- Keep dependencies updated (Dependabot/Renovate)
- Use `sealed-secrets` for Kubernetes secrets

### Pre-commit Security Checks

```bash
# Run security checks manually
bandit -r apps/api apps/cli services
trufflehog --fail --no-verification .
```

## Release Process

1. Version bump in `pyproject.toml` and `package.json`
2. Update `CHANGELOG.md`
3. Create release PR
4. Merge to `main` triggers CI/CD
5. GitHub Actions builds and publishes artifacts
6. Create GitHub Release with notes

---

**Questions?** Open a discussion or reach out to the maintainers.

**Thank you for contributing!** 🚀