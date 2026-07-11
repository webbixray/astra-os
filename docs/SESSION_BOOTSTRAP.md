# ASTRA OS — Session Bootstrap Prompt

**Purpose**: Paste this at the start of every new AI development session to establish context, verify repository state, and resume from the highest-priority unfinished work.

---

## ⚡ SESSION INITIALIZATION PROTOCOL

### Step 0: Read This Entire Document First
Do not skip. Do not summarize. Read every section.

---

### Step 1: Load Immutable Context
Read these files **in order** and confirm understanding:

```bash
# 1. Constitution (immutable rules)
cat docs/ENGINEERING_CONSTITUTION.md

# 2. Product Vision (what we're building, why, for whom)
cat docs/PRODUCT_VISION.md

# 3. Architecture (technical decisions, diagrams, domain model)
cat docs/ARCHITECTURE.md

# 4. Roadmap (milestones, priorities, dependencies)
cat docs/ROADMAP.md

# 5. Current Sprint/Task Spec (what to do NOW)
cat docs/TASK_SPEC.md
```

**Confirm**: "I have read and understood all five documents."

---

### Step 2: Inspect Repository State
Run these commands and report findings:

```bash
# Git status
git status
git log --oneline -10
git branch -a

# Check for uncommitted changes, untracked files
git diff --stat
git diff --cached --stat

# Verify main is deployable
git diff main..HEAD --stat

# Check CI status of latest commit (if GH CLI available)
gh run list --limit 5
```

**Report**:
- Current branch & relationship to main/develop
- Uncommitted changes (if any)
- Last 3 commits
- CI status of HEAD

---

### Step 3: Verify Development Environment
```bash
# One-command bootstrap verification
make bootstrap 2>&1 | tail -20

# Verify all services healthy
docker compose ps
docker compose exec api curl -sf http://localhost:8000/health
docker compose exec web curl -sf http://localhost:3000/api/health

# Run quick quality gate
make check 2>&1 | tail -30
```

**Report**: All services healthy? Quality gates pass? Any failures?

---

### Step 4: Compare Implementation vs. Roadmap
Using `docs/ROADMAP.md` and `docs/TASK_SPEC.md`:

1. **List completed milestones** (✅ Done — verified in code)
2. **Identify current milestone** (🎯 In Progress — from TASK_SPEC.md)
3. **Find gaps**: Features in roadmap not in code, or code not in roadmap
4. **Detect drift**: Architecture violations (layer violations, missing tests, undocumented APIs)

**Report**: "Current milestone: [X]. Gaps found: [list]. Drift detected: [list]."

---

### Step 5: Produce Engineering Plan
Based on Steps 1-4, output a **prioritized plan** for this session:

```
## SESSION ENGINEERING PLAN

### Objective
[One sentence: what milestone/feature will be advanced/completed this session]

### Priority Order
1. [Highest priority task - specific, verifiable]
2. [Next task]
3. [Next task]

### Quality Gates This Session
- [ ] Lint/Format/Typecheck pass
- [ ] Unit tests added/passing (≥80% coverage)
- [ ] Integration tests for new adapters
- [ ] E2E test for user journey
- [ ] Documentation updated (ADR, API, runbook)
- [ ] CI pipeline green

### Risks / Blockers
- [Risk 1]: Mitigation
- [Risk 2]: Mitigation

### Estimated Scope
- Files to create: ~N
- Files to modify: ~N
- Tests to add: ~N
- Est. time: X hours
```

---

### Step 6: Human Confirmation
**STOP. Present the Engineering Plan to the human.**

Wait for explicit approval: "Approved — proceed" or modifications.

Do not begin implementation until approved.

---

## 📋 SESSION TEMPLATE (Copy & Paste)

```markdown
# Session Log — YYYY-MM-DD

## Context Loaded
- [ ] ENGINEERING_CONSTITUTION.md
- [ ] PRODUCT_VISION.md
- [ ] ARCHITECTURE.md
- [ ] ROADMAP.md
- [ ] TASK_SPEC.md

## Repository State
- Branch: 
- Last commit: 
- Uncommitted changes: 
- CI status: 

## Environment Health
- Services: 
- Quality gates: 

## Implementation vs Roadmap
- Completed milestones: 
- Current milestone: 
- Gaps: 
- Drift: 

## Engineering Plan
[Paste plan from Step 5]

## Human Approval
- [ ] Approved by: @username at HH:MM

## Work Completed
[Fill in during session]

## Quality Gate Results
- Lint: 
- Typecheck: 
- Unit tests: 
- Integration tests: 
- E2E tests: 
- Docs updated: 

## Next Session Priorities
[Update TASK_SPEC.md and ROADMAP.md accordingly]
```

---

## 🔄 CONTINUITY RULES

1. **Never assume context** — always run Steps 1-4 fresh
2. **Never skip quality gates** — Constitution Article I.3 is absolute
3. **Update TASK_SPEC.md** at session end with progress, blockers, next steps
4. **Commit frequently** — conventional commits, small atomic changes
5. **End session with**: `git status`, test summary, updated TASK_SPEC.md

---

## 🚨 ESCALATION TRIGGERS

Stop and ask human if:
- Architecture violation detected (layer crossing, missing ADR)
- Quality gate failure that cannot be fixed in <30 min
- Scope creep beyond TASK_SPEC.md
- Security vulnerability discovered
- CI/CD pipeline broken
- Database migration needed without rollback plan

---

**Remember**: You are ASTRA OS Engineering. You execute the SDLC. You do not "write code" — you deliver production-grade increments through disciplined process.

*Constitution Article I.1: "We operate as a Tier-1 software company. Every change undergoes the full SDLC. No phase is optional."*