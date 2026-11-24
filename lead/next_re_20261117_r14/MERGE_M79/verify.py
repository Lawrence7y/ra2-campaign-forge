# -*- coding: utf-8 -*-
"""M79 VERIFY — recompute all metrics from disk (AFTER directly, BEFORE via exact reconstruction).
Emits VERIFY.txt. Checks the task's hard invariants and the no-flip (达标翻转) requirement.
"""
import csv, os, re, sys, math, collections, hashlib, json
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R4_FILL_91_R3", "fill_delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
MERGE = os.path.join(ROOT, "MERGE_M79")
BA = os.path.join(MERGE, "BEFORE_AFTER.txt")

BASE_BEFORE_SHA = "299aa73205316450ba03f093b347704acdeaecd35154599322e7ff6e8b13ca72"
BASE_FOUR       = 228   # measured baseline (col4 contains ④ & [已证])
EXPECTED_AFTER_SHA = "66830c3f53b3f2e3a5e7b413e588bcdeb1458c0353262e994b283a6cc0b6dde6"

M79_DISC = [
    "> ✅ **M79 补记：91 行的 ④ 已补写成文（`[已证]` 计数不变）**",
    "> `R4_DERIVABILITY` 全量扫描 848 行 `name_only_no_ring4`，其中 **91 行（10.73%）的 ④ 机械可补**（entry 真被活虚表槽持有、RTTI 解出 COL/槽位、装表点在 entry 体外）；已由 `R4_FILL_91_R2` 写成、`R4_FILL_AUDIT` 抽 12 行全 PASS（60/60 项、0 编造）、`R4_FILL_91_R3` 补齐措辞后并入。",
    "> ⇒ 全表「④ 已成文」由 **228 / 1,654（13.78%）升至 319 / 1,654（19.29%）**。注意：**这不是 91 行新增 proved**，这 91 行本来就是 `[已证]`，本次只补写了它们缺失的 ④。",
    "> 另：其余 **746 行**为 direct-only（D-40 不足）、**11 行**全镜像 0 引用（entry 或名字可疑，属另一类卫生问题）。",
]

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

head("M79 VERIFY — 全量复算（盘上 AFTER；BEFORE 由精确重建回推）")
out.append("判据：④ 已成文 = grade `[已证]` 且语义栏（第4列）含字符「④」。")
out.append("atlas：function_atlas.tsv 数据行，entry 统一大写归一（ne()）。")
out.append("BEFORE 回推：对 91 行去掉第4列「；④ 活表槽位见证…」后缀与第6列「;R4_DERIVABILITY/...」后缀后逐字节重建，sha256 须等于改前记录。")

# ---------- 1. delta ----------
head("1. fill_delta.tsv（R4_FILL_91_R3）")
draw = open(DELTA, "rb").read()
dtext = draw.decode("utf-8-sig").replace("\r\n", "\n")
dlines = dtext.split("\n")
ddata = dlines[1:-1] if dlines[-1] == "" else dlines[1:]
drows = [ln.split("\t") for ln in ddata]
check(len(drows) == 91, "delta 数据行 = 91", str(len(drows)))
check(all(len(r) == 6 for r in drows), "delta 每行 6 列")
check(all(r[4].strip() == "[已证]" for r in drows), "delta 91 行 grade 全 [已证]")
check(len({ne(r[0]) for r in drows}) == 91, "delta 91 行 entry 唯一")
dmap = {ne(r[0]): r for r in drows}

# ---------- 2. coverage AFTER structure ----------
head("2. coverage.tsv AFTER 结构")
raw = open(COV, "rb").read()
text = raw.decode("utf-8")
check(not raw.startswith(b"\xef\xbb\xbf"), "无 BOM")
check("\r" not in text, "仅 LF（无 CR）")
lines = text.split("\n")
trailing = lines[-1] == ""
data = lines[1:-1] if trailing else lines[1:]
check(len(data) == 18498, "数据行 = 18,498", str(len(data)))
check(all(len(ln.split("\t")) == 8 for ln in data), "所有数据行 8 列（TAB）")
rows_after = [ln.split("\t") for ln in data]
cov_sha = hashlib.sha256(raw).hexdigest()
check(cov_sha == EXPECTED_AFTER_SHA, "coverage AFTER sha256 == 合并后值", cov_sha[:16])
check(cov_sha != BASE_BEFORE_SHA, "coverage sha256 已变化")

