# -*- coding: utf-8 -*-
"""R16-MERGE-D1-WIDE-B3 · 写盘：coverage 17 行第 4 列 + PANEL 插入 1 条 M101 披露。

写域：仅 COVERAGE\\coverage.tsv（17 行第 4 列）、COVERAGE\\PANEL.md（插入 1 条 M101）、
        以及本目录 R16_MERGE_D1_WIDE_B3\\ 的产物。不动其它任何文件。
字节级：coverage 无 BOM、LF、末尾无换行；PANEL 无 BOM、LF、末尾有换行。

17 行第 4 列来源：R16_D1_WIDE_B3/delta.tsv 的 18 行里排除 005F4B10（Lead 裁定 +
异族审计复核：该行 ② 指向 BuildingLightClass、极性 NEG、slot65 被 16 表共有无 ② 支持
归 ObjectClass；其 ④ 字节为真，剔除的是「行不该在集合里」），余 17 行第 4 列照抄。
"""
import os, sys, json, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_WIDE_B3")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_D1_WIDE_B3", "delta.tsv")
EXCLUDE = {"005F4B10"}
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
merged4 = {ne(d[0]): d[3] for d in drows if ne(d[0]) not in EXCLUDE}
assert len(drows)==18 and len(merged4)==17
assert set(merged4)==set(before_col4.keys())

# ---------- 1. coverage: 只改 17 行第 4 列 ----------
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
assert m_before["cal_A"]==baseline["invariants_before"]["cal_A"]==430
assert m_before["cal_B"]==baseline["invariants_before"]["cal_B"]==263
pct = lambda n: "%.2f" % (100.0*n/1654)

# ---------- 3. PANEL: 紧接 M100 块之后插入 1 条 M101 ----------
panel_lines = pin_panel.split(b"\n")        # last segment is b"" because trailing LF
assert pin_panel.endswith(b"\n")
assert panel_lines[-1] == b""
assert len(panel_lines) == 700, len(panel_lines)   # 699 LF -> 700 segments
# 锚点：M100 块 L305-L313（1-based），L314 是 M77 并表实算说明；插在 L314 之前 => 0-based 313
assert b"M100 " in panel_lines[304], panel_lines[304][:100]
assert b"M99 " in panel_lines[296], panel_lines[296][:100]
assert "判定与计数均未变".encode("utf-8") in panel_lines[312], panel_lines[312][:100]
assert b"M77 " in panel_lines[313], panel_lines[313][:100]
INSERT_AT = 313

