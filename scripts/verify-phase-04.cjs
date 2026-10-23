const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const output = path.resolve(__dirname, '../docs/evidence/phase-04');
const base = process.env.BASE_URL || 'http://127.0.0.1:15173';
(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  const results = { browser: browser.version(), fixtures: 'Isolated DB, injected DNS/socket; no external scan', flow: [], viewports: [], errors: [] };
  page.on('pageerror', e => results.errors.push(e.message));
  await page.goto(base + '/app/assets');
  await page.getByRole('heading', { name: 'Sign in', exact: true }).waitFor();
  results.flow.push('private route requires authentication');
  await page.getByRole('link', { name: 'Create an account', exact: true }).click();
  const email = `qa-${crypto.randomUUID()}@example.com`;
  const password = crypto.randomBytes(24).toString('base64url');
  await page.getByRole('textbox', { name: 'Email address' }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await page.getByRole('heading', { name: 'Sign in', exact: true }).waitFor();
  await page.getByRole('textbox', { name: 'Email address' }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('textbox', { name: 'Company name' }).fill('LOCAL QA — injected network fixtures');
  await page.getByRole('button', { name: 'Create workspace', exact: true }).click();
  await page.getByRole('heading', { name: 'LOCAL QA — injected network fixtures', exact: true }).waitFor();
  await page.getByRole('link', { name: 'Assets', exact: true }).click();
  const axe = fs.readFileSync(require.resolve(process.env.AXE_MODULE || 'axe-core'), 'utf8');
  async function capture(name) {
    for (const width of [360, 768, 1280, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => document.fonts.ready);
      await page.evaluate(() => {
        let label = document.getElementById('qa-label');
        if (!label) {
          label = document.createElement('p'); label.id = 'qa-label';
          label.textContent = 'LOCAL QA — isolated database and injected DNS/socket fixtures. Not a live security assessment.';
          document.querySelector('main').prepend(label);
        }
        window.scrollTo(0, 0);
      });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name} overflow at ${width}`);
      await page.evaluate(axe);
      const violations = await page.evaluate(async () => (await window.axe.run(document, {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] }
      })).violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })));
      assert.deepEqual(violations, [], `${name}/${width} accessibility`);
      await page.screenshot({ path: path.join(output, `${name}-${width}.png`), fullPage: true });
      results.viewports.push({ page: name, width, overflow: false, violations });
    }
  }
  async function enroll(host, verify = true) {
    await page.goto(base + '/app/assets');
    await page.getByRole('textbox', { name: 'Domain name' }).fill(host);
    await page.getByRole('checkbox').check();
    await page.getByRole('button', { name: 'Add domain', exact: true }).click();
    await page.getByRole('heading', { name: `DNS TXT instructions: ${host}` }).waitFor();
    const article = page.locator('.asset-list article').filter({ has: page.getByRole('heading', { name: host, exact: true }) });
    assert(await article.getByRole('button', { name: 'Run security checks' }).isDisabled());
    if (verify) {
      await page.getByRole('button', { name: 'Verify ownership', exact: true }).click();
      await page.getByText('Domain control verified. This is not a security assessment.', { exact: true }).waitFor();
      assert(await article.getByRole('button', { name: 'Run security checks' }).isEnabled());
    }
    return article;
  }
  await enroll('qapending.example.com', false);
  await page.getByRole('link', { name: 'Scan history for qapending.example.com' }).click();
  await page.getByText('No completed scans yet', { exact: true }).waitFor();
  results.flow.push('pending asset disabled; genuine empty history');
  await capture('empty');
  let article = await enroll('qacomplete.example.com');
  await article.getByRole('button', { name: 'Run security checks' }).click();
  await page.getByRole('heading', { name: 'Security check record', exact: true }).waitFor();
  await page.locator('.scan-summary').getByText(/queued|running/, { exact: true }).waitFor();
  await page.screenshot({ path: path.join(output, 'progress.png'), fullPage: true });
  await page.locator('.scan-summary').getByText('completed', { exact: true }).waitFor();
  assert.equal(await page.locator('.observation').count(), 13);
  const completeURL = page.url();
  const summary = page.locator('.observation summary').first();
  await summary.focus(); await page.keyboard.press('Enter');
  assert(await summary.evaluate(el => el.parentElement.open));
  const focus = await summary.evaluate(el => ({ width: getComputedStyle(el).outlineWidth, style: getComputedStyle(el).outlineStyle }));
  assert.notEqual(focus.width, '0px'); assert.notEqual(focus.style, 'none');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  assert.equal(await summary.evaluate(el => getComputedStyle(el).transitionDuration), '0s');
  results.flow.push('queued/running -> 13 persisted observations; keyboard disclosure/focus/reduced motion');
  await capture('completed');
  await page.reload();
  await page.locator('.scan-summary').getByText('completed', { exact: true }).waitFor();
  assert.equal(await page.locator('.observation').count(), 13);
  await page.getByRole('link', { name: 'View scan history', exact: true }).click();
  await page.getByRole('link', { name: 'View scan record', exact: true }).waitFor();
  await capture('history');
  await page.getByRole('link', { name: 'View scan record', exact: true }).click();
  assert.equal(page.url(), completeURL);
  results.flow.push('reload and history preserve scan ID/evidence');
  article = await enroll('qapartial.example.com');
  await article.getByRole('button', { name: 'Run security checks' }).click();
  await page.locator('.scan-summary').getByText('partial', { exact: true }).waitFor();
  await page.getByText('Scan limitation', { exact: true }).waitFor();
  await page.screenshot({ path: path.join(output, 'partial.png'), fullPage: true });
  results.flow.push('TLS failure is partial; DNS and HTTP survive');
  article = await enroll('qablocked.example.com');
  await article.getByRole('button', { name: 'Run security checks' }).click();
  await page.locator('.scan-summary').getByText('failed', { exact: true }).waitFor();
  await page.getByText('DNS includes a private or special-use address. Network probes were blocked.', { exact: true }).waitFor();
  await page.screenshot({ path: path.join(output, 'blocked.png'), fullPage: true });
  results.flow.push('unsafe DNS fails closed with explanatory feedback');
  await page.goto(base + '/app/assets');
  await page.getByRole('heading', { name: 'Assets', exact: true }).waitFor();
  await capture('assets');
  await page.route('**/api/v1/domains/*/scans/*', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { message: 'Controlled QA outage' } }) }));
  await page.goto(completeURL);
  await page.getByRole('button', { name: 'Retry loading scans' }).waitFor();
  await page.unroute('**/api/v1/domains/*/scans/*');
  await page.getByRole('button', { name: 'Retry loading scans' }).click();
  await page.locator('.scan-summary').getByText('completed', { exact: true }).waitFor();
  results.flow.push('real UI recovers after controlled API outage');
  assert.deepEqual(results.errors, []);
  fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
