// Isolated LOCAL QA with injected TXT and persisted fixture observations; never a live assessment.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs"),
  path = require("node:path"),
  assert = require("node:assert/strict"),
  crypto = require("node:crypto");
const { execFileSync } = require("node:child_process");
const base = process.env.BASE_URL || "http://127.0.0.1:15573";
const output = path.resolve(__dirname, "../docs/evidence/phase-07");
const compose = [
  "compose",
  "-p",
  "shieldmate-phase07-qa",
  "-f",
  "scripts/qa/phase07.compose.yaml",
];
function docker(...args) {
  return execFileSync("docker", [...compose, ...args], { encoding: "utf8" });
}
function seed(asset, scenario) {
  return JSON.parse(
    docker(
      "exec",
      "-T",
      "backend",
      ".venv/bin/python",
      "-m",
      "scripts.qa.phase05_seed",
      "--asset-id",
      asset,
      "--scenario",
      scenario,
    ),
  ).scan_id;
}
(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const results = {
    browser: browser.version(),
    fixtures:
      "LOCAL QA — injected TXT and saved synthetic observations; real API, database, sessions, worker and PDFs. No external scans.",
    flows: [],
    views: [],
    errors: [],
  };
  page.on("pageerror", (e) => results.errors.push(e.message));
  const axe = fs.readFileSync(
    require.resolve(process.env.AXE_MODULE || "axe-core"),
    "utf8",
  );
  async function get(resource) {
    const r = await context.request.get(base + "/api/v1" + resource);
    assert(r.ok(), resource + " " + r.status());
    return r.json();
  }
  async function write(resource, method, body) {
    const token = (await get("/auth/csrf")).csrf_token;
    return context.request.fetch(base + "/api/v1" + resource, {
      method,
      data: body,
      headers: { Origin: base, "X-CSRF-Token": token },
    });
  }
  async function until(resource, test) {
    for (let i = 0; i < 100; i++) {
      try {
        const r = await get(resource);
        if (test(r)) return r;
      } catch (e) {
        if (i === 99) throw e;
      }
      await new Promise((r) => setTimeout(r, 200));
    }
    throw Error("Timed out " + resource);
  }
  async function capture(name, qa = true) {
    for (const width of [360, 768, 1280, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => document.fonts.ready);
      if (qa)
        await page.evaluate(() => {
          if (!document.querySelector("#qa-label")) {
            const p = document.createElement("p");
            p.id = "qa-label";
            p.textContent =
              "LOCAL QA — synthetic saved evidence, not a live security assessment.";
            document.querySelector("main").prepend(p);
          }
        });
      assert(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        name + "/" + width + " overflow",
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
      assert.deepEqual(violations, [], name + "/" + width + " accessibility");
      await page.evaluate(() => {
        document.activeElement?.blur();
        scrollTo(0, 0);
      });
      await page.screenshot({
        path: path.join(output, name + "-" + width + ".png"),
        fullPage: true,
      });
      results.views.push({ name, width, overflow: false, violations });
    }
  }
  const email = "qa-phase07-" + crypto.randomUUID() + "@example.com",
    password = crypto.randomBytes(24).toString("base64url");
  assert.equal(
    (await write("/auth/register", "POST", { email, password })).status(),
    201,
  );
  assert.equal(
    (await write("/auth/login", "POST", { email, password })).status(),
    200,
  );
  assert.equal(
    (
      await write("/organizations", "POST", {
        name: "LOCAL QA — Phase 07 ТОО ӘҒҚҢӨҰҮҺІ",
      })
    ).status(),
    201,
  );
  await page.goto(base + "/app/reports");
  await page.getByText("No qualifying report data", { exact: true }).waitFor();
  assert(
    await page
      .getByRole("button", { name: "Generate PDF Snapshot" })
      .isDisabled(),
  );
  await capture("reports-empty");
  let asset = (
    await (
      await write("/domains", "POST", {
        fqdn: "qa-reports.example.com",
        authorization_acknowledged: true,
      })
    ).json()
  ).id;
  assert.equal(
    (
      await write("/domains/" + asset + "/verification/check", "POST", {})
    ).status(),
    200,
  );
  seed(asset, "issues");
  const findings = await until("/findings", (r) => r.total === 6);
  const finding = findings.priorities[0];
  const task = await (
    await write("/findings/" + finding.id + "/task", "POST", {})
  ).json();
  assert.equal(
    (
      await write("/tasks/" + task.id, "PATCH", {
        version: task.version,
        status: "done",
        owner_label: "QA ИТ-провайдер",
        note: "PRIVATE-NOTE-MUST-NOT-ENTER-PDF",
      })
    ).status(),
    200,
  );
  const snapshot = await get("/reports/overview");
  assert.deepEqual(
    snapshot.priorities.map((f) => f.id),
    findings.priorities.map((f) => f.id),
  );
  assert.equal(snapshot.task_counts.done, 1);
  await page.reload();
  await page.getByText("No saved snapshots yet.", { exact: true }).waitFor();
  await capture("reports-ready");
  const created = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/reports") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Generate PDF Snapshot" }).click();
  const en = await (await created).json();
  assert.equal(en.status, "ready");
  await page
    .getByRole("button", { name: "Download PDF", exact: true })
    .waitFor();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download PDF", exact: true }).click();
  await (
    await download
  ).saveAs(path.join(output, "LOCAL-QA-security-snapshot-en.pdf"));
  await page.getByRole("button", { name: "Русский", exact: true }).click();
  assert.equal(await page.locator("html").getAttribute("lang"), "ru");
  const createdRu = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/reports") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Создать PDF-снимок", exact: true })
    .click();
  const ru = await (await createdRu).json();
  assert.equal(ru.locale, "ru");
  assert.equal(ru.status, "ready");
  const ruBytes = await context.request.get(
    base + "/api/v1/reports/" + ru.id + "/download",
  );
  fs.writeFileSync(
    path.join(output, "LOCAL-QA-security-snapshot-ru.pdf"),
    await ruBytes.body(),
  );
  await page.getByText(ru.id, { exact: true }).waitFor();
  await capture("reports-history-ru");
  await page.reload();
  assert.equal(await page.locator("html").getAttribute("lang"), "ru");
  await page.getByText(ru.id, { exact: true }).waitFor();
  const original = await context.request.get(
    base + "/api/v1/reports/" + en.id + "/download",
  );
  const hash = crypto
    .createHash("sha256")
    .update(await original.body())
    .digest("hex");
  assert.equal(hash, en.sha256);
  seed(asset, "clean");
  await until("/findings", (r) =>
    r.items.every((f) => f.status === "resolved"),
  );
  assert.equal(
    crypto
      .createHash("sha256")
      .update(
        await (
          await context.request.get(
            base + "/api/v1/reports/" + en.id + "/download",
          )
        ).body(),
      )
      .digest("hex"),
    hash,
  );
  docker("restart", "backend", "worker");
  await until("/health", (r) => r.status === "ok");
  assert.equal((await get("/reports")).total, 2);
  assert.equal(
    crypto
      .createHash("sha256")
      .update(
        await (
          await context.request.get(
            base + "/api/v1/reports/" + en.id + "/download",
          )
        ).body(),
      )
      .digest("hex"),
    hash,
  );
  results.flows.push(
    "Real report generation EN/RU, authenticated browser download, immutable bytes after findings change, DB/container restart/session durability",
  );
  for (const [route, name] of [
    ["/app", "dashboard"],
    ["/app/assets", "assets"],
    ["/app/findings", "findings"],
    ["/app/findings/" + finding.id, "finding-detail"],
    ["/app/tasks", "tasks"],
    ["/app/tasks/" + task.id, "task-detail"],
    ["/app/settings", "workspace"],
    ["/app/assets/" + asset + "/scans", "scans"],
  ]) {
    await page.goto(base + route);
    await page.locator("main h1").waitFor();
    if (name === "task-detail")
      await page
        .getByRole("heading", {
          name: "На момент наблюдения сертификат нужно было продлить в течение 7 дней",
          exact: true,
        })
        .waitFor();
    await page.waitForTimeout(300);
    await capture(name + "-ru");
  }
  await page.goto(base + "/app/reports");
  await page.getByText(ru.id, { exact: true }).waitFor();
  await page.getByRole("button", { name: "English", exact: true }).click();
  await capture("reports-history-en");
  // Explicit transport failure, preserving real backend behavior outside this browser interception.
  await page.route("**/api/v1/reports/overview", (r) =>
    r.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: { message: "Reports unavailable" } }),
    }),
  );
  await page.reload();
  await page.getByRole("alert").first().waitFor();
  await capture("reports-error");
  await page.unroute("**/api/v1/reports/overview");
  await page
    .getByRole("button", { name: "Retry reports", exact: true })
    .click();
  await page.getByRole("button", { name: "Generate PDF Snapshot" }).waitFor();
  seed(asset, "unknown");
  await until("/reports/overview", (r) => r.readiness === "incomplete");
  await page.reload();
  await page.getByText("incomplete", { exact: true }).waitFor();
  await capture("reports-incomplete");
  await page.getByRole("button", { name: "Generate PDF Snapshot" }).focus();
  assert.notEqual(
    await page.evaluate(
      () => getComputedStyle(document.activeElement).outlineWidth,
    ),
    "0px",
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(
    await page
      .getByRole("button", { name: "Generate PDF Snapshot" })
      .evaluate((el) => getComputedStyle(el).transitionDuration),
    "0s",
  );
  const second = await context.newPage();
  await second.goto(base + "/app/reports");
  await second.getByText(en.id, { exact: true }).waitFor();
  await second.close();
  results.flows.push(
    "Reports empty/normal/incomplete/error/retry; language persistence; keyboard outline; reduced motion; second-tab access",
  );
  const demoRequests = [];
  page.on("request", (r) => {
    if (new URL(r.url()).pathname.startsWith("/api/v1/"))
      demoRequests.push(new URL(r.url()).pathname);
  });
  await page.goto(base + "/demo");
  await page.getByText("Sample Merchant KZ", { exact: false }).waitFor();
  for (const locale of ["en", "ru"]) {
    await page
      .getByRole("button", {
        name: locale === "ru" ? "Русский" : "English",
        exact: true,
      })
      .click();
    for (let index = 0; index < 4; index++) {
      await page.locator(".demo-steps button").nth(index).click();
      assert.equal(await page.locator(".demo-banner strong").count(), 1);
      await capture("demo-" + locale + "-" + (index + 1), false);
    }
    const d = await context.request.get(
      base + "/api/v1/demo/report?locale=" + locale,
    );
    assert.equal(d.status(), 200);
    fs.writeFileSync(
      path.join(output, "DEMO-security-snapshot-" + locale + ".pdf"),
      await d.body(),
    );
  }
  assert(
    demoRequests.every(
      (p) => p === "/api/v1/demo" || p === "/api/v1/demo/report",
    ),
    JSON.stringify(demoRequests),
  );
  assert.equal((await get("/reports")).total, 2);
  results.flows.push(
    "Demo while signed in accesses only public synthetic endpoints, four read-only steps EN/RU, no customer writes or network scans",
  );
  await page.getByRole("link", { name: "Войти", exact: true }).last().click();
  await page.getByLabel("Электронная почта", { exact: true }).fill(email);
  await page.getByLabel("Пароль", { exact: true }).fill(password);
  await page.getByRole("button", { name: "English", exact: true }).click();
  assert.equal(
    await page.getByLabel("Email address", { exact: true }).inputValue(),
    email,
  );
  assert.equal(
    await page.getByLabel("Password", { exact: true }).inputValue(),
    password,
  );
  assert.deepEqual(await page.evaluate(() => Object.keys(localStorage)), [
    "shieldmate-language",
  ]);
  assert.equal((await write("/auth/logout", "POST", {})).status(), 200);
  assert.equal(
    (
      await context.request.get(base + "/api/v1/reports/" + en.id + "/download")
    ).status(),
    401,
  );
  await page.goto(base + "/app/reports");
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  await capture("login-en", false);
  await page.getByRole("button", { name: "Русский", exact: true }).click();
  await capture("login-ru", false);
  await page.goto(base + "/does-not-exist");
  await page.locator("main h1").waitFor();
  await capture("not-found-ru", false);
  assert.deepEqual(results.errors, []);
  fs.writeFileSync(
    path.join(output, "browser-results.json"),
    JSON.stringify(results, null, 2) + "\n",
  );
  await browser.close();
  console.log(
    JSON.stringify({
      flows: results.flows.length,
      views: results.views.length,
      errors: results.errors,
    }),
  );
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
