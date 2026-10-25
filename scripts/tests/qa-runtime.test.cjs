// ENGINEERING TEST ONLY — no participants, browser traffic or research observations.
const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const path = require("node:path");
const file = path.resolve(__dirname, "../qa/runtime.cjs");
function run(phase) {
  const env = { ...process.env };
  delete env.SHIELDMATE_QA_PHASE;
  if (phase !== undefined) env.SHIELDMATE_QA_PHASE = phase;
  return spawnSync(
    process.execPath,
    [
      "-e",
      "process.stdout.write(JSON.stringify(require(process.argv[1])))",
      file,
    ],
    { env, encoding: "utf8" },
  );
}
test("default Phase 08 profile preserves existing isolated paths", () => {
  const r = run();
  assert.equal(r.status, 0);
  const c = JSON.parse(r.stdout);
  assert.equal(c.base, "http://127.0.0.1:15873");
  assert.equal(c.project, "shieldmate-phase08-qa");
  assert(c.out.endsWith("docs/evidence/phase-08"));
});
test("Phase 09 uses new volumes/ports and separate engineering output", () => {
  const r = run("09");
  assert.equal(r.status, 0);
  const c = JSON.parse(r.stdout);
  assert.equal(c.base, "http://127.0.0.1:16073");
  assert.equal(c.restoredBase, "http://127.0.0.1:16173");
  assert.equal(c.project, "shieldmate-phase09-qa");
  assert(c.out.endsWith("phase09/engineering"));
});
test("unsupported/arbitrary phase cannot select a network destination", () => {
  for (const value of ["10", "../../", "https://external.invalid"]) {
    assert.notEqual(run(value).status, 0);
  }
});
