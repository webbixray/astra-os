# Changelog

All notable changes to Astra OS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Setup wizard for first-time installation (`/setup`)
- Interactive onboarding tour for new users
- API key management system
- Webhook support for integrations
- Data export/import functionality (CSV, JSON, XLSX)
- User preferences page with theme, timezone, and notification settings
- Toast notification system for user feedback
- Version checking and update notifications
- Keyboard shortcuts help modal (Cmd+/)
- Configuration management utility
- Health dashboard component for monitoring
- Database seed script for development
- Makefile with 25+ development commands
- One-click setup script
- Production Docker configurations
- Vercel, Railway, and Fly.io deployment scripts
- Comprehensive error types and messages
- CONTRIBUTING.md guide
- DEVELOPMENT.md comprehensive guide
- CHANGELOG.md
- Performance optimization utilities (debounce, lazy loading, virtualization)
- Security headers and CSP configuration
- Comprehensive test utilities and mock helpers
- Enhanced error boundary with error reporting
- Loading state components (spinner, overlay, card, table, page)
- Form validation utilities with common validators
- Notification preferences component
- Activity log component with filtering
- Quick actions menu (Cmd+K)
- Status indicators and connection status components
- Internationalization (i18n) support with 6 languages (en, es, fr, de, ja, zh)
- Offline support with service worker and offline page
- Accessibility utilities (focus trap, screen reader announcements)
- Data table component with sorting, filtering, and pagination
- Empty state components for various scenarios
- Breadcrumb navigation and page header components
- Confirmation dialog with hook for async operations
- Progress indicators (linear, step, circular)
- Avatar and user menu components
- Theme switcher component
- Analytics dashboard components (MetricCard, MetricsGrid, AnalyticsOverview, ConversionFunnel, RealTimeVisitors)
- Campaign management components (CampaignCard, CampaignList, CampaignStats)
- Content management components (ContentCard, ContentList, ContentCalendar)
- Team management components (TeamMemberCard, TeamList, TeamStats)
- Workflow builder components (WorkflowStepCard, WorkflowCard, WorkflowBuilder, WorkflowList)
- Integration marketplace components (IntegrationCard, IntegrationList, ConnectedIntegrations)
- Billing and subscription components (PricingCard, PricingSection, BillingHistory, SubscriptionStatus)
- Help center components (HelpCenter, FAQSection, ContactSupport, QuickStartGuide)
- Performance monitoring utilities (marks, measures, timers, Web Vitals observers)
- Error tracking system with breadcrumbs and context
- Structured logging utilities with levels and context
- Caching utilities (MemoryCache, StorageCache, apiCache, uiCache)
- Resilience utilities (retry, circuit breaker, timeout, debounce, throttle, memoize)
- Rate limiting utilities with configurable windows
- Health check utilities with checker class
- Feature flag utilities with rollout percentages and user targeting
- Comprehensive testing framework (test runner, assertions, reporters)
- API testing utilities with request helpers and assertions
- Snapshot testing utilities with comparison functions
- Accessibility testing utilities with WCAG compliance checks
- Performance testing utilities with benchmarking and memory profiling
- Mock data generators for users, campaigns, content, analytics, teams
- Test report generators (JSON, HTML, Markdown, Console formats)
- Visual regression testing utilities with screenshot comparison

### Changed
- Protected all authenticated routes in middleware
- Improved startup validation with AI provider checks
- Enhanced health check endpoint with detailed status
- Updated CI/CD pipeline with Docker build and deployment automation

### Fixed
- Missing `@astra/ui` package reference
- Invalid `services/*` workspace reference
- Missing Kubernetes manifests for Temporal and Worker
- Web deployment health probe path
- Dependabot placeholder reviewer values

### Removed
- Non-existent `services/*` workspace reference

## [0.0.1] - 2026-01-01

### Added
- Initial project setup
- Backend API with FastAPI
- Frontend with Next.js 15
- PostgreSQL database with SQLAlchemy
- Redis cache integration
- JWT authentication
- AI provider integration (OpenAI, NVIDIA NIM)
- Campaign management
- Content management
- Analytics dashboard
- Team management
- Email marketing
- Workflow automation
- Ad platform integrations
- Kubernetes deployment manifests
- CI/CD pipeline with GitHub Actions
- Comprehensive documentation

[Unreleased]: https://github.com/webbixray/astra-os/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/webbixray/astra-os/releases/tag/v0.0.1
