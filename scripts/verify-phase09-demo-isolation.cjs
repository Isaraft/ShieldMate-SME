// AUTOMATED ENGINEERING ONLY — fresh participant-like contexts, never human beta sessions.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs"),
  assert = require("node:assert/strict"),
  path = require("node:path");
const root = path.resolve(__dirname, ".."),
  out = path.resolve(root, "../../work/phase09/engineering/checks");
const base = "http://127.0.0.1:8080";
(async () => {
  const browser = await chromium.launch(),
    cases = [],
    denied = [],
    errors = [];
  const source = JSON.parse(
    fs.readFileSync(root + "/backend/app/reports/demo_snapshot.json"),
  );
  for (const locale of ["en", "ru", "kk"]) {
    const ctx = await browser.newContext(),
      page = await ctx.newPage(),
      requests = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await ctx.route("**/*", (r) => {
      const u = new URL(r.request().url());
      if (
        ["http:", "https:"].includes(u.protocol) &&
        (u.origin !== base ||
          (u.pathname.startsWith("/api/") &&
            !u.pathname.startsWith("/api/v1/demo")))
      ) {
        denied.push("Unexpected external/private request blocked");
        return r.abort();
      }
      return r.continue();
    });
    page.on("request", (r) => {
      const u = new URL(r.url());
      if (u.pathname.startsWith("/api/")) requests.push(u.pathname);
    });
    await page.goto(base + "/demo");
    await page
      .getByRole("button", {
        name: { en: "English", ru: "Русский", kk: "Қазақша" }[locale],
        exact: true,
      })
      .click();
    for (const width of [360, 768, 1280, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.locator(".demo-steps button").first().waitFor();
      assert.equal(await page.locator("html").getAttribute("lang"), locale);
      assert(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      );
      assert((await page.locator(".demo-banner").innerText()).includes("DEMO"));
      assert.equal(await page.locator("input,textarea,select").count(), 0);
      await page.locator(".demo-steps button").nth(2).click();
      await page.reload();
      await page.locator(".demo-steps button").first().waitFor();
      assert.equal(
        await page
          .locator(".demo-steps button")
          .first()
          .getAttribute("aria-current"),
        "step",
      );
      cases.push({ locale, width, reset_to_assets: true, read_only: true });
    }
    const response = await ctx.request.get(
      base + "/api/v1/demo?locale=" + locale,
    );
    assert(response.ok());
    const data = await response.json();
    const { template_version, ...payload } = data;
    assert.equal(template_version, "assessment-2");
    assert.deepEqual({ ...payload, locale: "en" }, source);
    assert.deepEqual(await ctx.cookies(), []);
    assert.deepEqual(await page.evaluate(() => Object.keys(localStorage)), [
      "shieldmate-language",
    ]);
    assert(requests.every((p) => p === "/api/v1/demo"));
    await ctx.close();
  }
  assert.deepEqual(denied, []);
  assert.deepEqual(errors, []);
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(
    out + "/demo-isolation.json",
    JSON.stringify(
      {
        classification: "AUTOMATED ENGINEERING — NOT HUMAN RESEARCH",
        cases,
        unexpected_requests: denied,
        page_errors: errors,
        guest_cookies: 0,
        local_storage: "language only",
        fixture_matches: true,
      },
      null,
      2,
    ) + "\n",
  );
  await browser.close();
  console.log(
    JSON.stringify(
      {
        cases: cases.length,
        unexpected_requests: denied,
        page_errors: errors,
        fixture_matches: true,
      },
      null,
      2,
    ),
  );
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
