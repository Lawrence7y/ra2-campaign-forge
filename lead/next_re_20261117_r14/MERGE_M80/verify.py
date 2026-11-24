# -*- coding: utf-8 -*-
"""M80 VERIFY — recompute all metrics from disk (AFTER directly, BEFORE via exact reconstruction).
Emits VERIFY.txt. Checks the task's hard invariants + no-flip + named-column invariance.
"""
import csv, os, re, sys, math, collections, hashlib, json
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
MERGE = os.path.join(ROOT, "MERGE_M80")
BA = os.path.join(MERGE, "BEFORE_AFTER.txt")

BEFORE_SHA = "66830c3f53b3f2e3a5e7b413e588bcdeb1458c0353262e994b283a6cc0b6dde6"
AFTER_SHA  = "4245191f94c47b6a291a29d5c85666dcc043c23410efa5faa6b54ce6e068372e"
PANEL_BEFORE_SHA = "2317d26e6ac7cdddf89a8dc5acd4e8d2ac5b6c96b87404dfd64c66fd42389b38"
PANEL_AFTER_SHA  = "369cef3c7cf80a53bf5dde70d2fd1db85474785a03fceb7bd014d266d614a2e3"

FIX = {
    "004CC680": ("MapClass::MapClass",               "TrajectoryHelper::IsCliffHit",   "S06"),
    "0054E690": ("Kamikaze::Kamikaze",               "KamikazeControl::~Kamikaze",     "S13"),
    "004C6800": ("NetworkEvents::FillEvent_Animation","NetworkEvent::FillEvent_Animation","S18"),
}
def note(old, new):
    return f"；M80 名更正：原记 {old}，据 HYGIENE_R11 与 YRpp 同址声明更正为 {new}（该行 name/地址原可信，仅名不符）"

M80_DISC = [
    "> ✅ **M80 名更正：3 行的 name 与 YRpp 同址声明不符，已更正（grade 与 named 计数均不变）**",
    "> `HYGIENE_R11` 核查 11 行「全镜像 0 引用」的行，结论是**地址全部可信**（`in_atlas=yes`、`looks_like_func=yes`、`prologue_within_16=none`、`real_func_start` 即 entry 本身），问题在**名字**：",
    "> - `004CC680`：原记 `MapClass::MapClass` → 实为 `TrajectoryHelper::IsCliffHit`（YRpp 同址声明）",
    "> - `0054E690`：原记 `Kamikaze::Kamikaze` → 实为 `KamikazeControl::~Kamikaze`",
    "> - `004C6800`：原记 `NetworkEvents::FillEvent_Animation` → 实为 `NetworkEvent::FillEvent_Animation`（单复数之差）",
    "> ⇒ 「构造函数 0 引用」这个矛盾的解释是**名字错**、不是地址错。这也揭示一类数据质量风险：**错的 name 仍会被 `named_S(R14)` 计为一个名字**。",
    "> 其余 8 行的名字与 YRpp 同址声明一致（均为 `NOVTABLE` 抽象类方法），未改。",
]

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = re.compile(r"::v?slot\d+$")

def named_L(n):
    return bool(n.strip()) and not n.strip().startswith("sub_")
def named_S14(n):
    return named_L(n) and (RE_CSUB.search(n.strip()) is None)
def named_strict(n):
    return named_S14(n) and (RE_SLOT.search(n.strip()) is None)

out = []
ok = 0
fail = 0
def check(cond, label, detail=""):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
    out.append(f"{'PASS' if cond else 'FAIL'} | {label} | {detail}")
    print(f"[{('PASS' if cond else 'FAIL')}] {label} {detail}")
def head(title):
    out.extend(["", "=" * 72, title, "=" * 72])

head("M80 VERIFY — 全量复算（盘上 AFTER；BEFORE 由精确重建回推）")
out.append("口径：named_L = name 非空且不以 sub_ 开头；named_S(R14) = named_L 排除 ::sub_[0-9A-Fa-f]+$；named_strict 再排除 ::v?slot\\d+$。")
out.append("BEFORE 回推：对 3 行去掉第4列 M80 追加后缀、并把第3列改回旧名后逐字节重建，sha256 须等于改前记录。")

