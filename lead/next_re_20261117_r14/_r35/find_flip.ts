// 定位 102→103 翻类的那一锚：用 before-§2.21 / before-H59,H60 / before-AZ 快照重建旧池
import * as fs from "node:fs";
import * as path from "node:path";

const norm = (s: string): string => s.replace(/[*_~\s]/g, "").replace(/\u0060/g, "");
const ROOT = "D:\\Project\\ra2-campaign-forge";
const BASE = path.join(ROOT, "lead", "next_re_20261117_r14", "R17_LEAD_BASELINE");

// 被改过的三个文件 → 旧快照（v5.10 anchor_check 记录时刻 10:46:32 之前的版本）
const SNAP: Record<string, string> = {
  "lead\\next_re_20261117_r14\\R14_COMMON.md": path.join(BASE, "R14_COMMON.before_221.md"),
  "lead\\next_re_20261117_r14\\LEAD_LOCK": path.join(BASE, "LEAD_LOCK.before_AZ"),
  "lead\\next_re_20261117_r14\\BOARD_ARCHIVE.md": path.join(BASE, "BOARD_ARCHIVE.before_H59.md"),
};

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

const tsv = process.argv[2];
const rows = fs.readFileSync(tsv, "utf8").split("\n").filter(l => l.length).map(l => l.split("\t"));
const data = rows.slice(1);

const cur: Record<string, string> = {}, old: Record<string, string> = {};
function load(f: string, into: Record<string, string>) {
  if (into[f] !== undefined) return;
  const abs = path.join(ROOT, f.replace(/\\/g, "/"));
  into[f] = fs.existsSync(abs) && fs.statSync(abs).isFile() ? norm(fs.readFileSync(abs, "utf8")) : "";
  if (SNAP[f]) {
    const sp = SNAP[f];
    old[f] = fs.existsSync(sp) ? norm(fs.readFileSync(sp, "utf8")) : into[f];
  } else {
    old[f] = into[f];
  }
}

let flips = 0;
for (const r of data) for (const it of splitPaths(r[3] || "")) {
  const { file, anchor } = splitAnchor(it);
  if (!anchor) continue;
  const f = file.replace(/^\u0060+|\u0060+$/g, "").trim();
  load(f, cur);
  const nowHit = anchorHits(cur[f] || "", anchor);
  const oldHit = anchorHits(old[f] || "", anchor);
  if (nowHit && !oldHit) {
    flips++;
    console.log("FLIP-to-mech   " + r[0] + "   " + f.split("\\").pop() + "(" + anchor + ")");
  }
  if (!nowHit && oldHit) {
    console.log("FLIP-away      " + r[0] + "   " + f.split("\\").pop() + "(" + anchor + ")  <== 池变小了？");
  }
}
console.log("flips to mech = " + flips);
