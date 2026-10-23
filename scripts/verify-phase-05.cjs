const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const { execFileSync } = require("node:child_process");
const base = process.env.BASE_URL || "http://127.0.0.1:15373";
const output = path.resolve(
  process.env.EVIDENCE_DIR || path.join(__dirname, "../docs/evidence/phase-05"),
);
const compose = [
  "compose",
  "-p",
  "shieldmate-phase05-qa",
  "-f",
  "scripts/qa/phase05.compose.yaml",
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
    fixtures: "Isolated QA observations only; no live network assessment",
    flow: [],
    viewports: [],
    errors: [],
  };
  page.on("pageerror", (e) => results.errors.push(e.message));
  const axe = fs.readFileSync(
    require.resolve(process.env.AXE_MODULE || "axe-core"),
    "utf8",
  );
  async function capture(name) {
    for (const width of [360, 768, 1280, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => document.fonts.ready);
      await page.evaluate(() => {
        if (!document.getElementById("qa-label")) {
          const el = document.createElement("p");
          el.id = "qa-label";
          el.textContent =
            "LOCAL QA — injected saved observations in an isolated database. Not a live security assessment.";
          document.querySelector("main").prepend(el);
        }
        window.scrollTo(0, 0);
      });
      assert(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        `${name}/${width} overflow`,
      );
      if (await page.locator(".findings-page caption").count())
        assert(
          await page
            .locator(".findings-page caption")
            .evaluate((el) => el.getBoundingClientRect().width > 100),
          "readable caption width",
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
      assert.deepEqual(violations, [], `${name}/${width} accessibility`);
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
  async function get(resource) {
    const response = await context.request.get(base + "/api/v1" + resource);
    assert(response.ok(), resource);
    return response.json();
  }
  async function until(resource, predicate) {
    for (let i = 0; i < 60; i++) {
      const value = await get(resource);
      if (predicate(value)) return value;
      await new Promise((r) => setTimeout(r, 250));
    }
    throw Error("Timed out waiting for persisted finding state");
  }
  await page.goto(base + "/app/findings");
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  await page
    .getByRole("link", { name: "Create an account", exact: true })
    .click();
  const email = `qa-findings-${crypto.randomUUID()}@example.com`,
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
    .fill("LOCAL QA — Phase 05 fixture evidence");
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await page
    .getByRole("heading", {
      name: "LOCAL QA — Phase 05 fixture evidence",
      exact: true,
    })
    .waitFor();
  const org = (await get("/auth/me")).organization.id;
  await page.getByRole("link", { name: "Findings", exact: true }).click();
  await page.getByText("No assessments yet", { exact: true }).waitFor();
  await capture("empty");
  results.flow.push(
    "real authentication, owned workspace and no-scan empty state",
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
  const asset = await enroll("qa-findings.example.com");
  docker("stop", "worker");
  const first = seed(asset, "issues");
  await page.goto(`${base}/app/assets/${asset}/scans/${first}`);
  await page.getByRole("link", { name: "Review derived findings" }).click();
  await page
    .getByText("Assessment still processing", { exact: true })
    .waitFor();
  await page.screenshot({
    path: path.join(output, "pending.png"),
    fullPage: true,
  });
  docker("start", "worker");
  await page
    .getByText("6 findings in this selection · 6 open · 0 resolved.", {
      exact: true,
    })
    .waitFor();
  const initial = await get("/findings?domain_id=" + asset);
  assert.equal(initial.total, 6);
  assert.equal(initial.priorities.length, 3);
  assert.deepEqual(
    await page
      .locator(".priority-list h3 a")
      .evaluateAll((nodes) => nodes.map((n) => n.getAttribute("href"))),
    initial.priorities.map((f) => "/app/findings/" + f.id),
  );
  const ids = initial.items.map((f) => f.id).sort();
  const firstSeen = Object.fromEntries(
    initial.items.map((f) => [f.id, f.first_seen_at]),
  );
  await capture("findings");
  await page.reload();
  await page
    .getByText("6 findings in this selection · 6 open · 0 resolved.", {
      exact: true,
    })
    .waitFor();
  assert.deepEqual(
    (await get("/findings?domain_id=" + asset)).priorities.map((f) => f.id),
    initial.priorities.map((f) => f.id),
  );
  results.flow.push(
    "saved Phase04-shaped observations -> automatic worker evaluation -> exact counts and stable Top3",
  );
  await page
    .getByRole("combobox", { name: "Priority", exact: true })
    .selectOption("high");
  await page
    .getByRole("combobox", { name: "Category", exact: true })
    .selectOption("tls");
  await page
    .getByRole("button", { name: "Apply filters", exact: true })
    .click();
  await page
    .getByText("1 finding in this selection · 1 open · 0 resolved.", {
      exact: true,
    })
    .waitFor();
  await capture("filtered");
  await page.getByRole("radio", { name: "Technical", exact: true }).check();
  await page.locator(".priority-list h3 a").first().click();
  await page.waitForURL(/\/app\/findings\/[0-9a-f-]+$/);
  await page.locator(".finding-detail h1").waitFor();
  const detailURL = page.url();
  await page
    .getByRole("heading", { name: "Why this matters", exact: true })
    .waitFor();
  await page.getByRole("radio", { name: "Technical", exact: true }).check();
  const disclosure = page.getByText("Inspect saved technical evidence", {
    exact: true,
  });
  assert(
    await page
      .getByRole("radio", { name: "Technical", exact: true })
      .isChecked(),
  );
  await disclosure.waitFor({ state: "visible" });
  await page.waitForFunction(
    () => document.querySelector(".finding-detail details")?.open === true,
  );
  await disclosure.focus();
  await page.keyboard.press("Enter");
  await page.waitForFunction(
    () => document.querySelector(".finding-detail details")?.open === false,
  );
  await page.keyboard.press("Enter");
  await page.waitForFunction(
    () => document.querySelector(".finding-detail details")?.open === true,
  );
  assert(await disclosure.evaluate((el) => el.parentElement.open));
  assert.notEqual(
    await disclosure.evaluate((el) => getComputedStyle(el).outlineWidth),
    "0px",
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(
    await disclosure.evaluate((el) => getComputedStyle(el).transitionDuration),
    "0s",
  );
  await capture("detail");
  await page
    .getByRole("link", { name: "Open source scan", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Security check record", exact: true })
    .waitFor();
  await page.locator(".observation").nth(12).waitFor();
  assert.equal(await page.locator(".observation").count(), 13);
  results.flow.push(
    "working filters, Business/Technical toggle, keyboard disclosure/focus/reduced motion and intact scan provenance",
  );
  seed(asset, "unknown");
  await until("/findings?domain_id=" + asset, (d) =>
    d.items.every(
      (f) => f.status === "open" && f.recheck_status === "not_rechecked",
    ),
  );
  await page.goto(base + "/app/findings?domain_id=" + asset);
  await page
    .getByText("6 findings in this selection · 6 open · 0 resolved.", {
      exact: true,
    })
    .waitFor();
  await page.screenshot({
    path: path.join(output, "incomplete.png"),
    fullPage: true,
  });
  results.flow.push(
    "partial/unknown evidence preserves all six open findings as not rechecked",
  );
  seed(asset, "clean");
  await until("/findings?domain_id=" + asset, (d) =>
    d.items.every((f) => f.status === "resolved"),
  );
  await page.reload();
  await page
    .getByText("6 findings in this selection · 0 open · 6 resolved.", {
      exact: true,
    })
    .waitFor();
  await page.screenshot({
    path: path.join(output, "resolved.png"),
    fullPage: true,
  });
  assert.equal(
    (await get("/findings?domain_id=" + asset)).priorities.length,
    0,
  );
  seed(asset, "issues");
  const reopened = await until("/findings?domain_id=" + asset, (d) =>
    d.items.every(
      (f) => f.status === "open" && f.recheck_status === "confirmed",
    ),
  );
  assert.deepEqual(reopened.items.map((f) => f.id).sort(), ids);
  assert.deepEqual(
    Object.fromEntries(reopened.items.map((f) => [f.id, f.first_seen_at])),
    firstSeen,
  );
  const selected = initial.priorities[0].id;
  let detail = await get("/findings/" + selected);
  assert(
    detail.history.some((e) => e.kind === "resolved") &&
      detail.history.some((e) => e.kind === "reopened"),
  );
  const historyLength = detail.history.length;
  docker("restart", "backend", "worker");
  for (let attempt = 0; attempt < 100; attempt++) {
    try {
      const health = await context.request.get(base + "/api/v1/health");
      if (health.ok()) break;
    } catch {}
    await new Promise((r) => setTimeout(r, 250));
  }
  await page.goto(detailURL);
  await page
    .getByRole("heading", { name: "Finding history", exact: true })
    .waitFor();
  detail = await get("/findings/" + selected);
  assert.equal(detail.history.length, historyLength);
  assert.equal(detail.first_seen_at, firstSeen[selected]);
  const backfill = docker(
    "exec",
    "-T",
    "worker",
    ".venv/bin/python",
    "-m",
    "app.findings.backfill",
    "--organization-id",
    org,
  );
  assert(backfill.includes("Evaluated 0 terminal scans"));
  await page.getByRole("radio", { name: "Technical", exact: true }).check();
  await page.screenshot({
    path: path.join(output, "lifecycle-history.png"),
    fullPage: true,
  });
  results.flow.push(
    "real resolution -> reopening with stable IDs/firstSeen -> container restart persistence -> idempotent maintenance backfill",
  );
  const staleAsset = await enroll("qa-stale.example.com");
  seed(staleAsset, "stale");
  await until(
    "/findings?domain_id=" + staleAsset,
    (d) => d.total === 6 && d.items.every((f) => f.stale),
  );
  await page.goto(base + "/app/findings?domain_id=" + staleAsset);
  await page
    .getByText("6 findings in this selection · 6 open · 0 resolved.", {
      exact: true,
    })
    .waitFor();
  await capture("stale");
  results.flow.push(
    "source-time freshness produces explicit stale evidence without false resolution",
  );
  await page.route("**/api/v1/findings?*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: { message: "Controlled QA outage" } }),
    }),
  );
  await page.goto(base + "/app/findings");
  await page.getByRole("button", { name: "Retry findings" }).waitFor();
  await page.screenshot({
    path: path.join(output, "error.png"),
    fullPage: true,
  });
  await page.unroute("**/api/v1/findings?*");
  await page.getByRole("button", { name: "Retry findings" }).click();
  await page
    .getByText("12 findings in this selection · 12 open · 0 resolved.", {
      exact: true,
    })
    .waitFor();
  assert.deepEqual(results.errors, []);
  results.flow.push("API error/retry and exact cross-asset counts");
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
