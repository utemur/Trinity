import { prisma } from "@trinity/db";
import { logger } from "./logger.js";
import { runBroadcastForJob } from "./broadcastService.js";

export async function publishJob(jobId: string): Promise<void> {
  const job = await prisma.job.findUnique({
    where: { id: jobId },
    include: { employer: true },
  });
  if (!job) return;
  logger.info({ jobId, employerId: job.employerId }, "Job published");
  runBroadcastForJob(jobId).catch((err) => {
    logger.error({ err, jobId }, "Broadcast failed");
  });
}