# ---------- 1. coverage AFTER structure ----------
head("1. coverage.tsv AFTER 结构")
raw = open(COV, "rb").read()
text = raw.decode("utf-8")
check(not raw.startswith(b"\xef\xbb\xbf"), "无 BOM")
check("\r" not in text, "仅 LF（无 CR）")
lines = text.split("\n")
trailing = lines[-1] == ""
check(trailing is False, "无末尾换行（保持）")
data = lines[1:-1] if trailing else lines[1:]
check(len(data) == 18498, "数据行 = 18,498", str(len(data)))
check(all(len(ln.split("\t")) == 8 for ln in data), "所有数据行 8 列（TAB）")
rows_after = [ln.split("\t") for ln in data]
cov_sha = hashlib.sha256(raw).hexdigest()
check(cov_sha == AFTER_SHA, "coverage AFTER sha256 == 合并后值", cov_sha[:16])
check(cov_sha != BEFORE_SHA, "coverage sha256 已变化")

# ---------- 2. BEFORE exact reconstruction ----------
head("2. BEFORE 精确重建（证明只改 3 行第3列 + 第4列追加）")
recon = []
for ln in data:
    c = ln.split("\t")
    if c[0] in FIX:
        old, new, sub = FIX[c[0]]
        nt = note(old, new)
        check(c[3].endswith(nt), f"{c[0]} 第4列以 M80 追加句结尾")
        c[3] = c[3][:-len(nt)]
        c[2] = old
    recon.append("\t".join(c))
recon_text = "\n".join([lines[0]] + recon) + ("\n" if trailing else "")
recon_sha = hashlib.sha256(recon_text.encode("utf-8")).hexdigest()
check(recon_sha == BEFORE_SHA, "重建 BEFORE sha256 == 改前记录", recon_sha[:16])
rows_before = [ln.split("\t") for ln in recon]

# ---------- 3. locate 3 rows, verify col edits strict ----------
head("3. 3 行：第3列 name 旧→新、第4列纯追加、grade/其余列逐字未动")
idx_by_e = {}
for i, r in enumerate(rows_after):
    idx_by_e.setdefault(r[0], []).append(i)
for e, (old, new, sub) in FIX.items():
    check(len(idx_by_e.get(e, [])) == 1, f"{e} 在 coverage 唯一", str(len(idx_by_e.get(e, []))))
    i = idx_by_e[e][0]
    a, b = rows_after[i], rows_before[i]
    check(a[2] == new, f"{e} 第3列 = 新名", a[2])
    check(b[2] == old, f"{e} BEFORE 第3列 = 旧名", b[2])
    check(a[3].startswith(b[3]), f"{e} 第4列纯追加（含旧文）")
    check(a[3] == b[3] + note(old, new), f"{e} 第4列 = 原第4列 + M80 句")
    check(a[4] == b[4] == "[已证]", f"{e} 第5列 grade 未变 = [已证]")
    for k in (0, 1, 5, 6, 7):
        check(a[k] == b[k], f"{e} 第{k+1}列未动", f"before={b[k][:20]!r} after={a[k][:20]!r}")
    check(("[未证]" in a[3]) == ("[未证]" in b[3]), f"{e} 第4列 [未证] 字面 presence 不变")
    check(("④" in a[3]) == ("④" in b[3]), f"{e} 第4列 ④ 字面 presence 不变")

# no other row changed
other_changed = [i for i in range(len(rows_after)) if rows_after[i][0] not in FIX and rows_after[i] != rows_before[i]]
check(len(other_changed) == 0, "其余 18,495 行零变化", f"changed={len(other_changed)}")

# ---------- 4. [已证] counts ----------
head("4. 全表 / atlas 内 / atlas 外 [已证]（改前=改后）")
atlas = set()
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))
check(len(atlas) == 12916, "atlas 唯一 entry = 12,916", str(len(atlas)))
def proved_counts(rows):
    full = [r for r in rows if r[4].strip() == "[已证]"]
    ain = [r for r in full if ne(r[0]) in atlas]
    aout = [r for r in full if ne(r[0]) not in atlas]
    return len(full), len(ain), len(aout)
fa, ia, oa = proved_counts(rows_after)
fb, ib, ob = proved_counts(rows_before)
check(fa == 1654, "AFTER 全表 [已证] = 1,654", str(fa))
check(ia == 1648, "AFTER atlas 内 [已证] = 1,648", str(ia))
check(oa == 6, "AFTER atlas 外 [已证] = 6", str(oa))
check((fb, ib, ob) == (1654, 1648, 6), "BEFORE [已证] 1654/1648/6", f"{fb}/{ib}/{ob}")
check((fa, ia, oa) == (fb, ib, ob), "[已证] 计数改前改后不变")

