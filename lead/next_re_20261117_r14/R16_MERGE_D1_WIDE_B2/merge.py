# -*- coding: utf-8 -*-
"""R16-MERGE-D1-WIDE-B2 · 写盘：coverage 18 行第 4 列 + PANEL 插入 1 条 M100。

写域：仅 COVERAGE\\coverage.tsv（18 行第 4 列）、COVERAGE\\PANEL.md（插入 1 条 M100）、
       以及本目录 R16_MERGE_D1_WIDE_B2\\ 的产物。不动其它任何文件。
字节级：coverage 无 BOM、LF、末尾无换行；PANEL 无 BOM、LF、末尾有换行。

18 行第 4 列来源：17 行取 R16_D1_WIDE_B2/delta.tsv；
00473B10 取 R16_FIX_B2_1ROW/delta.tsv（修复版，替换 B2 旧 ④）。
"""
import os, sys, json, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_WIDE_B2")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA_B2  = os.path.join(ROOT, "R16_D1_WIDE_B2", "delta.tsv")
DELTA_FIX = os.path.join(ROOT, "R16_FIX_B2_1ROW", "delta.tsv")
FIX_ENTRIES = {"00473B10"}

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
b2_b  = open(DELTA_B2, "rb").read()
fix_b = open(DELTA_FIX, "rb").read()

def parse_delta(b):
    dl = b.decode("utf-8-sig").split("\n")
    if dl and dl[-1] == "": dl = dl[:-1]
    return [ln.split("\t") for ln in dl[1:]]

brows = parse_delta(b2_b)
frows = parse_delta(fix_b)
b4 = {ne(d[0]): d[3] for d in brows}
f4 = {ne(d[0]): d[3] for d in frows}
merged4 = dict(b4); merged4.update(f4)
assert len(brows)==18 and len(frows)==1 and len(merged4)==18

