// Minimal stdio MCP client for Premiere Pro:
//   node pr_call.mjs list
//   node pr_call.mjs call <tool> '<json args or @file.json>'
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";

const [, , mode, tool, argJson] = process.argv;
const srv = spawn("node", ["C:/Users/btaza/mcp/Adobe-Premiere-Pro-MCP/dist/server.js"], {
  stdio: ["pipe", "pipe", "pipe"],
});

let buf = "", id = 0;
const waits = {};
let cepConnected = false;
let cepWaitResolve = null;
const cepReady = new Promise((res) => { cepWaitResolve = res; });

srv.stderr.on("data", (d) => {
  const s = d.toString();
  process.stderr.write(s);
  if (s.includes("CEP panel connected")) {
    cepConnected = true;
    if (cepWaitResolve) cepWaitResolve(true);
  }
});

srv.stdout.on("data", (d) => {
  buf += d;
  let i;
  while ((i = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, i).trim();
    buf = buf.slice(i + 1);
    if (!line) continue;
    try {
      const m = JSON.parse(line);
      if (m.id && waits[m.id]) {
        waits[m.id](m);
        delete waits[m.id];
      }
    } catch {}
  }
});

const rpc = (method, params) =>
  new Promise((r) => {
    const n = ++id;
    waits[n] = r;
    srv.stdin.write(JSON.stringify({ jsonrpc: "2.0", id: n, method, params }) + "\n");
  });
const note = (method, params) =>
  srv.stdin.write(JSON.stringify({ jsonrpc: "2.0", method, params }) + "\n");

await rpc("initialize", {
  protocolVersion: "2025-06-18",
  capabilities: {},
  clientInfo: { name: "agy-pr-call", version: "1.0" },
});
note("notifications/initialized", {});

if (mode === "list") {
  const r = await rpc("tools/list", {});
  for (const t of r.result.tools) {
    console.log(t.name, "-", (t.description || "").slice(0, 110).replace(/\s+/g, " "));
  }
} else {
  if (!cepConnected) {
    await Promise.race([cepReady, new Promise((r) => setTimeout(r, 5500))]);
  }
  const argText = (argJson && argJson.startsWith("@") ? readFileSync(argJson.slice(1), "utf8") : (argJson || "{}")).replace(/^\uFEFF/, "");
  const r = await rpc("tools/call", { name: tool, arguments: JSON.parse(argText) });
  const res = r.result ?? r.error;
  console.log(res && res.content ? res.content.filter((c) => c.type === "text").map((c) => c.text).join("\n") : JSON.stringify(res));
}

srv.kill();
process.exit(0);
