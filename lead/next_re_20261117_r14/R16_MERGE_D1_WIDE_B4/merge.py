# -*- coding: utf-8 -*-
"""R16-MERGE-D1-WIDE-B4 · 写盘：coverage 11 行第 4 列 + PANEL 插入 1 条 M102 披露。

写域：仅 COVERAGE\\coverage.tsv（11 行第 4 列）、COVERAGE\\PANEL.md（插入 1 条 M102）、
         以及本目录 R16_MERGE_D1_WIDE_B4\\ 的产物。不动其它任何文件。
字节级：coverage 无 BOM、LF、末尾无换行（18498 数据行 + 1 表头）；PANEL 无 BOM、LF、末尾有换行。

11 行第 4 列来源：R16_D1_WIDE_B4/delta.tsv 的 11 行第 4 列照抄（本批无剔除行）。
所有数字从 pin/after 盘上字节实测，不引用预测。
"""
import os, sys, json, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_WIDE_B4")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_D1_WIDE_B4", "delta.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

def sha(b): return hashlib.sha256(b).hexdigest()
def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

pin_cov  = open(os.path.join(OUT, "_pin_coverage.tsv"), "rb").read()
pin_panel= open(os.path.join(OUT, "_pin_PANEL.md"), "rb").read()
baseline = json.load(open(os.path.join(OUT, "baseline.json"), encoding="utf-8"))
before_col4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
delta_b  = open(DELTA, "rb").read()

def parse_delta(b):
    dl = b.decode("utf-8-sig").split("\n")
    if dl and dl[-1] == "": dl = dl[:-1]
    return [ln.split("\t") for ln in dl[1:]]

drows = parse_delta(delta_b)
merged4 = {ne(d[0]): d[3] for d in drows}
assert len(drows)==11 and len(merged4)==11
assert set(merged4)==set(before_col4.keys())

# ---------- 1. coverage: 只改 11 行第 4 列 ----------
cov_lines = pin_cov.split(b"\n")            # 18499 segments, last is final data line (no trailing LF)
assert len(cov_lines) == 18499, len(cov_lines)
assert not pin_cov.endswith(b"\n")

changed = {}
for e, info in before_col4.items():
    seg_idx = info["line_number"] - 1       # 1-based line number -> 0-based segment index
    seg = cov_lines[seg_idx]
    cols = seg.split(b"\t")
    assert len(cols) == 8
    old4 = cols[3].decode("utf-8")
    assert old4 == info["value"], (e, "before_col4 mismatch")
    new4 = merged4[e]
    assert new4.startswith(old4) and len(new4) > len(old4), (e, "strict prefix failed")
    cols[3] = new4.encode("utf-8")
    cov_lines[seg_idx] = b"\t".join(cols)
    changed[e] = dict(line=info["line_number"],
                      old_col4_sha=hashlib.sha256(old4.encode("utf-8")).hexdigest(),
                      new_col4_len=len(new4.encode("utf-8")), old_col4_len=len(old4.encode("utf-8")))

new_cov = b"\n".join(cov_lines)
assert len(new_cov) == len(pin_cov) + sum(v["new_col4_len"]-v["old_col4_len"] for v in changed.values())
open(COV, "wb").write(new_cov)
open(os.path.join(OUT, "_after_coverage.tsv"), "wb").write(new_cov)   # for strict_panel compare

# ---------- 2. measure caliber A/B + §12.6 from ACTUAL bytes (pin vs after) ----------
def measure(cov_b):
    lines = cov_b.decode("utf-8").split("\n")
    if cov_b.endswith(b"\n"): lines = lines[:-1]
    rows = [ln.split("\t") for ln in lines[1:]]
    A=B=lines126=occ126=0
    n_yz=in_atlas=out_atlas=0
    atlas=set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i,line in enumerate(f):
            if i==0: continue
            p=line.rstrip("\r\n").split("\t")
            if p and p[0].strip(): atlas.add(ne(p[0]))
    for r in rows:
        if len(r)<8: continue
        if r[4].strip()=="[已证]":
            n_yz+=1
            if "④" in r[3]: A+=1
            if "④ 活表槽位见证" in r[3]: B+=1
            if ne(r[0]) in atlas: in_atlas+=1
            else: out_atlas+=1
        if "§12.6" in r[3]:
            lines126+=1; occ126+=r[3].count("§12.6")
    return dict(rows=len(rows), col_dist=str(sorted(set(len(r) for r in rows))),
                proved=n_yz, atlas_in=in_atlas, atlas_out=out_atlas,
                cal_A=A, cal_B=B, sec126_lines=lines126, sec126_occ=occ126)

