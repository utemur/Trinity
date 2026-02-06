import { Telegraf, session, Scenes } from "telegraf";
import { Markup } from "telegraf";
import { config } from "./config.js";
import { logger } from "./logger.js";
import { prisma } from "@trinity/db";
import { WORKER_TEXTS } from "./worker.texts.js";
import { PROFESSIONS } from "./keyboards.js";

const CALLBACK_CONSENT = "worker_consent";
const CALLBACK_APPLY = "job:apply:";
const CALLBACK_HIDE = "job:hide:";

const profileScene = new Scenes.BaseScene<Scenes.SceneContext>("worker_profile");

profileScene.enter(async (ctx) => {
  const s = (ctx as any).scene.session as WorkerProfileSession;
  s.step = 1;
  s.lastActivity = Date.now();
  const rows = [
    PROFESSIONS.map((p) => Markup.button.callback(p, `worker_prof:${p}`)),
    [Markup.button.callback("Готово", "worker_prof_done")],
  ];
  await ctx.reply(WORKER_TEXTS.profile.professions, Markup.inlineKeyboard(rows.flat()));
});

profileScene.action(/^worker_prof:(.+)$/, async (ctx) => {
  const prof = ctx.match[1]!;
  const s = (ctx as any).scene.session as WorkerProfileSession;
  s.professions = s.professions ?? [];
  if (!s.professions.includes(prof)) {
    s.professions = [...s.professions, prof];
  }
  s.lastActivity = Date.now();
  await ctx.answerCbQuery();
  await ctx.reply(`Добавлено: ${prof}. Выберите ещё или «Готово».`);
});

profileScene.action("worker_prof_done", async (ctx) => {
  const s = (ctx as any).scene.session as WorkerProfileSession;
  if (!s.professions?.length) {
    await ctx.answerCbQuery();
    return ctx.reply("Выберите хотя бы одну профессию.");
  }
  s.step = 2;
  s.lastActivity = Date.now();
  await ctx.answerCbQuery();
  await ctx.reply(WORKER_TEXTS.profile.city);
});

profileScene.on("text", async (ctx) => {
  const s = (ctx as any).scene.session as WorkerProfileSession;
  const text = ctx.message.text?.trim() ?? "";

  if (s.step === 2) {
    s.city = text || null;
    s.step = 3;
    return ctx.reply(WORKER_TEXTS.profile.area);
  }

  if (s.step === 3) {
    if (text.toLowerCase() === "/skip") {
      s.area = null;
    } else {
      s.area = text || null;
    }
    s.step = 4;
    return ctx.reply(WORKER_TEXTS.profile.minRate);
  }

  if (s.step === 4) {
    if (text.toLowerCase() === "/skip") {
      s.minRate = null;
    } else {
      const n = parseInt(text.replace(/\s/g, ""), 10);
      if (isNaN(n) || n < 0) {
        return ctx.reply("Введите число или /skip:");
      }
      s.minRate = n;
    }
    await saveWorkerProfile(ctx, s);
    await ctx.reply(WORKER_TEXTS.profile.saved);
    return (ctx as any).scene.leave();
  }
});

async function saveWorkerProfile(ctx: any, s: WorkerProfileSession): Promise<void> {
  const tid = BigInt(ctx.from!.id);
  let worker = await prisma.worker.findUnique({ where: { telegramId: tid } });
  if (!worker) {
    worker = await prisma.worker.create({
      data: {
        telegramId: tid,
        username: ctx.from?.username ?? null,
        firstName: ctx.from?.first_name ?? "User",
        lastName: ctx.from?.last_name ?? null,
        professions: s.professions ?? [],
        city: s.city ?? null,
        area: s.area ?? null,
        minRate: s.minRate ?? null,
      },
    });
  } else {
    await prisma.worker.update({
      where: { id: worker.id },
      data: {
        professions: s.professions ?? [],
        city: s.city ?? null,
        area: s.area ?? null,
        minRate: s.minRate ?? null,
      },
    });
  }
}

interface WorkerProfileSession {
  step?: number;
  professions?: string[];
  city?: string | null;
  area?: string | null;
  minRate?: number | null;
  lastActivity?: number;
}

const stage = new Scenes.Stage([profileScene] as any);

export const workerBot = new Telegraf(config.botTokenWorker);
workerBot.use(session());
workerBot.use(stage.middleware() as any);

workerBot.start(async (ctx) => {
  const tid = BigInt(ctx.from!.id);
  let worker = await prisma.worker.findUnique({ where: { telegramId: tid } });
  if (!worker) {
    worker = await prisma.worker.create({
      data: {
        telegramId: tid,
        username: ctx.from!.username ?? null,
        firstName: ctx.from!.first_name ?? "User",
        lastName: ctx.from!.last_name ?? null,
      },
    });
  }
  if (!worker.isConsented) {
    await ctx.reply(
      WORKER_TEXTS.start.greeting + "\n\n" + WORKER_TEXTS.start.consent,
      Markup.inlineKeyboard([Markup.button.callback("✅ Согласен", CALLBACK_CONSENT)])
    );
    return;
  }
  await ctx.reply(WORKER_TEXTS.start.greeting + "\n\n" + WORKER_TEXTS.start.mainMenu, workerMainMenu());
});

