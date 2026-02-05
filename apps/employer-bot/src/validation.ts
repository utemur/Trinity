const DATE_REG = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/;
const TIME_REG = /^(\d{1,2}):(\d{2})$/;

export function parseDate(input: string): { valid: boolean; date?: Date; error?: string } {
  const m = input.trim().match(DATE_REG);
  if (!m) return { valid: false, error: "invalid_format" };
  const [, d, mo, y] = m;
  const day = parseInt(d!, 10);
  const month = parseInt(mo!, 10) - 1;
  const year = parseInt(y!, 10);
  const date = new Date(year, month, day);
  if (date.getFullYear() !== year || date.getMonth() !== month || date.getDate() !== day) {
    return { valid: false, error: "invalid_date" };
  }
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (date < today) return { valid: false, error: "past" };
  return { valid: true, date };
}

export function parseTime(input: string): { valid: boolean; error?: string } {
  const m = input.trim().match(TIME_REG);
  if (!m) return { valid: false, error: "invalid_format" };
  const [, h, min] = m;
  const hour = parseInt(h!, 10);
  const minute = parseInt(min!, 10);
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) {
    return { valid: false, error: "invalid_time" };
  }
  return { valid: true };
}

export function parseRate(input: string): { valid: boolean; value?: number } {
  const n = parseInt(input.trim().replace(/\s/g, ""), 10);
  if (isNaN(n) || n <= 0) return { valid: false };
  return { valid: true, value: n };
}
