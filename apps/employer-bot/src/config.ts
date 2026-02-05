function requireEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env: ${name}`);
  return v;
}

export const config = {
  botToken: requireEnv("BOT_TOKEN_EMPLOYER"),
  databaseUrl: requireEnv("DATABASE_URL"),
  adminTelegramId: process.env.ADMIN_TELEGRAM_ID
    ? BigInt(process.env.ADMIN_TELEGRAM_ID)
    : null,
};
