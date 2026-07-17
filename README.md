# Astra OS

![CI/CD](https://github.com/webbixray/astra-os/actions/workflows/ci-cd.yaml/badge.svg)
![Tests](https://img.shields.io/badge/tests-1089%20passed-brightgreen)
![License](https://img.shields.io/badge/license-proprietary-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Node](https://img.shields.io/badge/node-20+-brightgreen)
![TypeScript](https://img.shields.io/badge/typescript-5.5+-blue)

**AI-Native Marketing & Business Growth Operating System**

Astra OS is a comprehensive platform that replaces your entire marketing department with AI-powered agents, workflow automation, content generation, ad management, analytics, and knowledge management.

## Features

- **AI Content Generation** - Create marketing copy, blog posts, and social media content with AI
- **Campaign Management** - Plan, execute, and track multi-channel marketing campaigns
- **Ad Management** - Manage Google Ads, Meta, LinkedIn, and TikTok campaigns
- **Analytics & Reporting** - Real-time insights and customizable dashboards
- **Team Collaboration** - Work together with roles, permissions, and approval workflows
- **Workflow Automation** - Automate repetitive marketing tasks with visual workflows
- **Email Marketing** - Create and send targeted email campaigns
- **Content Calendar** - Plan and schedule your content pipeline

## Quick Start

### Prerequisites

- Node.js >= 20.0.0
- pnpm >= 9.0.0
- Python >= 3.12
- Docker (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/webbixray/astra-os.git
cd astra-os

# Run the setup script
./scripts/setup.sh

# Start development
make dev
```

### Docker

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

## Documentation

- [Development Guide](DEVELOPMENT.md) - Setup, configuration, and development workflow
- [Contributing](CONTRIBUTING.md) - How to contribute to the project
- [Architecture](docs/phase-1/) - Technical architecture and design decisions
- [API Documentation](http://localhost:8000/api/v1/docs) - Interactive API docs (Swagger UI)

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0
- **Cache**: Redis 7
- **Workflow**: Temporal
- **AI**: OpenAI, Anthropic, Google Gemini, NVIDIA NIM

### Frontend
- **Framework**: Next.js 15 with React 19
- **Styling**: Tailwind CSS 4
- **State**: TanStack React Query
- **Components**: Radix UI + shadcn/ui

### Infrastructure
- **Container**: Docker with multi-stage builds
- **Orchestration**: Kubernetes with Kustomize
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry, OpenTelemetry, Prometheus

## Project Structure

```
astraos/
├── apps/
│   ├── api/              # Python/FastAPI backend
│   └── web/              # Next.js frontend
├── packages/
│   ├── shared/           # Shared TypeScript types
│   ├── ui/               # Shared UI components
│   └── config-*/         # Shared configurations
├── docker/               # Docker configurations
├── k8s/                  # Kubernetes manifests
├── scripts/              # Development scripts
└── docs/                 # Documentation
```

## Development

```bash
# Start development
make dev

# Run tests
make test

# Lint code
make lint

# Format code
make format
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for more details.

## Deployment

### Docker Compose

```bash
# Production deployment
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Deploy to cluster
kubectl apply -k k8s/
```

### Cloud Providers

- [Vercel](scripts/deploy/vercel.sh)
- [Railway](scripts/deploy/railway.sh)
- [Fly.io](scripts/deploy/flyio.sh)

## Environment Variables

See [docker/dev/.env.example](docker/dev/.env.example) for all configuration options.

### Required

```env
SECRET_KEY=your-secret-key-min-32-chars
DATABASE_URL=postgresql+asyncpg://astra:astra_dev@localhost:5432/astra
```

### AI Providers (at least one)

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Proprietary - See [LICENSE](LICENSE) for details.

## Support

- [GitHub Issues](https://github.com/webbixray/astra-os/issues)
- [GitHub Discussions](https://github.com/webbixray/astra-os/discussions)
