import "dotenv/config";
import { bot } from "./bot.js";
import { logger } from "./logger.js";
import { prisma } from "@trinity/db";

async function main() {
  logger.info("EmployerBot starting");
  try {
    await prisma.$connect();
    logger.info("Database connected");
  } catch (err) {
    logger.fatal({ err }, "Database connection failed");
    throw err;
  }
  await bot.launch();
  logger.info("EmployerBot started");
}

main().catch((err) => {
  logger.fatal({ err }, "Fatal error");
  process.exit(1);
});

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