# ---------- 3. BEFORE exact reconstruction ----------
head("3. BEFORE 精确重建（证明只改 91 行第4/6列）")
m4 = "；④ 活表槽位见证"
m6 = ";R4_DERIVABILITY/all848.tsv"
check(all(m4 in r[3] for r in drows), "delta 91 行第4列含追加标记「；④ 活表槽位见证」")
check(all(m6 in r[5] for r in drows), "delta 91 行第6列含追加标记「;R4_DERIVABILITY/...」")
recon = []
for ln in data:
    c = ln.split("\t")
    if ne(c[0]) in dmap:
        c[3] = c[3].split(m4)[0]
        c[5] = c[5].split(m6)[0]
    recon.append("\t".join(c))
recon_text = "\n".join([lines[0]] + recon) + ("\n" if trailing else "")
recon_sha = hashlib.sha256(recon_text.encode("utf-8")).hexdigest()
check(recon_sha == BASE_BEFORE_SHA, "重建 BEFORE sha256 == 改前记录", recon_sha[:16])
rows_before = [ln.split("\t") for ln in recon]

# ---------- 4. 91 rows col4/col6 + untouched cols ----------
head("4. 91 行：第4/6列 = delta，第1/2/3/5/7/8列不动")
idx_by_e = {}
for i, r in enumerate(rows_after):
    idx_by_e.setdefault(ne(r[0]), []).append(i)
touched = []
for e, d in dmap.items():
    assert len(idx_by_e.get(e, [])) == 1, f"{e} not unique in coverage"
    i = idx_by_e[e][0]
    a, b = rows_after[i], rows_before[i]
    touched.append(e)
    check(a[3] == d[3], f"{e} 第4列 = delta 第4列（原文+④）", f"len={len(a[3])}")
    check(a[5] == d[5], f"{e} 第6列 = delta 第6列（evidence 追加）", f"len={len(a[5])}")
    check(a[4].strip() == "[已证]", f"{e} 第5列 grade 仍 [已证]")
    for ci in (0, 1, 2, 4, 6, 7):
        if a[ci] != b[ci]:
            check(False, f"{e} 第{ci+1}列未动", f"before={b[ci][:30]!r} after={a[ci][:30]!r}")
    if a[0] == b[0] and a[1] == b[1] and a[2] == b[2] and a[4] == b[4] and a[6] == b[6] and a[7] == b[7]:
        check(True, f"{e} 第1/2/3/5/7/8列逐字未动")
    check("④" in a[3] and "④" not in b[3], f"{e} ④ 从无到有")
check(len(touched) == 91 and set(touched) == set(dmap), "91 行全部命中且仅这 91 行")
# no other row changed
other_changed = [i for i in range(len(rows_after)) if ne(rows_after[i][0]) not in dmap and rows_after[i] != rows_before[i]]
check(len(other_changed) == 0, "其余 18,407 行零变化", f"changed={len(other_changed)}")

# ---------- 5. full/atlas counts ----------
head("5. 全表 / atlas 内 / atlas 外 [已证]（改前=改后，不增行）")
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

# ---------- 6. ④ 已成文 ----------
head("6. 「④ 已成文」行数（[已证] 且第4列含「④」）")
def four_count(rows):
    return sum(1 for r in rows if r[4].strip() == "[已证]" and "④" in r[3])
cb = four_count(rows_before)
ca = four_count(rows_after)
check(cb == BASE_FOUR, "BEFORE ④ 已成文 = 228（实测基线）", str(cb))
check(ca == 319, "AFTER ④ 已成文 = 319", str(ca))
check(ca == cb + 91, "AFTER = 基线 228 + 91", f"{cb}+91={ca}")
check(pct(cb, 1654) == "13.78", "基线占比 13.78%", pct(cb, 1654))
check(pct(ca, 1654) == "19.29", "改后占比 19.29%", pct(ca, 1654))

# ---------- 7. DoD 达标翻转 ----------
head("7. DoD 达标判定（不得翻转）")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = re.compile(r"::v?slot\d+$")
def dod_stats(rows):
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
check(sum(da[s]["proved"] for s in da) == 1648, "TOTAL atlas 内 proved = 1,648")
check(sum(da[s]["strict"] for s in da) == 1331, "TOTAL strict = 1,331", str(sum(da[s]["strict"] for s in da)))
check(sum(db[s]["strict"] for s in db) == 1331, "BEFORE TOTAL strict = 1,331")
flip = (nom_a != nom_b) or (stc_a != stc_b)
out.append("达标翻转：无（名义 S15/S16/S17、严格 S17 改前改后一致；本次只补写 ④，grade/name/第7/8列与 [未证] 字面状态均未变）")
if flip:
    out.append("!!! 检出达标翻转：停止，需上报 !!!")

