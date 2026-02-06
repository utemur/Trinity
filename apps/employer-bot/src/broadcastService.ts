import type { Telegraf } from "telegraf";
import { prisma } from "@trinity/db";
import { config } from "./config.js";
import { logger } from "./logger.js";
import { formatJobCardForWorker } from "./formatters.js";
import { Markup } from "telegraf";

let _workerBot: Telegraf | null = null;

export function setWorkerBot(bot: Telegraf): void {
  _workerBot = bot;
}

const CALLBACK_APPLY = "job:apply:";
const CALLBACK_HIDE = "job:hide:";

export async function runBroadcastForJob(jobId: string): Promise<void> {
  const job = await prisma.job.findUnique({
    where: { id: jobId },
    include: { employer: true },
  });
  if (!job || job.status !== "OPEN") return;

  if (job.broadcastStatus === "SENT" || job.broadcastStatus === "SENDING") {
    logger.info({ jobId }, "Broadcast already in progress or sent");
    return;
  }

  await prisma.job.update({
    where: { id: jobId },
    data: { broadcastStatus: "SENDING" },
  });

  try {
    const workers = await findMatchingWorkers(job);
    const limited = workers.slice(0, config.maxBroadcastPerJob);

    if (limited.length === 0) {
      await prisma.job.update({
        where: { id: jobId },
        data: { broadcastStatus: "SENT" },
      });
      logger.info({ jobId }, "No matching workers for broadcast");
      return;
    }

    const workerIds = limited.map((w) => w.id);
    await prisma.broadcastLog.createMany({
      data: workerIds.map((workerId) => ({
        jobId,
        workerId,
        status: "PENDING" as const,
      })),
      skipDuplicates: true,
    });

    const delayMs = (60 * 1000) / config.rateLimitPerMinute;
    const batchDelay = Math.max(delayMs, config.minBroadcastBatchDelayMs);

    const workerBot = _workerBot;
    if (!workerBot) {
      logger.warn({ jobId }, "WorkerBot not initialized, skipping broadcast");
      await prisma.job.update({
        where: { id: jobId },
        data: { broadcastStatus: "FAILED" },
      });
      return;
    }

    const card = formatJobCardForWorker(job);
    const keyboard = Markup.inlineKeyboard([
      [Markup.button.callback("✅ Откликнуться", CALLBACK_APPLY + jobId)],
      [Markup.button.callback("🚫 Скрыть", CALLBACK_HIDE + jobId)],
    ]);

    let sent = 0;
    let failed = 0;

    for (const worker of limited) {
      try {
        await workerBot.telegram.sendMessage(Number(worker.telegramId), card, keyboard);
        await prisma.broadcastLog.updateMany({
          where: { jobId, workerId: worker.id },
          data: { status: "SENT", sentAt: new Date() },
        });
        sent++;
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : String(err);
        await prisma.broadcastLog.updateMany({
          where: { jobId, workerId: worker.id },
          data: { status: "FAILED", errorText: errMsg },
        });
        failed++;
        logger.warn({ err, jobId, workerId: worker.id }, "Broadcast send failed");
      }
      await sleep(batchDelay);
    }

    await prisma.job.update({
      where: { id: jobId },
      data: { broadcastStatus: "SENT" },
    });

    logger.info({ jobId, sent, failed, total: limited.length }, "Broadcast completed");
  } catch (err) {
    logger.error({ err, jobId }, "Broadcast failed");
    await prisma.job.update({
      where: { id: jobId },
      data: { broadcastStatus: "FAILED" },
    });
  }
}

async function findMatchingWorkers(
  job: { profession: string; location: string; ratePerHour: number }
): Promise<{ id: string; telegramId: bigint }[]> {
  const workers = await prisma.worker.findMany({
    where: {
      isConsented: true,
      isActive: true,
      professions: { has: job.profession },
    },
    select: { id: true, telegramId: true, minRate: true, city: true, area: true },
  });

  return workers.filter((w) => {
    if (w.minRate != null && job.ratePerHour < w.minRate) return false;
    const loc = (job.location || "").toLowerCase();
    if (w.city && !loc.includes(w.city.toLowerCase())) return false;
    if (w.area && !loc.includes(w.area.toLowerCase())) return false;
    return true;
  });
}

export async function resumePendingBroadcasts(): Promise<void> {
  const jobs = await prisma.job.findMany({
    where: {
      status: "OPEN",
      broadcastStatus: { in: ["NOT_SENT", "SENDING"] },
    },
  });

  for (const job of jobs) {
    try {
      await runBroadcastForJob(job.id);
    } catch (err) {
      logger.error({ err, jobId: job.id }, "Resume broadcast failed");
    }
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
