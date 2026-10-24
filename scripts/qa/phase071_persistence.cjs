// Reuse private local QA session; never print cookies or credentials.
const { request } = require(process.env.PLAYWRIGHT_MODULE || "playwright"),
  fs = require("node:fs"),
  assert = require("node:assert/strict"),
  crypto = require("node:crypto"),
  { execFileSync } = require("node:child_process");
(async () => {
  const c = await request.newContext({
      storageState: "../../work/phase071-auth-state.json",
    }),
    base = "http://127.0.0.1:15673/api/v1";
  async function artifacts() {
    const r = await c.get(base + "/reports");
    assert(r.ok());
    let rows = await r.json(),
      result = [];
    for (const row of rows.items) {
      const d = await c.get(base + "/reports/" + row.id + "/download");
      assert(d.ok());
      const sha = crypto
        .createHash("sha256")
        .update(await d.body())
        .digest("hex");
      assert.equal(sha, row.sha256);
      result.push({ id: row.id, sha256: sha });
    }
    return result;
  }
  const before = await artifacts();
  execFileSync("docker", [
    "compose",
    "-p",
    "shieldmate-phase071-qa",
    "-f",
    "scripts/qa/phase071.compose.yaml",
    "restart",
    "backend",
    "worker",
  ]);
  for (let i = 0; i < 60; i++) {
    try {
      const r = await c.get(base + "/health");
      if (r.ok()) break;
    } catch {}
    await new Promise((r) => setTimeout(r, 250));
  }
  const after = await artifacts();
  assert.deepEqual(after, before);
  fs.writeFileSync(
    "docs/evidence/phase-07-1/checks/restart-persistence.json",
    JSON.stringify(
      {
        reports: after.length,
        session_valid: true,
        bytes_unchanged: true,
        artifacts: after,
      },
      null,
      2,
    ) + "\n",
  );
  await c.dispose();
  console.log(
    "Restart retained session, history and " +
      after.length +
      " report checksums.",
  );
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
