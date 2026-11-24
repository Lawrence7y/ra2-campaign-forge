// 定位 v5.10 基数漂移：列出所有「含 § 的锚」中现被判为 mech 的项
import * as fs from "node:fs";
import * as path from "node:path";

const norm = (s: string): string => s.replace(/[*_~\s]/g, "").replace(/\u0060/g, "");

function splitPaths(s: string): string[] {
  const out: string[] = []; let depth = 0, cur = "";
  for (const ch of s) {
    if (ch === "(" || ch === "（") depth++;
    else if (ch === ")" || ch === "）") depth = Math.max(0, depth - 1);
    if (ch === ";" && depth === 0) { out.push(cur); cur = ""; continue; }
    cur += ch;
  }
  if (cur.trim()) out.push(cur);
  return out.map(x => x.trim()).filter(Boolean);
}
function splitAnchor(item: string): { file: string; anchor: string | null } {
  if (!/[)\uFF09]$/.test(item)) return { file: item, anchor: null };
  let depth = 0, start = -1;
  for (let i = item.length - 1; i >= 0; i--) {
    const c = item[i];
    if (c === ")" || c === "）") { depth++; continue; }
    if (c === "(" || c === "（") { depth--; if (depth === 0) { start = i; break; } }
  }
  if (start <= 0) return { file: item, anchor: null };
  return { file: item.slice(0, start), anchor: item.slice(start + 1, item.length - 1) };
}
function anchorHits(pool: string, anchor: string): boolean {
  const parts = norm(anchor).split("/").map(x => x.replace(/段$/, "").trim()).filter(Boolean);
  return parts.length > 0 && parts.every(p => pool.includes(p));
}

const repoRoot = "D:\\Project\\ra2-campaign-forge";
const tsv = process.argv[2];
const rows = fs.readFileSync(tsv, "utf8").split("\n").filter(l => l.length).map(l => l.split("\t"));
const data = rows.slice(1);

const cache: Record<string, string> = {};
for (const r of data) for (const it of splitPaths(r[3] || "")) {
  const { file, anchor } = splitAnchor(it);
  if (!anchor) continue;
  const f = file.replace(/^\u0060+|\u0060+$/g, "").trim();
  if (cache[f] !== undefined) continue;
  const abs = path.join(repoRoot, f.replace(/\\/g, "/"));
  cache[f] = fs.existsSync(abs) && fs.statSync(abs).isFile() ? norm(fs.readFileSync(abs, "utf8")) : "";
}

let mechSec = 0;
for (const r of data) for (const it of splitPaths(r[3] || "")) {
  const { file, anchor } = splitAnchor(it);
  if (!anchor) continue;
  const f = file.replace(/^\u0060+|\u0060+$/g, "").trim();
  const pool = cache[f] || "";
  const isSectionStyle = /§\s*\d/.test(anchor);
  if (isSectionStyle && anchorHits(pool, anchor)) {
    mechSec++;
    const parts = norm(anchor).split("/");
    const hits = parts.map(p => pool.includes(p.replace(/段$/, "").trim()));
    console.log("MECH(§-style)  " + r[0] + "  " + f.split("\\").pop() + "(" + anchor + ")  parts=" + JSON.stringify(hits));
  }
}
console.log("total §-style anchors passing mech = " + mechSec);
