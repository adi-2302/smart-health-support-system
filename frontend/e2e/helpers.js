import { expect } from "@playwright/test";

export const DEMO = { email: "demo@mindtrack.test", password: "demo-pass-123" };
export const PASSWORD = "password123";

// Questions where a HIGH option means a healthy answer (the rest are "bad when high").
const POSITIVE = new Set(["self_esteem", "sleep_quality", "living_conditions", "safety", "basic_needs",
  "academic_performance", "teacher_student_relationship", "social_support"]);

export function uniqueEmail(tag) {
  return `${tag}.${Date.now()}.${Math.floor(Math.random() * 1e4)}@example.com`;
}

export function localISO(offsetDays = 0) {
  const d = new Date(); d.setDate(d.getDate() + offsetDays);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export async function login(page, email, password) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

export async function register(page, { name = "Test Student", email, password = PASSWORD, examInDays = 20, extra = {} }) {
  await page.goto("/register");
  await page.getByLabel("Name", { exact: true }).fill(name);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel(/^Password/).fill(password);
  if (extra.age !== undefined) await page.getByLabel("Age").fill(String(extra.age));
  await page.getByLabel("Next exam date").fill(localISO(examInDays));
  await page.getByRole("button", { name: "Create account" }).click();
}

export async function signOut(page) {
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
}

// mode: "healthy" | "worst" | "middle"
export async function fillCheckin(page, mode) {
  await expect(page.getByRole("heading", { name: "Daily check-in" })).toBeVisible();
  const names = await page.$$eval("input[type=radio]", (els) => [...new Set(els.map((e) => e.name))]);
  expect(names).toHaveLength(19);
  for (const name of names) {
    const options = page.locator(`label.opt:has(input[name="${name}"])`);
    const n = await options.count();
    let idx;
    if (mode === "middle") idx = Math.floor(n / 2);
    else if (name === "blood_pressure") idx = mode === "healthy" ? 1 : n - 1;   // Normal / High
    else {
      const wantHigh = (mode === "healthy") === POSITIVE.has(name);
      idx = wantHigh ? n - 1 : 0;
    }
    await options.nth(idx).click();
  }
}

export async function scoreOf(page) {
  return parseFloat(await page.locator(".gauge .score").first().innerText());
}
