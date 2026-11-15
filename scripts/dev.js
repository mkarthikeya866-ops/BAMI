const { spawn } = require("node:child_process");
const { existsSync } = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const venvPython = process.platform === "win32"
    ? path.join(root, ".venv", "Scripts", "python.exe")
    : path.join(root, ".venv", "bin", "python");
const python = existsSync(venvPython)
    ? venvPython
    : process.platform === "win32" ? "python" : "python3";

let stopping = false;
let exitCode = 0;
const children = [];

function stop(code = 0) {
    if (stopping) {
        return;
    }

    stopping = true;
    exitCode = code;
    children.forEach((child) => {
        if (child.exitCode === null && child.signalCode === null) {
            child.kill();
        }
    });
}

function start(name, cwd, args) {
    const child = spawn(python, args, { cwd, stdio: "inherit" });
    children.push(child);
    child.on("error", (error) => {
        console.error(`${name} failed to start: ${error.message}`);
        stop(1);
    });
    child.on("exit", (code, signal) => {
        if (!stopping) {
            console.error(`${name} stopped${signal ? ` (${signal})` : ` with exit code ${code}`}.`);
            stop(code || 1);
        }
    });
}

start("Backend", path.join(root, "Backend"), [
    "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"
]);
start("Frontend", path.join(root, "Frontend"), [
    "-m", "http.server", "5501", "--bind", "127.0.0.1"
]);

process.on("SIGINT", () => stop(0));
process.on("SIGTERM", () => stop(0));
process.on("exit", () => {
    process.exitCode = exitCode;
});
