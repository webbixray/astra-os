# ASTRA OS — Session Bootstrap Protocol

**Version**: 1.0
**Purpose**: Standardized process for starting each development session

---

## Session Startup Checklist

Run this checklist at the start of **every** development session:

### 1. Environment Verification

```bash
# 1. Verify git status
git status
git log --oneline -5

# 2. Verify branch
git branch --show-current

# 3. Pull latest changes
git pull origin main

# 4. Verify Python environment
cd apps/api
source .venv/bin/activate
python --version  # Should be 3.12+

# 5. Verify Node environment
cd ../web
node --version  # Should be 20+
pnpm --version

# 6. Verify infrastructure
docker-compose ps  # postgres, redis running?
```

### 2. Context Loading

Read these files to understand current state:

```bash
# 1. Current task status
cat docs/TASK_SPEC.md | head -100

# 2. Recent decisions
cat docs/SESSION_LOG.md | tail -50

# 3. Architecture reference
cat docs/ARCHITECTURE.md | head -50
```

### 3. Test Baseline

```bash
# Quick sanity check
cd apps/api
PYTHONPATH=. pytest tests/unit/test_basic.py -v -x -q

cd ../web
pnpm test --run --reporter=dot 2>&1 | tail -5
```

---

## Session Workflow

### Planning (First 15 min)

1. **Review TASK_SPEC.md** - Current priorities
2. **Check GitHub Issues** - Assigned/related
3. **Review PRs** - Need review?
4. **Plan work** - Break into 2-4 hour chunks
5. **Update TASK_SPEC.md** - Mark planned items

### Execution (Core Time)

Follow this loop:

```
1. Pick next task from TASK_SPEC.md
2. Create feature branch: git checkout -b feat/xxx
3. Write failing test first (TDD)
4. Implement feature
4. Run tests: make test
5. Lint/format: make lint && make format
6. Type check: make typecheck
7. Commit: git commit -m "feat(scope): description"
8. Push: git push origin feat/xxx
9. Create PR
10. Repeat
```

### Documentation (Continuous)

Update as you go:

- **API_REFERENCE.md** - New endpoints
- **ARCHITECTURE.md** - Structural changes
- **DEVELOPMENT.md** - New tools/workflows
- **CHANGELOG.md** - Every commit (brief)

### Session Wrap-up (Last 15 min)

```bash
# 1. Run full test suite
make test

# 2. Final lint/format
make lint && make format

# 3. Update TASK_SPEC.md
# - Mark completed items ✅
# - Add notes for next session
# - Update "Next Session Priorities"

# 4. Update SESSION_LOG.md
# - Date, branch, commits
# - What was completed
# - Blockers, decisions, notes

# 5. Push all changes
git push origin main

# 6. Verify CI passes
# Check GitHub Actions
```

---

## Required Session Artifacts

### TASK_SPEC.md Updates

At session end, ensure:

- [ ] Completed items marked ✅
- [ ] In-progress items marked 🔄
- [ ] Blockers documented 🔴
- [ ] Next priorities listed
- [ ] Session log entry added

### SESSION_LOG.md Format

```markdown
## Session YYYY-MM-DD

**Branch**: feat/xxx
**Commits**: 3
**Duration**: 4h

### Completed
- ✅ Shadow mode lift calculation for ROAS
- ✅ Observability API routes for SLA reporting

### Decisions
- Used Prometheus for metrics (not Datadog) - cost savings
- Shadow session auto-approve threshold: 0.85 confidence

### Blockers
- 🔴 Frontend tests failing on Node 20 - upgrading to 20.12

### Next Session Priorities
1. Fix frontend test environment
2. Implement shadow mode batch compare API
3. Add SLA breach alerting

### Blockers
```

---

## Quality Gates

### Before Commit

- [ ] Tests pass (`make test`)
- [ ] Lint passes (`make lint`)
- [ ] Format correct (`make format`)
- [ ] Types check (`make typecheck`)
- [ ] No `console.log` / `print()` / `debugger`
- [ ] No commented-out code
- [ ] Commit message follows convention

### Before PR

- [ ] All quality gates pass
- [ ] Tests cover new behavior (90%+ domain)
- [ ] Documentation updated
- [ ] CHANGELOG.md entry added
- [ ] No merge conflicts
- [ ] CI passes (or known flaky tests documented)

### Before Merge

- [ ] 1+ approvals
- [ ] All CI checks green
- [ ] No merge conflicts
- [ ] Squash and merge
- [ ] Branch deleted

---

## Emergency Procedures

### Hotfix Process

```bash
# 1. Create hotfix branch from main
git checkout main
git pull
git checkout -b hotfix/critical-bug

# 2. Fix + test
# ... make changes ...
make test

# 2. Commit + PR
git commit -m "fix: critical bug description"
git push origin hotfix/critical-bug

# 3. Fast-track review (1 approval)
# 4. Merge + tag
git tag -a v0.1.1 -m "Hotfix: critical bug"
git push origin v0.1.1
```

### Rollback

```bash
# If bad deploy:
kubectl rollout undo deployment/astra-api -n astra-prod

# If bad migration:
alembic downgrade -1
```

---

## Tools Reference

### Make Targets (Create Makefile in root)

```makefile
.PHONY: test lint format typecheck migrate seed dev build deploy

test:
	cd apps/api && PYTHONPATH=. pytest tests/ -v --cov=app --cov-fail-under=80
	cd apps/web && pnpm test --run

lint:
	cd apps/api && ruff check .
	cd apps/web && pnpm lint

format:
	cd apps/api && ruff format .
	cd apps/web && pnpm format

typecheck:
	cd apps/api && mypy app/
	cd apps/web && pnpm typecheck

migrate:
	cd apps/api && alembic upgrade head

seed:
	cd apps/api && python scripts/seed_db.py

dev:
	docker-compose up -d postgres redis
	cd apps/api && uvicorn app.main:app --reload &
	cd apps/web && pnpm dev

build:
	docker build -t astra-api:latest -f docker/api.Dockerfile .
	docker build -t astra-web:latest -f docker/web.Dockerfile .

deploy:
	kubectl apply -k k8s/overlays/prod
```

---

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `docs/TASK_SPEC.md` | Current sprint tasks |
| `docs/ROADMAP.md` | Milestone roadmap |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/API_REFERENCE.md` | API documentation |
| `docs/DEVELOPMENT.md` | Dev guide |
| `docs/ENGINEERING_CONSTITUTION.md` | Coding standards |
| `CHANGELOG.md` | Release history |

### Key Commands

```bash
# Backend
cd apps/api
PYTHONPATH=. pytest tests/ -v          # Run tests
PYTHONPATH=. pytest tests/unit/ -v      # Unit only
PYTHONPATH=. pytest tests/integration/  # Integration
ruff check . && ruff format .           # Lint + format
mypy app/                               # Type check
alembic upgrade head                    # Migrate
python scripts/seed_db.py               # Seed

# Frontend
cd apps/web
pnpm test --run                         # Tests
pnpm test:ui                            # UI mode
pnpm lint && pnpm format                # Lint + format
pnpm typecheck                          # Type check
pnpm build                              # Build
```

---

*Follow this protocol every session for consistent, high-quality delivery.*
