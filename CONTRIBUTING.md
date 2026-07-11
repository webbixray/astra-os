# Contributing to Astra OS

Thank you for your interest in contributing to Astra OS! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Node.js >= 20.0.0
- pnpm >= 9.0.0
- Python >= 3.12
- Docker (recommended)

### Setup

1. Fork the repository on GitHub

2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/astra-os.git
   cd astra-os
   ```

3. Run the setup script:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

4. Create a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

## Development Workflow

### Making Changes

1. **Create a feature branch** from `main`
2. **Make your changes** following the code style guidelines
3. **Write tests** for new functionality
4. **Run tests** to ensure nothing is broken
5. **Commit your changes** with a clear message
6. **Push to your fork** and create a Pull Request

### Running Tests

```bash
# Run all tests
make test

# Run API tests only
make test-api

# Run Web tests only
make test-web

# Run E2E tests
make test-e2e
```

### Code Quality

```bash
# Lint all code
make lint

# Format all code
make format

# Type check
make typecheck
```

## Code Style

### Python (API)

- **Formatter**: Ruff
- **Linter**: Ruff
- **Type Checker**: mypy
- **Line Length**: 100 characters max

```bash
cd apps/api
ruff format .
ruff check .
mypy . --ignore-missing-imports
```

### TypeScript (Web)

- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checker**: TypeScript

```bash
pnpm format
pnpm lint
pnpm typecheck
```

### General Guidelines

- Write clear, descriptive comments
- Keep functions small and focused
- Use meaningful variable and function names
- Follow the existing code patterns
- Add tests for new features

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat(campaigns): add budget tracking
fix(auth): resolve token refresh issue
docs(readme): update installation guide
test(api): add tests for user endpoints
```

## Pull Request Process

### Before Submitting

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass** (`make test`)
4. **Lint your code** (`make lint`)
5. **Update the changelog** if applicable

### PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Checklist

- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. All PRs require at least one review
2. CI must pass before merging
3. Address review feedback
4. Squash and merge when approved

## Reporting Issues

### Bug Reports

Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
- Screenshots (if applicable)

### Feature Requests

Include:
- Problem description
- Proposed solution
- Alternatives considered
- Additional context

## Questions?

- Open a [Discussion](https://github.com/webbixray/astra-os/discussions)
- Check the [Documentation](docs/)

Thank you for contributing to Astra OS!
