function requireEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env: ${name}`);
  return v;
}

function envInt(name: string, def: number): number {
  const v = process.env[name];
  if (!v) return def;
  const n = parseInt(v, 10);
  return isNaN(n) ? def : n;
}

export const config = {
  botTokenEmployer: requireEnv("BOT_TOKEN_EMPLOYER"),
  botTokenWorker: requireEnv("BOT_TOKEN_WORKER"),
  databaseUrl: requireEnv("DATABASE_URL"),
  adminTelegramId: process.env.ADMIN_TELEGRAM_ID
    ? BigInt(process.env.ADMIN_TELEGRAM_ID)
    : null,
  appTimezone: process.env.APP_TIMEZONE ?? "Asia/Tashkent",
  rateLimitPerMinute: envInt("RATE_LIMIT_PER_MINUTE", 60),
  maxBroadcastPerJob: envInt("MAX_BROADCAST_PER_JOB", 500),
  minBroadcastBatchDelayMs: envInt("MIN_BROADCAST_BATCH_DELAY_MS", 300),
};
