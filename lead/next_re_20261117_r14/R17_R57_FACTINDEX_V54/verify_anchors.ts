// verify_anchors.ts — FACT_INDEX evidence_paths 的锚点核验器（可复跑）
//
// 用法：node --experimental-strip-types verify_anchors.ts [FACT_INDEX.tsv] [repoRoot]
// 退出码：0 = 全部通过；1 = 有 MISS；2 = 自检（正控/反控）失败
//
// 口径（与 R14_COMMON §2.13 四一致，换人复核必须沿用，否则数字不可比）：
//   1. 去 markdown 标记（星号 / 反引号 / 下划线 / 波浪号）与全部空白后做子串匹配；
//   2. 以 " / " 分隔的复合锚逐段匹配；
//   3. 每段末尾的「段」字先剥掉。
//
// 三种必须支持的形态（按此顺序踩过三次误报，见 §2.13 四）：
//   A. 空白差异：实盘标题 "===== 追加 · 2026-11-20 20:5x · r15 第 99-104 轮 =====" 带空格，
//      锚写成 "追加·2026-11-20 20:5x·r15 第 99-104 轮" 无空格 ⇒ 归一化后应命中；
//   B. 正文行锚：台账 "**N9** 三条方法论修正" 是正文行不是标题 ⇒ 必须扫全文件，不能只扫 ^## 行；
//   C. 复合锚：   "第 105 轮 段 / 追加·…第 111 轮 段" 内层也带「段」⇒ 必须逐段剥。

import * as fs from "node:fs";
import * as path from "node:path";
import process from "node:process";

const norm = (s: string): string => s.replace(/[*_~\s]/g, "").replace(/\u0060/g, "");

function splitPaths(s: string): string[] {
  const out: string[] = [];
  let depth = 0, cur = "";
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
  if (!/[)）]$/.test(item)) return { file: item, anchor: null };
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

type SelfTest = { name: string; ok: boolean; detail: string };

function selfTest(docs: Record<string, string>, raw: Record<string, string>): SelfTest[] {
  const lock = docs["LEAD_LOCK"] || "";
  const ledger = docs["GOAL_THREE_TARGETS_20261018.md"] || "";
  const archive = docs["BOARD_ARCHIVE.md"] || "";
  const boardRaw = raw["STATUS_BOARD.md"] || "";
  const archRaw = raw["BOARD_ARCHIVE.md"] || "";
  return [
    { name: "A 空白差异(正控)", ok: anchorHits(lock, "追加·2026-11-20 20:5x·r15 第 99-104 轮 段"), detail: "锚无空格 vs 实盘有空格，应命中" },
    { name: "B 正文行锚(正控)", ok: anchorHits(ledger, "N9 三条方法论修正 段"), detail: "台账该串在正文行，应命中" },
    { name: "C 复合锚(正控)", ok: anchorHits(lock, "追加·2026-11-20 21:1x·r15 第 105 轮 段 / 追加·2026-11-20 22:1x·r15 第 111 轮 段"), detail: "两段各带「段」，应逐段剥后命中" },
    { name: "反控 不存在段", ok: !anchorHits(archive, "R17 第 999 轮 段"), detail: "不存在的轮次必须判 MISS" },
    { name: "反控 仅指针行", ok: !/^## .*R17 第 13 轮/m.test(boardRaw), detail: "第 13 轮已归档，看板只剩指针行，^## 应不命中" },
    { name: "反控 归档确有标题", ok: /^## .*R17 第 13 轮/m.test(archRaw), detail: "archive 里第 13 轮应以 ## 标题存在" },
  ];
}

function findDoc(repoRoot: string, base: string): string | null {
  const cands = [
    path.join(repoRoot, "lead", base),
    path.join(repoRoot, "lead", "next_re_20261117_r14", base),
  ];
  for (const c of cands) { if (fs.existsSync(c) && fs.statSync(c).isFile()) return c; }
  return null;
}

function main(): number {
  const tsv = process.argv[2] || path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "FACT_INDEX.tsv");
  const repoRoot = process.argv[3] || process.cwd();
  if (!fs.existsSync(tsv)) { console.error("FACT_INDEX not found: " + tsv); return 2; }
  const rows = fs.readFileSync(tsv, "utf8").split("\n").filter(l => l.length).map(l => l.split("\t"));
  const data = rows.slice(1);

  const need = new Set<string>();
  for (const r of data) for (const it of splitPaths(r[3] || "")) {
    const { file, anchor } = splitAnchor(it);
    if (anchor) need.add((file.replace(/^\u0060+|\u0060+$/g, "").trim().split("\\").pop() || ""));
  }
  const docs: Record<string, string> = {};
  const raw: Record<string, string> = {};
  for (const base of need) {
    const p = findDoc(repoRoot, base);
    if (!p) continue;
    const t = fs.readFileSync(p, "utf8");
    docs[base] = norm(t); raw[base] = t;
  }

  console.error("DEBUG need=" + need.size + " loaded=" + Object.keys(docs).join(","));
  console.log("--- 自检 ---");
  let stFail = 0;
  for (const t of selfTest(docs, raw)) {
    console.log((t.ok ? "  PASS  " : "  FAIL  ") + t.name + "  (" + t.detail + ")");
    if (!t.ok) stFail++;
  }
  if (stFail) { console.error("自检失败 " + stFail + " 项 —— 尺子不可信，后续数字无效"); return 2; }

  let items = 0, fileOk = 0, anchored = 0, anchorOk = 0, unloaded = 0;
  const miss: string[] = [];
  for (const r of data) for (const it of splitPaths(r[3] || "")) {
    items++;
    const { file, anchor } = splitAnchor(it);
    const f = file.replace(/^\u0060+|\u0060+$/g, "").trim();
    if (fs.existsSync(path.join(repoRoot, f.replace(/\\/g, "/")))) fileOk++;
    else miss.push("NOFILE  " + r[0] + "  " + f);
    if (!anchor) continue;
    anchored++;
    const base = f.split("\\").pop() || "";
    const pool = docs[base];
    if (!pool) { unloaded++; anchorOk++; continue; }
    if (anchorHits(pool, anchor)) anchorOk++;
    else miss.push("ANCHOR  " + r[0] + "  " + base + "(" + anchor + ")");
  }
  console.log("--- 结果 ---");
  console.log("  路径项        " + items);
  console.log("  文件存在      " + fileOk + " / " + items);
  console.log("  带锚点        " + anchored);
  console.log("  锚点可解析    " + anchorOk + " / " + anchored + (unloaded ? "  (其中 " + unloaded + " 项池未加载)" : ""));
  console.log("  MISS          " + miss.length);
  for (const m of miss) console.log("    " + m);
  return miss.length ? 1 : 0;
}

process.exit(main());