# ---------- 5. named 3 columns invariance for the 3 rows ----------
head("5. 3 行 named_L / named_S(R14) / named_strict：旧名新名判定均不变")
for e, (old, new, sub) in FIX.items():
    i = idx_by_e[e][0]
    check(ne(e) in atlas, f"{e} 在 atlas 内（HYGIENE_R11 in_atlas=yes）")
    for col, nm in (("旧名", old), ("新名", new)):
        check(named_L(nm), f"{e} {col} named_L = True", nm)
        check(named_S14(nm), f"{e} {col} named_S(R14) = True", nm)
        check(named_strict(nm), f"{e} {col} named_strict = True", nm)
    tup_old = (named_L(old), named_S14(old), named_strict(old))
    tup_new = (named_L(new), named_S14(new), named_strict(new))
    check(tup_old == tup_new == (True, True, True), f"{e} 三列判定改前=改后=全 True", f"{tup_old}->{tup_new}")

# ---------- 6. special regex check ----------
head("6. 特别核：::sub_[0-9A-Fa-f]+$ / ::slotN 均不匹配")
SPECIAL = {
    "旧名 Kamikaze::Kamikaze": "Kamikaze::Kamikaze",
    "新名 KamikazeControl::~Kamikaze": "KamikazeControl::~Kamikaze",
    "新名 TrajectoryHelper::IsCliffHit": "TrajectoryHelper::IsCliffHit",
}
for label, nm in SPECIAL.items():
    check(RE_CSUB.search(nm) is None, f"{label} 不匹配 ::sub_...$", nm)
    check("::slot" not in nm, f"{label} 不含 ::slotN", nm)
    check(RE_SLOT.search(nm) is None, f"{label} 不匹配 ::v?slot\\d+$", nm)

# ---------- 7. named aggregates (per subsystem + total) unchanged ----------
head("7. named 三列：逐子系统 + TOTAL 聚合计数改前=改后")
def named_stats(rows):
    d = collections.defaultdict(collections.Counter)
    for r in rows:
        e = ne(r[0]); s = r[1].strip()
        if e not in atlas:
            continue
        nm = r[2].strip()
        d[s]["atlas_n"] += 1
        if named_L(nm):
            d[s]["named_L"] += 1
            if named_S14(nm):
                d[s]["named_S14"] += 1
                if named_strict(nm):
                    d[s]["named_strict"] += 1
    return d
na, nb = named_stats(rows_after), named_stats(rows_before)
subs = sorted(k for k in set(na) | set(nb) if re.match(r"^S\d\d$", k))
for k in ("atlas_n", "named_L", "named_S14", "named_strict"):
    ta = sum(na[s][k] for s in subs); tb = sum(nb[s][k] for s in subs)
    check(ta == tb, f"TOTAL {k} 改前=改后", f"{tb}->{ta}")
for s in subs:
    for k in ("named_L", "named_S14", "named_strict"):
        check(na[s][k] == nb[s][k], f"{s} {k} 改前=改后", f"{nb[s][k]}->{na[s][k]}")

# ---------- 8. DoD 达标翻转 ----------
head("8. DoD 达标判定（不得翻转）")
def dod_stats(rows):
    d = collections.defaultdict(collections.Counter)
    for r in rows:
        e = ne(r[0]); s = r[1].strip()
        if e not in atlas:
            continue
        name, sem, grade = r[2].strip(), r[3], r[4].strip()
        d[s]["atlas_n"] += 1
        if named_L(name):
            d[s]["named_L"] += 1
            if named_S14(name):
                d[s]["named_S14"] += 1
                if named_strict(name):
                    d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved"] += 1
            if "[未证]" not in sem:
                d[s]["strict"] += 1
    return d
def dod(d, key):
    res = []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        a = d[s]["atlas_n"]; tn = math.ceil(0.9 * a); tp = math.ceil(0.5 * a)
        if d[s]["named_S14"] >= tn and d[s][key] >= tp:
            res.append(s)
    return res