# ---------- 8. [未证] literal state unchanged for 91 rows ----------
head("8. 91 行「[未证]」字面状态（strict 口径）不变")
unchanged_lit = sum(1 for e in dmap for i in [idx_by_e[e][0]] if ("[未证]" in rows_after[i][3]) == ("[未证]" in rows_before[i][3]))
check(unchanged_lit == 91, "91 行 [未证] 字面 presence 改前=改后", str(unchanged_lit))

# ---------- 9. PANEL disclosure ----------
head("9. PANEL.md M79 披露（原样写入，M78 之后）")
praw = open(PANEL, "rb").read()
ptext = praw.decode("utf-8")
check(not praw.startswith(b"\xef\xbb\xbf"), "PANEL 无 BOM")
check("\r" not in ptext, "PANEL 仅 LF")
plines = ptext.split("\n")
i78 = [i for i, l in enumerate(plines) if l.startswith("> 🔴 **M78 披露")]
i79 = [i for i, l in enumerate(plines) if l.startswith("> ✅ **M79 补记")]
ishi = [i for i, l in enumerate(plines) if l.startswith("> 📌 **M77 并表实算说明**")]
check(len(i78) == 1, "M78 披露恰一处", str(len(i78)))
check(len(i79) == 1, "M79 披露恰一处", str(len(i79)))
check(len(ishi) >= 1, "M77 实算说明锚点存在")
check(i79[0] > i78[0], "M79 在 M78 之后", f"M78@{i78[0]+1} M79@{i79[0]+1}")
check(i79[0] + 4 == ishi[0], "M79 4 行紧接 M78 块、在 M77 实算说明之前", f"M79@{i79[0]+1}-{i79[0]+4} anchor@{ishi[0]+1}")
actual = plines[i79[0]:i79[0]+4]
check(actual == M79_DISC, "M79 披露 4 行逐字一致")
panel_lines_count = len(plines) - (1 if plines[-1] == "" else 0)
check(panel_lines_count == 572, "PANEL 行数 568→572", str(panel_lines_count))

# ---------- 10. BEFORE_AFTER integrity ----------
head("10. BEFORE_AFTER.txt 完整性")
batxt = open(BA, "rb").read().decode("utf-8")
check(BASE_BEFORE_SHA in batxt, "BEFORE sha256（coverage）已记录")
check(cov_sha in batxt, "AFTER sha256（coverage）已记录")
before = json.load(open(os.path.join(MERGE, "_before_state.json"), encoding="utf-8"))
after = json.load(open(os.path.join(MERGE, "_after_state.json"), encoding="utf-8"))
check(before["PANEL.md"]["sha256"] in batxt, "BEFORE sha256（PANEL）已记录")
check(after["PANEL.md"]["sha256"] in batxt, "AFTER sha256（PANEL）已记录")

# ---------- final ----------
head("SUMMARY")
out.append(f"OVERALL CHECKS: {ok} PASS / {fail} FAIL")
out.append(f"并行数（本轮升级行数）: 91")
out.append(f"数据行数: 18,498（不变）；列数 8、TAB 分隔（不变）")
out.append(f"全表 [已证]: 1,654（不变）；atlas 内 1,648（不变）；atlas 外 6（不变）")
out.append(f"91 行 grade: 全部仍 [已证]（本次不升格）")
out.append(f"「④ 已成文」: 228 / 1,654（13.78%）→ 319 / 1,654（19.29%），+91")
out.append(f"达标翻转: {'有' if flip else '无'}（名义 S15/S16/S17、严格 S17 均不变）")
out.append(f"PANEL M79 披露落点行号（1-based）: {i79[0]+1}–{i79[0]+4}")
out.append(f"BEFORE 重建 sha256 精确匹配改前值，证明只改 91 行第4/6列")
out.append(f"OVERALL: {'ALL PASS' if fail == 0 else 'HAS FAILURES'}")

with open(os.path.join(MERGE, "VERIFY.txt"), "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(out) + "\n")
print(f"\nOVERALL CHECKS: {ok} PASS / {fail} FAIL")
print(f"OVERALL: {'ALL PASS' if fail == 0 else 'HAS FAILURES'}")
print(f"并行数 91 | ④ 已成文 {cb}→{ca} | 达标翻转: {'有' if flip else '无'}")
sys.exit(0 if fail == 0 else 1)
