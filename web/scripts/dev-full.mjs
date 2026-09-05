import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(here, "..");
const repoRoot = path.resolve(webRoot, "..");
const windows = process.platform === "win32";
const managedPython = windows && process.env.LOCALAPPDATA
  ? path.join(process.env.LOCALAPPDATA, "Python", "bin", "python.exe")
  : null;
const python = process.env.JB_CLARITY_PYTHON || (managedPython && existsSync(managedPython) ? managedPython : (windows ? "python" : "python3"));
const sync = spawnSync(process.execPath, [path.join(here, "sync-workbench.mjs")], { cwd: webRoot, stdio: "inherit", env: process.env });
if (sync.status !== 0) process.exit(sync.status ?? 1);

const engine = spawn(python, ["-m", "uvicorn", "jb_clarity.api:app", "--app-dir", "engine/src", "--host", "127.0.0.1", "--port", "8000"], {
  cwd: repoRoot,
  stdio: "inherit",
  env: process.env,
});
const web = spawn(process.execPath, [path.join(webRoot, "node_modules", "next", "dist", "bin", "next"), "dev", "--hostname", "127.0.0.1", "--port", "3000"], {
  cwd: webRoot,
  stdio: "inherit",
  env: process.env,
});

let closing = false;
function close(code = 0) {
  if (closing) return;
  closing = true;
  if (windows) {
    for (const child of [engine, web]) {
      if (child.pid) spawn("taskkill.exe", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" });
    }
    setTimeout(() => process.exit(code), 400);
  } else {
    engine.kill("SIGTERM");
    web.kill("SIGTERM");
    process.exitCode = code;
  }
}

engine.on("exit", (code) => { if (!closing) close(code ?? 1); });
web.on("exit", (code) => { if (!closing) close(code ?? 1); });
process.on("SIGINT", () => close(0));
process.on("SIGTERM", () => close(0));