da, db = dod_stats(rows_after), dod_stats(rows_before)
nom_a, nom_b = dod(da, "proved"), dod(db, "proved")
stc_a, stc_b = dod(da, "strict"), dod(db, "strict")
check(",".join(nom_b) == "S15,S16,S17", "BEFORE 名义达标 = S15,S16,S17", ",".join(nom_b))
check(",".join(stc_b) == "S17", "BEFORE 严格达标 = S17", ",".join(stc_b))
check(nom_a == nom_b, "AFTER 名义达标集合 == BEFORE", ",".join(nom_a))
check(stc_a == stc_b, "AFTER 严格达标集合 == BEFORE", ",".join(stc_a))
flip = (nom_a != nom_b) or (stc_a != stc_b)
out.append("达标翻转：无（名义 S15/S16/S17、严格 S17 改前改后一致；本次只改名与追加说明，grade/name 已具名性/第7/8列/[未证]字面均未变）")
if flip:
    out.append("!!! 检出达标翻转：停止，需上报 !!!")

# ---------- 9. PANEL disclosure ----------
head("9. PANEL.md M80 披露（原样写入，M79 之后）")
praw = open(PANEL, "rb").read()
ptext = praw.decode("utf-8")
check(not praw.startswith(b"\xef\xbb\xbf"), "PANEL 无 BOM")
check("\r" not in ptext, "PANEL 仅 LF")
check(ptext.endswith("\n"), "PANEL 末尾换行保持")
plines = ptext.split("\n")
i79 = [i for i, l in enumerate(plines) if l.startswith("> ✅ **M79 补记")]
i80 = [i for i, l in enumerate(plines) if l.startswith("> ✅ **M80 名更正")]
ishi = [i for i, l in enumerate(plines) if l.startswith("> 📌 **M77 并表实算说明**")]
check(len(i79) == 1, "M79 披露恰一处", str(len(i79)))
check(len(i80) == 1, "M80 披露恰一处", str(len(i80)))
check(len(ishi) >= 1, "M77 实算说明锚点存在")
check(i80[0] == i79[0] + 4, "M80 紧接 M79 披露块之后", f"M79@{i79[0]+1}-{i79[0]+4} M80@{i80[0]+1}")
check(ishi[0] == i80[0] + 7, "M80 7 行之后是 M77 实算说明", f"M80@{i80[0]+1}-{i80[0]+7} anchor@{ishi[0]+1}")
actual = plines[i80[0]:i80[0]+7]
check(actual == M80_DISC, "M80 披露 7 行逐字一致")
panel_lines_count = len(plines) - (1 if plines[-1] == "" else 0)
check(panel_lines_count == 579, "PANEL 行数 572→579", str(panel_lines_count))

# ---------- 10. BEFORE_AFTER integrity ----------
head("10. BEFORE_AFTER.txt 完整性")
batxt = open(BA, "rb").read().decode("utf-8")
for label, h in (("BEFORE coverage", BEFORE_SHA), ("AFTER coverage", AFTER_SHA),
                 ("BEFORE PANEL", PANEL_BEFORE_SHA), ("AFTER PANEL", PANEL_AFTER_SHA)):
    check(h in batxt, f"{label} sha256 已记录", h[:12])

# ---------- final ----------
head("SUMMARY")
out.append(f"OVERALL CHECKS: {ok} PASS / {fail} FAIL")
out.append("改动 3 行：004CC680 / 0054E690 / 004C6800（仅 name 旧→新 + 语义栏末追加 M80 句）")
out.append("数据行数: 18,498（不变）；列数 8、TAB（不变）；全表 [已证]: 1,654（不变）")
out.append("3 行 grade: 全部仍 [已证]（不改）；named_L / named_S(R14) / named_strict 三列逐行与聚合均不变")
out.append("特殊核：KamikazeControl::~Kamikaze / Kamikaze::Kamikaze / TrajectoryHelper::IsCliffHit 均不匹配 ::sub_...$、不含 ::slotN")
out.append(f"达标翻转: {'有' if flip else '无'}（名义 S15/S16/S17、严格 S17 均不变）")
out.append(f"PANEL M80 披露落点行号（1-based）: {i80[0]+1}–{i80[0]+7}（M79 之后、M77 实算说明之前）")
out.append("BEFORE 重建 sha256 精确匹配改前值，证明只改 3 行第3列 + 第4列追加")
out.append(f"OVERALL: {'ALL PASS' if fail == 0 else 'HAS FAILURES'}")
with open(os.path.join(MERGE, "VERIFY.txt"), "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(out) + "\n")
print(f"\nOVERALL CHECKS: {ok} PASS / {fail} FAIL")
print(f"OVERALL: {'ALL PASS' if fail == 0 else 'HAS FAILURES'}")
print(f"达标翻转: {'有' if flip else '无'}")
sys.exit(0 if fail == 0 else 1)
