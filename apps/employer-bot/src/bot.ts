import { Telegraf, session } from "telegraf";
import { Scenes } from "telegraf";
import { config } from "./config.js";
import { logger } from "./logger.js";
import { prisma } from "@trinity/db";
import { createJobScene } from "./scenes/createJob.js";
import { Markup } from "telegraf";
import {
  mainMenu,
  consentKeyboard,
  CALLBACK,
} from "./keyboards.js";
import { TEXTS } from "./texts.js";
import { formatJobCard } from "./formatters.js";
export const bot = new Telegraf(config.botToken);

const stage = new Scenes.Stage([createJobScene] as any);

bot.use(session());
bot.use(stage.middleware() as any);

bot.start(async (ctx) => {
  const tid = BigInt(ctx.from!.id);
  let employer = await prisma.employer.findUnique({
    where: { telegramId: tid },
  });
  if (!employer) {
    employer = await prisma.employer.create({
      data: {
        telegramId: tid,
        username: ctx.from!.username ?? null,
        firstName: ctx.from!.first_name ?? "User",
        lastName: ctx.from!.last_name ?? null,
      },
    });
  }
  if (!employer.isConsented) {
    await ctx.reply(TEXTS.start.greeting + "\n\n" + TEXTS.start.consent, consentKeyboard());
    return;
  }
  await ctx.reply(TEXTS.start.greeting + "\n\n" + TEXTS.start.mainMenu, mainMenu());
});

bot.action(CALLBACK.consent, async (ctx) => {
  const tid = BigInt(ctx.from!.id);
  await prisma.employer.update({
    where: { telegramId: tid },
    data: { isConsented: true, consentedAt: new Date() },
  });
  await ctx.answerCbQuery();
  await ctx.reply("Спасибо! Теперь вы можете создавать заявки.", mainMenu());
});

bot.hears("➕ Создать заявку", async (ctx) => {
  const tid = BigInt(ctx.from!.id);
  const employer = await prisma.employer.findUnique({
    where: { telegramId: tid },
  });
  if (!employer?.isConsented) {
    return ctx.reply(TEXTS.errors.consentRequired);
  }
  await (ctx as any).scene.enter("create_job");
});

async function showMyJobs(ctx: any, page: number = 1) {
  const tid = BigInt(ctx.from!.id);
  const employer = await prisma.employer.findUnique({
    where: { telegramId: tid },
  });
  if (!employer) {
    logger.warn({ telegramId: ctx.from?.id }, "showMyJobs: employer not found");
    return ctx.reply(TEXTS.errors.generic);
  }
  const PER_PAGE = 5;
  const all = await prisma.job.findMany({
    where: { employerId: employer.id, status: { not: "DELETED" } },
    orderBy: { createdAt: "desc" },
  });
  const totalPages = Math.max(1, Math.ceil(all.length / PER_PAGE));
  const start = (page - 1) * PER_PAGE;
  const jobs = all.slice(start, start + PER_PAGE);
  if (jobs.length === 0) {
    return ctx.reply(TEXTS.myJobs.empty);
  }
  const lines = jobs.map((j) => formatJobCard(j) + `\n[${j.id}]`);
  const text = TEXTS.myJobs.title + "\n\n" + lines.join("\n\n") + `\n\n${TEXTS.myJobs.page.replace("{page}", String(page)).replace("{total}", String(totalPages))}`;
  const rows: any[] = [];
  for (const j of jobs) {
    rows.push([
      Markup.button.callback("🛑", CALLBACK.myJobsClose(j.id)),
      Markup.button.callback("🗑", CALLBACK.myJobsDelete(j.id)),
      Markup.button.callback("🔁", CALLBACK.myJobsRepeat(j.id)),
    ]);
  }
  const nav: any[] = [];
  if (page > 1) nav.push(Markup.button.callback("⬅️", CALLBACK.myJobsPage(page - 1)));
  if (page < totalPages) nav.push(Markup.button.callback("➡️", CALLBACK.myJobsPage(page + 1)));
  if (nav.length) rows.push(nav);
  return ctx.reply(text, Markup.inlineKeyboard(rows));
}

bot.hears("📄 Мои заявки", async (ctx) => showMyJobs(ctx, 1));
bot.command("my", async (ctx) => showMyJobs(ctx, 1));

