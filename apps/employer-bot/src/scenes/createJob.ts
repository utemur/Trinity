import { Scenes } from "telegraf";
import { prisma } from "@trinity/db";
import { TEXTS } from "../texts.js";
import {
  professionKeyboard,
  confirmKeyboard,
  CALLBACK,
} from "../keyboards.js";
import { parseDate, parseTime, parseRate } from "../validation.js";
import { publishJob } from "../jobService.js";
import { formatJobCard } from "../formatters.js";
import { logger } from "../logger.js";
import { config } from "../config.js";

const WIZARD_TIMEOUT_MS = 15 * 60 * 1000;

interface CreateJobSession {
  profession?: string;
  date?: string;
  time?: string;
  location?: string;
  ratePerHour?: number;
  step?: number;
  lastActivity?: number;
}

export const createJobScene = new Scenes.BaseScene("create_job");

createJobScene.enter(async (ctx) => {
  const s = (ctx as any).scene.session as CreateJobSession;
  const init = (ctx as any).scene.state as Partial<CreateJobSession> | undefined;
  if (init?.profession && init?.location && init?.ratePerHour != null) {
    Object.assign(s, { profession: init.profession, location: init.location, ratePerHour: init.ratePerHour });
    s.step = 2;
    s.lastActivity = Date.now();
    await ctx.reply(TEXTS.wizard.date);
  } else {
    s.step = 1;
    s.lastActivity = Date.now();
    await ctx.reply(TEXTS.wizard.profession, professionKeyboard());
  }
});

createJobScene.action(/^prof:(.+)$/, async (ctx) => {
  const match = ctx.match;
  const profession = match?.[1];
  if (!profession) return ctx.answerCbQuery();
  const s = (ctx as any).scene.session as CreateJobSession;
  s.profession = profession;
  s.step = 2;
  s.lastActivity = Date.now();
  await ctx.answerCbQuery();
  await ctx.reply(TEXTS.wizard.date);
});

createJobScene.action(CALLBACK.professionOther, async (ctx) => {
  const s = (ctx as any).scene.session as CreateJobSession;
  s.step = 1.5;
  s.lastActivity = Date.now();
  await ctx.answerCbQuery();
  await ctx.reply(TEXTS.wizard.professionOtherPrompt);
});

createJobScene.action(CALLBACK.wizardCancel, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.reply(TEXTS.wizard.cancelled);
  await (ctx as any).scene.leave();
});

createJobScene.on("text", async (ctx) => {
  const s = (ctx as any).scene.session as CreateJobSession;
  if (Date.now() - (s.lastActivity ?? 0) > WIZARD_TIMEOUT_MS) {
    await ctx.reply(TEXTS.errors.wizardTimeout);
    return (ctx as any).scene.leave();
  }
  s.lastActivity = Date.now();
  const text = ctx.message.text?.trim() ?? "";

  if (s.step === 1.5) {
    if (!text) return ctx.reply(TEXTS.wizard.professionOtherPrompt);
    s.profession = text;
    s.step = 2;
    return ctx.reply(TEXTS.wizard.date);
  }

  if (s.step === 2) {
    const r = parseDate(text);
    if (!r.valid) {
      if (r.error === "past") return ctx.reply(TEXTS.wizard.datePast);
      return ctx.reply(TEXTS.wizard.dateInvalid);
    }
    s.date = text;
    s.step = 3;
    return ctx.reply(TEXTS.wizard.time);
  }

  if (s.step === 3) {
    const r = parseTime(text);
    if (!r.valid) return ctx.reply(TEXTS.wizard.timeInvalid);
    s.time = text;
    s.step = 4;
    return ctx.reply(TEXTS.wizard.location);
  }

  if (s.step === 4) {
    if (!text) return ctx.reply(TEXTS.wizard.locationEmpty);
    s.location = text;
    s.step = 5;
    return ctx.reply(TEXTS.wizard.rate);
  }

  if (s.step === 5) {
    const r = parseRate(text);
    if (!r.valid) return ctx.reply(TEXTS.wizard.rateInvalid);
    s.ratePerHour = r.value!;
    s.step = 6;
    const card = formatJobCard({
      profession: s.profession!,
      date: s.date!,
      time: s.time!,
      location: s.location!,
      ratePerHour: s.ratePerHour!,
      currency: "UZS",
    });
    return ctx.reply(TEXTS.wizard.confirm + "\n\n" + card, confirmKeyboard());
  }
});

createJobScene.action(CALLBACK.wizardPublish, async (ctx) => {
  const s = (ctx as any).scene.session as CreateJobSession;
  await ctx.answerCbQuery();
  if (!s.profession || !s.date || !s.time || !s.location || s.ratePerHour == null) {
    logger.warn({ session: s }, "wizardPublish: incomplete session data");
    return ctx.reply(TEXTS.errors.generic);
  }
  const employer = await prisma.employer.findUnique({
    where: { telegramId: BigInt(ctx.from!.id) },
  });
  if (!employer) {
    logger.warn({ telegramId: ctx.from?.id }, "wizardPublish: employer not found");
    return ctx.reply(TEXTS.errors.generic);
  }
  try {
    const job = await prisma.job.create({
      data: {
        employerId: employer.id,
        profession: s.profession,
        date: s.date,
        time: s.time,
        location: s.location,
        ratePerHour: s.ratePerHour,
        currency: "UZS",
        status: "OPEN",
      },
    });
    await publishJob(job.id);
    if (config.adminTelegramId) {
      try {
        const card = formatJobCard(job) + `\n\nID: ${job.id}`;
        await ctx.telegram.sendMessage(Number(config.adminTelegramId), card);
      } catch (e) {
        logger.warn({ err: e }, "Admin notification failed");
      }
    }
    await ctx.reply(TEXTS.wizard.published.replace("{jobId}", job.id));
  } catch (e) {
    const errMsg = e instanceof Error ? e.message : String(e);
    const errStack = e instanceof Error ? e.stack : undefined;
    logger.error({ err: e, errMsg, errStack, session: s }, "Failed to create job");
    await ctx.reply(TEXTS.errors.generic);
  }
  await (ctx as any).scene.leave();
});

createJobScene.action(CALLBACK.wizardEdit, async (ctx) => {
  await ctx.answerCbQuery();
  const s = (ctx as any).scene.session as CreateJobSession;
  s.step = 1;
  await ctx.reply(TEXTS.wizard.profession, professionKeyboard());
});
