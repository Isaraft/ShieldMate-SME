// Local-only visual QA. Requires the phase071 Compose harness; never probes real domains.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs"),
  path = require("node:path"),
  assert = require("node:assert/strict"),
  crypto = require("node:crypto"),
  { execFileSync } = require("node:child_process");
const base = process.env.BASE_URL || "http://127.0.0.1:15673";
const root = path.resolve(__dirname, ".."),
  work = path.resolve(root, "../../work"),
  out = path.join(root, "docs/evidence/phase-07-1");
const state = path.join(work, "phase071-auth-state.json"),
  manifest = path.join(work, "phase071-report-records.json");
const compose = [
  "compose",
  "-p",
  "shieldmate-phase071-qa",
  "-f",
  "scripts/qa/phase071.compose.yaml",
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const hash = (b) => crypto.createHash("sha256").update(b).digest("hex");
(async () => {
  fs.mkdirSync(out + "/after", { recursive: true });
  fs.mkdirSync(out + "/pdfs", { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    storageState: state,
    acceptDownloads: true,
  });
  async function get(p, ctx = context) {
    const r = await ctx.request.get(base + "/api/v1" + p);
    assert(r.ok(), p + " " + r.status());
    return r.json();
  }
  async function write(p, body, method = "POST", ctx = context) {
    const token = (await get("/auth/csrf", ctx)).csrf_token;
    const r = await ctx.request.fetch(base + "/api/v1" + p, {
      method,
      data: body,
      headers: { Origin: base, "X-CSRF-Token": token },
    });
    assert(r.ok(), p + " " + r.status() + " " + (await r.text()));
    return r.json();
  }
  async function until(p, test, ctx = context) {
    for (let i = 0; i < 150; i++) {
      const r = await get(p, ctx);
      if (test(r)) return r;
      await sleep(200);
    }
    throw Error("Timed out " + p);
  }
  async function asset(fqdn, scenario, ctx = context) {
    let assets = await get("/domains", ctx);
    let a = assets.find((a) => a.canonical_fqdn === fqdn);
    if (!a) {
      a = await write(
        "/domains",
        { fqdn, authorization_acknowledged: true },
        "POST",
        ctx,
      );
      if (scenario) {
        await write(
          "/domains/" + a.id + "/verification/check",
          {},
          "POST",
          ctx,
        );
        execFileSync(
          "docker",
          [
            ...compose,
            "exec",
            "-T",
            "backend",
            ".venv/bin/python",
            "-m",
            "scripts.qa.phase05_seed",
            "--asset-id",
            a.id,
            "--scenario",
            scenario,
          ],
          { cwd: root },
        );
      }
    }
    return a;
  }
  const before =
    process.env.SKIP_HISTORICAL === "1"
      ? { reports: [] }
      : JSON.parse(fs.readFileSync(out + "/checks/legacy-before.json"));
  const legacy = [];
  for (const report of before.reports) {
    const r = await context.request.get(
      base + "/api/v1/reports/" + report.id + "/download",
    );
    assert(r.ok());
    assert.equal(hash(await r.body()), report.sha256);
    legacy.push({ id: report.id, sha256: report.sha256, unchanged: true });
  }
  if (process.env.SKIP_HISTORICAL !== "1")
    fs.writeFileSync(
      out + "/checks/legacy-after.json",
      JSON.stringify({ legacy }, null, 2) + "\n",
    );
  for (let i = 1; i <= 3; i++)
    await asset(
      "long-authorized-domain-" +
        i +
        "-for-local-layout-verification.example.com",
      "issues",
    );
  const findings = await until("/findings?limit=50", (r) => r.total === 24),
    finding = findings.priorities[0];
  let tasks = await get("/tasks");
  for (let i = 0; i < 3; i++) {
    let task = tasks.items.find((t) => t.finding_id === findings.items[i].id);
    if (!task) {
      task = await write("/findings/" + findings.items[i].id + "/task", {});
      await write(
        "/tasks/" + task.id,
        {
          version: task.version,
          status: ["todo", "in_progress", "done"][i],
          owner_label: "LOCAL QA — Әкімші / ИТ-провайдер",
          note: "LOCAL QA note <script> is plain text; private notes excluded from PDF.",
        },
        "PATCH",
      );
    }
  }
  tasks = await get("/tasks");
  assert(
    tasks.items.some((t) => t.status === "done" && t.finding.status === "open"),
  );
  let records = fs.existsSync(manifest)
    ? JSON.parse(fs.readFileSync(manifest))
    : {};
  async function reports(kind, ctx) {
    for (const locale of ["en", "ru", "kk"]) {
      const name = kind + "-" + locale;
      if (!records[name]) {
        records[name] = await write(
          "/reports",
          { locale, request_key: crypto.randomUUID() },
          "POST",
          ctx,
        );
        fs.writeFileSync(manifest, JSON.stringify(records), { mode: 0o600 });
      }
      const r = await ctx.request.get(
        base + "/api/v1/reports/" + records[name].id + "/download",
      );
      assert(r.ok());
      const bytes = await r.body();
      assert.equal(hash(bytes), records[name].sha256);
      if (!fs.existsSync(out + "/checks/final-report-records.json"))
        fs.writeFileSync(out + "/pdfs/" + name + ".pdf", bytes);
    }
  }
  await reports("complex", context);
  // A separate session and workspace proves report IDOR denial and honest partial/empty states.
  let shortState = path.join(work, "phase071-short-state.json");
  let short = await browser.newContext(
    fs.existsSync(shortState) ? { storageState: shortState } : {},
  );
  if (!fs.existsSync(shortState)) {
    const email = "qa-short-" + crypto.randomUUID() + "@example.com",
      password = crypto.randomBytes(24).toString("base64url");
    await write("/auth/register", { email, password }, "POST", short);
    await write("/auth/login", { email, password }, "POST", short);
    await write(
      "/organizations",
      { name: "LOCAL QA — Толық емес тексеру / Неполная проверка" },
      "POST",
      short,
    );
    await short.storageState({ path: shortState });
    fs.chmodSync(shortState, 0o600);
  }
  assert.equal(
    (
      await short.request.get(
        base +
          "/api/v1/reports/" +
          (before.reports[0]?.id ?? records["complex-en"].id) +
          "/download",
      )
    ).status(),
    404,
  );
  await asset("partial-local-qa.example.com", "unknown", short);
  await asset("not-yet-verified.example.com", null, short);
  await until(
    "/reports/overview",
    (r) => r.can_generate && r.readiness === "incomplete",
    short,
  );
  await reports("partial", short);
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (e) => {
    if (e.type() === "error") errors.push(e.text());
  });
  const axe = fs.readFileSync(
    require.resolve(process.env.AXE_MODULE || "axe-core"),
    "utf8",
  );
  let views =
    process.env.RESUME && fs.existsSync(out + "/checks/browser-matrix.json")
      ? JSON.parse(fs.readFileSync(out + "/checks/browser-matrix.json")).views
      : [];
  async function shot(name) {
    const c = await context.newCDPSession(page);
    const r = await c.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false,
    });
    fs.writeFileSync(
      out + "/after/" + name + ".png",
      Buffer.from(r.data, "base64"),
    );
    await c.detach();
  }
  async function locale(lang) {
    await page.evaluate(
      (l) => localStorage.setItem("shieldmate-language", l),
      lang,
    );
  }
  async function view(route, name, lang, width, { capture = false } = {}) {
    if (
      process.env.RESUME &&
      views.some(
        (v) => v.route === route && v.lang === lang && v.width === width,
      )
    )
      return;
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(base + route);
    await locale(lang);
    await page.reload();
    await page.locator("main h1").first().waitFor();
    if (name === "finding-detail") {
      const catalog = JSON.parse(
        fs.readFileSync(path.join(root, "backend/app/locales", lang + ".json")),
      );
      await page
        .getByRole("heading", { level: 1, name: catalog[finding.title] })
        .waitFor();
    }
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(100);
    if (lang === "kk")
      assert(
        !/\bM\d{1,2}\b/.test(await page.locator("main").innerText()),
        name + ": unlocalized month token",
      );
    const bounds = await page.evaluate(() => ({
      width: innerWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    assert(
      bounds.scroll <= bounds.width + 1,
      `${name}/${lang}/${width} overflow ${JSON.stringify(bounds)}`,
    );
    await page.evaluate(axe);
    const violations = await page.evaluate(async () =>
      (
        await window.axe.run(document, {
          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
        })
      ).violations.map((v) => ({
        id: v.id,
        targets: v.nodes.map((n) => n.target),
      })),
    );
    assert.deepEqual(violations, [], `${name}/${lang}/${width} axe`);
    if (capture) await shot(name + "-" + lang + "-" + width);
    views.push({ route, name, lang, width, overflow: false, axe: violations });
    fs.writeFileSync(
      out + "/checks/browser-matrix.json",
      JSON.stringify({ browser: browser.version(), views, errors }, null, 2) +
        "\n",
    );
  }
  const routes = [
    ["/", "landing"],
    ["/app", "dashboard"],
    ["/app/assets", "assets"],
    ["/app/assets/" + findings.items[0].asset_id + "/scans", "scans"],
    ["/app/findings", "findings"],
    ["/app/findings/" + finding.id, "finding-detail"],
    ["/app/tasks", "tasks"],
    ["/app/tasks/" + tasks.items[0].id, "task-detail"],
    ["/app/reports", "reports"],
    ["/app/settings", "settings"],
    ["/demo", "demo"],
    ["/preview/ui-kit", "ui-kit"],
    ["/not-a-route", "404"],
  ];
  // Resolve actual asset ID from authoritative domain response, not a display hostname.
  const domains = await get("/domains");
  routes[3][0] = "/app/assets/" + domains[0].id + "/scans";
  for (const lang of ["en", "ru", "kk"])
    for (const [route, name] of routes)
      for (const width of [360, 390, 768, 1024, 1280, 1440, 1920])
        await view(route, name, lang, width, {
          capture: [360, 1280].includes(width),
        });
  // Matching before/after defect captures and geometry assertions.
  for (const [lang, width, height, name, steps] of [
    ["en", 1247, 827, "hero-en-1247", false],
    ["en", 360, 1000, "hero-en-360", false],
    ["ru", 1082, 679, "steps-ru-1082", true],
    ["ru", 360, 1000, "steps-ru-360", true],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto(base + "/");
    await locale(lang);
    await page.reload();
    await page.evaluate(() => document.fonts.ready);
    if (steps) {
      await page.locator(".workflow-list").scrollIntoViewIfNeeded();
      const deltas = await page
        .locator(".workflow-list li")
        .evaluateAll((rows) =>
          rows.map((row) => {
            const n =
              row.querySelector(".workflow-number") || row.firstElementChild;
            const a = row.getBoundingClientRect(),
              b = n.getBoundingClientRect();
            return Math.abs((a.top + a.bottom - b.top - b.bottom) / 2);
          }),
        );
      assert(
        deltas.every((d) => d < 2),
        "Step numerals not centered " + deltas,
      );
    } else {
      const r = await page
        .locator(".hero-line,.hero-action")
        .evaluateAll((es) =>
          es.map((e) => {
            const r = e.getBoundingClientRect();
            return { top: r.top, bottom: r.bottom };
          }),
        );
      assert(r[0].bottom <= r[1].top + 1, "Hero overlap");
    }
    await shot(name);
  }
  // Demo has four actual interactive steps, three independently exported PDFs.
  for (const lang of ["en", "ru", "kk"]) {
    await page.goto(base + "/demo");
    await locale(lang);
    await page.reload();
    for (let i = 0; i < 4; i++) {
      await page.locator(".demo-steps button").nth(i).click();
      await shot("demo-step-" + i + "-" + lang);
    }
    if (!fs.existsSync(out + "/pdfs/demo-" + lang + ".pdf")) {
      const r = await context.request.get(
        base + "/api/v1/demo/report?locale=" + lang,
      );
      assert(r.ok());
      fs.writeFileSync(out + "/pdfs/demo-" + lang + ".pdf", await r.body());
    }
  }
  // Reduced motion, enlarged text, keyboard focus and native language switch stability.
  await page.goto(base + "/");
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert(
    await page.evaluate(
      () => matchMedia("(prefers-reduced-motion: reduce)").matches,
    ),
  );
  assert.equal(
    await page
      .locator(".language-switch button")
      .first()
      .evaluate((e) => getComputedStyle(e).transitionDuration),
    "0s",
  );
  for (const lang of ["en", "ru", "kk"]) {
    await page
      .getByRole("button", {
        name: { en: "English", ru: "Русский", kk: "Қазақша" }[lang],
        exact: true,
      })
      .click();
    await page.waitForFunction(
      (l) => document.documentElement.lang === l,
      lang,
    );
    await page.setViewportSize({ width: 360, height: 1000 });
    await page.evaluate(
      () => (document.documentElement.style.fontSize = "200%"),
    );
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.waitForFunction(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
      null,
      { timeout: 3000 },
    );
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
      "200% text overflow " +
        lang +
        " " +
        JSON.stringify(
          await page.evaluate(() =>
            [...document.querySelectorAll("body *")]
              .filter((e) => e.getBoundingClientRect().right > innerWidth + 1)
              .map((e) => ({
                tag: e.tagName,
                cls: e.className,
                text: e.textContent.slice(0, 80),
                right: e.getBoundingClientRect().right,
              }))
              .slice(-10),
          ),
        ),
    );
    await shot("zoom-200-" + lang);
    await page.evaluate(() => (document.documentElement.style.fontSize = ""));
  }
  await page.keyboard.press("Tab");
  assert(
    await page.evaluate(
      () => getComputedStyle(document.activeElement).outlineStyle !== "none",
    ),
    "Keyboard focus missing",
  );
  fs.writeFileSync(
    out + "/checks/visual-flows.json",
    JSON.stringify(
      {
        hero_overlap: "PASS",
        step_centers_within_2px: "PASS",
        demo_steps: 12,
        text_zoom_200: ["en", "ru", "kk"],
        reduced_motion: "PASS",
        visible_keyboard_focus: "PASS",
        page_errors: errors,
      },
      null,
      2,
    ) + "\n",
  );
  assert.deepEqual(errors, []);
  await context.storageState({ path: state });
  await short.close();
  await browser.close();
  console.log(
    JSON.stringify(
      {
        views: views.length,
        errors,
        legacy: legacy.length,
        pdfs: Object.keys(records).length + 3,
      },
      null,
      2,
    ),
  );
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
