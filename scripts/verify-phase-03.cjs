const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const output = path.resolve(__dirname, "../docs/evidence/phase-03");
const base = process.env.BASE_URL || "http://127.0.0.1:5173";
(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  const email = `qa-${crypto.randomUUID()}@example.com`;
  const password = crypto.randomBytes(24).toString("base64url");
  const results = {
    browser: browser.version(),
    viewports: [],
    flow: [],
    errors: [],
  };
  page.on("pageerror", (e) => results.errors.push(e.message));
  await page.goto(base + "/app");
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  results.flow.push("unauthenticated redirect");
  await page
    .getByRole("link", { name: "Create an account", exact: true })
    .click();
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
    .getByRole("heading", { name: "Create your workspace", exact: true })
    .waitFor();
  results.flow.push("register and login");
  await page
    .getByRole("textbox", { name: "Company name" })
    .fill("QA workspace — local verification");
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await page
    .getByRole("heading", {
      name: "QA workspace — local verification",
      exact: true,
    })
    .waitFor();
  await page.reload();
  await page
    .getByRole("heading", {
      name: "QA workspace — local verification",
      exact: true,
    })
    .waitFor();
  results.flow.push("onboarding and session reload");
  const cookie = (await context.cookies()).find(
    (c) => c.name === "shieldmate_session",
  );
  assert(cookie.httpOnly);
  assert.equal(cookie.sameSite, "Lax");
  assert.equal(cookie.path, "/api");
  assert.equal(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
    0,
  );
  await page
    .getByRole("link", { name: "Organization settings", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Company name" })
    .fill("Renamed QA workspace");
  await page
    .getByRole("button", { name: "Save company name", exact: true })
    .click();
  await page.getByText("Workspace saved.", { exact: true }).waitFor();
  await page.reload();
  await page.getByRole("textbox", { name: "Company name" }).waitFor();
  assert.equal(
    await page.getByRole("textbox", { name: "Company name" }).inputValue(),
    "Renamed QA workspace",
  );
  results.flow.push("rename survives reload");
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.getByRole("link", { name: "Assets", exact: true }).click();
  await page
    .getByText("Your domain list starts here.", { exact: true })
    .waitFor();
  assert(!(await page.getByRole("checkbox").isChecked()));
  await page
    .getByRole("textbox", { name: "Domain name" })
    .fill("qaowned.example.com");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Add domain", exact: true }).click();
  await page
    .getByRole("heading", { name: "DNS TXT instructions: qaowned.example.com" })
    .waitFor();
  const value = await page
    .locator(".dns-instructions dd code")
    .nth(1)
    .innerText();
  await page
    .getByRole("button", { name: "Copy TXT value", exact: true })
    .click();
  assert.equal(
    await page.evaluate(() => navigator.clipboard.readText()),
    value,
  );
  await page.reload();
  await page
    .getByRole("button", {
      name: "DNS instructions for qaowned.example.com",
      exact: true,
    })
    .click();
  assert.equal(
    await page.locator(".dns-instructions dd code").nth(1).innerText(),
    value,
  );
  results.flow.push("authorization enrollment, copy and reload persistence");
  await page
    .getByRole("button", { name: "Verify ownership", exact: true })
    .click();
  await page
    .getByText("Domain control verified. This is not a security assessment.", {
      exact: true,
    })
    .waitFor();
  assert(
    await page
      .getByRole("button", { name: "Scan unavailable", exact: true })
      .isDisabled(),
  );
  results.flow.push(
    "injected DNS exact-match verification persisted by backend",
  );
  for (const width of [360, 768, 1280, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.evaluate(() => {
      let label = document.getElementById("qa-label");
      if (!label) {
        label = document.createElement("p");
        label.id = "qa-label";
        label.textContent =
          "LOCAL QA — isolated database and injected DNS response. Not live DNS verification.";
        document.querySelector("main").prepend(label);
      }
    });
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    );
    await page.screenshot({
      path: path.join(output, `assets-${width}.png`),
      fullPage: true,
    });
    await page.evaluate(
      fs.readFileSync(
        require.resolve(process.env.AXE_MODULE || "axe-core"),
        "utf8",
      ),
    );
    const scan = await page.evaluate(async () => {
      const result = await axe.run(document, {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
      });
      return result.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => n.target),
      }));
    });
    assert.deepEqual(scan, []);
    results.viewports.push({ width, violations: scan, overflow: false });
  }
  await page
    .getByRole("button", { name: "Generate new challenge", exact: true })
    .click();
  await page
    .getByText(
      "New challenge generated. Previous verification was revoked; replace the old TXT value.",
      { exact: true },
    )
    .waitFor();
  assert.notEqual(
    await page.locator(".dns-instructions dd code").nth(1).innerText(),
    value,
  );
  await page
    .getByRole("button", { name: "Remove domain", exact: true })
    .click();
  await page.getByRole("dialog", { name: "Remove domain?" }).waitFor();
  await page.keyboard.press("Escape");
  assert(!(await page.getByRole("dialog").isVisible()));
  await page
    .getByRole("button", { name: "Remove domain", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Confirm removal", exact: true })
    .click();
  await page
    .getByText("Your domain list starts here.", { exact: true })
    .waitFor();
  results.flow.push(
    "rotation invalidation, keyboard dialog cancellation and confirmed deletion",
  );
  for (const [name, message] of [
    ["qapending.example.com", "The exact TXT record was not found."],
    ["qatemporary.example.com", "DNS could not be checked right now."],
  ]) {
    await page.getByRole("textbox", { name: "Domain name" }).fill(name);
    await page.getByRole("checkbox").check();
    await page.getByRole("button", { name: "Add domain", exact: true }).click();
    await page
      .getByRole("heading", { name: "DNS TXT instructions: " + name })
      .waitFor();
    await page
      .getByRole("button", { name: "Verify ownership", exact: true })
      .click();
    await page.getByText(new RegExp(message.replace(".", "\."))).waitFor();
  }
  results.flow.push("missing record and temporary DNS error feedback");
  assert.deepEqual(results.errors, []);
  fs.writeFileSync(
    path.join(output, "browser-results.json"),
    JSON.stringify(results, null, 2),
  );
  await browser.close();
  console.log(JSON.stringify(results, null, 2));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
