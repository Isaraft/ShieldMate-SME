// Fixed localhost-only QA profiles. No arbitrary origin/project can be supplied.
const path = require("node:path");
const root = path.resolve(__dirname, "../..");
const phase = process.env.SHIELDMATE_QA_PHASE || "08";
if (!["08", "09"].includes(phase))
  throw new Error("Unsupported local QA phase");
const work = path.resolve(root, "../../work/phase" + phase);
module.exports = Object.freeze({
  phase,
  root,
  work,
  out:
    phase === "08"
      ? path.join(root, "docs/evidence/phase-08")
      : path.join(work, "engineering"),
  base: "http://127.0.0.1:" + (phase === "08" ? "15873" : "16073"),
  restoredBase: "http://127.0.0.1:" + (phase === "08" ? "15973" : "16173"),
  project: "shieldmate-phase" + phase + "-qa",
  restoredProject: "shieldmate-phase" + phase + "-restored",
  backup: "phase" + phase + ".sqlite",
});
