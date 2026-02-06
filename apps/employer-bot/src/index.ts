import "dotenv/config";
import { bot } from "./bot.js";
import { workerBot } from "./worker.bot.js";
import { setWorkerBot, resumePendingBroadcasts } from "./broadcastService.js";
import { logger } from "./logger.js";
import { prisma } from "@trinity/db";

async function main() {
  logger.info("Backend starting (EmployerBot + WorkerBot)");
  try {
    await prisma.$connect();
    logger.info("Database connected");
  } catch (err) {
    logger.fatal({ err }, "Database connection failed");
    throw err;
  }

  setWorkerBot(workerBot);

  try {
    await bot.launch();
    logger.info("EmployerBot started");
  } catch (err) {
    logger.fatal({ err }, "EmployerBot launch failed");
    throw err;
  }
  try {
    await workerBot.launch();
    logger.info("WorkerBot started");
  } catch (err) {
    logger.fatal({ err }, "WorkerBot launch failed");
    throw err;
  }

  resumePendingBroadcasts().catch((err) => {
    logger.error({ err }, "Resume pending broadcasts failed");
  });
}

main().catch((err) => {
  logger.fatal({ err }, "Fatal error");
  process.exit(1);
});

process.once("SIGINT", () => {
  bot.stop("SIGINT");
  workerBot.stop("SIGINT");
});
process.once("SIGTERM", () => {
  bot.stop("SIGTERM");
  workerBot.stop("SIGTERM");
});
