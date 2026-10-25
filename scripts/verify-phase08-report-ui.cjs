// Additional real export-button/download rehearsal in its own explicitly synthetic workspace.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs"),
  crypto = require("node:crypto"),
  assert = require("node:assert/strict");
const { base, out } = require("./qa/runtime.cjs");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch(),
    context = await browser.newContext({ acceptDownloads: true }),
    page = await context.newPage(),
    errors = [],
    reports = [];
  page.on("pageerror", (e) => errors.push(e.message));
  async function get(p) {
    const r = await context.request.get(base + "/api/v1" + p);
    assert(r.ok(), p + " " + r.status());
    return r.json();
  }
  async function write(p, data) {
    const t = (await get("/auth/csrf")).csrf_token;
    const r = await context.request.post(base + "/api/v1" + p, {
      data,
      headers: { Origin: base, "X-CSRF-Token": t },
    });
    assert(r.ok(), p + " " + r.status());
    return r.json();
  }
  const email = "qa-pdf-ui-" + crypto.randomUUID() + "@example.com",
    password = crypto.randomBytes(24).toString("base64url");
  await write("/auth/register", { email, password });
  await write("/auth/login", { email, password });
  await write("/organizations", {
    name: "LOCAL QA — PDF interface rehearsal ӘҒҚҢӨҰҮҺІ",
  });
  const asset = await write("/domains", {
    fqdn: "qa-export-buttons.example.com",
    authorization_acknowledged: true,
  });
  await write("/domains/" + asset.id + "/verification/check", {});
  const scan = await write("/domains/" + asset.id + "/scans", {});
  let ready = false;
  for (let i = 0; i < 150; i++) {
    if (
      (await get("/findings/assessments/" + scan.id)).status === "evaluated"
    ) {
      ready = true;
      break;
    }
    await sleep(200);
  }
  assert(ready);
  await page.goto(base + "/app/reports");
  await page.bringToFront();
  await page.locator(".private-nav:visible").waitFor();
  for (const locale of ["en", "ru", "kk"]) {
    const catalog = JSON.parse(
      fs.readFileSync("backend/app/locales/" + locale + ".json"),
    );
    await page
      .getByRole("button", {
        name: { en: "English", ru: "Русский", kk: "Қазақша" }[locale],
        exact: true,
      })
      .click();
    const response = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/v1/reports") && r.request().method() === "POST",
    );
    await page
      .getByRole("button", {
        name: catalog["Generate PDF Snapshot"],
        exact: true,
      })
      .click();
    const record = await (await response).json();
    assert.equal(record.locale, locale);
    assert.equal(record.status, "ready");
    const row = page
      .locator(".work-queue li")
      .filter({ has: page.getByText(record.id, { exact: true }) });
    await row.waitFor();
    const download = page.waitForEvent("download");
    await row
      .getByRole("button", { name: catalog["Download PDF"], exact: true })
      .click();
    const artifact = await download;
    const file = await artifact.path(),
      bytes = fs.readFileSync(file);
    assert.equal(
      crypto.createHash("sha256").update(bytes).digest("hex"),
      record.sha256,
    );
    assert(artifact.suggestedFilename().endsWith("-" + locale + ".pdf"));
    reports.push({
      locale,
      id: record.id,
      sha256: record.sha256,
      button_and_browser_download: "PASS",
    });
  }
  const locale = "kk",
    catalog = JSON.parse(fs.readFileSync("backend/app/locales/kk.json"));
  await page.route("**/api/v1/reports/overview", (r) =>
    r.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: { message: "Reports unavailable" } }),
    }),
  );
  await page.reload();
  await page.getByRole("alert").first().waitFor();
  await page.unroute("**/api/v1/reports/overview");
  await page
    .getByRole("button", { name: catalog["Retry reports"], exact: true })
    .click();
  await page
    .getByRole("button", {
      name: catalog["Generate PDF Snapshot"],
      exact: true,
    })
    .waitFor();
  assert.equal(await page.getByRole("alert").count(), 0);
  await page.goto(base + "/demo");
  for (const l of ["en", "ru", "kk"]) {
    await page
      .getByRole("button", {
        name: { en: "English", ru: "Русский", kk: "Қазақша" }[l],
        exact: true,
      })
      .click();
    for (let i = 0; i < 4; i++) {
      await page.locator(".demo-steps button").nth(i).click();
      assert.equal(
        await page
          .locator(".demo-steps button")
          .nth(i)
          .getAttribute("aria-current"),
        "step",
      );
    }
  }
  fs.writeFileSync(
    out + "/checks/export-ui.json",
    JSON.stringify(
      { reports, report_retry: "PASS", demo_steps: 12, errors },
      null,
      2,
    ) + "\n",
  );
  assert.deepEqual(errors, []);
  await browser.close();
  console.log(
    JSON.stringify(
      { reports: reports.length, report_retry: "PASS", demo_steps: 12, errors },
      null,
      2,
    ),
  );
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
