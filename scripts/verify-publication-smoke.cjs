// Engineering smoke only; fresh guest, no real target or human research.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const out = path.resolve(__dirname, "../../../work/phase10"),
  base = "http://127.0.0.1:16273";
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch(),
    rows = [],
    errors = [],
    violations = [];
  try {
    for (const locale of ["en", "ru", "kk"]) {
      const context = await browser.newContext(),
        page = await context.newPage();
      await page.addInitScript({
        path: require.resolve("axe-core/axe.min.js", {
          paths: [
            path.dirname(process.env.AXE_MODULE || require.resolve("axe-core")),
          ],
        }),
      });
      page.on("pageerror", (e) => errors.push(e.name));
      await context.route("**/*", (route) => {
        const u = new URL(route.request().url());
        if (["http:", "https:"].includes(u.protocol) && u.origin !== base)
          throw Error("Unexpected external request");
        return route.continue();
      });
      const response = await page.goto(base + "/demo");
      const csp = response.headers()["content-security-policy"];
      assert(csp.includes("script-src 'self'"));
      assert(!csp.includes("'unsafe-inline'"));
      await page
        .getByRole("button", {
          name: { en: "English", ru: "Русский", kk: "Қазақша" }[locale],
          exact: true,
        })
        .click();
      await page.locator(".demo-steps button").first().waitFor();
      for (const width of [360, 768, 1280, 1920]) {
        await page.setViewportSize({ width, height: 1000 });
        assert.equal(await page.locator("html").getAttribute("lang"), locale);
        assert(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth + 1,
          ),
        );
        const result = await page.evaluate(() => axe.run());
        violations.push(
          ...result.violations.map((v) => ({
            locale,
            width,
            id: v.id,
            nodes: v.nodes.map((n) => ({
              target: n.target,
              summary: n.failureSummary,
              html: n.html,
            })),
          })),
        );
        rows.push({
          locale,
          width,
          overflow: false,
          axe_violations: result.violations.length,
        });
      }
      const pdfResponse = await context.request.get(
        base + "/api/v1/demo/report?locale=" + locale,
      );
      assert.equal(pdfResponse.status(), 200);
      assert(
        pdfResponse.headers()["content-type"].startsWith("application/pdf"),
      );
      fs.writeFileSync(
        path.join(out, "smoke-DEMO-" + locale + ".pdf"),
        await pdfResponse.body(),
      );
      assert.equal((await context.cookies()).length, 0);
      await context.close();
    }
    const ctx = await browser.newContext(),
      page = await ctx.newPage();
    await page.goto(base + "/app");
    await page.waitForURL("**/login**");
    assert.equal(
      (await ctx.request.get(base + "/api/v1/reports")).status(),
      401,
    );
    const private_redirect = page.url().includes("/login");
    await page.goto(base + "/not-a-route");
    assert.equal(await page.locator("main h1").count(), 1);
    await browser.close();
    fs.writeFileSync(
      path.join(out, "smoke-attempt.json"),
      JSON.stringify({ rows, errors, violations }, null, 2),
    );
    assert.deepEqual(errors, []);
    assert.deepEqual(violations, []);
    fs.writeFileSync(
      path.join(out, "smoke.json"),
      JSON.stringify(
        {
          classification: "AUTOMATED ENGINEERING ONLY",
          origin: base,
          cases: rows,
          page_errors: errors,
          axe_violations: violations,
          private_redirect,
          foreign_private_no_session: 401,
          demo_pdfs: 3,
        },
        null,
        2,
      ) + "\n",
    );
    console.log(
      "PASS: 12 localized responsive axe views, 3 demo PDFs, private redirect and unauthenticated denial",
    );
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e.message);
  process.exitCode = 1;
});
