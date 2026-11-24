# -*- coding: utf-8 -*-
"""M77 verify: recompute all coverage/atlas/strict metrics from disk (after) and emit VERIFY.txt.
Checks: 4 rows col4/5/6, cols 1/2/3/7/8 byte-preserving, 18498/8col/LF/noBOM,
full/atlas_in/atlas_out, S07/S11 proved+strict, TOTAL, DoD (no flip),
PANEL numeric cells, 备注 remarks, disclosure verbatim+line, BEFORE_AFTER integrity.
"""
import csv, os, re, sys, math, collections, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S07S11_B2", "delta.tsv")
VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT20", "verdict.tsv")
MERGE = os.path.join(ROOT, "MERGE_M77")
BA = os.path.join(MERGE, "BEFORE_AFTER.txt")

EXP = ["006DBE00", "0069EE30", "00719E30", "0075C7F0"]
EXP_SUB = {"006DBE00": "S07", "0069EE30": "S11", "00719E30": "S11", "0075C7F0": "S11"}
EV = "NAMED_PUSH_AUDIT20/VERDICT.md"
REMARK = ("M77 并表 NAMED_PUSH_AUDIT20 PASS 4 行（S07 006DBE00 + S11 0069EE30/00719E30/0075C7F0，"
          "evidence_path 改指 NAMED_PUSH_AUDIT20/VERDICT.md）；具名通道至此收口（剩余预期 < 3 行）")
DISC = [
    "> ⚠️ **M77 披露：006DBE00 的两个边界（未收紧）**",
    "> `a-final4` 审计指出两点，均不影响本轮判 PASS，但引用时须同读：",
    "> 1. `006DBE00` 是 `0x1C` 字节的 HRESULT 归一化包装，**映射近似恒等**，形态贴近「纯转发」；若取「恒等映射即 ③a」的严口径，此行应改判 FAIL。",
    "> 2. `006DBE00` **找不到静态 slot-6 派发点**（无直接调用者、无 `push imm`；沿 Tactical 单例 `[0x887324]` 窗口内无 `call [reg+0x18]`），④ 依赖 ctor 装活表 + `new` 堆实例 + 全局被读 447 次——**弱于另 3 行可见的 `ff 10` 派发**。",
]
BEFORE_SHA = {"coverage.tsv": "22cde4b82a161c41004247c5a78f7ca5e8065371aa16c32bae5f95349ce4ba27",
              "PANEL.md": "2a9cdb96cc47780f49822fee0b90e82e86fe730d9d9bb860cf3d5d749fad3a1e"}


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def pct(n, d):
    return "%.2f" % (100.0 * n / d)


def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.reader(f, delimiter="\t")]


lines_out = []
ok = 0
fail = 0
def check(cond, label, detail=""):
    global ok, fail
    if cond:
        ok += 1
        lines_out.append(f"PASS | {label} | {detail}")
    else:
        fail += 1
        lines_out.append(f"FAIL | {label} | {detail}")
    print(f"[{'PASS' if cond else 'FAIL'}] {label} {detail}")


def head(title):
    lines_out.append("")
    lines_out.append("=" * 72)
    lines_out.append(title)
    lines_out.append("=" * 72)


head("M77 VERIFY — 全量复算（盘上 AFTER）")
lines_out.append("strict 口径：strict_panel.py 第 78 行 if \"[未证]\" not in sem: 的带方括号字面口径")
lines_out.append("atlas：function_atlas.tsv 数据行，entry 统一大写归一（ne）")

# ---- verdict ----
head("1. 异族审计 verdict（NAMED_PUSH_AUDIT20/verdict.tsv）")
vrows = [r for r in read_tsv(VERDICT)[1:] if r]
check(len(vrows) == 4, "verdict 数据行 = 4", str(len(vrows)))
check(sorted(ne(r[0]) for r in vrows) == sorted(EXP), "verdict entry 集 = 4 目标")
check(all(r[2].strip() == "PASS" for r in vrows), "verdict 4 行全 PASS")
for r in vrows:
    check(EXP_SUB.get(ne(r[0])) == r[1].strip(), f"verdict {ne(r[0])} subsystem={r[1].strip()}")

# ---- delta ----
head("2. delta（NAMED_PUSH_S07S11_B2/delta.tsv）")
drows = [r for r in read_tsv(DELTA)[1:] if r]
check(len(drows) == 4, "delta 数据行 = 4", str(len(drows)))
check(all(len(r) == 6 for r in drows), "delta 每行 6 列")
check(sorted(ne(r[0]) for r in drows) == sorted(EXP), "delta entry 集 = 4 目标")
dmap = {ne(r[0]): r for r in drows}
check(all(r[4].strip() == "[已证]" for r in drows), "delta grade 全 [已证]")
check(all("[未证]" not in r[3] for r in drows), "delta col4 全不含字面 [未证]")

# ---- atlas ----
head("3. atlas 归属（function_atlas.tsv）")
atlas = set()
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))
check(len(atlas) == 12916, "atlas 数据行（唯一 entry）= 12,916", str(len(atlas)))
for e in EXP:
    check(e in atlas, f"{e} 在 atlas 内")