# ---------- 1. coverage: 只改 18 行第 4 列 ----------
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
    changed[e] = dict(line=info["line_number"], src=info["src"],
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
    with open(os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv"),
              encoding="utf-8-sig") as f:
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
assert m_before["cal_A"]==baseline["invariants_before"]["cal_A"]==412
assert m_before["cal_B"]==baseline["invariants_before"]["cal_B"]==245
pct = lambda n: "%.2f" % (100.0*n/1654)

# ---------- 3. PANEL: 紧接 M99 块之后插入 1 条 M100 ----------
panel_lines = pin_panel.split(b"\n")        # last segment is b"" because trailing LF
assert pin_panel.endswith(b"\n")
assert panel_lines[-1] == b""
assert len(panel_lines) == 691, len(panel_lines)   # 690 LF -> 691 segments
# 锚点：M99 块 L297-L304（1-based），L305 是 M77 并表实算说明；插在 L305 之前 => 0-based 304
assert b"M99 " in panel_lines[296], panel_lines[296][:80]
assert b"M98 " in panel_lines[289], panel_lines[289][:80]
assert "判定与计数均未变".encode("utf-8") in panel_lines[303], panel_lines[303][:80]
assert b"M77 " in panel_lines[304], panel_lines[304][:80]
INSERT_AT = 304

M100 = [
  f"> ✅ **M100 补记：R16-D1-WIDE-B2 并入 18 行（D-52 宽读集合 65 行待做部分的第 19–36 行；含 1 行修复）**",
  f"> 本批 18 行取自 `R16_SIEVE_D1_WIDE` 按用户 D-52 宽读口径筛出的 81 行集合：其中 has_ring4_on_disk==是 16 行跳过，待做 65 行；本批为按 entry 升序第 19–36 行（`no_rows[18:36]`，与 B1 前 18 行 entry 集合交集为 0）。17 行第 4 列取 `R16_D1_WIDE_B2/delta.tsv`，1 行（`00473B10`）第 4 列取 `R16_FIX_B2_1ROW/delta.tsv`（修复版，替换 B2 旧 ④）；18/18 严格前缀（新第 4 列 = 原第 4 列 + `；④ 活表槽位见证：…`），只改 coverage 第 4 列，第 1/2/3/5/6/7/8 列逐字节相同、grade 未改 `[已证]`。",
  f"> ① **异族审计 `R16_AUDIT_D1_WIDE_B2/AUDIT_REPORT.md` 判 17 PASS / 1 FAIL**：A 原文保全（严格前缀 + 其余列逐字节 + grade 未变）0/18 不合格、B 字节事实 18/18 × 6 项全真 0/18 不合格、E 反抄袭 0/18 不合格、F 清单一致性（sieve 81 → 是 16 / 否 65 → 按 entry 升序第 19–36 行，顺序完全一致）0/18 不合格；唯一 FAIL 行 `00473B10`（`CCFileClass::slot9`），C 装配方式标注与 D 文本一致两项同时不过，与 B1 翻车同一形态（栈临时对象被标成 `ctor_body`）。",
  f"> ② **1 行 FAIL 的真相与修复（如实披露）**：`00473B10` 旧版把栈临时写 `mov dword ptr [esp+0x20],0x7e16b0`（装表点 `004014AC`，宿主 `004011C0`）当成构造器装表；审计实测宿主 `004011C0` 是 1729 条指令的无关函数，写在栈临时对象上（`lea ecx,[esp+0x20]` 取该临时对象作 thiscall 实参），并非 this。`R16_FIX_B2_1ROW` 已改取真构造器 `00473A80` 里的 `00473A9B`（指令 `mov [esi],0x7e16b0`）替换 B2 旧 ④ 后并入，其余 17 行审计无同类可疑。",
  f"> ③ **「最低地址命中」启发式的典型风险（已入账）**：同一 vt `007E16B0` 共 **185 个装表点**、其中仅 **5 个真 `this` 目标**（`004019A6`/`00473A12`/`00473A4F`/`00473A9B`/`00535A76`）；旧取法 `derive_raw.py:160` 的 `site = es[0]`（最低地址命中）恰好落在栈临时写 `004014AC`，5 个真 `this` 目标被最低地址命中丢弃。这是该启发式的典型风险，已入账；`R16_FIX_B2_1ROW/host_rule.py` 的可执行 G1–G5 宿主身份校验规则（G1 非栈 / G2 this 对象 / G3 非析构 / G4 基类构造前序 / G5 返回 this）已落实。",
  f"> ④ **审计另确认本批 5 行 CLASS_FIX 全部成立（5/5）**：`004A8960`/`004A9840`/`004AAD30`/`004AAE90`（TabClass 改取 `007EDFB4`）、`004AB9B0`（DisplayClass 改取 `007E6114`），均严格类一致、同址持有该 entry、COL offset=0、有体外装表点且 6 项字节复核全真（`R16_AUDIT_D1_WIDE_B2/AUDIT_REPORT.md` §4）。",
  f"> 数字（口径 A/B 实测，改前→改后）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **{m_before['cal_A']} / 1,654（{pct(m_before['cal_A'])}%）**升至 **{m_after['cal_A']} / 1,654（{pct(m_after['cal_A'])}%）**，本批净增 **{m_after['cal_A']-m_before['cal_A']} 行**（18 行改前 `④` 计数全 0，N_pre_A=0）；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **{m_before['cal_B']} / 1,654（{pct(m_before['cal_B'])}%）**升至 **{m_after['cal_B']} / 1,654（{pct(m_after['cal_B'])}%）**，净增 **{m_after['cal_B']-m_before['cal_B']} 行**（18 行均写入 `④ 活表槽位见证` 子串，实测非推算）。",
  f"> §12.6 命中（第 4 列字面 `§12.6`）：命中行数 **{m_before['sec126_lines']} → {m_after['sec126_lines']}（+{m_after['sec126_lines']-m_before['sec126_lines']}）**、命中次数 **{m_before['sec126_occ']} → {m_after['sec126_occ']}（+{m_after['sec126_occ']-m_before['sec126_occ']}）**；18 行各追加 1 处 D-47 披露指向 §12.6（实测非推算）。",
  f"> 判定与计数均未变：coverage 18,498 数据行、列分布 `{{8:18498}}`、全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6；名义仍 S15/S16/S17、严格仍 S17，**达标判定未翻转**。",
]
insert_bytes = [ln.encode("utf-8") for ln in M100]
new_panel_lines = panel_lines[:INSERT_AT] + insert_bytes + panel_lines[INSERT_AT:]
new_panel = b"\n".join(new_panel_lines)
open(PANEL, "wb").write(new_panel)
open(os.path.join(OUT, "_after_PANEL.md"), "wb").write(new_panel)    # for reversibility compare

# ---------- 4. log ----------
log = dict(
    coverage=dict(before_sha=sha(pin_cov), after_sha=sha(new_cov), before_bytes=len(pin_cov), after_bytes=len(new_cov)),
    panel=dict(before_sha=sha(pin_panel), after_sha=sha(new_panel), before_bytes=len(pin_panel), after_bytes=len(new_panel),
               inserted_after_line=304, inserted_before_line=305, inserted_lines=len(M100), m100_text=M100),
    measure_before=m_before, measure_after=m_after,
    changed_rows=changed,
)
with open(os.path.join(OUT, "MERGE_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("COV  ", json.dumps(log["coverage"], ensure_ascii=False))
print("PANEL", json.dumps({k:v for k,v in log["panel"].items() if k!="m100_text"}, ensure_ascii=False))
print("MEASURE before", json.dumps(m_before, ensure_ascii=False))
print("MEASURE after ", json.dumps(m_after, ensure_ascii=False))
print("changed_rows", len(changed), "M100 lines", len(M100))
