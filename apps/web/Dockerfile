# ============================================================
# ASTRA OS WEB - Production Dockerfile (Next.js Standalone)
# Multi-stage build (3 stages) with minimal attack surface
# ============================================================

# Stage 1: Dependencies
FROM node:20-alpine AS deps
LABEL stage=builder

RUN apk add --no-cache libc6-compat python3 make g++
RUN npm install -g pnpm@9

WORKDIR /app

COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json apps/web/
COPY packages/ui/package.json packages/ui/

RUN pnpm install --frozen-lockfile --prefer-offline

# Stage 2: Builder
FROM node:20-alpine AS builder
LABEL stage=builder

RUN npm install -g pnpm@9

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY --from=deps /app/packages/ui/node_modules ./packages/ui/node_modules

COPY pnpm-lock.yaml pnpm-workspace.yaml package.json turbo.json ./
COPY apps/web ./apps/web
COPY packages/ui ./packages/ui

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-https://api.astra-os.io/api/v1}
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN pnpm exec turbo build --filter=@astra/web

# Stage 3: Production Runner
FROM node:20-alpine AS runner
LABEL maintainer="Astra OS Team"

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

RUN apk add --no-cache tini curl

WORKDIR /app

COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/public ./apps/web/public

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NODE_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["node", "apps/web/server.js"]
