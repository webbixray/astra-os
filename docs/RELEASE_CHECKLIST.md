# ASTRA OS - Release Checklist

## Pre-Release

### Code Quality
- [ ] All tests pass (`python -m pytest tests/ -v`)
- [ ] No new lint errors (`ruff check .`)
- [ ] No new type errors (`mypy .`)
- [ ] Frontend tests pass (`pnpm test`)
- [ ] Frontend lint passes (`pnpm lint`)
- [ ] Frontend type check passes (`pnpm typecheck`)

### Security
- [ ] No hardcoded secrets in code
- [ ] Environment variables properly configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Security headers enabled (COOP, COEP, CORP)
- [ ] Field-level encryption active for sensitive data
- [ ] Dependencies scanned for vulnerabilities

### Database
- [ ] Migration tree is linear (`./scripts/check-migrations.sh`)
- [ ] Migration test passes (up → down → up)
- [ ] All FK constraints defined
- [ ] All indexes defined

### Performance
- [ ] No N+1 query patterns
- [ ] Redis cache working
- [ ] Prometheus metrics accessible
- [ ] Connection pool properly sized

### Documentation
- [ ] API docs up to date (Swagger)
- [ ] Changelog updated
- [ ] Breaking changes documented

## Release

### Cut Release
- [ ] Create release branch: `git checkout -b release/vX.Y.Z`
- [ ] Bump version in `apps/api/pyproject.toml`
- [ ] Bump version in `apps/web/package.json`
- [ ] Update changelog with release date
- [ ] Merge to main: `git checkout main && git merge release/vX.Y.Z`
- [ ] Tag release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] Push to main: `git push origin main`
- [ ] Push tags: `git push --tags`

### Deploy
- [ ] Deploy to staging
- [ ] Run smoke tests on staging
- [ ] Verify API responses
- [ ] Verify frontend rendering
- [ ] Deploy to production
- [ ] Monitor for errors (first hour)
- [ ] Verify metrics and health checks

## Post-Release

- [ ] Announce release
- [ ] Update any external documentation
- [ ] Archive release branch: `git branch -d release/vX.Y.Z`
- [ ] Review any immediate post-release issues
- [ ] Plan next sprint