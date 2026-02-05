interface JobLike {
  id?: string;
  profession: string;
  date: string;
  time: string;
  location: string;
  ratePerHour: number;
  currency?: string;
}
import { TEXTS } from "./texts.js";

export function formatJobCard(job: JobLike): string {
  return TEXTS.card.format
    .replace("{id}", job.id ?? "—")
    .replace("{profession}", job.profession)
    .replace("{date}", job.date)
    .replace("{time}", job.time)
    .replace("{location}", job.location)
    .replace("{rate}", job.ratePerHour.toLocaleString())
    .replace("{currency}", job.currency ?? "UZS");
}