M101 = [
  f"> ✅ **M101 补记：R16-D1-WIDE-B3 并入 17 行（D-52 宽读集合 65 行待做部分的第 37–54 行；1 行经裁定剔除，实并 17 行）**",
  f"> 本批 18 行取自 `R16_SIEVE_D1_WIDE` 按用户 D-52 宽读口径筛出的 81 行集合：其中 has_ring4_on_disk==是 16 行跳过，待做 65 行，本批为按 entry 升序第 37–54 行（`no_rows[36:54]`，与 B1/B2 entry 集合交集为 0）。其中 1 行（`005F4B10`）经 Lead 裁定与异族审计复核后**剔除**，实并 17 行；17 行第 4 列取 `R16_D1_WIDE_B3/delta.tsv`，均为严格前缀（新第 4 列 = 原第 4 列 + `；④ 活表槽位见证：…`），只改 coverage 第 4 列，第 1/2/3/5/6/7/8 列逐字节相同、grade 未改 `[已证]`；被剔的 `005F4B10` 在盘上原样未动（第 4 列仍为 `ObjectClass slot65 wrapper (consumes NeedsRedraw)`）。",
  f"> ① **剔除 `005F4B10` 的理由（Lead 裁定 + 异族审计 `R16_AUDIT_D1_WIDE_B3/AUDIT_REPORT.md` §5.2 独立复核成立）**：其 ② 审计原文（`C06_census/_audit/VERDICT.md:15`）只写「`005F4B10 <- BuildingLightClass vt 007E3AD0 slot 65`」、全文不含 `ObjectClass`，`verdict_polarity=NEG`（本批唯一负极性行）；该 entry 在 slot65 被 **16 张表**共有（含 AircraftClass / BuildingLightClass / ObjectClass 等），无任何 ② 产物支持归到 ObjectClass。其 ④ 字节**为真**（`007EF060` slot65 确为该 entry，RTTI `.?AVObjectClass@@`），故剔除理由是**「这行不该在集合里」**（不满足 D-52 的 ② 独立审计链），**不是「④ 写错」**；未并、未改其盘上任何字节。",
  f"> ② **本批 6 行 SITE_FIX 经审计 6/6 成立（`AUDIT_REPORT.md` §4）**：4 行 `RawFileClass`（`0065CAC0`/`0065CDD0`/`0065CF00`/`0065D0D0`）旧决定性装表点 `0065CA03` 实为析构器写（尾回写基类 `FileClass` vptr、被 scalar-deleting 包装器调用），2 行 `CDFileClass`（`0065D150`/`0065D190`）旧点 `004014C4` 实为栈临时写（`mov [esp+0x20],0x7e1668`，与 B1/B2 翻车的 `00473B10` 同一函数同一栈槽）；执行器已改取真构造器 `0065CAA8`（宿主 `0065CA80`）与 `0047AA3C`（宿主 `0047AA30`），审计独立复算两族缺陷与改取点全真。",
  f"> ③ **2 行 CLASS_FIX：`00631CC0` 成立、`005F4B10` 撤回（`AUDIT_REPORT.md` §5）**：`00631CC0`（FilePipe::slot3）原表 `007E4D78` RTTI 为 `SHAPipe` 类不符、6 处装表点全是栈写，改取 `007E4DA0`（`.?AVFilePipe@@`）唯一写 `this` 点 `007BA426` 且宿主确为析构器，标 `reg` 诚实有据，成立；`005F4B10` 按上条撤回收场（非「成立/不成立」，是行不该在集合里）。",
  f"> ④ **审计如实指出的口径限制（`AUDIT_REPORT.md` §E）**：本批 ④ 正文完整串 18/18 互异、8 位十六进制归一为 `ENTRY` 后仍 18/18 不同；但若把 `slotN`/`槽 N` 也归一，则**只有 12/18 互异**，收敛成 **4 组**（`0062B250/0062B300`、`0065C0D0/0065C180`、`0065CAC0/0065CDD0/0065CF00/0065D0D0`、`0065D150/0065D190`）同 class / 同 vt / 同装表点、仅差 slot 与 entry，且差异逐条字节可验为真 ⇒ **属事实同源而非抄袭，判 E 通过**；**不得声称「slot 归一后仍 18/18 不同」**（本批做不到）。",
  f"> 数字（口径 A/B 实测，改前→改后）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **{m_before['cal_A']} / 1,654（{pct(m_before['cal_A'])}%）**升至 **{m_after['cal_A']} / 1,654（{pct(m_after['cal_A'])}%）**，本批净增 **{m_after['cal_A']-m_before['cal_A']} 行**（17 行改前 `④` 计数全 0，N_pre_A=0；`005F4B10` 未并、其原第 4 列无 `④`）；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **{m_before['cal_B']} / 1,654（{pct(m_before['cal_B'])}%）**升至 **{m_after['cal_B']} / 1,654（{pct(m_after['cal_B'])}%）**，净增 **{m_after['cal_B']-m_before['cal_B']} 行**（17 行均写入 `④ 活表槽位见证` 子串，实测非推算）。",
  f"> §12.6 命中（第 4 列字面 `§12.6`）：命中行数 **{m_before['sec126_lines']} → {m_after['sec126_lines']}（+{m_after['sec126_lines']-m_before['sec126_lines']}）**、命中次数 **{m_before['sec126_occ']} → {m_after['sec126_occ']}（+{m_after['sec126_occ']-m_before['sec126_occ']}）**；17 行各追加 1 处 D-47 披露指向 §12.6（被剔的 `005F4B10` 不计，实测非推算）。",
  f"> 判定与计数均未变：coverage 18,498 数据行、列分布 `{{8:18498}}`、全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6；名义仍 S15/S16/S17、严格仍 S17，**达标判定未翻转**。",
]
insert_bytes = [ln.encode("utf-8") for ln in M101]
new_panel_lines = panel_lines[:INSERT_AT] + insert_bytes + panel_lines[INSERT_AT:]
new_panel = b"\n".join(new_panel_lines)
open(PANEL, "wb").write(new_panel)
open(os.path.join(OUT, "_after_PANEL.md"), "wb").write(new_panel)    # for reversibility compare

# ---------- 4. log ----------
log = dict(
    coverage=dict(before_sha=sha(pin_cov), after_sha=sha(new_cov), before_bytes=len(pin_cov), after_bytes=len(new_cov)),
    panel=dict(before_sha=sha(pin_panel), after_sha=sha(new_panel), before_bytes=len(pin_panel), after_bytes=len(new_panel),
               inserted_after_line=313, inserted_before_line=314, inserted_lines=len(M101), m101_text=M101),
    measure_before=m_before, measure_after=m_after,
    excluded_entry="005F4B10",
    changed_rows=changed,
)
with open(os.path.join(OUT, "MERGE_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("COV  ", json.dumps(log["coverage"], ensure_ascii=False))
print("PANEL", json.dumps({k:v for k,v in log["panel"].items() if k!="m101_text"}, ensure_ascii=False))
print("MEASURE before", json.dumps(m_before, ensure_ascii=False))
print("MEASURE after ", json.dumps(m_after, ensure_ascii=False))
print("changed_rows", len(changed), "M101 lines", len(M101))