bot.action(/^my_page:(\d+)$/, async (ctx) => {
  const page = parseInt(ctx.match[1]!, 10);
  await ctx.answerCbQuery();
  const tid = BigInt(ctx.from!.id);
  const employer = await prisma.employer.findUnique({
    where: { telegramId: tid },
  });
  if (!employer) return;
  const PER_PAGE = 5;
  const all = await prisma.job.findMany({
    where: { employerId: employer.id, status: { not: "DELETED" } },
    orderBy: { createdAt: "desc" },
  });
  const totalPages = Math.max(1, Math.ceil(all.length / PER_PAGE));
  const start = (page - 1) * PER_PAGE;
  const jobs = all.slice(start, start + PER_PAGE);
  if (jobs.length === 0) return;
  const lines = jobs.map((j) => formatJobCard(j) + `\n[${j.id}]`);
  const text = TEXTS.myJobs.title + "\n\n" + lines.join("\n\n") + `\n\n${TEXTS.myJobs.page.replace("{page}", String(page)).replace("{total}", String(totalPages))}`;
  const rows: any[] = [];
  for (const j of jobs) {
    rows.push([
      Markup.button.callback("🛑", CALLBACK.myJobsClose(j.id)),
      Markup.button.callback("🗑", CALLBACK.myJobsDelete(j.id)),
      Markup.button.callback("🔁", CALLBACK.myJobsRepeat(j.id)),
    ]);
  }
  const nav: any[] = [];
  if (page > 1) nav.push(Markup.button.callback("⬅️", CALLBACK.myJobsPage(page - 1)));
  if (page < totalPages) nav.push(Markup.button.callback("➡️", CALLBACK.myJobsPage(page + 1)));
  if (nav.length) rows.push(nav);
  await ctx.editMessageText(text, Markup.inlineKeyboard(rows));
});

bot.action(/^my_close:(.+)$/, async (ctx) => {
  const jobId = ctx.match[1]!;
  const tid = BigInt(ctx.from!.id);
  const employer = await prisma.employer.findUnique({
    where: { telegramId: tid },
  });
  if (!employer) return ctx.answerCbQuery();
  const job = await prisma.job.findFirst({
    where: { id: jobId, employerId: employer.id },
  });
  if (!job) return ctx.answerCbQuery();
  await prisma.job.update({
    where: { id: jobId },
    data: { status: "CLOSED" },
  });
  await ctx.answerCbQuery();
  await ctx.reply(TEXTS.myJobs.closed);
});

bot.action(/^my_del:(.+)$/, async (ctx) => {
  const jobId = ctx.match[1]!;
  const tid = BigInt(ctx.from!.id);
  const employer = await prisma.employer.findUnique({
    where: { telegramId: tid },
  });
  if (!employer) return ctx.answerCbQuery();
  const job = await prisma.job.findFirst({
    where: { id: jobId, employerId: employer.id },
  });
  if (!job) return ctx.answerCbQuery();
  await prisma.job.update({
    where: { id: jobId },
    data: { status: "DELETED" },
  });
  await ctx.answerCbQuery();
  await ctx.reply(TEXTS.myJobs.deleted);
});

bot.action(/^my_rep:(.+)$/, async (ctx) => {
  const jobId = ctx.match[1]!;
  await ctx.answerCbQuery();
  const tid = BigInt(ctx.from!.id);
  const employer = await prisma.employer.findUnique({
    where: { telegramId: tid },
  });
  if (!employer) return;
  const job = await prisma.job.findFirst({
    where: { id: jobId, employerId: employer.id },
  });
  if (!job) return;
  await (ctx as any).scene.enter("create_job", { profession: job.profession, location: job.location, ratePerHour: job.ratePerHour });
});

bot.hears("❓ Помощь", (ctx) => ctx.reply(TEXTS.help.text));
bot.hears("⚙️ Настройки", (ctx) => ctx.reply("Настройки в разработке."));

bot.catch((err, ctx) => {
  const errMsg = err instanceof Error ? err.message : String(err);
  const errStack = err instanceof Error ? err.stack : undefined;
  logger.error(
    { err, errMsg, errStack, update: ctx.update, updateType: ctx.updateType },
    "Bot error (generic handler)"
  );
  ctx.reply(TEXTS.errors.generic).catch(() => {});
});