# ---- coverage structure ----
head("4. coverage.tsv 结构")
with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
check(not raw.startswith(b"\xef\xbb\xbf"), "无 BOM")
check("\r" not in text, "仅 LF（无 CR）")
lines = text.split("\n")
trailing = lines[-1] == ""
data = lines[1:-1] if trailing else lines[1:]
check(len(data) == 18498, "数据行 = 18,498", str(len(data)))
check(all(len(ln.split("\t")) == 8 for ln in data), "所有数据行 8 列（TAB 分隔）")
rows = [ln.split("\t") for ln in data]
cov_sha = hashlib.sha256(raw).hexdigest()
check(cov_sha != BEFORE_SHA["coverage.tsv"], "coverage sha256 已变化", cov_sha)

# ---- 4 rows col4/5/6 ----
head("5. 4 行 col4/5/6 改动 + cols 1/2/3/7/8 不动")
tmap = {}
for i, r in enumerate(rows):
    if ne(r[0]) in EXP:
        tmap[ne(r[0])] = (i, r)
check(set(tmap) == set(EXP), "4 目标各出现一次")
for e in EXP:
    i, r = tmap[e]
    d = dmap[e]
    check(r[3] == d[3], f"{e} col4 = delta col4 原文", f"len={len(r[3])}")
    check(r[4].strip() == "[已证]", f"{e} col5 = [已证]", r[4])
    check(r[5].strip() == EV, f"{e} col6 = {EV}", r[5])
    check(r[1].strip() == EXP_SUB[e], f"{e} col2 subsystem 未动 = {EXP_SUB[e]}")
    check(r[6] == "1" and r[7] == "0", f"{e} col7=1 col8=0 未动", f"{r[6]}/{r[7]}")
    check("[未证]" not in r[3], f"{e} col4 不含字面 [未证]")

# ---- full/atlas counts ----
head("6. 全表 / atlas 内 / atlas 外 [已证]")
full = sum(1 for r in rows if r[4].strip() == "[已证]")
atl_in = sum(1 for r in rows if ne(r[0]) in atlas and r[4].strip() == "[已证]")
atl_out = full - atl_in
check(full == 1654, "全表 [已证] = 1,654", str(full))
check(atl_in == 1648, "atlas 内 [已证] = 1,648", str(atl_in))
check(atl_out == 6, "atlas 外 [已证] = 6", str(atl_out))

# ---- recompute strict per subsystem ----
head("7. S07 / S11 proved + strict（strict_panel.py 口径）")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = re.compile(r"::v?slot\d+$")
d = collections.defaultdict(collections.Counter)
for r in rows:
    e = ne(r[0]); s = r[1].strip()
    if e not in atlas:
        continue
    name, sem, grade = r[2].strip(), r[3], r[4].strip()
    d[s]["atlas_n"] += 1
    if name and not name.startswith("sub_"):
        d[s]["named_L"] += 1
        if not RE_CSUB.search(name):
            d[s]["named_S14"] += 1
            if not RE_SLOT.search(name):
                d[s]["named_strict"] += 1
    if grade == "[已证]":
        d[s]["proved"] += 1
        if "[未证]" not in sem:
            d[s]["strict"] += 1
for s, wp, ws in (("S07", 75, 52), ("S11", 35, 34)):
    c = d[s]
    check(c["proved"] == wp, f"{s} proved = {wp}", f"atlas_n={c['atlas_n']} pct={pct(c['proved'], c['atlas_n'])}")
    check(c["strict"] == ws, f"{s} strict = {ws}", f"pct={pct(c['strict'], c['atlas_n'])}")
tot_proved = sum(c["proved"] for c in d.values())
tot_strict = sum(c["strict"] for c in d.values())
check(tot_proved == 1648, "TOTAL atlas 内 proved = 1,648", f"pct={pct(tot_proved,12916)}")
check(tot_strict == 1331, "TOTAL strict = 1,331", f"pct={pct(tot_strict,12916)}")

