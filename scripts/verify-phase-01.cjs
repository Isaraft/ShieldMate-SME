// Optional QA tooling stays outside the application dependency tree.
// See docs/phase-01-results.md for the exact invocation and tool versions.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const axePath = require.resolve(process.env.AXE_MODULE || "axe-core");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const base = process.env.BASE_URL || "http://127.0.0.1:5173";
const output = path.resolve(
  process.env.EVIDENCE_DIR || path.join(__dirname, "../docs/evidence/phase-01"),
);
const results = {
  base,
  viewports: [],
  interactions: [],
  errors: [],
  apiRequests: [],
  contrast: {},
};
const palettes = {
  ink: "#321015",
  burgundy: "#570711",
  crimson: "#98121F",
  red: "#CF2431",
  canvas: "#F7F0EA",
  raised: "#FFF9F5",
  success: "#23613E",
  warning: "#785000",
};
function luminance(hex) {
  const rgb = hex
    .slice(1)
    .match(/../g)
    .map((v) => parseInt(v, 16) / 255)
    .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
}
for (const [a, b] of [
  ["ink", "canvas"],
  ["ink", "raised"],
  ["raised", "burgundy"],
  ["raised", "red"],
  ["raised", "crimson"],
  ["crimson", "canvas"],
  ["success", "raised"],
  ["success", "canvas"],
  ["warning", "raised"],
]) {
  const lum = [luminance(palettes[a]), luminance(palettes[b])].sort(
    (a, b) => b - a,
  );
  const ratio = (lum[0] + 0.05) / (lum[1] + 0.05);
  results.contrast[`${a}/${b}`] = +ratio.toFixed(2);
  assert(ratio >= 4.5);
}
(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  results.browser = browser.version();
  const page = await browser.newPage();
  page.on("pageerror", (error) => results.errors.push(error.message));
  let expectedHealthFailure = false;
  page.on("console", (message) => {
    if (
      message.type() === "error" &&
      !(expectedHealthFailure && message.text().includes("503"))
    )
      if (!message.text().includes("401")) results.errors.push(message.text());
  });
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.pathname.startsWith("/api/"))
      results.apiRequests.push(url.pathname);
    assert.equal(
      url.origin,
      new URL(base).origin,
      `Unexpected external request: ${url.origin}`,
    );
  });
  async function visit(route) {
    await page.goto(base + route);
    await page.evaluate(() => document.fonts.ready);
  }
  async function overflow() {
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      "Horizontal page overflow",
    );
  }
  for (const width of [360, 768, 1280, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    for (const [route, name] of [
      ["/", "landing"],
      ["/preview", "workspace"],
      ["/preview/ui-kit", "ui-kit"],
      ["/not-a-page", "404"],
    ]) {
      await visit(route);
      await overflow();
      assert.equal(await page.locator("h1").count(), 1);
      assert.equal(
        await page
          .locator(".site-footer")
          .evaluate((el) => getComputedStyle(el).paddingTop),
        "40px",
      );
      if (width < 1024)
        assert.equal(
          await page
            .locator(".menu-toggle")
            .evaluate((el) => getComputedStyle(el).minHeight),
          "44px",
        );
      await page.screenshot({
        path: path.join(output, `${name}-${width}.png`),
        fullPage: true,
      });
      if (name === "landing")
        await page.screenshot({ path: path.join(output, `hero-${width}.png`) });
      // Evaluate the local axe source directly so CSP remains unchanged and produces no blocked script noise.
      await page.evaluate(fs.readFileSync(axePath, "utf8"));
      const scan = await page.evaluate(async () => {
        const r = await axe.run(document, {
          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
        });
        return {
          violations: r.violations.map((v) => ({
            id: v.id,
            impact: v.impact,
            nodes: v.nodes.map((n) => n.target),
          })),
          incomplete: r.incomplete.map((v) => ({
            id: v.id,
            nodes: v.nodes.map((n) => n.target),
          })),
        };
      });
      results.viewports.push({ width, route, overflow: false, ...scan });
      assert.deepEqual(
        scan.violations,
        [],
        `Accessibility violations: ${width} ${route}`,
      );
    }
  }
  await page.setViewportSize({ width: 360, height: 900 });
  await visit("/");
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "Skip to content");
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(":focus").getAttribute("id"), "main");
  await visit("/");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  assert.equal(
    await page.locator(":focus").getAttribute("aria-controls"),
    "header-nav",
  );
  assert.equal(
    await page
      .locator(":focus")
      .evaluate((el) => getComputedStyle(el).outlineWidth),
    "3px",
  );
  await page.keyboard.press("Enter");
  assert(
    await page.getByRole("navigation", { name: "Main navigation" }).isVisible(),
  );
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "EN");
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "RU");
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "Product");
  await page.keyboard.press("Escape");
  assert.equal(
    await page.locator(":focus").getAttribute("aria-expanded"),
    "false",
  );
  assert(
    !(await page
      .getByRole("navigation", { name: "Main navigation" })
      .isVisible()),
  );
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "EN");
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "RU");
  await page.keyboard.press("Tab");
  assert.match(await page.locator(":focus").innerText(), /See how it works/);
  await page.getByRole("button", { name: "Menu", exact: true }).click();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name: "Product", exact: true })
    .click();
  await page.waitForFunction(() => document.activeElement.id === "product");
  assert(
    !(await page
      .getByRole("navigation", { name: "Main navigation" })
      .isVisible()),
  );
  await page
    .getByRole("link", { name: "See how it works", exact: true })
    .click();
  await page.waitForFunction(
    () => document.activeElement.id === "how-it-works",
  );
  await page
    .getByRole("link", { name: "See how it works", exact: true })
    .click();
  await page.waitForFunction(
    () => document.activeElement.id === "how-it-works",
  );
  const faq = page.getByText("Can I run a check today?", { exact: true });
  await faq.focus();
  await page.keyboard.press("Enter");
  assert(await page.locator("details[open]").isVisible());
  await page
    .getByRole("link", { name: "View interface preview", exact: true })
    .click();
  await page.getByText("Interface preview", { exact: true }).waitFor();
  assert(await page.getByRole("button", { name: "Run a check" }).isDisabled());
  await page.getByText("Responding", { exact: true }).waitFor();
  for (const [name, heading] of [
    ["Assets", "Assets"],
    ["Findings", "Findings"],
    ["Action plan", "Action plan"],
    ["Reports", "Reports"],
  ]) {
    await page
      .getByRole("navigation", { name: "Workspace navigation" })
      .getByRole("link", { name: new RegExp(name) })
      .click();
    await page
      .getByRole("heading", { name: heading, exact: true, level: 1 })
      .waitFor();
    assert.equal(await page.locator(":focus").getAttribute("id"), "main");
    await overflow();
  }
  await visit("/preview/findings");
  await page.screenshot({
    path: path.join(output, "findings-360.png"),
    fullPage: true,
  });
  await visit("/preview/ui-kit");
  await page.getByRole("button", { name: "Try validation" }).click();
  const input = page.getByRole("textbox", { name: "Example label" });
  assert.equal(await input.getAttribute("aria-invalid"), "true");
  assert.equal(
    await page.locator(":focus").getAttribute("id"),
    await input.getAttribute("id"),
  );
  await page.screenshot({
    path: path.join(output, "validation-error-360.png"),
    fullPage: true,
  });
  await input.fill("Example label");
  await page.getByRole("button", { name: "Try validation" }).click();
  assert(
    await page.getByText("Example validated", { exact: true }).isVisible(),
  );
  await page.getByRole("button", { name: "Reset", exact: true }).click();
  assert.equal(await input.inputValue(), "");
  await page
    .locator(".ui-kit > .prose")
    .evaluate((el) => (el.textContent = "LongUnbrokenText".repeat(30)));
  await overflow();
  await visit("/not-a-page");
  await page.getByRole("link", { name: "Return to home", exact: true }).click();
  await page
    .getByRole("heading", { name: /Know what to fix first/i, level: 1 })
    .waitFor();
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(
    await page
      .locator(".button-light")
      .first()
      .evaluate((el) => getComputedStyle(el).transitionDuration),
    "0s",
  );
  await page.emulateMedia({ forcedColors: "active" });
  await page.getByRole("button", { name: "Menu", exact: true }).focus();
  await page.keyboard.press("Tab");
  await page.keyboard.press("Shift+Tab");
  assert.equal(
    await page
      .locator(":focus")
      .evaluate((el) => getComputedStyle(el).outlineStyle),
    "solid",
  );
  await page.screenshot({ path: path.join(output, "forced-colors-360.png") });
  await page.emulateMedia({
    forcedColors: "none",
    reducedMotion: "no-preference",
  });
  expectedHealthFailure = true;
  await page.route("**/api/v1/health", (route) =>
    route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
  );
  await visit("/preview");
  await page.getByRole("button", { name: "Retry connection" }).waitFor();
  await page.unroute("**/api/v1/health");
  await page.getByRole("button", { name: "Retry connection" }).click();
  await page.getByText("Responding", { exact: true }).waitFor();
  results.interactions = [
    "skip link",
    "keyboard menu open and Escape restore",
    "visible 3px focus",
    "closed menu inaccessible",
    "anchor focus and repeated anchor",
    "FAQ keyboard disclosure",
    "preview CTA",
    "all workspace routes",
    "disabled feature actions",
    "empty findings table",
    "validation and focus/error/success/reset",
    "long text wrapping",
    "404 recovery",
    "reduced motion",
    "forced colors focus",
    "health failure and retry",
  ];
  assert(
    results.apiRequests.every((url) =>
      ["/api/v1/health", "/api/v1/auth/me"].includes(url),
    ),
  );
  assert.deepEqual(results.errors, []);
  fs.writeFileSync(
    path.join(output, "browser-results.json"),
    JSON.stringify(results, null, 2) + "\n",
  );
  await browser.close();
  console.log(
    JSON.stringify(
      {
        viewportChecks: results.viewports.length,
        interactions: results.interactions.length,
        contrast: results.contrast,
        errors: results.errors,
        browser: results.browser,
      },
      null,
      2,
    ),
  );
})().catch((error) => {
  console.error(error);
  fs.writeFileSync(
    path.join(output, "browser-failure.json"),
    JSON.stringify({ ...results, failure: error.message }, null, 2),
  );
  process.exit(1);
});
