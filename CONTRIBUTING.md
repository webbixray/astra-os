# ASTRA OS — Contributing Guide

**Version**: 1.0  
**Welcome!** We're excited you want to contribute to ASTRA OS.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
4. [Pull Request Process](#pull-request-process)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Security](#security)
9. [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming, inclusive environment for everyone. We pledge to:

- **Be respectful** of differing viewpoints and experiences
- **Accept constructive criticism** gracefully
- **Focus on what's best** for the community
- **Show empathy** towards other contributors
- **Zero tolerance** for harassment, discrimination, or toxic behavior

### Enforcement

Violations will be addressed by project maintainers. Consequences may include:
- Warning
- Temporary ban
- Permanent ban

Report violations to: conduct@astra-os.com

---

## Getting Started

### 1. Set Up Development Environment

```bash
# Clone
git clone https://github.com/webbixray/astra-os.git
cd astra-os

# Backend
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_db.py

# Frontend
cd ../web
pnpm install

# Start dev servers
# Terminal 1: Backend
cd apps/api && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd apps/web && pnpm dev
```

### 2. Verify Setup

- API: http://localhost:8000/api/v1/docs
- Frontend: http://localhost:3000
- Health: http://localhost:8000/api/v1/health

### 3. Run Tests

```bash
# Backend
cd apps/api && PYTHONPATH=. pytest tests/ -v

# Frontend
cd apps/web && pnpm test --run
```

---

## How to Contribute

### 1. Find Work

- **Good First Issues**: Labelled `good first issue`
- **Bug Fixes**: Labelled `bug`
- **Features**: Labelled `enhancement`
- **Docs**: Labelled `documentation`

### 2. Create a Branch

```bash
git checkout main
git pull origin main
git checkout -b feat/your-feature-name
# or fix/your-bug-fix
```

### 3. Make Changes

- Write code
- Write tests
- Update documentation
- Follow coding standards

### 3. Run Quality Checks

```bash
# Backend
cd apps/api
PYTHONPATH=. pytest tests/ -v
ruff check . && ruff format .
mypy app/

# Frontend
cd apps/web
pnpm test --run
pnpm lint
pnpm format --check
pnpm typecheck
```

### 4. Commit

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: add shadow mode lift calculation

- Add LiftMeasurementService for statistical lift calculation
- Include significance testing with p-values
- Add batch calculation endpoint
"
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `security`

### 5. Push & Create PR

```bash
git push origin feat/your-feature-name
# Create PR on GitHub
```

---

## Pull Request Process

### PR Requirements

- [ ] Clear title and description
- [ ] Linked to issue (if applicable)
- [ ] Tests pass
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] CHANGELOG.md entry added
- [ ] No merge conflicts

### PR Template

```markdown
## Summary
Brief description of changes

## Related Issue
Fixes #123

## Changes
- [ ] Added feature X
- [ ] Fixed bug Y
- [ ] Updated docs Z

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Manual testing done

## Screenshots (if UI)
[Add screenshots]

## Checklist
- [ ] Tests pass
- [ ] Lint passes
- [ ] Types pass
- [ ] Docs updated
- [ ] CHANGELOG updated
```

### Review Process

1. **Automated Checks**: CI runs (lint, typecheck, tests, security)
2. **Code Review**: 1+ maintainer approval
3. **Merge**: Squash and merge after approval
4. **Cleanup**: Branch deleted after merge

---

## Coding Standards

### Python (Backend)

Follow the [Engineering Constitution](ENGINEERING_CONSTITUTION.md):

- **Formatter**: Ruff (100 char line)
- **Linter**: Ruff (all rules + pydantic, fastapi, sqlalchemy)
- **Types**: MyPy strict mode
- **Imports**: Absolute, grouped (stdlib, third-party, local)

```python
# Good
from uuid import UUID
from fastapi import APIRouter
from app.domain.entities.campaign import Campaign

# Bad
from app.domain.entities.campaign import *
import app.domain.entities.campaign as c
```

### TypeScript (Frontend)

- **Formatter**: Prettier (single quotes, trailing commas)
- **Linter**: ESLint (Airbnb + TypeScript)
- **Strict Mode**: Enabled
- **No `any`**: Use `unknown` if needed

```typescript
// Good
interface Campaign {
  id: string;
  name: string;
  budget: number;
}

// Bad
interface Campaign {
  id: any;
  name: string;
  budget: any;
}
```

### Database

- **Tables**: snake_case, plural
- **Columns**: snake_case
- **PKs**: UUID
- **FKs**: Explicit, indexed
- **Enums**: Native PostgreSQL enums
- **JSONB**: For flexible data

---

## Testing

### Backend

```bash
# All tests
PYTHONPATH=. pytest tests/ -v

# Unit only
PYTHONPATH=. pytest tests/unit/ -v

# Integration
PYTHONPATH=. pytest tests/integration/ -v

# Coverage
PYTHONPATH=. pytest --cov=app --cov-report=html
```

### Frontend

```bash
# All tests
pnpm test --run

# Watch mode
pnpm test

# UI mode
pnpm test:ui

# Coverage
pnpm test:coverage
```

### Test Patterns

```python
# Unit test example
def test_campaign_creation():
    campaign = Campaign.create(
        organization_id=uuid4(),
        name="Test Campaign",
        created_by=uuid4(),
    )
    assert campaign.name == "Test Campaign"
    assert campaign.status == CampaignStatus.DRAFT
```

```typescript
// Frontend test example
import { render, screen } from '@testing-library/react';
import { CampaignCard } from '@/features/campaigns/components/campaign-card';

describe('CampaignCard', () => {
  it('renders campaign name', () => {
    render(<CampaignCard campaign={{ id: '1', name: 'Test Campaign' }} />);
    expect(screen.getByText('Test Campaign')).toBeInTheDocument();
  });
});
```

---

## Documentation

### When to Update

- New API endpoints → API_REFERENCE.md
- Architecture changes → ARCHITECTURE.md
- New features → DEVELOPMENT.md
- Config changes → DEPLOYMENT.md
- Process changes → SESSION_BOOTSTRAP.md

### Style

- Clear, concise, examples
- Code blocks for all examples
- Links to related docs
- Keep it current

---

## Security

### Reporting Vulnerabilities

**DO NOT** create public issues for security vulnerabilities.

Email: security@astra-os.com

Include:
- Description
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

### Response Timeline

- **Acknowledgement**: 24 hours
- **Assessment**: 72 hours
- **Fix Timeline**: Based on severity
- **Disclosure**: Coordinated after fix

### Security Practices

- Never commit secrets
- Rotate keys quarterly
- Use dependabot/renovate
- Run `pip-audit` / `pnpm audit` weekly

---

## Community

### Communication Channels

| Channel | Purpose |
|---------|---------|
| **GitHub Discussions** | Questions, ideas, RFCs |
| **GitHub Issues** | Bugs, features, tasks |
| **Discord** | Real-time chat, help |
| **Email** | security@astra-os.com, conduct@astra-os.com |

### Getting Help

1. Search existing issues/discussions
2. Read docs (ARCHITECTURE.md, DEVELOPMENT.md)
3. Ask in Discord #help channel
4. Create GitHub Discussion

### Recognition

Contributors recognized in:
- CHANGELOG.md
- Release notes
- GitHub Contributors graph
- Annual contributors report

---

## License

By contributing, you agree your contributions are licensed under the project's license (MIT).

---

*Thank you for contributing to ASTRA OS! 🚀*