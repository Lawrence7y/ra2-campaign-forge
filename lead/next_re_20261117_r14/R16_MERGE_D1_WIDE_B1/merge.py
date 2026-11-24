# -*- coding: utf-8 -*-
"""R16-MERGE-D1-WIDE-B1 · 写盘：coverage 18 行第 4 列 + PANEL 插入 1 条 M99。

写域：仅 COVERAGE\\coverage.tsv（18 行第 4 列）、COVERAGE\\PANEL.md（插入 1 条 M99）、
      以及本目录 R16_MERGE_D1_WIDE_B1\\ 的产物。不动其它任何文件。
字节级：coverage 无 BOM、LF、末尾无换行；PANEL 无 BOM、LF、末尾有换行。

18 行第 4 列来源：16 行取 R16_D1_WIDE_B1/delta.tsv；
004322A0/004324B0 两行取 R16_FIX_B1_2ROWS/delta.tsv（修复版）。
"""
import os, sys, json, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_WIDE_B1")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA_B1  = os.path.join(ROOT, "R16_D1_WIDE_B1", "delta.tsv")
DELTA_FIX = os.path.join(ROOT, "R16_FIX_B1_2ROWS", "delta.tsv")
FIX_ENTRIES = {"004322A0", "004324B0"}

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
b1_b  = open(DELTA_B1, "rb").read()
fix_b = open(DELTA_FIX, "rb").read()

def parse_delta(b):
    dl = b.decode("utf-8-sig").split("\n")
    if dl and dl[-1] == "": dl = dl[:-1]
    return [ln.split("\t") for ln in dl[1:]]

brows = parse_delta(b1_b)
frows = parse_delta(fix_b)
b4 = {ne(d[0]): d[3] for d in brows}
f4 = {ne(d[0]): d[3] for d in frows}
merged4 = dict(b4); merged4.update(f4)
assert len(brows)==18 and len(frows)==2 and len(merged4)==18

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
assert m_before["cal_A"]==baseline["invariants_before"]["cal_A"]
assert m_before["cal_B"]==baseline["invariants_before"]["cal_B"]
pct = lambda n: "%.2f" % (100.0*n/1654)

# ---------- 3. PANEL: 紧接 M98 块之后插入 1 条 M99 ----------
panel_lines = pin_panel.split(b"\n")        # last segment is b"" because trailing LF
assert pin_panel.endswith(b"\n")
assert panel_lines[-1] == b""
assert len(panel_lines) == 683, len(panel_lines)   # 682 LF -> 683 segments
# 锚点：M98 块 L290-L296（1-based），L297 是 M77 并表实算说明；插在 L297 之前 => 0-based 296
assert b"M98 " in panel_lines[289], panel_lines[289][:80]
assert b"M97 " in panel_lines[283], panel_lines[283][:80]
assert b"M77 " in panel_lines[296], panel_lines[296][:80]
INSERT_AT = 296

