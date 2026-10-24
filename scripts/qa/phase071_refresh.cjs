// New isolated workspaces only: produce final immutable PDF fixtures without changing old records.
const { request } = require(process.env.PLAYWRIGHT_MODULE || "playwright"),
  fs = require("node:fs"),
  crypto = require("node:crypto"),
  { execFileSync } = require("node:child_process");
const base = "http://127.0.0.1:15673",
  output = "docs/evidence/phase-07-1",
  compose = [
    "compose",
    "-p",
    "shieldmate-phase071-qa",
    "-f",
    "scripts/qa/phase071.compose.yaml",
  ];
(async () => {
  const results = [];
  for (const kind of ["complex", "partial"]) {
    const c = await request.newContext();
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
      if (!r.ok()) throw Error(p + " " + r.status() + " " + (await r.text()));
      return r.json();
    }
    const email = "qa-final-" + crypto.randomUUID() + "@example.com",
      password = crypto.randomBytes(24).toString("base64url");
    await write("/auth/register", { email, password });
    await write("/auth/login", { email, password });
    await write("/organizations", {
      name: "LOCAL QA — ӘҒҚҢӨҰҮҺІ / Финальная проверка " + kind,
    });
    for (let i = 0; i < (kind === "complex" ? 4 : 2); i++) {
      const a = await write("/domains", {
        fqdn:
          (kind === "complex"
            ? "long-authorized-domain-" + i + "-for-local-layout-verification"
            : "partial-" + i) + ".example.com",
        authorization_acknowledged: true,
      });
      if (kind === "partial" && i === 1) continue;
      await write("/domains/" + a.id + "/verification/check", {});
      execFileSync("docker", [
        ...compose,
        "exec",
        "-T",
        "backend",
        ".venv/bin/python",
        "-m",
        "scripts.qa.phase05_seed",
        "--asset-id",
        a.id,
        "--scenario",
        kind === "complex" ? "issues" : "unknown",
      ]);
    }
    for (let i = 0; i < 150; i++) {
      const s = await get("/reports/overview");
      if (
        s.can_generate &&
        (kind === "partial"
          ? s.readiness === "incomplete"
          : s.findings.length === 24)
      )
        break;
      await new Promise((r) => setTimeout(r, 200));
    }
    if (kind === "complex") {
      const f = await get("/findings");
      for (let i = 0; i < 3; i++) {
        const t = await write("/findings/" + f.items[i].id + "/task", {});
        const token = (await get("/auth/csrf")).csrf_token;
        const r = await c.patch(base + "/api/v1/tasks/" + t.id, {
          data: {
            version: t.version,
            status: ["todo", "in_progress", "done"][i],
            owner_label: "LOCAL QA — Әкімші / ИТ-провайдер",
            note: "PRIVATE-NOTE-NOT-FOR-PDF <script>",
          },
          headers: { Origin: base, "X-CSRF-Token": token },
        });
        if (!r.ok()) throw Error("Task patch");
      }
    }
    for (const locale of ["en", "ru", "kk"]) {
      const record = await write("/reports", {
        locale,
        request_key: crypto.randomUUID(),
      });
      if (record.status !== "ready")
        throw Error("PDF failed " + kind + "/" + locale);
      const r = await c.get(
          base + "/api/v1/reports/" + record.id + "/download",
        ),
        bytes = await r.body();
      if (
        crypto.createHash("sha256").update(bytes).digest("hex") !==
        record.sha256
      )
        throw Error("Hash mismatch");
      fs.writeFileSync(output + "/pdfs/" + kind + "-" + locale + ".pdf", bytes);
      results.push({ kind, ...record });
    }
    await c.dispose();
  }
  const c = await request.newContext();
  for (const locale of ["en", "ru", "kk"]) {
    const r = await c.get(base + "/api/v1/demo/report?locale=" + locale);
    if (!r.ok()) throw Error("Demo PDF failed");
    fs.writeFileSync(output + "/pdfs/demo-" + locale + ".pdf", await r.body());
  }
  await c.dispose();
  fs.writeFileSync(
    output + "/checks/final-report-records.json",
    JSON.stringify(results, null, 2) + "\n",
  );
  console.log("Created six final immutable reports and three demo exports.");
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
