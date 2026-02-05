import { prisma } from "@trinity/db";
import { logger } from "./logger.js";

export async function publishJob(jobId: string): Promise<void> {
  const job = await prisma.job.findUnique({
    where: { id: jobId },
    include: { employer: true },
  });
  if (!job) return;
  logger.info({ jobId, employerId: job.employerId }, "Job published");
  // TODO: триггер рассылки WorkerBot — здесь можно вызвать очередь/хук
}
