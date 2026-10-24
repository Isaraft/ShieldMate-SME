// Additional real-browser auth, empty/error/modal, filters, language and keyboard checks.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright"),
  fs = require("node:fs"),
  assert = require("node:assert/strict"),
  crypto = require("node:crypto");
const base = "http://127.0.0.1:15873",
  out = "docs/evidence/phase-08",
  work = "../../work";
(async () => {
  const browser = await chromium.launch(),
    context = await browser.newContext({
      storageState: work + "/phase08/golden-state.json",
    }),
    anon = await browser.newContext(),
    page = await context.newPage(),
    publicPage = await anon.newPage(),
    axe = fs.readFileSync(
      require.resolve(process.env.AXE_MODULE || "axe-core"),
      "utf8",
    );
  let views = fs.existsSync(out + "/checks/interactions.json")
      ? JSON.parse(fs.readFileSync(out + "/checks/interactions.json")).views
      : [],
    flows = [];
  async function check(p, name, lang, width) {
    if (
      views.some((v) => v.name === name && v.lang === lang && v.width === width)
    )
      return;
    await p.bringToFront();
    await p.evaluate(() => document.fonts.ready);
    if (name === "domain-dialog") {
      const geometry = await p.locator("dialog[open]").evaluate((el) => {
        const r = el.getBoundingClientRect();
        return {
          center: Math.abs(r.left - (innerWidth - r.width) / 2),
          top: r.top,
          bottom: r.bottom,
          height: innerHeight,
        };
      });
      assert(
        geometry.center < 1 &&
          geometry.top >= 23 &&
          geometry.bottom <= geometry.height - 23,
        "Dialog centering/viewport bounds " + JSON.stringify(geometry),
      );
    }
    assert(
      await p.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
      name + " overflow",
    );
    await p.evaluate(axe);
    const violations = await p.evaluate(async () =>
      (
        await window.axe.run(document, {
          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
        })
      ).violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => n.target),
      })),
    );
    assert.deepEqual(violations, [], name);
    views.push({ name, lang, width, axe: violations });
    {
      const c = await p.context().newCDPSession(p),
        r = await c.send("Page.captureScreenshot", {
          format: "png",
          fromSurface: true,
          captureBeyondViewport: false,
        });
      fs.writeFileSync(
        out + "/screenshots/" + name + "-" + lang + "-" + width + ".png",
        Buffer.from(r.data, "base64"),
      );
      await c.detach();
    }
    fs.writeFileSync(
      out + "/checks/interactions.json",
      JSON.stringify({ views, flows }, null, 2) + "\n",
    );
  }
  async function locale(p, lang) {
    await p.goto(base + "/");
    await p.evaluate(
      (l) => localStorage.setItem("shieldmate-language", l),
      lang,
    );
  }
  for (const lang of ["en", "ru", "kk"]) {
    await locale(publicPage, lang);
    for (const route of ["/login", "/register"])
      for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
        await publicPage.setViewportSize({ width, height: 1000 });
        await publicPage.goto(base + route);
        await publicPage.locator("main h1").waitFor();
        await check(publicPage, route.slice(1), lang, width);
      }
    await publicPage.goto(base + "/register");
    const fields = publicPage.locator("input");
    await fields.first().fill("qa-unsent@example.com");
    await fields.nth(1).fill("Unsent-value-123!");
    await publicPage
      .getByRole("button", { name: "English", exact: true })
      .click();
    await publicPage
      .getByRole("button", { name: "Қазақша", exact: true })
      .click();
    assert.equal(await fields.first().inputValue(), "qa-unsent@example.com");
    assert.equal(await fields.nth(1).inputValue(), "Unsent-value-123!");
    await locale(page, lang);
    for (const route of ["/", "/app", "/app/reports"]) {
      await page.goto(base + route);
      await page.bringToFront();
      if (route.startsWith("/app"))
        await page.locator(".private-nav:visible").waitFor();
      await page.locator("main h1").waitFor();
      await page.waitForTimeout(150);
      for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
        await page.setViewportSize({ width, height: 1000 });
        await check(
          page,
          "all-widths-" + (route.split("/").pop() || "landing"),
          lang,
          width,
        );
      }
    }

    await page.goto(base + "/app/findings");
    await page.bringToFront();
    await page.locator(".private-nav:visible").waitFor();
    await page.locator("select[name=severity]").selectOption("high");
    await page.locator("select[name=category]").selectOption("tls");
    await page.locator(".finding-filters button[type=submit]").click();
    await page.waitForTimeout(200);
    assert(new URL(page.url()).searchParams.get("severity") === "high");
    assert(new URL(page.url()).searchParams.get("category") === "tls");
    assert.equal(await page.locator("[role=alert]").count(), 0);
    await page.goto(base + "/app/tasks");
    await page.locator("select[name=severity]").selectOption("high");
    await page.locator(".finding-filters button[type=submit]").click();
    await page.waitForTimeout(100);
    assert(new URL(page.url()).searchParams.get("severity") === "high");
    await page.goto(base + "/app/assets");
    await page.locator(".asset-list article .button-secondary").first().click();
    const remove = page.getByRole("button", {
      name: { en: "Remove domain", ru: "Удалить домен", kk: "Доменді жою" }[
        lang
      ],
      exact: true,
    });
    await remove.waitFor();
    await remove.focus();
    await page.keyboard.press("Enter");
    await page.locator("dialog[open]").waitFor();
    for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      await check(page, "domain-dialog", lang, width);
    }
    await page.keyboard.press("Escape");
    assert(await remove.evaluate((e) => e === document.activeElement));
    await page.goto(base + "/");
    await page.setViewportSize({ width: 360, height: 1000 });
    const menu = page.locator(".menu-toggle");
    await menu.focus();
    await page.keyboard.press("Enter");
    assert.equal(await menu.getAttribute("aria-expanded"), "true");
    await check(page, "mobile-menu", lang, 360);
    await page.keyboard.press("Escape");
    assert.equal(await menu.getAttribute("aria-expanded"), "false");
    // Explicit network error presentation only; fixtures remain persisted and API safety unchanged.
    await page.route("**/api/v1/reports/overview", (r) =>
      r.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ error: { message: "Reports unavailable" } }),
      }),
    );
    await page.goto(base + "/app/reports");
    await page.getByRole("alert").first().waitFor();
    await check(page, "reports-error", lang, 360);
    await page.unroute("**/api/v1/reports/overview");
    flows.push(
      lang +
        ": form preservation, canonical filters, dialog keyboard focus, mobile menu, report error",
    );
  }
  fs.writeFileSync(
    out + "/checks/interactions.json",
    JSON.stringify({ views, flows }, null, 2) + "\n",
  );
  await browser.close();
  console.log(JSON.stringify({ views: views.length, flows }, null, 2));
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
