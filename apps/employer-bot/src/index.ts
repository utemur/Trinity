import "dotenv/config";
import { bot } from "./bot.js";
import { logger } from "./logger.js";

async function main() {
  logger.info("EmployerBot starting");
  await bot.launch();
  logger.info("EmployerBot started");
}

main().catch((err) => {
  logger.fatal({ err }, "Fatal error");
  process.exit(1);
});

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
