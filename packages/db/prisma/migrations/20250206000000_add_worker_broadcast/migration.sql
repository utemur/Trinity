-- CreateEnum
CREATE TYPE "BroadcastStatus" AS ENUM ('NOT_SENT', 'SENDING', 'SENT', 'FAILED');
CREATE TYPE "ApplicationStatus" AS ENUM ('APPLIED', 'CANCELLED');
CREATE TYPE "BroadcastLogStatus" AS ENUM ('PENDING', 'SENT', 'SKIPPED', 'FAILED');

-- AlterTable
ALTER TABLE "Job" ADD COLUMN IF NOT EXISTS "broadcastStatus" "BroadcastStatus" NOT NULL DEFAULT 'NOT_SENT';

-- CreateTable
CREATE TABLE "Worker" (
    "id" TEXT NOT NULL,
    "telegramId" BIGINT NOT NULL,
    "username" TEXT,
    "firstName" TEXT NOT NULL,
    "lastName" TEXT,
    "isConsented" BOOLEAN NOT NULL DEFAULT false,
    "consentedAt" TIMESTAMP(3),
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "city" TEXT,
    "area" TEXT,
    "minRate" INTEGER,
    "professions" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Worker_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Application" (
    "id" TEXT NOT NULL,
    "jobId" TEXT NOT NULL,
    "workerId" TEXT NOT NULL,
    "status" "ApplicationStatus" NOT NULL DEFAULT 'APPLIED',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Application_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BroadcastLog" (
    "id" TEXT NOT NULL,
    "jobId" TEXT NOT NULL,
    "workerId" TEXT NOT NULL,
    "status" "BroadcastLogStatus" NOT NULL DEFAULT 'PENDING',
    "sentAt" TIMESTAMP(3),
    "errorText" TEXT,

    CONSTRAINT "BroadcastLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Worker_telegramId_key" ON "Worker"("telegramId");

-- CreateIndex
CREATE UNIQUE INDEX "Application_jobId_workerId_key" ON "Application"("jobId", "workerId");
CREATE INDEX "Application_jobId_idx" ON "Application"("jobId");
CREATE INDEX "Application_workerId_idx" ON "Application"("workerId");

-- CreateIndex
CREATE UNIQUE INDEX "BroadcastLog_jobId_workerId_key" ON "BroadcastLog"("jobId", "workerId");
CREATE INDEX "BroadcastLog_jobId_idx" ON "BroadcastLog"("jobId");
CREATE INDEX "BroadcastLog_workerId_idx" ON "BroadcastLog"("workerId");
CREATE INDEX "BroadcastLog_status_idx" ON "BroadcastLog"("status");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "Job_broadcastStatus_idx" ON "Job"("broadcastStatus");

-- AddForeignKey
ALTER TABLE "Application" ADD CONSTRAINT "Application_jobId_fkey" FOREIGN KEY ("jobId") REFERENCES "Job"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "Application" ADD CONSTRAINT "Application_workerId_fkey" FOREIGN KEY ("workerId") REFERENCES "Worker"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "BroadcastLog" ADD CONSTRAINT "BroadcastLog_jobId_fkey" FOREIGN KEY ("jobId") REFERENCES "Job"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "BroadcastLog" ADD CONSTRAINT "BroadcastLog_workerId_fkey" FOREIGN KEY ("workerId") REFERENCES "Worker"("id") ON DELETE CASCADE ON UPDATE CASCADE;
