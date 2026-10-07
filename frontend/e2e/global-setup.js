import { spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";

// Runs once after the servers are up: creates the demo account with six earlier days of check-ins.
export default async function globalSetup() {
  const python = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
  const db = "sqlite:///" + path.join(os.tmpdir(), "mindtrack_e2e.db").replace(/\\/g, "/");
  const r = spawnSync(python, ["seed_demo.py"], {
    cwd: path.resolve("../backend"),
    env: { ...process.env, DATABASE_URL: db, ALLOW_BACKDATED_CHECKINS: "true", PYTHONWARNINGS: "ignore" },
    encoding: "utf-8",
  });
  if (r.status !== 0) throw new Error("seed_demo.py failed:\n" + r.stdout + r.stderr);
}
