// _si_extract_gate.mjs — 从 dwfrun payload 的 lowered 工作流脚本里按 JS 语义还原 GATE_CODE 数组，拼接为 Python 源码。
// 用法: node _si_extract_gate.mjs <payload.mjs> <out.py>
// fps 表按当前磁盘实算 sha256（与门禁运行时同一来源语义）。只读 payload 与被指纹引用的文件；只写 out.py。
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { resolve, posix } from "node:path";

const ROOT = "D:/Project/ra2-campaign-forge";
const [payloadPath, outPath] = process.argv.slice(2);
if (!payloadPath || !outPath) {
  console.error("usage: node _si_extract_gate.mjs <payload.mjs> <out.py>");
  process.exit(2);
}
const src = readFileSync(payloadPath, "utf8");
const pm = src.match(/export const payload = (\{.*\});/);
if (!pm) {
  console.error("payload object not found");
  process.exit(1);
}
const payload = JSON.parse(pm[1]);
const lowered = payload.lowered;
if (typeof lowered !== "string") {
  console.error("payload.lowered is not a string");
  process.exit(1);
}
const gm = lowered.match(/const GATE_CODE = \[([\s\S]*?)\]\s*\.\s*join\(/);
if (!gm) {
  console.error("GATE_CODE array not found in lowered script");
  process.exit(1);
}
const region = gm[1];

// 1) fps 表：lowered 里所有 fps["path"] 引用 → 当前磁盘指纹对象（与门禁运行时同构：{sha256, bytes}）
const entryOf = (rel) => {
  const p = resolve(ROOT, rel);
  if (!existsSync(p)) return { sha256: "MISSING" };
  const buf = readFileSync(p);
  return { sha256: createHash("sha256").update(buf).digest("hex"), bytes: buf.length };
};
const fps = {};
for (const m of lowered.matchAll(/fps\["([^"]+)"\]/g)) {
  if (!(m[1] in fps)) fps[m[1]] = entryOf(m[1]);
}

// 2) 收集数组区域里用到的裸标识符（剔除字符串字面量内容），逐个找其 const 定义并按 fps 语义求值
const strsStripped = region.replace(/"(?:[^"\\]|\\.)*"/g, '""').replace(/'(?:[^'\\]|\\.)*'/g, "''");
const usedIds = new Set();
for (const m of strsStripped.matchAll(/[A-Za-z_$][\w$]*/g)) usedIds.add(m[0]);
const KEYWORDS = new Set(["in", "of", "not", "if", "else", "for", "return", "true", "false", "null", "None", "len", "repr"]);
const env = { fps };
for (const id of usedIds) {
  if (KEYWORDS.has(id)) continue;
  const dm = lowered.match(new RegExp("(?:const|let|var)\\s+" + id + "\\s*=\\s*([^;]+);"));
  if (!dm) continue;
  env[id] = new Function("fps", "return (" + dm[1] + ")")(fps);
}

// 3) 按原语义求值数组
const names = Object.keys(env);
const arr = new Function(...names, "return [" + region + "]")(...names.map((k) => env[k]));
const py = arr.join("\n");
writeFileSync(outPath, py, "utf8");
console.log("elements=" + arr.length + " chars=" + py.length + " fpsEntries=" + Object.keys(fps).length + " envIds=" + names.join(",") + " -> " + outPath);