# ---- DoD ----
head("8. DoD 达标判定（不得翻转）")
def dod(key):
    out = []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        a = d[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if d[s]["named_S14"] >= tn and d[s][key] >= tp:
            out.append(s)
    return out
nom, stc = dod("proved"), dod("strict")
check(",".join(nom) == "S15,S16,S17", "名义达标 = S15,S16,S17", ",".join(nom))
check(",".join(stc) == "S17", "严格达标 = S17", ",".join(stc))
lines_out.append("达标翻转：无（改前改后名义 S15/S16/S17、严格 S17；named 三列未动，S07/S11 proved 远低于门槛 402/184）")

# ---- PANEL ----
head("9. PANEL.md 数字 / 备注 / 披露")
with open(PANEL, "rb") as f:
    praw = f.read()
ptxt = praw.decode("utf-8")
panel_sha = hashlib.sha256(praw).hexdigest()
check(panel_sha != BEFORE_SHA["PANEL.md"], "PANEL sha256 已变化", panel_sha)
check(ptxt.count("| 全表 `[已证]` / atlas 内 `[已证]` | **1,654 / 1,648** | " + REMARK + "；M76 并表") == 1,
      "全表/atlas 单元格 1,654/1,648 + M77 备注")
check(ptxt.count(f"| S07 | 804 | 587 | 73.01 | 587 | 73.01 | 64 | 7.96 | 75 | 9.33 | " + REMARK + "；M72 并表") == 1,
      "主表 S07 proved 75/9.33 + M77 备注")
check(ptxt.count(f"| S11 | 368 | 358 | 97.28 | 358 | 97.28 | 29 | 7.88 | 35 | 9.51 | " + REMARK + "；M72 并表") == 1,
      "主表 S11 proved 35/9.51 + M77 备注")
check(ptxt.count("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1648** | **12.76** | " + REMARK + "；M76 并表") == 1,
      "主表 TOTAL proved 1,648/12.76 + M77 备注")
check(ptxt.count("| S07 | 804 | 75 | 9.33 | **52** | **6.47** | 402 | — | — |") == 1,
      "严格表 S07 75/9.33 + 52/6.47")
check(ptxt.count("| S11 | 368 | 35 | 9.51 | **34** | **9.24** | 184 | — | — |") == 1,
      "严格表 S11 35/9.51 + 34/9.24")
check(ptxt.count("| **TOTAL** | **12916** | **1648** | **12.76** | **1331** | **10.31** | — | **3/22** | **1/22** |") == 1,
      "严格表 TOTAL 1,648/12.76 + 1,331/10.31")
M77_TITLE = (
    "# PANEL — R14 coverageM77 并表 4 行（NAMED_PUSH_AUDIT20 PASS 4 行"
    "（S07 006DBE00 + S11 0069EE30/00719E30/0075C7F0），均 atlas 内，仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；"
    "coverage 18,498 行不变；全表 [已证] 1,650→1,654、atlas 内 1,644→1,648、atlas 外仍 6；"
    "面板 S07 proved 74→75、strict 51→52，S11 proved 32→35、strict 31→34；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17，名义仍 S15/S16/S17）；"
    + REMARK + "；不 git commit）；M76 并表 7 行（"
)
check(ptxt.startswith(M77_TITLE), "标题行首为 M77 并表摘要（接 M76）")
plines = ptxt.split("\n")
i76 = [i+1 for i, l in enumerate(plines) if l.startswith("> ⚠️ **M76 披露：")]
i77 = [i+1 for i, l in enumerate(plines) if l.startswith("> ⚠️ **M77 披露：")]
check(len(i76) == 1 and len(i77) == 1, "M76/M77 披露各一处", f"M76={i76} M77={i77}")
check(i77[0] == i76[0] + 4, "M77 披露紧接 M76 披露 4 行块之后", f"M76@{i76[0]} M77@{i77[0]}")
disc_actual = plines[i77[0]-1:i77[0]-1+4]
check(disc_actual == DISC, "M77 披露 4 行原样写入（逐字）")
check(any("M77 并表实算说明" in l for l in plines), "M77 实算说明已追加")

# ---- BEFORE_AFTER integrity ----
head("10. BEFORE_AFTER.txt 完整性")
with open(BA, "rb") as f:
    batxt = f.read().decode("utf-8")
for name, sha in BEFORE_SHA.items():
    check(sha in batxt, f"BEFORE sha256 记录 {name}", sha[:12])
check(cov_sha in batxt, "AFTER sha256 记录 coverage.tsv", cov_sha[:12])
check(panel_sha in batxt, "AFTER sha256 记录 PANEL.md", panel_sha[:12])

# ---- final ----
head("SUMMARY")
lines_out.append(f"OVERALL CHECKS: {ok} PASS / {fail} FAIL")
lines_out.append(f"并行数（本轮并表行数）: 4")
lines_out.append(f"全表 [已证]: 1,650 → 1,654")
lines_out.append(f"atlas 内 [已证]: 1,644 → 1,648")
lines_out.append(f"atlas 外 [已证]: 6（不变）")
lines_out.append(f"S07 proved: 74 → 75（9.33%），strict: 51 → 52（6.47%）")
lines_out.append(f"S11 proved: 32 → 35（9.51%），strict: 31 → 34（9.24%）")
lines_out.append(f"TOTAL proved: 1,644 → 1,648（12.76%），strict: 1,327 → 1,331（10.31%）")
lines_out.append(f"M77 披露落点行号（1-based）: {i77[0]}–{i77[0]+3}")
lines_out.append(f"有无达标翻转: 无（名义 S15/S16/S17、严格 S17 均不变）")
lines_out.append(f"OVERALL: {'ALL PASS' if fail == 0 else 'HAS FAILURES'}")

with open(os.path.join(MERGE, "VERIFY.txt"), "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(lines_out) + "\n")
print(f"\nOVERALL CHECKS: {ok} PASS / {fail} FAIL")
print(f"OVERALL: {'ALL PASS' if fail == 0 else 'HAS FAILURES'}")
sys.exit(0 if fail == 0 else 1)
