// Minimal stdio MCP client: node mcpcall.mjs list | node mcpcall.mjs call <tool> '<json args>'
import { spawn } from "node:child_process";
const [, , mode, tool, argJson] = process.argv;
const srv = spawn("npx", ["-y", "@kumoproductions/mcp-aftereffects"], { shell: true, stdio: ["pipe", "pipe", "inherit"] });
let buf = "", id = 0; const waits = {};
srv.stdout.on("data", d => {
  buf += d; let i;
  while ((i = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
    if (!line) continue;
    try { const m = JSON.parse(line); if (m.id && waits[m.id]) { waits[m.id](m); delete waits[m.id]; } } catch {}
  }
});
const rpc = (method, params) => new Promise(r => { const n = ++id; waits[n] = r; srv.stdin.write(JSON.stringify({ jsonrpc: "2.0", id: n, method, params }) + "\n"); });
const note = (method, params) => srv.stdin.write(JSON.stringify({ jsonrpc: "2.0", method, params }) + "\n");
await rpc("initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "1" } });
note("notifications/initialized", {});
if (mode === "schema") {
  const r = await rpc("tools/list", {});
  for (const t of r.result.tools) if (t.name === tool) console.log(JSON.stringify(t.inputSchema), " | ", t.description);
} else if (mode === "list") {
  const r = await rpc("tools/list", {});
  for (const t of r.result.tools) console.log(t.name, "-", (t.description || "").slice(0, 110).replace(/\s+/g, " "));
} else {
  const { readFileSync } = await import("node:fs");
  const argText = argJson && argJson.startsWith("@") ? readFileSync(argJson.slice(1), "utf8") : (argJson || "{}");
  const r = await rpc("tools/call", { name: tool, arguments: JSON.parse(argText) });
  const res = r.result ?? r.error;
  console.log(res && res.content ? res.content.filter(c => c.type === "text").map(c => c.text).join("\n") : JSON.stringify(res));
}
srv.kill(); process.exit(0);
