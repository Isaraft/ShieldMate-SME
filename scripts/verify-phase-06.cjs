// Local isolated workflow QA only. No external network scans; no shipped demo data.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs"),
  path = require("node:path"),
  assert = require("node:assert/strict"),
  crypto = require("node:crypto");
const { execFileSync } = require("node:child_process");
const base = process.env.BASE_URL || "http://127.0.0.1:15473";
const output = path.resolve(__dirname, "../docs/evidence/phase-06");
const compose = [
  "compose",
  "-p",
  "shieldmate-phase06-qa",
  "-f",
  "scripts/qa/phase06.compose.yaml",
];
function docker(...args) {
  return execFileSync("docker", [...compose, ...args], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
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
  const context = await browser.newContext();
  const page = await context.newPage();
  const results = {
    browser: browser.version(),
    fixtures:
      "LOCAL QA: synthetic saved observations and injected TXT verification; real app/session/task APIs and worker. No external scans.",
    flow: [],
    viewports: [],
    errors: [],
  };
  page.on("pageerror", (e) => results.errors.push(e.message));
  const axe = fs.readFileSync(
    require.resolve(process.env.AXE_MODULE || "axe-core"),
    "utf8",
  );
  async function get(resource) {
    const r = await context.request.get(base + "/api/v1" + resource);
    assert(r.ok(), resource);
    return r.json();
  }
  async function write(resource, method, body) {
    const csrf = (await get("/auth/csrf")).csrf_token;
    return context.request.fetch(base + "/api/v1" + resource, {
      method,
      data: body,
      headers: { Origin: base, "X-CSRF-Token": csrf },
    });
  }
  async function until(resource, predicate) {
    for (let i = 0; i < 100; i++) {
      const d = await get(resource);
      if (predicate(d)) return d;
      await new Promise((r) => setTimeout(r, 200));
    }
    throw Error("Timed out: " + resource);
  }
  async function capture(name) {
    for (const width of [360, 768, 1280, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => document.fonts.ready);
      await page.evaluate(() => {
        if (!document.getElementById("qa-label")) {
          const p = document.createElement("p");
          p.id = "qa-label";
          p.textContent =
            "LOCAL QA — synthetic saved observations, not a live security assessment.";
          document.querySelector("main").prepend(p);
        }
        scrollTo(0, 0);
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
          nodes: v.nodes.map((n) => n.target),
        })),
      );
      assert.deepEqual(violations, [], name + "/" + width + " accessibility");
      await page.screenshot({
        path: path.join(output, `${name}-${width}.png`),
        fullPage: true,
      });
      results.viewports.push({
        page: name,
        width,
        overflow: false,
        violations,
      });
    }
  }
  await page.goto(base + "/app");
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  await page
    .getByRole("link", { name: "Create an account", exact: true })
    .click();
  const email = `qa-workflow-${crypto.randomUUID()}@example.com`,
    password = crypto.randomBytes(24).toString("base64url");
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
    .getByRole("textbox", { name: "Company name" })
    .fill("LOCAL QA — Phase 06 workflow");
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await page
    .getByRole("heading", {
      name: "Start with a domain you control",
      exact: true,
    })
    .waitFor();
  await capture("empty-dashboard");
  results.flow.push(
    "real account/session/onboarding and truthful empty overview",
  );
  async function enroll(host) {
    await page.goto(base + "/app/assets");
    await page.getByRole("textbox", { name: "Domain name" }).fill(host);
    await page.getByRole("checkbox").check();
    const response = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/v1/domains") && r.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Add domain", exact: true }).click();
    const asset = (await (await response).json()).id;
    await page
      .getByRole("heading", { name: `DNS TXT instructions: ${host}` })
      .waitFor();
    await page
      .getByRole("button", { name: "Verify ownership", exact: true })
      .click();
    await page
      .getByText(
        "Domain control verified. This is not a security assessment.",
        { exact: true },
      )
      .waitFor();
    return asset;
  }
  const asset = await enroll("qa-actions.example.com");
  await page.goto(base + "/app");
  await page
    .getByText("Ready for the first assessment", { exact: true })
    .waitFor();
  seed(asset, "issues");
  await until("/findings", (d) => d.total === 6);
  await page.reload();
  await page.locator(".priority-list li").nth(2).waitFor();
  const summary = await get("/dashboard/summary"),
    findings = await get("/findings");
  assert.equal(summary.verified_assets, 1);
  assert.equal(summary.findings.total, 6);
  assert.equal(summary.recent_scan_count, 1);
  assert.deepEqual(
    summary.findings.priorities.map((f) => f.id),
    findings.priorities.map((f) => f.id),
  );
  assert.deepEqual(
    await page
      .locator(".priority-list h3 a")
      .evaluateAll((nodes) => nodes.map((n) => n.getAttribute("href"))),
    findings.priorities.map((f) => "/app/findings/" + f.id),
  );
  await capture("dashboard");
  results.flow.push(
    "verified fixture asset -> persisted observations -> dashboard exact counts and unchanged Phase05 Top3",
  );
  const finding = findings.priorities[0];
  await page
    .locator(".priority-list li")
    .first()
    .getByRole("button", { name: "Create task", exact: true })
    .click();
  await page.waitForURL(/\/app\/tasks\/[0-9a-f-]+$/);
  await page
    .getByRole("heading", { name: "Record the work", exact: true })
    .waitFor();
  const taskURL = page.url(),
    taskId = taskURL.split("/").pop();
  await page
    .getByRole("textbox", { name: "Owner label" })
    .fill("External IT provider");
  const note = 'LOCAL QA note: <img src=x onerror="window.qaXss=true">';
  await page.getByRole("textbox", { name: "Work note" }).fill(note);
  await page
    .getByRole("combobox", { name: "Work status" })
    .selectOption("in_progress");
  await page
    .getByRole("button", { name: "Save work changes", exact: true })
    .click();
  await page
    .getByText("Work changes saved. Technical finding state is unchanged.", {
      exact: true,
    })
    .waitFor();
  await page
    .getByRole("heading", { name: "updated · revision 2", exact: true })
    .waitFor();
  await page.reload();
  await page.getByRole("textbox", { name: "Work note" }).waitFor();
  assert.equal(
    await page.getByRole("textbox", { name: "Owner label" }).inputValue(),
    "External IT provider",
  );
  assert.equal(
    await page.getByRole("textbox", { name: "Work note" }).inputValue(),
    note,
  );
  assert.equal(await page.evaluate(() => window.qaXss), undefined);
  assert.equal(await page.locator(".task-detail img").count(), 0);
  await page.getByRole("textbox", { name: "Work note" }).focus();
  assert.notEqual(
    await page
      .getByRole("textbox", { name: "Work note" })
      .evaluate((el) => getComputedStyle(el).outlineWidth),
    "0px",
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(
    await page
      .getByRole("button", { name: "Save work changes" })
      .evaluate((el) => getComputedStyle(el).transitionDuration),
    "0s",
  );
  await capture("task-detail");
  const existing = await write("/findings/" + finding.id + "/task", "POST", {});
  assert.equal((await existing.json()).id, taskId);
  assert.equal((await get("/tasks")).total, 1);
  results.flow.push(
    "create-or-open task; owner/note/status/history persist after reload; escaped XSS text, keyboard focus and reduced motion",
  );
  await page
    .getByRole("combobox", { name: "Work status" })
    .selectOption("done");
  await page
    .getByRole("button", { name: "Save work changes", exact: true })
    .click();
  await page
    .getByText("Task marked done — remediation not yet verified", {
      exact: true,
    })
    .waitFor();
  await page
    .getByRole("heading", { name: "updated · revision 3", exact: true })
    .waitFor();
  assert.equal((await get("/findings/" + finding.id)).status, "open");
  await capture("done-unverified");
  await page.goto(base + "/app/tasks?status=done");
  await page
    .getByText("1 saved task in this selection.", { exact: true })
    .waitFor();
  await capture("task-list");
  await page.getByRole("link", { name: finding.title, exact: true }).click();
  await page
    .getByRole("heading", { name: "Record the work", exact: true })
    .waitFor();
  // A separate actor request changes the same record; a stale editor cannot overwrite it.
  let current = await get("/tasks/" + taskId);
  assert(
    (
      await write("/tasks/" + taskId, "PATCH", {
        version: current.version,
        owner_label: "QA concurrent edit",
      })
    ).ok(),
  );
  await page
    .getByRole("textbox", { name: "Work note" })
    .fill("QA draft kept during conflict");
  await page
    .getByRole("button", { name: "Save work changes", exact: true })
    .click();
  await page
    .getByText(
      "This task changed elsewhere. Reload the latest version before saving.",
      { exact: true },
    )
    .waitFor();
  assert.equal(
    await page.getByRole("textbox", { name: "Work note" }).inputValue(),
    "QA draft kept during conflict",
  );
  await page
    .getByRole("button", {
      name: "Reload latest and discard draft",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", {
      name: "Reload latest and discard draft",
      exact: true,
    })
    .waitFor({ state: "hidden" });
  assert.equal(
    await page.getByRole("textbox", { name: "Owner label" }).inputValue(),
    "QA concurrent edit",
  );
  await page
    .getByRole("combobox", { name: "Work status" })
    .selectOption("in_progress");
  await page
    .getByRole("button", { name: "Save work changes", exact: true })
    .click();
  await page
    .getByText("Work changes saved. Technical finding state is unchanged.", {
      exact: true,
    })
    .waitFor();
  seed(asset, "unknown");
  await until(
    "/tasks/" + taskId,
    (d) => d.finding.recheck_status === "not_rechecked",
  );
  await page.reload();
  await page
    .getByText(
      "The latest check could not reassess this condition; its last known state is retained.",
      { exact: true },
    )
    .waitFor();
  seed(asset, "clean");
  await until("/tasks/" + taskId, (d) => d.finding.status === "resolved");
  await page.reload();
  await page.getByText(/Evidence indicates resolved at/).waitFor();
  assert.equal((await get("/tasks/" + taskId)).status, "in_progress");
  seed(asset, "issues");
  await until(
    "/tasks/" + taskId,
    (d) => d.finding.status === "open" && d.reopened_at,
  );
  await page.reload();
  await page.getByText("Recurrence recorded", { exact: true }).waitFor();
  assert.equal(
    await page.getByRole("textbox", { name: "Work note" }).inputValue(),
    note,
  );
  await page.screenshot({
    path: path.join(output, "recurrence.png"),
    fullPage: true,
  });
  results.flow.push(
    "manual done leaves finding open; concurrent edit conflict retains draft; incomplete preserves state; valid clean resolves; recurrence leaves human work/history intact",
  );
  current = await get("/tasks/" + taskId);
  docker("restart", "backend", "worker");
  for (let i = 0; i < 100; i++) {
    try {
      const r = await context.request.get(base + "/api/v1/health");
      if (r.ok()) break;
    } catch {}
    await new Promise((r) => setTimeout(r, 250));
  }
  await page.goto(taskURL);
  await page
    .getByRole("heading", { name: "Work history", exact: true })
    .waitFor();
  const restarted = await get("/tasks/" + taskId);
  assert.deepEqual(restarted, current);
  results.flow.push(
    "backend/worker container restart preserves task, actor/history, notes and authenticated session",
  );
  await page
    .getByRole("link", { name: "Open source scan", exact: true })
    .click();
  await page.locator(".observation").nth(12).waitFor();
  await page
    .getByRole("link", { name: "Review derived findings", exact: true })
    .click();
  await page
    .getByText("6 findings in this selection · 6 open · 0 resolved.", {
      exact: true,
    })
    .waitFor();
  await page
    .locator(".priority-list li")
    .first()
    .getByRole("link", { name: /Open task/ })
    .click();
  await page.waitForURL(taskURL);
  results.flow.push(
    "bidirectional dashboard/finding/task/source-scan navigation uses real resources",
  );
  await page
    .getByRole("heading", { name: "Record the work", exact: true })
    .waitFor();
  await page
    .getByRole("link", {
      name: "Recheck ownership & scan controls",
      exact: true,
    })
    .click();
  const assetTarget = page.locator(`#asset-${asset}`);
  await assetTarget.waitFor();
  await page.waitForFunction(
    (id) => document.activeElement?.id === id,
    `asset-${asset}`,
  );
  assert.equal(
    await assetTarget
      .getByRole("button", { name: "Run security checks", exact: true })
      .isEnabled(),
    true,
  );
  // Deliberately do not start real network checks in this observation-fixture stack.
  const staleAsset = await enroll("qa-stale-actions.example.com");
  seed(staleAsset, "stale");
  await until("/findings", (d) => d.total === 12);
  await page.goto(base + "/app");
  await page
    .getByText("Historical evidence", { exact: true })
    .first()
    .waitFor();
  await capture("stale-dashboard");
  await page.route("**/api/v1/dashboard/summary", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: { message: "LOCAL QA controlled outage" },
      }),
    }),
  );
  await page.goto(base + "/app");
  await page.getByRole("button", { name: "Retry overview" }).waitFor();
  await page.screenshot({
    path: path.join(output, "dashboard-error.png"),
    fullPage: true,
  });
  await page.unroute("**/api/v1/dashboard/summary");
  await page.getByRole("button", { name: "Retry overview" }).click();
  await page.locator(".priority-list li").nth(2).waitFor();
  results.flow.push(
    "stale coverage and controlled API failure/retry remain honest",
  );
  assert.deepEqual(results.errors, []);
  fs.writeFileSync(
    path.join(output, "browser-results.json"),
    JSON.stringify(results, null, 2),
  );
  console.log(JSON.stringify(results, null, 2));
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