workerBot.action(CALLBACK_CONSENT, async (ctx) => {
  const tid = BigInt(ctx.from!.id);
  await prisma.worker.update({
    where: { telegramId: tid },
    data: { isConsented: true, consentedAt: new Date() },
  });
  await ctx.answerCbQuery();
  await ctx.reply("Спасибо! Заполните анкету, чтобы получать вакансии.", workerMainMenu());
});

function workerMainMenu() {
  return Markup.keyboard([
    [Markup.button.text(WORKER_TEXTS.menu.profile)],
    [Markup.button.text(WORKER_TEXTS.menu.filters), Markup.button.text(WORKER_TEXTS.menu.pause)],
    [Markup.button.text(WORKER_TEXTS.menu.help)],
  ]).resize();
}

workerBot.hears(WORKER_TEXTS.menu.profile, async (ctx) => {
  const tid = BigInt(ctx.from!.id);
  const worker = await prisma.worker.findUnique({ where: { telegramId: tid } });
  if (!worker?.isConsented) {
    return ctx.reply(WORKER_TEXTS.errors.consentRequired);
  }
  await (ctx as any).scene.enter("worker_profile");
});

workerBot.hears(WORKER_TEXTS.menu.filters, (ctx) =>
  ctx.reply(WORKER_TEXTS.filters.text)
);

workerBot.hears(WORKER_TEXTS.menu.pause, async (ctx) => {
  const tid = BigInt(ctx.from!.id);
  const worker = await prisma.worker.findUnique({ where: { telegramId: tid } });
  if (!worker) return ctx.reply(WORKER_TEXTS.errors.generic);
  const next = !worker.isActive;
  await prisma.worker.update({
    where: { id: worker.id },
    data: { isActive: next },
  });
  if (next) {
    await ctx.reply(WORKER_TEXTS.pause.off, workerMainMenu());
  } else {
    await ctx.reply(
      WORKER_TEXTS.pause.on,
      Markup.keyboard([[Markup.button.text("▶️ Продолжить")]]).resize()
    );
  }
});

workerBot.hears("▶️ Продолжить", async (ctx) => {
  const tid = BigInt(ctx.from!.id);
  await prisma.worker.updateMany({
    where: { telegramId: tid },
    data: { isActive: true },
  });
  await ctx.reply("Уведомления включены ✅", workerMainMenu());
});

workerBot.hears(WORKER_TEXTS.menu.help, (ctx) => ctx.reply(WORKER_TEXTS.help.text));

workerBot.action(new RegExp(`^${CALLBACK_APPLY}(.+)$`), async (ctx) => {
  const jobId = ctx.match[1]!;
  await ctx.answerCbQuery();
  const tid = BigInt(ctx.from!.id);
  const worker = await prisma.worker.findUnique({ where: { telegramId: tid } });
  if (!worker) return ctx.reply(WORKER_TEXTS.errors.generic);

  const job = await prisma.job.findUnique({
    where: { id: jobId },
    include: { employer: true },
  });
  if (!job || job.status !== "OPEN") {
    return ctx.reply("Заявка больше недоступна.");
  }

  const existing = await prisma.application.findUnique({
    where: { jobId_workerId: { jobId, workerId: worker.id } },
  });
  if (existing) {
    return ctx.reply(WORKER_TEXTS.apply.already);
  }

  await prisma.application.create({
    data: { jobId, workerId: worker.id },
  });

  const workerLabel = worker.username ? `@${worker.username}` : worker.firstName;
  const notifyText = `📩 Новый отклик на заявку ${jobId}:\n${workerLabel} / ${worker.firstName}`;

  try {
    const { bot: employerBot } = await import("./bot.js");
    await employerBot.telegram.sendMessage(Number(job.employer.telegramId), notifyText);
  } catch (e) {
    logger.warn({ err: e, jobId }, "Failed to notify employer of application");
  }

  await ctx.reply(WORKER_TEXTS.apply.success);
  logger.info({ jobId, workerId: worker.id }, "Application created");
});

workerBot.action(new RegExp(`^${CALLBACK_HIDE}(.+)$`), async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.deleteMessage().catch(() => {});
  await ctx.reply(WORKER_TEXTS.hide.done);
});

workerBot.catch((err, ctx) => {
  const errMsg = err instanceof Error ? err.message : String(err);
  logger.error({ err, errMsg, update: ctx.update }, "WorkerBot error");
  ctx.reply(WORKER_TEXTS.errors.generic).catch(() => {});
});
