// verify_anchors.ts — FACT_INDEX evidence_paths 锚点核验器（可复跑）
//
// 用法：node --experimental-strip-types verify_anchors.ts [FACT_INDEX.tsv] [repoRoot]
// 退出码：0=全通过 1=有MISS 2=自检失败 3=有锚点未能核验（池未加载）
//
// 分三类计数，绝不把「未核验」混进「通过」：
//   mech     机械核验通过（归一化子串 / 复合锚逐段）
//   section  节号体例通过（§2.9四 这类：先定位节标题，再在节体内找小节标记）
//   unverified 池未加载，未核验

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

function sectionAnchorHits(raw: string, anchor: string): { ok: boolean; why: string } {
  const a = anchor.replace(/\s+/g, " ").trim();
  const m = a.match(/§\s*(\d+(?:\.\d+)*)/);
  if (!m) return { ok: false, why: "no section number" };
  const sec = m[1];
  const lines = raw.split(/\r?\n/);
  const headRe = new RegExp("^#{2,4}\\s+\u00A7?" + sec.replace(/\./g, "\\.") + "(?:\\s|$)");
  let start = -1;
  for (let i = 0; i < lines.length; i++) { if (headRe.test(lines[i])) { start = i; break; } }
  if (start < 0) return { ok: false, why: "section heading \u00A7" + sec + " absent" };
  const lvl = (lines[start].match(/^#+/) || ["##"])[0].length;
  let end = lines.length;
  for (let i = start + 1; i < lines.length; i++) {
    const hm = lines[i].match(/^(#+)\s/);
    if (hm && hm[1].length <= lvl) { end = i; break; }
  }
  const body = norm(lines.slice(start, end).join("\n"));
  const locator = a.replace(/§\s*\d+(?:\.\d+)*/, "").replace(/^[\s/]+/, "").trim();
  if (!locator) return { ok: true, why: "section only" };
  const parts = locator.split("/").map(x => norm(x).replace(/段$/, "")).filter(Boolean);
  const missing = parts.filter(pp => !body.includes(pp));
  if (missing.length === 0) return { ok: true, why: "locator in section body" };
  const positional = parts.every(pp => /^(行\d+|头部|尾部|第.步|小结|表|§?\d+)$/.test(pp));
  if (positional) return { ok: false, why: "POSITIONAL: " + parts.join("|") };
  return { ok: false, why: "locator missing in \u00A7" + sec + ": " + missing.join(" | ") };
}


function sectionAnchorHitsMulti(raw: string, anchor: string): { ok: boolean; why: string } {
  const idxs: number[] = [];
  for (let i = 0; i < anchor.length; i++) if (anchor[i] === "\u00A7") idxs.push(i);
  if (idxs.length <= 1) return sectionAnchorHits(raw, anchor);
  // split into segments, each starting at a section marker
  const segs: string[] = [];
  for (let k = 0; k < idxs.length; k++) {
    const from = idxs[k];
    const to = k + 1 < idxs.length ? idxs[k + 1] : anchor.length;
    segs.push(anchor.slice(from, to));
  }
  const fails: string[] = [];
  for (const s of segs) {
    const r = sectionAnchorHits(raw, s.replace(/[\s/]+$/, ""));
    if (!r.ok) fails.push(s + " => " + r.why);
  }
  if (fails.length === 0) return { ok: true, why: "all " + segs.length + " section segments ok" };
  return { ok: false, why: fails.join(" ;; ") };
}

function findDoc(repoRoot: string, base: string): string | null {
  const cands = [path.join(repoRoot, "lead", base), path.join(repoRoot, "lead", "next_re_20261117_r14", base)];
  for (const c of cands) { if (fs.existsSync(c) && fs.statSync(c).isFile()) return c; }
  return null;
}

type SelfTest = { name: string; ok: boolean; detail: string };

function selfTest(docs: Record<string, string>, raw: Record<string, string>): SelfTest[] {
  const get = (suffix: string): string => { for (const k of Object.keys(docs)) if (k === suffix || k.endsWith("\\" + suffix)) return docs[k]; return ""; };
  const getRaw = (suffix: string): string => { for (const k of Object.keys(raw)) if (k === suffix || k.endsWith("\\" + suffix)) return raw[k]; return ""; };
  const lock = get("LEAD_LOCK");
  const ledger = get("GOAL_THREE_TARGETS_20261018.md");
  const archive = get("BOARD_ARCHIVE.md");
  const rcRaw = getRaw("R14_COMMON.md");
  const boardRaw = getRaw("STATUS_BOARD.md");
  const archRaw = getRaw("BOARD_ARCHIVE.md");
  return [
    { name: "A 空白差异(正控)", ok: anchorHits(lock, "追加·2026-11-20 20:5x·r15 第 99-104 轮 段"), detail: "锚无空格 vs 实盘有空格" },
    { name: "B 正文行锚(正控)", ok: anchorHits(ledger, "N9 三条方法论修正 段"), detail: "台账该串在正文行" },
    { name: "C 复合锚(正控)", ok: anchorHits(lock, "追加·2026-11-20 21:1x·r15 第 105 轮 段 / 追加·2026-11-20 22:1x·r15 第 111 轮 段"), detail: "两段各带「段」" },
    { name: "D 节号体例(正控)", ok: sectionAnchorHits(rcRaw, "§2.9四").ok, detail: "§2.9 节体内应有「四」小节" },
    { name: "反控 不存在段", ok: !anchorHits(archive, "R17 第 999 轮 段"), detail: "不存在轮次必须 MISS" },
    { name: "反控 仅指针行", ok: !/^## .*R17 第 13 轮/m.test(boardRaw), detail: "第 13 轮已归档，看板只剩指针行" },
    { name: "反控 归档确有标题", ok: /^## .*R17 第 13 轮/m.test(archRaw), detail: "archive 里第 13 轮应以 ## 存在" },
    { name: "反控 错节号必失败", ok: !sectionAnchorHits(rcRaw, "§2.9九十九").ok, detail: "不存在的节内标记必须失败" },
  ];
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
    if (anchor) need.add(file.replace(/^\u0060+|\u0060+$/g, "").trim());
  }
  const docs: Record<string, string> = {};
  const raw: Record<string, string> = {};
  for (const base of need) {
    const direct = path.join(repoRoot, base.replace(/\\/g, "/"));
    const p = (fs.existsSync(direct) && fs.statSync(direct).isFile()) ? direct : findDoc(repoRoot, base.split("\\").pop() || base);
    if (!p) continue;
    const t = fs.readFileSync(p, "utf8");
    docs[base] = norm(t); raw[base] = t;
  }

  console.log("--- 自检（正控/反控）---");
  let stFail = 0;
  for (const t of selfTest(docs, raw)) {
    console.log((t.ok ? "  PASS  " : "  FAIL  ") + t.name + "  (" + t.detail + ")");
    if (!t.ok) stFail++;
  }
  if (stFail) { console.error("自检失败 " + stFail + " 项 —— 尺子不可信，后续数字无效"); return 2; }

  let items = 0, fileOk = 0, anchored = 0, mech = 0, sec = 0, unverified = 0, dirTargets = 0, cardDir = 0;
  const miss: string[] = [];
  const manual: string[] = [];
  const unloaded = new Set<string>();
  for (const r of data) for (const it of splitPaths(r[3] || "")) {
    items++;
    const { file, anchor } = splitAnchor(it);
    const f = file.replace(/^\u0060+|\u0060+$/g, "").trim();
    const absT = path.join(repoRoot, f.replace(/\\/g, "/"));
    const isDir = fs.existsSync(absT) && fs.statSync(absT).isDirectory();
    if (isDir) {
      if (anchor) { dirTargets++; miss.push("DIRANCHOR  " + r[0] + "  " + f + "(" + anchor + ")  (锚挂在目录上，无法解析)"); }
      else { cardDir++; }
    }
    if (fs.existsSync(absT)) fileOk++;
    else miss.push("NOFILE  " + r[0] + "  " + f);
    if (!anchor) continue;
    anchored++;
    const base = f.split("\\").pop() || "";
    const pool = docs[f];
    if (!pool) { unverified++; unloaded.add(f); continue; }
    if (anchorHits(pool, anchor)) { mech++; continue; }
    const sr = sectionAnchorHitsMulti(raw[f] || "", anchor);
    if (sr.ok) { sec++; continue; }
    if (sr.why.indexOf("no section number") >= 0 || sr.why.indexOf("POSITIONAL") >= 0) { manual.push(r[0] + "  " + base + "(" + anchor + ")"); }
    else miss.push("ANCHOR  " + r[0] + "  " + base + "(" + anchor + ")  [" + sr.why + "]");
  }
  console.log("--- 结果 ---");
  console.log("  路径项                " + items);
  console.log("  文件存在              " + fileOk + " / " + items);
  console.log("  带锚点                " + anchored);
  console.log("    机械核验通过        " + mech);
  console.log("    节号体例通过        " + sec);
  console.log("    池未加载(未核验)    " + unverified + (unloaded.size ? "  [" + [...unloaded].join(",") + "]" : ""));
  console.log("    人工核验类(无节号)  " + manual.length);
  console.log("    目录即卡(可接受)    " + cardDir);
  console.log("    目录+锚(NG)         " + dirTargets);
  console.log("    MISS                " + miss.length);
  for (const m of manual) console.log("      MANUAL  " + m);
  for (const m of miss) console.log("    " + m);
  if (unverified > 0) { console.log(""); console.log("  ⚠ 池未加载的锚点【未核验】，不得计入通过。"); }
  if (miss.length) return 1;
  return unverified > 0 ? 3 : 0;
}

process.exit(main());
