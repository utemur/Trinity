FROM node:20-slim

RUN apt-get update -y && apt-get install -y openssl ca-certificates && rm -rf /var/lib/apt/lists/* \
  && corepack enable && corepack prepare pnpm@9.0.0 --activate

WORKDIR /app

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/db/package.json packages/db/tsconfig.json ./packages/db/
COPY packages/db/prisma ./packages/db/prisma/
COPY packages/db/src ./packages/db/src/
COPY apps/employer-bot/package.json apps/employer-bot/tsconfig.json ./apps/employer-bot/
COPY apps/employer-bot/src ./apps/employer-bot/src/

RUN pnpm install --frozen-lockfile
RUN pnpm db:generate
RUN pnpm employer:build

CMD ["sh", "-c", "pnpm --filter @trinity/db migrate:deploy 2>/dev/null || true && node apps/employer-bot/dist/index.js"]
