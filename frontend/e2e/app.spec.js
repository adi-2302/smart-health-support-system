import { test, expect } from "@playwright/test";
import { DEMO, PASSWORD, fillCheckin, localISO, login, register, scoreOf, signOut, uniqueEmail } from "./helpers.js";

// Automated versions of the manual test cases (MindTrack_Manual_Test_Cases.xlsx). The TC numbers in
// the titles match that sheet. Tests run in order and share one throwaway database.
test.describe.configure({ mode: "serial" });

const A = { email: uniqueEmail("studenta"), name: "Test Student" };
const B = { email: uniqueEmail("studentb"), name: "Second Student" };
let resultScoreA = null;

async function loginA(page) { await login(page, A.email, PASSWORD); await expect(page.getByRole("heading", { name: /^Hello,/ })).toBeVisible(); }

test.describe("Registration & login", () => {
  test("TC01 register with valid details", async ({ page }) => {
    await register(page, { ...A, examInDays: 20 });
    await expect(page.getByRole("heading", { name: "Hello, Test" })).toBeVisible();
    await expect(page.getByText("Not checked in yet")).toBeVisible();
    await expect(page.getByText(/20 days to/)).toBeVisible();   // exam countdown computed automatically
  });

  test("TC02 short password is rejected", async ({ page }) => {
    await register(page, { name: "X", email: uniqueEmail("short"), password: "abc123" });
    await expect(page).toHaveURL(/\/register$/);
    await expect(page.getByRole("heading", { name: "Create your account" })).toBeVisible();
  });

  test("TC03 duplicate email is rejected", async ({ page }) => {
    await register(page, { name: "Dup", email: A.email });
    await expect(page.getByRole("alert")).toContainText("An account with this email already exists");
  });

  test("TC05 age outside 15-60 is rejected", async ({ page }) => {
    await register(page, { name: "Young", email: uniqueEmail("age"), extra: { age: 12 } });
    await expect(page).toHaveURL(/\/register$/);
  });

  test("TC06 login works", async ({ page }) => {
    await login(page, DEMO.email, DEMO.password);
    await expect(page.getByRole("heading", { name: "Hello, Demo" })).toBeVisible();
    await expect(page.getByText(/9 days to Semester 7 finals/)).toBeVisible();
  });

  test("TC07 wrong password", async ({ page }) => {
    await login(page, DEMO.email, "wrongpass1");
    await expect(page.getByRole("alert")).toHaveText("Incorrect email or password");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("TC08 unknown email gets the same message", async ({ page }) => {
    await login(page, "nobody@example.com", PASSWORD);
    await expect(page.getByRole("alert")).toHaveText("Incorrect email or password");
  });

  test("TC09 protected pages redirect to login", async ({ page }) => {
    await page.goto("/weekly");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("TC10 session survives refresh", async ({ page }) => {
    await loginA(page);
    await page.reload();
    await expect(page.getByRole("heading", { name: /^Hello,/ })).toBeVisible();
  });

  test("TC11 sign out, then Back does not reveal data", async ({ page }) => {
    await loginA(page);
    await signOut(page);
    await page.goBack();
    await expect(page.getByRole("heading", { name: /^Hello,/ })).toHaveCount(0);
    await page.goto("/");               // the dashboard URL no longer works without a login
    await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  });
});

test.describe("Check-in and result", () => {
  test("TC12 questionnaire layout and TC13 counter", async ({ page }) => {
    await loginA(page);
    await page.goto("/checkin");
    await expect(page.getByRole("heading", { name: "Daily check-in" })).toBeVisible();
    for (const g of ["Mind", "Body", "Studies", "People", "Surroundings"]) {
      await expect(page.getByRole("heading", { name: g, exact: true })).toBeVisible();
    }
    await expect(page.locator("fieldset.q")).toHaveCount(19);
    await expect(page.getByText("0 of 19 answered")).toBeVisible();
    await page.locator('label.opt:has(input[name="anxiety_level"])').nth(2).click();
    await page.locator('label.opt:has(input[name="headache"])').nth(1).click();
    await page.locator('label.opt:has(input[name="bullying"])').nth(0).click();
    await expect(page.getByText("3 of 19 answered")).toBeVisible();
  });

  test("TC14 incomplete check-in is not submitted", async ({ page }) => {
    await loginA(page);
    await page.goto("/checkin");
    await page.locator('label.opt:has(input[name="headache"])').nth(1).click();
    await page.getByRole("button", { name: "See my result" }).click();
    await expect(page.getByRole("alert")).toContainText("Please answer:");
    await expect(page).toHaveURL(/\/checkin$/);
    await page.goto("/");
    await expect(page.getByText("Not checked in yet")).toBeVisible();
  });

  test("TC15 healthy answers give a Low result (first check-in)", async ({ page }) => {
    await loginA(page);
    await page.goto("/checkin");
    await fillCheckin(page, "healthy");
    await page.getByRole("button", { name: "See my result" }).click();
    await expect(page).toHaveURL(/\/result$/);
    await expect(page.getByText("Most likely: Low")).toBeVisible();
    resultScoreA = await scoreOf(page);
    expect(resultScoreA).toBeLessThan(1.5);
    await expect(page.getByText("This is your first check-in")).toBeVisible();
    await expect(page.getByText("Early-warning check")).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Why this result?" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "What might help" })).toBeVisible();
  });

  test("TC18 probabilities add up to about 100%", async ({ page }) => {
    await loginA(page);
    await page.goto("/result");
    await expect(page.getByText("How sure is the model?")).toBeVisible();
    const pct = await page.locator(".bar-row .bar-val").allInnerTexts();
    const probs = pct.filter((t) => t.endsWith("%")).map((t) => parseInt(t, 10));
    expect(probs).toHaveLength(3);
    expect(probs.reduce((a, b) => a + b, 0)).toBeGreaterThanOrEqual(98);
    expect(probs.reduce((a, b) => a + b, 0)).toBeLessThanOrEqual(102);
  });

  test("TC21 refresh keeps the same result", async ({ page }) => {
    await loginA(page);
    await page.goto("/result");
    await page.reload();
    await expect(page.getByText("Most likely: Low")).toBeVisible();
    expect(await scoreOf(page)).toBe(resultScoreA);
  });

  test("TC22 only one check-in per day", async ({ page }) => {
    await loginA(page);
    await page.goto("/checkin");
    await expect(page.getByText("You've already checked in today")).toBeVisible();
    await expect(page.locator("fieldset.q")).toHaveCount(0);
  });

  test("TC23 dashboard matches the result", async ({ page }) => {
    await loginA(page);
    await expect(page.getByText("Most likely: Low")).toBeVisible();
    expect(await scoreOf(page)).toBe(resultScoreA);
    await expect(page.getByText(/vs last check-in: first one/)).toBeVisible();
  });

  test("TC16-17,19-20 worst answers: High, early warning, SHAP, exam-aware advice (demo account)", async ({ page }) => {
    await login(page, DEMO.email, DEMO.password);
    await expect(page.getByText("Not checked in yet")).toBeVisible();
    await page.goto("/checkin");
    await fillCheckin(page, "worst");
    await page.getByRole("button", { name: "See my result" }).click();
    await expect(page).toHaveURL(/\/result$/);
    await expect(page.getByText("Most likely: High")).toBeVisible();
    expect(await scoreOf(page)).toBeGreaterThanOrEqual(8.5);
    // rising trend 3 check-ins in a row -> early warning
    await expect(page.getByText("Early-warning check")).toBeVisible();
    // SHAP bars: between 1 and 6 factors, labelled with signed values
    const factors = page.locator("section:has(h2:text('Why this result?')) .bar-row");
    expect(await factors.count()).toBeGreaterThanOrEqual(1);
    expect(await factors.count()).toBeLessThanOrEqual(6);
    await expect(page.getByText("Main stress drivers today:")).toBeVisible();
    // recommendations mention the exam (demo exam is 9 days away)
    await expect(page.locator(".rec").filter({ hasText: "Exam in 9 days" })).toBeVisible();
    expect(await page.locator(".rec").count()).toBeGreaterThanOrEqual(2);
    await page.screenshot({ path: "e2e-results/result-high.png", fullPage: true });
  });
});

test.describe("Dashboard, weekly report, insights", () => {
  test("TC24-25 dashboard trend and exam countdown (demo)", async ({ page }) => {
    await login(page, DEMO.email, DEMO.password);
    await expect(page.getByText("Last 14 days")).toBeVisible();
    await expect(page.locator("svg.chart circle")).toHaveCount(7);   // 6 seeded days + today
    await expect(page.getByText("Exam period")).toBeVisible();        // 9 days <= 14
  });

  test("TC26-28 weekly report content and navigation", async ({ page }) => {
    await login(page, DEMO.email, DEMO.password);
    await expect(page.getByRole("heading", { name: "Hello, Demo" })).toBeVisible();
    await page.goto("/weekly");
    await expect(page.getByRole("heading", { name: "Weekly report" })).toBeVisible();
    await expect(page.locator(".stat", { hasText: "Check-ins" }).locator(".value")).toContainText("7");
    await expect(page.getByText("No earlier week to compare yet")).toBeVisible();
    await expect(page.getByRole("heading", { name: "What drove your stress" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Next week" })).toBeDisabled();
    await page.getByRole("button", { name: "Previous week" }).click();
    await page.getByRole("button", { name: "Previous week" }).click();
    await expect(page.getByText("No check-ins this week").first()).toBeVisible();
  });

  test("TC29 insights lists features with Blood pressure first", async ({ page }) => {
    await loginA(page);
    await page.goto("/insights");
    const rows = page.locator(".bar-row");
    await expect(rows).toHaveCount(12);
    await expect(rows.first()).toContainText("Blood pressure");
  });
});

test.describe("Profile and settings", () => {
  test("TC30 profile shows registration details", async ({ page }) => {
    await loginA(page);
    await page.goto("/profile");
    await expect(page.getByText(A.email)).toBeVisible();
    await expect(page.getByText("Test Student")).toBeVisible();
  });

  test("TC31 changing the exam date updates the countdown", async ({ page }) => {
    await loginA(page);
    await page.goto("/settings");
    await page.getByLabel("Exam date", { exact: true }).fill(localISO(30));
    await page.getByLabel("Exam name", { exact: true }).fill("Final viva");
    await page.getByRole("button", { name: "Save exam date" }).click();
    await expect(page.getByText("Exam date updated")).toBeVisible();
    await page.goto("/");
    await expect(page.getByText("30 days to Final viva")).toBeVisible();
    await expect(page.getByText("Exam period")).toHaveCount(0);      // 30 > 14 days
  });

  test("TC32 theme choice persists across refresh", async ({ page }) => {
    await loginA(page);
    await page.goto("/settings");
    await page.getByRole("button", { name: "Dark" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page.getByRole("button", { name: "System" }).click();
    await expect(page.locator("html")).not.toHaveAttribute("data-theme", /.+/);
  });
});

test.describe("Security, robustness, usability", () => {
  test("TC33 another user's data is not visible", async ({ page }) => {
    await register(page, { ...B, examInDays: 15 });
    await expect(page.getByRole("heading", { name: "Hello, Second" })).toBeVisible();
    await expect(page.getByText("Not checked in yet")).toBeVisible();
    await expect(page.getByText("No history yet")).toBeVisible();
    await page.goto("/weekly");
    await expect(page.getByText("No check-ins this week")).toBeVisible();
  });

  test("TC34 tampered token sends you back to login", async ({ page }) => {
    await loginA(page);
    await page.evaluate(() => localStorage.setItem("mindtrack.token", "abc"));
    await page.reload();
    await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  });

  test("TC35 friendly message when the backend is unreachable", async ({ page }) => {
    await page.route("http://localhost:8001/**", (route) => route.abort());
    await login(page, DEMO.email, DEMO.password);
    await expect(page.getByRole("alert")).toContainText("Can't reach the server");
  });

  test("TC36 API docs and health check", async ({ request }) => {
    const health = await request.get("http://localhost:8001/health");
    expect(await health.json()).toEqual({ status: "ok" });
    expect((await request.get("http://localhost:8001/docs")).ok()).toBeTruthy();
  });

  test("TC37 phone width has no sideways scrolling", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await login(page, DEMO.email, DEMO.password);
    await expect(page.getByRole("heading", { name: "Hello, Demo" })).toBeVisible();
    for (const path of ["/", "/result", "/weekly", "/insights", "/profile", "/settings"]) {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, `horizontal overflow on ${path}`).toBeLessThanOrEqual(0);
    }
    await page.goto("/");
    await page.screenshot({ path: "e2e-results/mobile-dashboard.png", fullPage: true });
  });

  test("TC38 keyboard can choose answers", async ({ page }) => {
    await login(page, B.email, PASSWORD);
    await expect(page.getByRole("heading", { name: "Hello, Second" })).toBeVisible();
    await page.goto("/checkin");
    const first = page.locator('input[name="anxiety_level"]').first();
    await first.focus();
    await page.keyboard.press("Space");
    await expect(first).toBeChecked();
    await page.keyboard.press("ArrowRight");
    await expect(page.locator('input[name="anxiety_level"]').nth(1)).toBeChecked();
    await expect(page.getByText("1 of 19 answered")).toBeVisible();
  });
});
