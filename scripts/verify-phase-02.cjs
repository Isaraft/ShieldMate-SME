const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const output = path.resolve(
  process.env.EVIDENCE_DIR || path.join(__dirname, "../docs/evidence/phase-02"),
);
const base = process.env.BASE_URL || "http://127.0.0.1:5173";
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  const email = `qa-${crypto.randomUUID()}@example.com`;
  const password = crypto.randomBytes(24).toString("base64url");
  const results = {
    browser: browser.version(),
    viewports: [],
    flow: [],
    errors: [],
  };
  page.on("pageerror", (e) => results.errors.push(e.message));
  await page.goto(base + "/app");
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  results.flow.push("unauthenticated redirect");
  await page
    .getByRole("link", { name: "Create an account", exact: true })
    .click();
  await page.getByRole("textbox", { name: "Email address" }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  await page.getByRole("textbox", { name: "Email address" }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page
    .getByRole("heading", { name: "Create your workspace", exact: true })
    .waitFor();
  results.flow.push("register and login");
  await page
    .getByRole("textbox", { name: "Company name" })
    .fill("QA workspace — local verification");
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await page
    .getByRole("heading", {
      name: "QA workspace — local verification",
      exact: true,
    })
    .waitFor();
  await page.reload();
  await page
    .getByRole("heading", {
      name: "QA workspace — local verification",
      exact: true,
    })
    .waitFor();
  results.flow.push("onboarding and session reload");
  const cookie = (await context.cookies()).find(
    (c) => c.name === "shieldmate_session",
  );
  assert(cookie.httpOnly);
  assert.equal(cookie.sameSite, "Lax");
  assert.equal(cookie.path, "/api");
  assert.equal(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
    0,
  );
  await page
    .getByRole("link", { name: "Organization settings", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Company name" })
    .fill("Renamed QA workspace");
  await page
    .getByRole("button", { name: "Save company name", exact: true })
    .click();
  await page.getByText("Workspace saved.", { exact: true }).waitFor();
  await page.reload();
  await page.getByRole("textbox", { name: "Company name" }).waitFor();
  assert.equal(
    await page.getByRole("textbox", { name: "Company name" }).inputValue(),
    "Renamed QA workspace",
  );
  results.flow.push("rename survives reload");
  for (const width of [360, 768, 1280, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    for (const [route, label] of [
      ["/app/settings", "settings"],
      ["/register", "register"],
      ["/login", "login"],
    ]) {
      await page.goto(base + route);
      await page.locator("h1").waitFor();
      await page.evaluate(() => document.fonts.ready);
      assert(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      );
      await page.screenshot({
        path: path.join(output, `${label}-${width}.png`),
        fullPage: true,
      });
      await page.evaluate(
        fs.readFileSync(
          require.resolve(process.env.AXE_MODULE || "axe-core"),
          "utf8",
        ),
      );
      const scan = await page.evaluate(async () => {
        const r = await axe.run(document, {
          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
        });
        return r.violations.map((v) => ({
          id: v.id,
          nodes: v.nodes.map((n) => n.target),
        }));
      });
      results.viewports.push({ width, route, violations: scan });
      assert.deepEqual(scan, []);
    }
  }
  const expired = await browser.newContext();
  await expired.addCookies([
    { ...cookie, value: "invalid-session-token-for-testing" },
  ]);
  const expiredPage = await expired.newPage();
  await expiredPage.goto(base + "/app/settings");
  await expiredPage
    .getByRole("heading", { name: "Sign in", exact: true })
    .waitFor();
  await expired.close();
  results.flow.push("invalid session redirects cleanly");
  await page.goto(base + "/app");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  const replay = await context.request.get(base + "/api/v1/auth/me", {
    headers: { Cookie: `shieldmate_session=${cookie.value}` },
  });
  assert.equal(replay.status(), 401);
  results.flow.push("logout revocation and replay denied");
  await page.goto(base + "/app");
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  results.flow.push("private access denied after logout");
  await page.getByRole("textbox", { name: "Email address" }).focus();
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").getAttribute("type"), "password");
  assert.equal(
    await page
      .locator(":focus")
      .evaluate((el) => getComputedStyle(el).outlineWidth),
    "3px",
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(
    await page
      .getByRole("button", { name: "Sign in", exact: true })
      .evaluate((el) => getComputedStyle(el).transitionDuration),
    "0s",
  );
  results.flow.push("keyboard focus and reduced motion");
  assert.deepEqual(results.errors, []);
  fs.writeFileSync(
    path.join(output, "browser-results.json"),
    JSON.stringify(results, null, 2),
  );
  await browser.close();
  console.log(JSON.stringify(results, null, 2));
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
