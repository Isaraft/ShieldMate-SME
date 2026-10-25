// LOCAL ONLY: real application/queue around explicitly synthetic DNS/socket fixtures.
// Requires compose.local.yaml + scripts/qa/phase08.override.yaml, never the normal worker.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs"),
  assert = require("node:assert/strict");
const crypto = require("node:crypto"),
  { execFileSync } = require("node:child_process");
const { root, work, out, base, project } = require("./qa/runtime.cjs");
const compose = [
  "compose",
  "-p",
  project,
  "-f",
  "compose.local.yaml",
  "-f",
  "scripts/qa/phase08.override.yaml",
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const hash = (b) => crypto.createHash("sha256").update(b).digest("hex");
const docker = (...args) =>
  execFileSync("docker", [...compose, ...args], {
    cwd: root,
    encoding: "utf8",
    env: { ...process.env, SHIELDMATE_RC_PORT: new URL(base).port },
  });
const save = (name, value) =>
  fs.writeFileSync(
    out + "/checks/" + name + ".json",
    JSON.stringify(value, null, 2) + "\n",
  );
(async () => {
  for (const d of ["checks", "screenshots", "pdfs"])
    fs.mkdirSync(out + "/" + d, { recursive: true });
  const browser = await chromium.launch(),
    errors = [],
    flows = [],
    records = [];
  const axe = fs.readFileSync(
    require.resolve(process.env.AXE_MODULE || "axe-core"),
    "utf8",
  );
  const locales = Object.fromEntries(
    ["en", "ru", "kk"].map((l) => [
      l,
      JSON.parse(fs.readFileSync(root + "/backend/app/locales/" + l + ".json")),
    ]),
  );
  const tr = (s, l = "en") => locales[l][s] || s;
  async function get(ctx, p) {
    const r = await ctx.request.get(base + "/api/v1" + p);
    assert(r.ok(), p + " " + r.status());
    return r.json();
  }
  async function write(ctx, p, data = {}, method = "POST") {
    const token = (await get(ctx, "/auth/csrf")).csrf_token;
    const r = await ctx.request.fetch(base + "/api/v1" + p, {
      method,
      data,
      headers: { Origin: base, "X-CSRF-Token": token },
    });
    assert(r.ok(), p + " " + r.status() + " " + (await r.text()));
    return r.json();
  }
  async function until(ctx, p, test, seconds = 35) {
    for (let i = 0; i < seconds * 5; i++) {
      const response = await ctx.request.get(base + "/api/v1" + p);
      if (response.ok()) {
        const result = await response.json();
        if (test(result)) return result;
      } else {
        // Expected only while the explicitly restarted upstream is coming back.
        assert(
          p === "/health/ready" && [502, 503].includes(response.status()),
          p + " " + response.status(),
        );
      }
      await sleep(200);
    }
    throw Error("Timeout " + p);
  }
  async function shot(page, name) {
    await page.bringToFront();
    await page.evaluate(() => document.fonts.ready);
    await sleep(100);
    const c = await page.context().newCDPSession(page),
      r = await c.send("Page.captureScreenshot", {
        format: "png",
        fromSurface: true,
        captureBeyondViewport: false,
      });
    fs.writeFileSync(
      out + "/screenshots/" + name + ".png",
      Buffer.from(r.data, "base64"),
    );
    await c.detach();
  }
  async function newAccount(kind, ui = false) {
    const ctx = await browser.newContext({ acceptDownloads: true });
    await ctx.route("**/*", (route) => {
      const url = new URL(route.request().url());
      if (["http:", "https:"].includes(url.protocol) && url.origin !== base) {
        errors.push("Unexpected external browser request blocked");
        return route.abort();
      }
      return route.continue();
    });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errors.push(e.message));
    const email = "qa-phase08-" + crypto.randomUUID() + "@example.com",
      password = crypto.randomBytes(24).toString("base64url");
    const name = "LOCAL QA — " + kind + ' / ӘҒҚҢӨҰҮҺІ <script> & "ТОО"';
    if (ui) {
      await page.goto(base + "/register");
      await page.getByLabel("Email address", { exact: true }).fill(email);
      await page.getByLabel("Password", { exact: true }).fill(password);
      await page
        .getByRole("button", { name: "Create account", exact: true })
        .click();
      await page.waitForURL("**/login?created=1");
      await page.getByLabel("Email address", { exact: true }).fill(email);
      await page.getByLabel("Password", { exact: true }).fill(password);
      await page.getByRole("button", { name: "Sign in", exact: true }).click();
      await page.getByLabel("Company name", { exact: true }).fill(name);
      await page
        .getByRole("button", { name: "Create workspace", exact: true })
        .click();
      await page.locator(".private-nav").waitFor();
    } else {
      await write(ctx, "/auth/register", { email, password });
      await write(ctx, "/auth/login", { email, password });
      await write(ctx, "/organizations", { name });
    }
    return { ctx, page, email, password, name };
  }
  async function asset(a, fqdn, scan = true) {
    let row = await write(a.ctx, "/domains", {
      fqdn,
      authorization_acknowledged: true,
    });
    await write(a.ctx, "/domains/" + row.id + "/verification/check");
    row = await get(a.ctx, "/domains/" + row.id);
    assert.equal(row.status, "verified");
    if (scan) {
      const run = await write(a.ctx, "/domains/" + row.id + "/scans");
      await until(
        a.ctx,
        "/domains/" + row.id + "/scans/" + run.id,
        (r) => !["queued", "running"].includes(r.status),
      );
      await until(
        a.ctx,
        "/findings/assessments/" + run.id,
        (r) => r.status === "evaluated",
      );
    }
    return row;
  }
  async function pdfs(a, kind) {
    for (const locale of ["en", "ru", "kk"]) {
      const r = await write(a.ctx, "/reports", {
        locale,
        request_key: crypto.randomUUID(),
      });
      assert.equal(r.status, "ready");
      const response = await a.ctx.request.get(
        base + "/api/v1/reports/" + r.id + "/download",
      );
      assert.equal(response.headers()["content-type"], "application/pdf");
      assert.equal(response.headers()["cache-control"], "private, no-store");
      const bytes = await response.body();
      assert.equal(hash(bytes), r.sha256);
      fs.writeFileSync(out + "/pdfs/" + kind + "-" + locale + ".pdf", bytes);
      records.push({ ...r, kind });
    }
  }
  const a = await newAccount("Golden path", true),
    page = a.page,
    ctx = a.ctx;
  const stateFile = work + "/golden-state.json";
  await page.goto(base + "/app/assets");
  await page
    .getByLabel("Domain name", { exact: true })
    .fill("qa-defense.example.com");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Add domain", exact: true }).click();
  await page
    .getByRole("button", { name: "Verify ownership", exact: true })
    .click();
  await until(ctx, "/domains", (rows) => rows[0]?.status === "verified");
  await page
    .getByRole("button", { name: "Run security checks", exact: true })
    .click();
  const domain = (await get(ctx, "/domains"))[0];
  const history = await until(
    ctx,
    "/domains/" + domain.id + "/scans",
    (r) => r.items[0]?.status === "completed",
  );
  const scan = history.items[0];
  const findings = await until(ctx, "/findings", (r) => r.total === 6),
    finding = findings.priorities[0];
  await page.goto(base + "/app/findings/" + finding.id);
  await page.getByRole("button", { name: "Create task", exact: true }).click();
  await page
    .getByLabel("Owner label", { exact: true })
    .fill("LOCAL QA — Әкімші");
  await page.getByLabel("Work status", { exact: true }).selectOption("done");
  await page
    .getByLabel("Work note", { exact: true })
    .fill("PRIVATE-NOTE <script> & sensitive work");
  await page
    .getByRole("button", { name: "Save work changes", exact: true })
    .click();
  const tasks = await until(
      ctx,
      "/tasks",
      (r) => r.items[0]?.status === "done",
    ),
    task = tasks.items[0];
  assert.equal((await get(ctx, "/findings/" + finding.id)).status, "open");
  assert.deepEqual(
    (await get(ctx, "/reports/overview")).priorities.map((f) => f.id),
    findings.priorities.map((f) => f.id),
  );
  await shot(page, "task-done-finding-open-en");
  await pdfs(a, "short");
  flows.push(
    "Browser registration/login/onboarding/consent/TXT/queued scan/finding/task done; finding remains open; shared Top 3 and real PDF API",
  );
  await ctx.storageState({ path: stateFile });
  fs.chmodSync(stateFile, 0o600);
  // Persist only a private operator resume file; never include credentials in evidence.
  fs.writeFileSync(
    work + "/golden-credentials.json",
    JSON.stringify({ email: a.email, password: a.password }),
    { mode: 0o600 },
  );
  const b = await newAccount("Long report");
  for (let i = 1; i <= 4; i++)
    await asset(
      b,
      "qa-long-authorized-domain-" + i + "-for-layout.example.com",
    );
  assert.equal((await get(b.ctx, "/findings?limit=50")).total, 24);
  await pdfs(b, "long");
  const edge = await newAccount("Edge / " + "Ұзақ атау ".repeat(5));
  await asset(edge, "qa-edge.example.com");
  await write(edge.ctx, "/domains", {
    fqdn: "qa-unverified.example.com",
    authorization_acknowledged: true,
  });
  assert.equal(
    (await get(edge.ctx, "/reports/overview")).readiness,
    "incomplete",
  );
  await pdfs(edge, "edge");
  const ids = [
    ["/domains/" + domain.id],
    ["/domains/" + domain.id + "/scans"],
    ["/domains/" + domain.id + "/scans/" + scan.id],
    ["/findings/" + finding.id],
    ["/findings/assessments/" + scan.id],
    ["/tasks/" + task.id],
    ["/reports/" + records[0].id],
    ["/reports/" + records[0].id + "/download"],
  ];
  for (const [p] of ids)
    assert.equal(
      (await b.ctx.request.get(base + "/api/v1" + p)).status(),
      404,
      p + " IDOR",
    );
  const csrf = (await get(ctx, "/auth/csrf")).csrf_token;
  assert.equal((await get(ctx, "/auth/csrf")).csrf_token, csrf);
  for (const headers of [
    { Origin: base },
    { Origin: "http://evil.example", "X-CSRF-Token": csrf },
  ]) {
    const r = await ctx.request.patch(base + "/api/v1/tasks/" + task.id, {
      data: {
        version: task.version,
        status: "todo",
        owner_label: "",
        note: "",
      },
      headers,
    });
    assert.equal(r.status(), 403);
  }
  const beforeDemo = await get(ctx, "/reports");
  for (const locale of ["en", "ru", "kk"]) {
    const r = await ctx.request.get(
      base + "/api/v1/demo/report?locale=" + locale,
    );
    assert(r.ok());
    fs.writeFileSync(out + "/pdfs/demo-" + locale + ".pdf", await r.body());
  }
  assert.deepEqual(await get(ctx, "/reports"), beforeDemo);
  flows.push(
    "Eight cross-tenant resource denials; CSRF/Origin rejection; stable CSRF reads; isolated demo leaves tenant reports unchanged",
  );
  save("final-report-records", records);
  save("resources", {
    domain: domain.id,
    scan: scan.id,
    finding: finding.id,
    task: task.id,
  });
  // All data is synthetic and remains in the separately named QA volume.
  const views = [];
  const routes = [
    ["/", "landing"],
    ["/login", "login"],
    ["/register", "register"],
    ["/app", "dashboard"],
    ["/app/assets", "assets"],
    ["/app/assets/" + domain.id + "/scans", "scans"],
    ["/app/findings", "findings"],
    ["/app/findings/" + finding.id, "finding-detail"],
    ["/app/tasks", "tasks"],
    ["/app/tasks/" + task.id, "task-detail"],
    ["/app/reports", "reports"],
    ["/app/settings", "settings"],
    ["/demo", "demo"],
    ["/unknown-phase08", "404"],
  ];
  for (const locale of ["en", "ru", "kk"]) {
    await page.goto(base + "/");
    await page
      .getByRole("button", {
        name: { en: "English", ru: "Русский", kk: "Қазақша" }[locale],
        exact: true,
      })
      .click();
    for (const [route, name] of routes) {
      await page.goto(base + route);
      await page.bringToFront();
      await page.locator("main h1").waitFor();
      if (route.startsWith("/app"))
        await page.locator(".private-nav:visible").waitFor();
      await sleep(220);
      for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
        await page.setViewportSize({ width, height: 1000 });
        await page.evaluate(() => document.fonts.ready);
        await sleep(60);
        assert.equal(await page.locator("html").getAttribute("lang"), locale);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth + 1,
        );
        assert(!overflow, locale + "/" + name + "/" + width + " overflow");
        await page.evaluate(axe);
        const violations = await page.evaluate(async () =>
          (
            await window.axe.run(document, {
              runOnly: {
                type: "tag",
                values: ["wcag2a", "wcag2aa", "wcag21aa"],
              },
            })
          ).violations.map((v) => ({
            id: v.id,
            targets: v.nodes.map((n) => n.target),
          })),
        );
        assert.deepEqual(
          violations,
          [],
          locale + "/" + name + "/" + width + " accessibility",
        );
        if (name === "landing") {
          const rects = await page
            .locator(".hero-line,.hero-action")
            .evaluateAll((es) =>
              es.map((e) => {
                const r = e.getBoundingClientRect();
                return { top: r.top, bottom: r.bottom };
              }),
            );
          assert(rects[0].bottom <= rects[1].top + 1, "hero overlap");
          const deltas = await page
            .locator(".workflow-list li")
            .evaluateAll((es) =>
              es.map((e) => {
                const a = e
                    .querySelector(".step-number")
                    .getBoundingClientRect(),
                  b = e.getBoundingClientRect();
                return Math.abs((a.top + a.bottom - b.top - b.bottom) / 2);
              }),
            );
          assert(
            deltas.every((d) => d < 2),
            "step alignment",
          );
        }
        if ([360, 1280].includes(width))
          await shot(page, name + "-" + locale + "-" + width);
        views.push({ locale, name, width, overflow, violations });
      }
    }
  }
  save("browser-matrix", views);
  console.log("Matrix completed: " + views.length + " rendered views");
  // Empty/onboarding views use a fresh account with no fixture data.
  const empty = await browser.newContext(),
    emptyPage = await empty.newPage();
  const emptyEmail = "qa-empty-" + crypto.randomUUID() + "@example.com",
    emptyPassword = crypto.randomBytes(24).toString("base64url");
  await write(empty, "/auth/register", {
    email: emptyEmail,
    password: emptyPassword,
  });
  await write(empty, "/auth/login", {
    email: emptyEmail,
    password: emptyPassword,
  });
  await emptyPage.goto(base + "/app");
  await emptyPage.bringToFront();
  await emptyPage.getByLabel("Company name", { exact: true }).waitFor();
  await shot(emptyPage, "onboarding-en-360");
  await write(empty, "/organizations", { name: "LOCAL QA — Empty workspace" });
  for (const locale of ["en", "ru", "kk"]) {
    await emptyPage.goto(base + "/");
    await emptyPage
      .getByRole("button", {
        name: { en: "English", ru: "Русский", kk: "Қазақша" }[locale],
        exact: true,
      })
      .click();
    for (const route of [
      "/app",
      "/app/assets",
      "/app/findings",
      "/app/tasks",
      "/app/reports",
    ]) {
      await emptyPage.goto(base + route);
      await emptyPage.bringToFront();
      await emptyPage.locator(".private-nav:visible").waitFor();
      await sleep(200);
      for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
        await emptyPage.setViewportSize({ width, height: 1000 });
        await sleep(50);
        assert(
          await emptyPage.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth + 1,
          ),
        );
        await emptyPage.evaluate(axe);
        const violations = await emptyPage.evaluate(async () =>
          (
            await window.axe.run(document, {
              runOnly: {
                type: "tag",
                values: ["wcag2a", "wcag2aa", "wcag21aa"],
              },
            })
          ).violations.map((v) => v.id),
        );
        assert.deepEqual(violations, []);
        views.push({
          locale,
          name: "empty-" + route,
          width,
          overflow: false,
          violations,
        });
        if (width === 360)
          await shot(
            emptyPage,
            "empty-" + route.split("/").pop() + "-" + locale,
          );
      }
    }
  }
  save("browser-matrix", views);
  await empty.close();
  // Text enlargement, reduced motion and form retention in all three languages.
  for (const l of ["en", "ru", "kk"]) {
    await page.goto(base + "/register");
    await page.bringToFront();
    await page
      .getByLabel(
        tr("Email address", await page.locator("html").getAttribute("lang")),
        { exact: true },
      )
      .fill("retained@example.com");
    await page
      .getByRole("button", {
        name: { en: "English", ru: "Русский", kk: "Қазақша" }[l],
        exact: true,
      })
      .click();
    assert.equal(
      await page
        .getByLabel(tr("Email address", l), { exact: true })
        .inputValue(),
      "retained@example.com",
    );
    await page.goto(base + "/");
    await page.setViewportSize({ width: 360, height: 1000 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.evaluate(
      () => (document.documentElement.style.fontSize = "200%"),
    );
    await sleep(150);
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    );
    await shot(page, "text-200-" + l);
    await page.evaluate(() => (document.documentElement.style.fontSize = ""));
    await page.keyboard.press("Tab");
    assert(
      await page.evaluate(
        () => getComputedStyle(document.activeElement).outlineStyle !== "none",
      ),
    );
  }
  // Evidence-backed resolution only after a second conclusive scan, with immutable old PDFs.
  docker(
    "exec",
    "-T",
    "worker",
    "python",
    "-c",
    "from pathlib import Path;Path('/tmp/phase08-clean').touch()",
  );
  const clean = await write(ctx, "/domains/" + domain.id + "/scans");
  await until(
    ctx,
    "/domains/" + domain.id + "/scans/" + clean.id,
    (r) => r.status === "completed",
  );
  await until(ctx, "/findings", (r) =>
    r.items.every((f) => f.status === "resolved"),
  );
  docker(
    "exec",
    "-T",
    "worker",
    "python",
    "-c",
    "from pathlib import Path;Path('/tmp/phase08-clean').unlink()",
  );
  for (const r of records.filter((r) => r.kind === "short"))
    assert.equal(
      hash(
        await (
          await ctx.request.get(base + "/api/v1/reports/" + r.id + "/download")
        ).body(),
      ),
      r.sha256,
    );
  flows.push(
    "Conclusive clean fixture scan resolves findings; done task alone did not; stored report bytes remain unchanged",
  );
  // Actual browser BroadcastChannel logout invalidates the other tab before re-entry.
  await page.goto(base + "/app");
  await page.bringToFront();
  await page.locator(".private-nav:visible").waitFor();
  const tab = await ctx.newPage();
  await tab.goto(base + "/app/tasks/" + task.id);
  await tab.bringToFront();
  await tab.locator(".private-nav:visible").waitFor();
  await tab
    .getByLabel(
      tr("Work note", await tab.locator("html").getAttribute("lang")),
      { exact: true },
    )
    .fill("UNSAVED TENANT A");
  await page.bringToFront();
  await page.locator(".preview-banner button").click();
  await page.waitForURL("**/login");
  await tab.bringToFront();
  await tab.waitForURL("**/login");
  assert.equal(
    await tab.getByText("UNSAVED TENANT A", { exact: true }).count(),
    0,
  );
  await page
    .getByLabel(
      tr("Email address", await page.locator("html").getAttribute("lang")),
      { exact: true },
    )
    .fill(b.email);
  await page
    .getByLabel(
      tr("Password", await page.locator("html").getAttribute("lang")),
      { exact: true },
    )
    .fill(b.password);
  await page.bringToFront();
  await page
    .getByRole("button", {
      name: tr("Sign in", await page.locator("html").getAttribute("lang")),
      exact: true,
    })
    .click();
  await page.locator(".private-nav:visible").waitFor();
  await tab.goto(base + "/app/tasks/" + task.id);
  await tab.bringToFront();
  await tab.getByRole("alert").waitFor();
  assert.equal(await tab.locator("#task-note").count(), 0);
  await tab.close();
  await write(ctx, "/auth/logout");
  await write(ctx, "/auth/login", { email: a.email, password: a.password });
  await ctx.storageState({ path: stateFile });
  fs.chmodSync(stateFile, 0o600);
  flows.push(
    "Actual same-browser two-tab logout/account transition removes tenant A draft and denies old task under tenant B",
  );
  // Real container crash while worker holds a persisted lease. No external network in fixture worker.
  const interrupted = await asset(a, "qa-interrupt.example.com", false),
    pending = await write(ctx, "/domains/" + interrupted.id + "/scans");
  await until(
    ctx,
    "/domains/" + interrupted.id + "/scans/" + pending.id,
    (r) => r.status === "running" && r.completed_checks >= 4,
  );
  docker("kill", "-s", "SIGKILL", "worker");
  console.log(
    "Worker killed; waiting for actual lease expiry (up to 100 seconds)",
  );
  const recovered = await until(
    ctx,
    "/domains/" + interrupted.id + "/scans/" + pending.id,
    (r) => r.status === "interrupted",
    110,
  );
  assert.equal(recovered.error_code, "worker_interrupted");
  docker("up", "-d", "--wait", "worker");
  await sleep(1000);
  const stable = await get(
    ctx,
    "/domains/" + interrupted.id + "/scans/" + pending.id,
  );
  assert.equal(stable.status, "interrupted");
  assert.equal(stable.observations.length, recovered.observations.length);
  const blocked = await asset(a, "qa-blocked.example.com", false),
    bad = await write(ctx, "/domains/" + blocked.id + "/scans");
  const failed = await until(
    ctx,
    "/domains/" + blocked.id + "/scans/" + bad.id,
    (r) => r.status === "failed",
  );
  assert.equal(failed.error_code, "unsafe_destination");
  save("worker-recovery", {
    scan_id: pending.id,
    status: stable.status,
    checks: stable.completed_checks,
    no_retry: true,
    blocked_scan: failed,
  });
  flows.push(
    "SIGKILL worker, real lease expiry, interrupted persistence/no automatic retry; unsafe destination fixture fails closed",
  );
  docker("restart", "backend", "worker");
  await until(ctx, "/health/ready", (r) => r.status === "ready", 40);
  assert.equal((await get(ctx, "/auth/me")).email, a.email);
  assert.equal((await get(ctx, "/tasks/" + task.id)).status, "done");
  for (const r of records.filter((r) => r.kind === "short"))
    assert.equal(
      hash(
        await (
          await ctx.request.get(base + "/api/v1/reports/" + r.id + "/download")
        ).body(),
      ),
      r.sha256,
    );
  save("workflow", {
    browser: browser.version(),
    fixture:
      "LOCAL QA — injected DNS and socket responses, real queue, API, DB and PDFs. No external assessment.",
    flows,
    errors,
    views: views.length,
  });
  assert.deepEqual(errors, []);
  await browser.close();
  console.log(
    JSON.stringify(
      { flows, views: views.length, reports: records.length + 3, errors },
      null,
      2,
    ),
  );
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
