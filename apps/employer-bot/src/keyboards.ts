import { Markup } from "telegraf";

const PROFESSIONS = [
  "Грузчик",
  "Курьер",
  "Официант",
  "Повар",
  "Уборка",
  "Строитель",
] as const;

export const CALLBACK = {
  consent: "consent",
  createJob: "create_job",
  myJobs: "my_jobs",
  help: "help",
  settings: "settings",
  profession: (p: string) => `prof:${p}`,
  professionOther: "prof:other",
  wizardCancel: "wizard_cancel",
  wizardPublish: "wizard_publish",
  wizardEdit: "wizard_edit",
  myJobsPage: (page: number) => `my_page:${page}`,
  myJobsClose: (id: string) => `my_close:${id}`,
  myJobsDelete: (id: string) => `my_del:${id}`,
  myJobsRepeat: (id: string) => `my_rep:${id}`,
} as const;

export function mainMenu() {
  return Markup.keyboard([
    [Markup.button.text("➕ Создать заявку")],
    [Markup.button.text("📄 Мои заявки")],
    [Markup.button.text("❓ Помощь"), Markup.button.text("⚙️ Настройки")],
  ]).resize();
}

export function consentKeyboard() {
  return Markup.inlineKeyboard([Markup.button.callback("✅ Согласен", CALLBACK.consent)]);
}

export function professionKeyboard() {
  const rows = [
    PROFESSIONS.map((p) => Markup.button.callback(p, CALLBACK.profession(p))),
    [Markup.button.callback("Другое", CALLBACK.professionOther)],
    [Markup.button.callback("❌ Отмена", CALLBACK.wizardCancel)],
  ];
  return Markup.inlineKeyboard(rows.flat());
}

export function confirmKeyboard() {
  return Markup.inlineKeyboard([
    [Markup.button.callback("✅ Опубликовать", CALLBACK.wizardPublish)],
    [Markup.button.callback("✏️ Изменить", CALLBACK.wizardEdit)],
    [Markup.button.callback("❌ Отмена", CALLBACK.wizardCancel)],
  ]);
}

export { PROFESSIONS };