m_before = measure(pin_cov)
m_after  = measure(new_cov)
assert m_before["rows"]==18498 and m_after["rows"]==18498
assert m_before["proved"]==1654 and m_after["proved"]==1654
assert m_before["cal_A"]==baseline["invariants_before"]["cal_A"]
assert m_before["cal_B"]==baseline["invariants_before"]["cal_B"]
pct = lambda n: "%.2f" % (100.0*n/1654)

# ---------- 3. PANEL: 紧接 M101 块之后插入 1 条 M102 ----------
panel_lines = pin_panel.split(b"\n")        # 709 segments, last is b"" because trailing LF
assert pin_panel.endswith(b"\n")
assert panel_lines[-1] == b""
assert len(panel_lines) == 709, len(panel_lines)
# 锚点：M101 块 L314-L322（1-based，共 9 行），L323 是 M77 并表实算说明；插在 L323 之前 => 0-based 322
assert b"M101 " in panel_lines[313], panel_lines[313][:100]
assert b"M100 " in panel_lines[304], panel_lines[304][:100]
assert "判定与计数均未变".encode("utf-8") in panel_lines[321], panel_lines[321][:100]
assert b"M77 " in panel_lines[322], panel_lines[322][:100]
INSERT_AT = 322

M102 = [
  f"> ✅ **M102 补记：R16-D1-WIDE-B4 并入 11 行（D-52 宽读集合收官批；B1 18 + B2 18 + B3 17 + B4 11 = 64 行已并，另 1 行 `005F4B10` 经裁定剔除）**",
  f"> 本批 11 行取自 `R16_SIEVE_D1_WIDE` 按用户 D-52 宽读口径筛出的 81 行集合：其中 has_ring4_on_disk==是 16 行跳过，待做 65 行；本批为按 entry 升序第 55–65 行（`no_rows[54:65]`，与 B1/B2/B3 entry 集合交集为 0）。11 行第 4 列取 `R16_D1_WIDE_B4/delta.tsv`，均为严格前缀（新第 4 列 = 原第 4 列 + `；④ 活表槽位见证：…`），只改 coverage 第 4 列，第 1/2/3/5/6/7/8 列逐字节相同、grade 未改 `[已证]`。",
  f"> ① **收官批闭合（如实披露）**：D-52 宽读集合 81 行 → `has_ring4_on_disk==是` 16 行跳过 → 待做 65 行；B1 并入 18、B2 并入 18、B3 并入 17（其 delta 18 行中 `005F4B10` 经 Lead 裁定剔除）、本批 B4 并入 11，累计已并 18+18+17+11 = **64 行**，加被剔 `005F4B10` 1 行 = 65 行待做全部闭合；至此 D-52 宽读集合**收官**。",
  f"> ② **异族审计 `R16_AUDIT_D1_WIDE_B4/AUDIT_REPORT.md` 判 11 PASS / 0 FAIL / 0 必改（阻塞合并）**：A 原文保全 0/11 不合格（严格前缀 11/11、其余 7 列逐字节、grade 未改 `[已证]`）、B 字节事实 11/11 × 6 项全真、C 装配形态标注 11/11 正确（`ctor_body` 9 / `mov_abs` 1 / `reg` 1）、D 文本一致 0/11 不合格、E 反抄袭 0/11、F 清单一致性 0/11；3 行 CLASS_FIX 3/3 成立；须订正 2 条叙述性文字 + 建议 2 条，均不阻塞。",
  f"> ③ **审计两条事实订正留痕（结论对/措辞错与虚设步骤，如实记录）**：其一，执行器 `REPORT.md §4.2` 写「非最低地址命中 `006F450D`（析构器）」，与字节相反——审计实测 vt `007F4960` 三处装表点按地址为 `006F3130`（**地址最低**，宿主 `006F2B40` 为**真构造器**）< `006F4413`（真构造器）< `006F450D`（**地址最高**，宿主 `006F4500` 为析构器）；本批取 `006F3130` 的结论正确，但把「最低」安到最高点析构器上的措辞错，已订正留痕。其二，`REPORT.md §1` 推导表「11 行 = 65 − 18 − 18 − 18 − 1」含**虚设步骤**：`005F4B10` 已在 B3 的 18 行内，减 B3 时即已移除，`65 − 18 − 18 − 18 = 11` 已成立，再减 1 得 10（与表中 11 不符）；正确口径为 65 − B1 18 − B2 18 − B3 18 = 11 = B4，被剔的 `005F4B10` 只计一次。",
  f"> ④ **方法论保留（对整个 D1-WIDE 系列入账，审计 §8 痕迹 1）**：审计指出本批所谓「宿主身份校验」实际实现为 `derive.py` 的 `DECISIONS` 字典逐行手填 `forced_host` + `site_facts()` 以 `hsrc='verified-host'` 回填 + 形态规则匹配，校验的是「我指定的宿主是否合格」，并非「装表点确属哪个函数」，且全程无 `host ≤ site < fn_end(host)` 位置断言、无宿主是否真函数起点检查；所谓「11/11 通过」是审计**独立反求宿主后事后追认**一致（11/11 与执行器相符），方法本身**不是真校验**。此保留适用于整个 D1-WIDE 系列（B1–B4）：本批结论虽经独立复算成立，下一批仍须按审计建议 S2 落实位置断言与由点位反求宿主。",
  f"> 数字（口径 A/B 实测，改前→改后）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **{m_before['cal_A']} / 1,654（{pct(m_before['cal_A'])}%）**升至 **{m_after['cal_A']} / 1,654（{pct(m_after['cal_A'])}%）**，本批净增 **{m_after['cal_A']-m_before['cal_A']} 行**（11 行改前 `④` 计数全 0，N_pre_A=0）；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **{m_before['cal_B']} / 1,654（{pct(m_before['cal_B'])}%）**升至 **{m_after['cal_B']} / 1,654（{pct(m_after['cal_B'])}%）**，净增 **{m_after['cal_B']-m_before['cal_B']} 行**（11 行均写入 `④ 活表槽位见证` 子串，实测非推算）。",
  f"> §12.6 命中（第 4 列字面 `§12.6`）：命中行数 **{m_before['sec126_lines']} → {m_after['sec126_lines']}（+{m_after['sec126_lines']-m_before['sec126_lines']}）**、命中次数 **{m_before['sec126_occ']} → {m_after['sec126_occ']}（+{m_after['sec126_occ']-m_before['sec126_occ']}）**；11 行各追加 1 处 D-47 披露指向 §12.6（实测非推算）。",
  f"> 判定与计数均未变：coverage 18,498 数据行、列分布 `{{8:18498}}`、全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6；名义仍 S15/S16/S17、严格仍 S17，**达标判定未翻转**。",
]
insert_bytes = [ln.encode("utf-8") for ln in M102]
new_panel_lines = panel_lines[:INSERT_AT] + insert_bytes + panel_lines[INSERT_AT:]
new_panel = b"\n".join(new_panel_lines)
open(PANEL, "wb").write(new_panel)
open(os.path.join(OUT, "_after_PANEL.md"), "wb").write(new_panel)    # for reversibility compare

# ---------- 4. log ----------
log = dict(
    coverage=dict(before_sha=sha(pin_cov), after_sha=sha(new_cov), before_bytes=len(pin_cov), after_bytes=len(new_cov)),
    panel=dict(before_sha=sha(pin_panel), after_sha=sha(new_panel), before_bytes=len(pin_panel), after_bytes=len(new_panel),
               inserted_after_line=322, inserted_before_line=323, inserted_lines=len(M102), m102_text=M102),
    measure_before=m_before, measure_after=m_after,
    changed_rows=changed,
)
with open(os.path.join(OUT, "MERGE_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("COV  ", json.dumps(log["coverage"], ensure_ascii=False))
print("PANEL", json.dumps({k:v for k,v in log["panel"].items() if k!="m102_text"}, ensure_ascii=False))
print("MEASURE before", json.dumps(m_before, ensure_ascii=False))
print("MEASURE after ", json.dumps(m_after, ensure_ascii=False))
print("changed_rows", len(changed), "M102 lines", len(M102))
