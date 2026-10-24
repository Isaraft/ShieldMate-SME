// Prepare private local browser-QA state. The historical baseline proof is separate evidence.
const { request } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs"),
  crypto = require("node:crypto"),
  { execFileSync } = require("node:child_process");
(async () => {
  const state = "../../work/phase071-auth-state.json";
  if (fs.existsSync(state))
    throw Error(
      "QA state already exists; preserve it or select another isolated environment.",
    );
  fs.mkdirSync("../../work", { recursive: true });
  const c = await request.newContext(),
    base = "http://127.0.0.1:15673";
  async function get(p) {
    const r = await c.get(base + "/api/v1" + p);
    if (!r.ok()) throw Error(p + " " + r.status());
    return r.json();
  }
  async function write(p, data) {
    const token = (await get("/auth/csrf")).csrf_token;
    const r = await c.post(base + "/api/v1" + p, {
      data,
      headers: { Origin: base, "X-CSRF-Token": token },
    });
    if (!r.ok()) throw Error(p + " " + r.status());
    return r.json();
  }
  const email = "qa-polish-" + crypto.randomUUID() + "@example.com",
    password = crypto.randomBytes(24).toString("base64url");
  await write("/auth/register", { email, password });
  await write("/auth/login", { email, password });
  await write("/organizations", {
    name: "LOCAL QA — Phase 07.1 ТОО ӘҒҚҢӨҰҮҺІ",
  });
  const a = await write("/domains", {
    fqdn: "qa-polish.example.com",
    authorization_acknowledged: true,
  });
  await write("/domains/" + a.id + "/verification/check", {});
  execFileSync("docker", [
    "compose",
    "-p",
    "shieldmate-phase071-qa",
    "-f",
    "scripts/qa/phase071.compose.yaml",
    "exec",
    "-T",
    "backend",
    ".venv/bin/python",
    "-m",
    "scripts.qa.phase05_seed",
    "--asset-id",
    a.id,
    "--scenario",
    "issues",
  ]);
  fs.writeFileSync(
    "../../work/phase071-auth-private.json",
    JSON.stringify({ email, password }),
    { mode: 0o600 },
  );
  await c.storageState({ path: state });
  fs.chmodSync(state, 0o600);
  await c.dispose();
  console.log("Prepared isolated QA session; no credentials printed.");
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
