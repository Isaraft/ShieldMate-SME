// Isolated local backup/recovery and real compiled-runtime checks. Never overwrites a DB.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs"),
  assert = require("node:assert/strict"),
  crypto = require("node:crypto");
const { execFileSync, spawnSync } = require("node:child_process");
const {
  root,
  work,
  out: evidenceOut,
  base,
  restoredBase,
  project,
  restoredProject,
  backup: backupName,
} = require("./qa/runtime.cjs");
const out = evidenceOut + "/checks";
const files = [
  "-f",
  "compose.local.yaml",
  "-f",
  "scripts/qa/phase08.override.yaml",
];
const docker = (args, env = {}) =>
  execFileSync("docker", args, {
    cwd: root,
    encoding: "utf8",
    env: { ...process.env, ...env },
  });
const qa = ["compose", "-p", project, ...files];
const hash = (b) => crypto.createHash("sha256").update(b).digest("hex");
(async () => {
  const backup = JSON.parse(
    docker([
      ...qa,
      "exec",
      "-T",
      "backend",
      ".venv/bin/python",
      "-m",
      "app.maintenance",
      "backup",
      "/app/backups/" + backupName,
    ]),
  );
  const restore = JSON.parse(
    docker([
      "run",
      "--rm",
      "--network",
      "none",
      "--read-only",
      "--tmpfs",
      "/tmp",
      "--mount",
      "source=" + project + "_backups,target=/backups,readonly",
      "--mount",
      "source=" + restoredProject + "_database,target=/app/storage",
      "shieldmate-backend",
      ".venv/bin/python",
      "-m",
      "app.maintenance",
      "restore",
      "/backups/" + backupName,
      "/app/storage/shieldmate.db",
    ]),
  );
  assert.deepEqual(restore.rows, backup.rows);
  assert.equal(restore.sha256, backup.sha256);
  const refusal = spawnSync(
    "docker",
    [
      ...qa,
      "exec",
      "-T",
      "backend",
      ".venv/bin/python",
      "-m",
      "app.maintenance",
      "backup",
      "/app/backups/" + backupName,
    ],
    { cwd: root, encoding: "utf8" },
  );
  assert.notEqual(refusal.status, 0);
  docker(["compose", "-p", restoredProject, ...files, "up", "-d", "--wait"], {
    SHIELDMATE_RC_PORT: new URL(restoredBase).port,
  });
  const browser = await chromium.launch(),
    ctx = await browser.newContext({
      storageState: work + "/golden-state.json",
    });
  async function get(base, p) {
    const r = await ctx.request.get(base + "/api/v1" + p);
    assert(r.ok(), p + " " + r.status());
    return r.json();
  }
  const ids = JSON.parse(fs.readFileSync(out + "/resources.json")),
    records = JSON.parse(fs.readFileSync(out + "/final-report-records.json"));
  const checks = [];
  for (const p of [
    "/auth/me",
    "/domains",
    "/domains/" + ids.domain + "/scans",
    "/findings",
    "/tasks/" + ids.task,
    "/reports",
    "/dashboard/summary",
  ]) {
    const original = await get(base, p),
      restored = await get(restoredBase, p);
    if (p === "/dashboard/summary") {
      delete original.generated_at;
      delete restored.generated_at;
    }
    assert.deepEqual(restored, original);
    checks.push(p);
  }
  for (const r of records.filter((r) => r.kind === "short")) {
    const response = await ctx.request.get(
      restoredBase + "/api/v1/reports/" + r.id + "/download",
    );
    assert(response.ok());
    assert.equal(hash(await response.body()), r.sha256);
  }
  const rc = await browser.newContext(),
    page = await rc.newPage();
  await page.goto("http://127.0.0.1:8080/app/assets");
  await page.bringToFront();
  await page.waitForURL("**/login");
  assert.equal(
    (await rc.request.get("http://127.0.0.1:8080/api/v1/auth/me")).status(),
    401,
  );
  for (const url of ["/", "/login", "/demo", "/unknown-phase08"]) {
    const r = await rc.request.get("http://127.0.0.1:8080" + url);
    assert.equal(r.status(), 200);
    assert(
      r.headers()["content-security-policy"].includes("frame-ancestors 'none'"),
    );
    assert.equal(r.headers()["x-frame-options"], "DENY");
    assert.equal(r.headers()["cache-control"], "no-store");
  }
  assert.equal(
    (
      await rc.request.get("http://127.0.0.1:8080/api/v1/health/ready", {
        headers: { Host: "evil.example" },
      })
    ).status(),
    400,
  );
  assert.equal(
    (
      await rc.request.post("http://127.0.0.1:8080/api/v1/auth/login", {
        data: "x".repeat(17000),
      })
    ).status(),
    413,
  );
  const deep = await ctx.newPage();
  await deep.goto(restoredBase + "/app/tasks/" + ids.task);
  await deep.bringToFront();
  await deep.locator(".private-nav:visible").waitFor();
  await deep.locator("#task-status").waitFor();
  assert.equal(await deep.locator("#task-status").inputValue(), "done");
  const c = await ctx.newCDPSession(deep),
    s = await c.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
    });
  fs.writeFileSync(
    evidenceOut + "/screenshots/restored-task-en.png",
    Buffer.from(s.data, "base64"),
  );
  await c.detach();
  const inspect = JSON.parse(
    docker([
      "inspect",
      "shieldmate-rc-backend-1",
      "shieldmate-rc-worker-1",
      "shieldmate-rc-frontend-1",
    ]),
  ).map((r) => ({
    name: r.Name,
    user: r.Config.User,
    readonly: r.HostConfig.ReadonlyRootfs,
    cap_drop: r.HostConfig.CapDrop,
    security: r.HostConfig.SecurityOpt,
    ports: r.NetworkSettings.Ports,
    health: r.State.Health?.Status || r.State.Status,
  }));
  for (const r of inspect) {
    assert(r.readonly);
    assert(r.cap_drop.includes("ALL"));
    assert(r.user && !r.user.startsWith("0"));
    assert(["healthy", "running"].includes(r.health));
  }
  assert.deepEqual(inspect[0].ports, { "8000/tcp": null });
  assert(
    inspect[2].ports["8080/tcp"].every(
      (p) => p.HostIp === "127.0.0.1" && p.HostPort === "8080",
    ),
  );
  const permissions = JSON.parse(
    docker([
      "compose",
      "-f",
      "compose.local.yaml",
      "exec",
      "-T",
      "backend",
      "python",
      "-c",
      'import os,stat,json;print(json.dumps({p:{"mode":oct(stat.S_IMODE(os.stat(p).st_mode)),"uid":os.stat(p).st_uid} for p in ["/app/storage","/app/storage/shieldmate.db","/app/backups"]}))',
    ]),
  );
  assert.equal(permissions["/app/storage/shieldmate.db"].mode, "0o600");
  assert.equal(permissions["/app/storage"].mode, "0o700");
  const migration = spawnSync(
    "docker",
    [
      "run",
      "--rm",
      "--network",
      "none",
      "--read-only",
      "--tmpfs",
      "/tmp",
      "-e",
      "SHIELDMATE_DATABASE_URL=sqlite:////tmp/bad.db",
      "shieldmate-backend",
      "sh",
      "-c",
      `.venv/bin/python -c 'import sqlite3;d=sqlite3.connect("/tmp/bad.db");d.execute("create table alembic_version(version_num varchar(32))");d.execute("insert into alembic_version values (?)",("invalid_qa_revision",));d.commit()' && .venv/bin/alembic upgrade head && exec .venv/bin/uvicorn app.main:app`,
    ],
    { cwd: root, encoding: "utf8" },
  );
  assert.notEqual(migration.status, 0);
  assert((migration.stdout + migration.stderr).includes("invalid_qa_revision"));
  fs.writeFileSync(
    out + "/operations.json",
    JSON.stringify(
      {
        backup,
        restore,
        existing_destination_refused: true,
        restored_api_checks: checks,
        restored_private_pdf_hashes: 3,
        rc_headers_host_size_deep_links: "PASS",
        runtime: inspect,
        permissions,
        failed_migration_exit: migration.status,
        failed_migration_never_started_http: !(
          migration.stdout + migration.stderr
        ).includes("Uvicorn running"),
      },
      null,
      2,
    ) + "\n",
  );
  await browser.close();
  console.log(
    JSON.stringify(
      { backup_rows: backup.rows, restored_api_checks: checks, checks: "PASS" },
      null,
      2,
    ),
  );
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