M99 = [
 f"> ✅ **M99 补记：R16-D1-WIDE-B1 并入 18 行（D-52 宽读集合 65 行待做部分的前 18 行；含 2 行修复）**",
 f"> 本批 18 行取自 `R16_SIEVE_D1_WIDE` 按用户 D-52 宽读口径筛出的 81 行集合：其中 has_ring4_on_disk==是 16 行跳过，待做 65 行；本批为按 entry 升序第 1–18 行。16 行第 4 列取 `R16_D1_WIDE_B1/delta.tsv`，2 行（`004322A0`/`004324B0`）第 4 列取 `R16_FIX_B1_2ROWS/delta.tsv`（修复版）；18/18 严格前缀（新第 4 列 = 原第 4 列 + `；④ 活表槽位见证：…`），只改 coverage 第 4 列，第 1/2/3/5/6/7/8 列逐字节相同、grade 未改 `[已证]`。",
 f"> ① **异族审计 `R16_AUDIT_D1_WIDE_B1/VERDICT.md` 判 16/18 PASS、2/18 FAIL（唯一失败点＝C 装配方式标注）**：A 原文保全 0/18 不合格、B 字节事实 108/108 全 True、D 文本一致 0/18 不合格、E 反抄袭 PASS、F 清单一致性 PASS（sieve 81 → 是 16 / 否 65 → 按 entry 升序第 1–18 行，不多不少、顺序一致）；FAIL 仅 C：`004322A0`/`004324B0` 的「装配方式=ctor_body」标错。",
 f"> ② **2 行 FAIL 的真相与修复（如实披露）**：旧版把栈临时写 `mov [esp+0x20],0x7e1668`（装表点 `004014C4`，宿主 `004011C0`）当成构造器装表；异族审计实测宿主 `004011C0` 是普通成员函数、写在栈临时对象上，且与 scalar deleting destructor `004019A0` 逐指令同构（`test byte [esp+8],1` + `call 0x7C8B3D` + `ret 4`），实为内联析构序列而非构造。`R16_FIX_B1_2ROWS` 已改取真构造器 `0047AA3C`（宿主 `0047AA30`，指令 `mov [esi],0x7e1668`）后并入，其余 16 行审计无同类可疑。",
 f"> ③ **根因与落实**：原 `generate.py` 的 `install_form`（`generate.py:82-88`）只看操作数形态（`0x` 前缀→mov_abs，其余→ctor_body）、从不校验宿主是不是构造器，装表点又直接继承最低地址命中——这是失效根因；已在后续批次用 G1–G5 宿主身份校验规则（`R16_FIX_B1_2ROWS/host_rule.py`）落实：G1 非栈、G2 this 对象、G3 非析构、G4 基类构造前序、G5 返回 this；严格 canonical 三站点 `0047A9E3`/`0047AA10`/`0047AA3C` 五门全通。",
 f"> 数字（口径 A/B 实测，改前→改后）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **{m_before['cal_A']} / 1,654（{pct(m_before['cal_A'])}%）**升至 **{m_after['cal_A']} / 1,654（{pct(m_after['cal_A'])}%）**，本批净增 **{m_after['cal_A']-m_before['cal_A']} 行**（18 行改前 `④` 计数全 0，N_pre_A=0）；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **{m_before['cal_B']} / 1,654（{pct(m_before['cal_B'])}%）**升至 **{m_after['cal_B']} / 1,654（{pct(m_after['cal_B'])}%）**，净增 **{m_after['cal_B']-m_before['cal_B']} 行**（18 行均写入 `④ 活表槽位见证` 子串，实测非推算）。",
 f"> §12.6 命中（第 4 列字面 `§12.6`）：命中行数 **{m_before['sec126_lines']} → {m_after['sec126_lines']}（+{m_after['sec126_lines']-m_before['sec126_lines']}）**、命中次数 **{m_before['sec126_occ']} → {m_after['sec126_occ']}（+{m_after['sec126_occ']-m_before['sec126_occ']}）**；18 行各追加 1 处 D-47 披露指向 §12.6（实测非推算）。",
 f"> 判定与计数均未变：coverage 18,498 数据行、列分布 `{{8:18498}}`、全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6；名义仍 S15/S16/S17、严格仍 S17，**达标判定未翻转**。",
]
insert_bytes = [ln.encode("utf-8") for ln in M99]
new_panel_lines = panel_lines[:INSERT_AT] + insert_bytes + panel_lines[INSERT_AT:]
new_panel = b"\n".join(new_panel_lines)
open(PANEL, "wb").write(new_panel)
open(os.path.join(OUT, "_after_PANEL.md"), "wb").write(new_panel)    # for reversibility compare

# ---------- 4. log ----------
log = dict(
    coverage=dict(before_sha=sha(pin_cov), after_sha=sha(new_cov), before_bytes=len(pin_cov), after_bytes=len(new_cov)),
    panel=dict(before_sha=sha(pin_panel), after_sha=sha(new_panel), before_bytes=len(pin_panel), after_bytes=len(new_panel),
               inserted_after_line=296, inserted_before_line=297, inserted_lines=len(M99), m99_text=M99),
    measure_before=m_before, measure_after=m_after,
    changed_rows=changed,
)
with open(os.path.join(OUT, "MERGE_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("COV  ", json.dumps(log["coverage"], ensure_ascii=False))
print("PANEL", json.dumps({k:v for k,v in log["panel"].items() if k!="m99_text"}, ensure_ascii=False))
print("MEASURE before", json.dumps(m_before, ensure_ascii=False))
print("MEASURE after ", json.dumps(m_after, ensure_ascii=False))
print("changed_rows", len(changed), "M99 lines", len(M99))
