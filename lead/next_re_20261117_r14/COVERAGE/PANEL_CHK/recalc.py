# -*- coding: utf-8 -*-
"""PANEL_CHK/recalc.py — PANEL.md 全量数值一致性普查（可复跑；只读输入，只写本目录）。

输入（全部只读）：
  COVERAGE/coverage.tsv                     18,498 数据行 + 表头，TAB 8 列
  ../../next_re_20261112_r10/W130_atlas/function_atlas.tsv   12,916 数据行（entry 小写十六进制）
  COVERAGE/PANEL.md                         被普查面板（不改）
  P0_INITTERM/INITTERM_TABLE.tsv            3,944 数据行（仅用于核对三分母 B 的前提）
  _hygiene/PANEL.M*.bak                     历史截面备份（仅用于「旧截面」归类的证据）

重算口径（任务卡 PANEL-CONSISTENCY「重算口径」逐条实现，别自创）：
  n            = 该 subsystem 且 entry 在 atlas 内的行数（entry 大小写归一为 %08X 大写）
  proved       = 上述行中 grade == [已证]
  named_L      = 上述行中 name 非空且不以 sub_ 开头
  named_S(R14) = named_L 再排除匹配 ::sub_[0-9A-Fa-f]+$ 的（任意长度十六进制，M53 明确）
  named_strict = named_S(R14) 再排除含 ::slotN / ::vslotN 的
  proved_strict= proved 中语义串（第 4 列）不含「未证」的 —— 卡片口径（裸子串）；
                 另算「[未证]」带括号变体（= RULING_R15 work/strict_panel.py 的实现）作对照
  门槛         = ceil(0.9n) / ceil(0.5n)
  nominal_pass = named_S(R14) >= ceil(0.9n) 且 proved >= ceil(0.5n)
  strict_pass  = nominal_pass 再加 proved_strict >= ceil(0.5n)
  （S22 按面板规则不参与达标排名；本脚本仍给出其原始布尔值，恒为 False）

输出（只写 PANEL_CHK/）：
  recalc_all.tsv   22 行 S01–S22 + 1 行 TOTAL
  mismatches.tsv   panel_line  table_id  subsystem  column  panel_value  recalc_value  class  affects_dod
  REPORT.md        方法、口径、逐表逐行结果、分类统计、头条核对
  控制台摘要       不符总数 / 按类别 / 翻转格子数
"""
import csv
import hashlib
import math
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent            # .../COVERAGE/PANEL_CHK
ROOT = SCRIPT_DIR.parents[1]                            # .../next_re_20261117_r14
LEAD = SCRIPT_DIR.parents[2]                            # .../lead
PROJ = SCRIPT_DIR.parents[3]                            # ra2-campaign-forge

COV = ROOT / "COVERAGE" / "coverage.tsv"
PANEL = ROOT / "COVERAGE" / "PANEL.md"
ATLAS = LEAD / "next_re_20261112_r10" / "W130_atlas" / "function_atlas.tsv"
INITTERM = ROOT / "P0_INITTERM" / "INITTERM_TABLE.tsv"
HYGIENE = ROOT / "_hygiene"

# ---------------------------------------------------------------- 基础工具

def ne(e):
    """entry 大小写归一：去空白、去 0x 前缀、按 int(e,16) 格式化为 8 位大写十六进制。"""
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def r2(x):
    """四舍五入（half-up）保留两位，Decimal 实现，避开银行家舍入。"""
    return float(Decimal(repr(float(x))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def clean_num(s):
    """面板数字单元格清洗：去 **、空格、千分位逗号。"""
    return s.replace("*", "").replace(",", "").replace(" ", "").strip()


def is_num(s):
    s = clean_num(s)
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", s))


# ---------------------------------------------------------------- 1. 输入装载

atlas_rows = 0
atlas_norm = Counter()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas_rows += 1
            atlas_norm[ne(p[0])] += 1
atlas_set = set(atlas_norm)
atlas_dup = {k: v for k, v in atlas_norm.items() if v > 1}

cov_rows_raw = 0
cov_malformed = 0
cov_entries = set()
grade_hist = Counter()
conflict1 = 0
sub_all = Counter()                 # subsystem -> coverage 全行数（含 atlas 外）
d = defaultdict(Counter)            # subsystem -> 各计数器
odd_sub_atlas = Counter()           # atlas 内非 S\d\d 的 subsystem
re_initterm_name = re.compile(r"^initterm_thunk_\d+$")
initterm_named_rows = 0
sub_re = re.compile(r"^S\d\d$")

with open(COV, encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f, delimiter="\t")
    header = next(reader)
    for r in reader:
        if len(r) < 8:
            cov_malformed += 1
            continue
        cov_rows_raw += 1
        e = ne(r[0])
        s = r[1].strip()
        name = r[2].strip()
        sem = r[3] if len(r) > 3 else ""
        grade = r[4].strip() if len(r) > 4 else ""
        conflict = r[7].strip() if len(r) > 7 else ""
        cov_entries.add(e)
        grade_hist[grade] += 1
        if conflict == "1":
            conflict1 += 1
        if re_initterm_name.match(name):
            initterm_named_rows += 1
        sub_all[s] += 1
        if e not in atlas_set:
            d[s]["cov_nonatlas"] += 1
            continue
        d[s]["atlas_n"] += 1
        if not sub_re.match(s):
            odd_sub_atlas[s] += 1
        if name and not name.startswith("sub_"):
            d[s]["named_L"] += 1
            if not re.search(r"::sub_[0-9A-Fa-f]+$", name):
                d[s]["named_S14"] += 1
                if not re.search(r"::v?slot\d+$", name):
                    d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved"] += 1
            if "未证" not in sem:            # 卡片口径：裸「未证」
                d[s]["proved_strict"] += 1
            if "[未证]" not in sem:          # 对照口径：字面「[未证]」（strict_panel.py 实现）
                d[s]["proved_strict_br"] += 1

S_LIST = sorted(k for k in d if sub_re.match(k))
OTHER_SUB = sorted(k for k in d if not sub_re.match(k))

sum_S = Counter()
for s in S_LIST:
    for k, v in d[s].items():
        sum_S[k] += v
sum_all = Counter(sum_S)                      # TOTAL 口径 = 全部 atlas 内行
for s in OTHER_SUB:
    for k, v in d[s].items():
        sum_all[k] += v

tot = {s: dict(d[s]) for s in S_LIST}
thr_named = {s: math.ceil(0.9 * tot[s]["atlas_n"]) for s in S_LIST}
thr_proved = {s: math.ceil(0.5 * tot[s]["atlas_n"]) for s in S_LIST}
nominal = {s: bool(tot[s]["named_S14"] >= thr_named[s] and tot[s]["proved"] >= thr_proved[s])
           for s in S_LIST}
strict = {s: bool(nominal[s] and tot[s]["proved_strict"] >= thr_proved[s]) for s in S_LIST}
strict_br = {s: bool(nominal[s] and tot[s]["proved_strict_br"] >= thr_proved[s]) for s in S_LIST}
nominal_set = [s for s in S_LIST if nominal[s]]
strict_set = [s for s in S_LIST if strict[s]]
strict_br_set = [s for s in S_LIST if strict_br[s]]

# 三分母 B 的前提核对（只读 INITTERM_TABLE.tsv）
interm_targets = set()
with open(INITTERM, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            interm_targets.add(ne(p[2]))
interm_in_cov = interm_targets & cov_entries
B_recalc = cov_rows_raw - len(interm_in_cov)

# ---------------------------------------------------------------- 2. PANEL.md 表格解析

panel_text = PANEL.read_text(encoding="utf-8")
panel_lines = panel_text.splitlines()

TABLE_LINE = re.compile(r"^\s*(?:>\s*)?\|")


def parse_blocks(lines):
    blocks = []
    cur = []
    for no, raw in enumerate(lines, start=1):
        if TABLE_LINE.match(raw):
            cur.append((no, raw))
        else:
            if cur:
                blocks.append(cur)
                cur = []
    if cur:
        blocks.append(cur)
    out = []
    for blk in blocks:
        header_cells = split_row(blk[0][1])
        out.append({"start": blk[0][0], "end": blk[-1][0],
                    "header": header_cells, "rows": blk})
    return out


def split_row(raw):
    s = raw.strip()
    if s.startswith(">"):
        s = s.lstrip("> ").strip()
    s = s.strip("|")
    return [c.strip() for c in s.split("|")]


def norm_cell(c):
    return c.replace("**", "").strip()


blocks = parse_blocks(panel_lines)
T1 = T2 = T3 = T4 = None
for b in blocks:
    h = "|".join(b["header"])
    if "口径" in h and "数值" in h and T1 is None:
        T1 = b
    elif "named_n(L)" in h and "proved_n" in h and "DoD差距说明" in h and T2 is None:
        T2 = b
    elif "proved_strict_n" in h and "名义" in h and T3 is None:
        T3 = b
    elif "ceil(0.9n)" in h and T4 is None:
        T4 = b

assert T1 and T2 and T3 and T4, "PANEL.md 四张表未识别齐"
T1_ID = "T1三分母@L%d-%d" % (T1["start"], T1["end"])
T2_ID = "T2主面板@L%d-%d" % (T2["start"], T2["end"])
T3_ID = "T3严格双列@L%d-%d" % (T3["start"], T3["end"])
T4_ID = "T4-M47同步@L%d-%d" % (T4["start"], T4["end"])

T2_COLS = ["S", "atlas_n", "named_n(L)", "named_pct_L", "named_n_S(R14)", "named_pct_S(R14)",
           "named_n_S(strict)", "named_pct_S(strict)", "proved_n", "proved_pct", "DoD差距说明"]
T3_COLS = ["S", "atlas_n", "proved_n", "proved_pct", "proved_strict_n", "proved_strict_pct",
           "门槛(50%)", "名义", "严格"]
T4_COLS = ["S", "atlas_n", "named_n(L)", "named_n_S(R14)", "named_n_S(strict)", "proved_n",
           "ceil(0.9n)", "ceil(0.5n)", "达标"]

# 历史截面备份（旧截面归类证据）
BACKUPS = {}
for bak in sorted(HYGIENE.glob("PANEL.M*.bak")):
    try:
        BACKUPS[bak.name] = parse_blocks(
            bak.read_text(encoding="utf-8", errors="replace").splitlines())
    except Exception:
        pass


def bak_cell(bak_blocks, want_header_key, row_key, col_index):
    """在备份的某张表里取 (行,列) 的原值；找不到返回 None。"""
    for b in bak_blocks:
        h = "|".join(b["header"])
        if want_header_key not in h:
            continue
        for no, raw in b["rows"][2:] if len(b["rows"]) > 2 else []:
            cells = split_row(raw)
            if not cells:
                continue
            if norm_cell(cells[0]).replace("TOTAL", "").strip() == "" and row_key == "TOTAL":
                pass
            key = norm_cell(cells[0])
            if key == row_key or (row_key == "TOTAL" and "TOTAL" in key):
                if col_index < len(cells):
                    return norm_cell(cells[col_index])
    return None


# ---------------------------------------------------------------- 3. M47 时点重建（T4 快照口径）
# 文档化增量（全部出自 PANEL.md 自身的并表注记，atlas 分母口径 proved 增量）：
DOC_DELTAS = [
    ("M55", {"S13": 11, "S02": 1, "S19": 7}, "PANEL L1/L77 M55 注记：S13 89→100、S02 34→35、S19 20→27"),
    ("M56", {"S17": 2}, "PANEL L1/L77 M56 注记：S17 proved 54→56"),
    ("M58", {"S09": 8}, "PANEL L63/L77 M58 注记：S09_KPROVED8 8 行全 atlas 内"),
    ("M59", {"S15": 5, "S16": 1}, "PANEL L509/L516 M59 注记：A 分母口径 S15 +5、S16 +1"),
]
m47_expected = {}
for s in S_LIST:
    m47_expected[s] = tot[s]["proved"]
m47_evidence = []
for merge, dd, ev in DOC_DELTAS:
    for s, v in dd.items():
        m47_expected[s] -= v
    m47_evidence.append("%s: %s" % (merge, ev))
m47_sum = sum(m47_expected[s] for s in S_LIST if s <= "S21")
M47_PROSE_SUM = 1400  # PANEL L192「21 行小计 … proved 1,400」
m47_reconstruction_ok = (m47_sum == M47_PROSE_SUM)

# ---------------------------------------------------------------- 4. 逐格比对

mismatches = []   # dict(line,table_id,sub,column,panel,recalc,cls,evidence,affects)


def pct_ok(panel_val, raw):
    """面板百分数与重算值是否一致（容许两种舍入约定的 2 位小数）。"""
    try:
        pv = float(clean_num(panel_val))
    except ValueError:
        return False
    if abs(pv - r2(raw)) < 1e-9:
        return True
    return abs(pv - raw) <= 0.0050000001


def add_mismatch(line, tid, sub, col, panel, recalc, cls, evidence, affects):
    mismatches.append(dict(line=line, tid=tid, sub=sub, col=col, panel=panel,
                           recalc=recalc, cls=cls, evidence=evidence, affects=affects))


def sub_with(cell_col, recalc_val, sub_row_panel):
    """把某一格替换为重算值后，该子系统名义/严格判定是否翻转（面板基线 → 修正后）。"""
    named_S14 = sub_row_panel.get("named_S14")
    proved = sub_row_panel.get("proved")
    strict_n = sub_row_panel.get("proved_strict")
    a = sub_row_panel.get("atlas_n")
    if None in (named_S14, proved, strict_n, a) or a == 0:
        return False, False
    tn, tp = math.ceil(0.9 * a), math.ceil(0.5 * a)
    base_nom = named_S14 >= tn and proved >= tp
    base_str = base_nom and strict_n >= tp
    n2, p2, s2 = named_S14, proved, strict_n
    if cell_col in ("named_n_S(R14)",):
        n2 = recalc_val
    if cell_col in ("proved_n",):
        p2 = recalc_val
    if cell_col in ("proved_strict_n",):
        s2 = recalc_val
    if cell_col in ("atlas_n",):
        # atlas_n 变了会同时改分子与门槛——本表 atlas_n 全部与盘上一致，防御性处理
        a2 = recalc_val
        tn2, tp2 = math.ceil(0.9 * a2), math.ceil(0.5 * a2)
        nom2 = n2 >= tn2 and p2 >= tp2
        str2 = nom2 and s2 >= tp2
        return nom2 != base_nom, str2 != base_str
    nom2 = n2 >= tn and p2 >= tp
    str2 = nom2 and s2 >= tp
    return nom2 != base_nom, str2 != base_str


# ---- T1 三分母 ----
t1_cells = []   # (line, colname, panel_raw, panel_num, recalc_num)
for no, raw in T1["rows"][2:]:
    cells = split_row(raw)
    if not cells:
        continue
    key = norm_cell(cells[0])
    val = norm_cell(cells[1]) if len(cells) > 1 else ""
    if key.startswith("A"):
        t1_cells.append((no, "A(atlas分母)", val, int(clean_num(val)), atlas_rows))
    elif key.startswith("B"):
        t1_cells.append((no, "B(审计口径)", val, int(clean_num(val)), B_recalc))
    elif key.startswith("C"):
        t1_cells.append((no, "C(审计口径)", val, int(clean_num(val)), cov_rows_raw))
    elif "coverage.tsv" in key and "行数" in key:
        t1_cells.append((no, "当前coverage行数", val, int(clean_num(val)), cov_rows_raw))
    elif "全表" in key and "atlas 内" in key:
        parts = [clean_num(x) for x in val.split("/")]
        if len(parts) == 2:
            t1_cells.append((no, "全表[已证]", parts[0], int(parts[0]), sum_all["proved"]))
            t1_cells.append((no, "atlas内[已证]", parts[1], int(parts[1]), 0))  # 占位，稍后修正

# atlas 内 [已证] 真值
atlas_proved_rec = 0
for s in list(d.keys()):
    pass
# 重新精确统计：全表/atlas 内 [已证]（不依赖 subsystem 归类）
all_proved = 0
all_proved_atlas = 0
with open(COV, encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f, delimiter="\t")
    next(reader)
    for r in reader:
        if len(r) < 8:
            continue
        if r[4].strip() == "[已证]":
            all_proved += 1
            if ne(r[0]) in atlas_set:
                all_proved_atlas += 1
# 修正 t1_cells 里占位
_fixed = []
for item in t1_cells:
    if item[1] == "atlas内[已证]":
        _fixed.append((item[0], item[1], item[2], item[3], all_proved_atlas))
    elif item[1] == "全表[已证]":
        _fixed.append((item[0], item[1], item[2], item[3], all_proved))
    else:
        _fixed.append(item)
t1_cells = _fixed

T1_EVIDENCE = {
    "全表[已证]": ("值 1,479 = M55 后截面（PANEL L1 M55 段「全表 [已证] 1,460→1,479」）；"
                   "其后 M56 +2、M58 +8、M59 +7（PANEL L77 TOTAL 行注记 1,481→1,489→1,496）"),
    "atlas内[已证]": ("值 1,474 = M55 后截面（PANEL L1「atlas 内 1,455→1,474」）；"
                      "其后 M56 1,476、M58 1,484、M59 1,490（PANEL L77 注记）"),
}

for no, col, panel_raw, panel_num, recalc_num in t1_cells:
    if panel_num == recalc_num:
        continue
    cls = "旧截面"
    ev = T1_EVIDENCE.get(col, "")
    # 备份证据
    hits = []
    for bakname, bblocks in BACKUPS.items():
        for b in bblocks:
            h = "|".join(b["header"])
            if not ("口径" in h and "数值" in h):
                continue
            for bno, braw in b["rows"][2:]:
                bc = split_row(braw)
                if len(bc) > 1 and "全表" in norm_cell(bc[0]) and clean_num(panel_raw) in clean_num(norm_cell(bc[1])).split("/"):
                    hits.append("%s L%d" % (bakname, bno))
    if hits:
        ev += "；备份证据：%s 同格值相同" % ", ".join(hits[:3])
    affects = "yes:对外头条数字（三分母节 atlas 内 [已证] 与全表 [已证] 为对外引用值）"
    add_mismatch(no, T1_ID, "—", col, panel_raw, str(recalc_num), cls, ev, affects)

# ---- T2 主面板（当前口径）----
def parse_t2_row(raw):
    cells = split_row(raw)
    if len(cells) > len(T2_COLS):
        cells = cells[:len(T2_COLS) - 1] + ["|".join(cells[len(T2_COLS) - 1:])]
    if len(cells) < len(T2_COLS):
        cells += [""] * (len(T2_COLS) - len(cells))
    return cells


t2_panel = {}      # sub -> {col: raw}
t2_line = {}
for no, raw in T2["rows"][2:]:
    cells = parse_t2_row(raw)
    key = norm_cell(cells[0])
    sub = "TOTAL" if "TOTAL" in key else key
    t2_panel[sub] = {T2_COLS[i]: cells[i] for i in range(len(T2_COLS))}
    t2_line[sub] = no

t2_recalc = {}
for s in S_LIST:
    t2_recalc[s] = dict(atlas_n=tot[s]["atlas_n"], **{
        "named_n(L)": tot[s]["named_L"],
        "named_n_S(R14)": tot[s]["named_S14"],
        "named_n_S(strict)": tot[s]["named_strict"],
        "proved_n": tot[s]["proved"]})
t2_recalc["TOTAL"] = dict(atlas_n=sum_all["atlas_n"], **{
    "named_n(L)": sum_all["named_L"],
    "named_n_S(R14)": sum_all["named_S14"],
    "named_n_S(strict)": sum_all["named_strict"],
    "proved_n": sum_all["proved"]})

PCT_COL = {"named_pct_L": "named_n(L)", "named_pct_S(R14)": "named_n_S(R14)",
           "named_pct_S(strict)": "named_n_S(strict)", "proved_pct": "proved_n"}

# 面板基线（用于翻转测试）：T2 数字 + T3 strict
panel_base = {}
for sub in list(t2_panel.keys()) + ["TOTAL"]:
    if sub not in t2_panel:
        continue
    row = t2_panel[sub]
    try:
        panel_base[sub] = dict(
            atlas_n=int(clean_num(row["atlas_n"])),
            named_S14=int(clean_num(row["named_n_S(R14)"])),
            proved=int(clean_num(row["proved_n"])),
        )
    except ValueError:
        pass

# ---- T3 严格双列（当前口径）----
T3_COLS_PARSE = T3_COLS


def parse_t3_row(raw):
    cells = split_row(raw)
    if len(cells) > len(T3_COLS):
        cells = cells[:len(T3_COLS) - 1] + ["|".join(cells[len(T3_COLS) - 1:])]
    if len(cells) < len(T3_COLS):
        cells += [""] * (len(T3_COLS) - len(cells))
    return cells


t3_panel = {}
t3_line = {}
for no, raw in T3["rows"][2:]:
    cells = parse_t3_row(raw)
    key = norm_cell(cells[0])
    sub = "TOTAL" if "TOTAL" in key else key
    t3_panel[sub] = {T3_COLS[i]: cells[i] for i in range(len(T3_COLS))}
    t3_line[sub] = no

for sub, row in t3_panel.items():
    try:
        panel_base.setdefault(sub, {})["proved_strict"] = int(clean_num(row["proved_strict_n"]))
    except (ValueError, KeyError):
        pass

t3_recalc = {}
for s in S_LIST:
    t3_recalc[s] = dict(atlas_n=tot[s]["atlas_n"], proved_n=tot[s]["proved"],
                        proved_strict_n=tot[s]["proved_strict"],
                        proved_strict_br=tot[s]["proved_strict_br"],
                        thr=thr_proved[s], nominal=nominal[s], strict=strict[s],
                        strict_br=strict_br[s])
t3_recalc["TOTAL"] = dict(atlas_n=sum_all["atlas_n"], proved_n=sum_all["proved"],
                          proved_strict_n=sum_all["proved_strict"],
                          proved_strict_br=sum_all["proved_strict_br"],
                          nominal_count=len(nominal_set), strict_count=len(strict_set),
                          strict_br_count=len(strict_br_set))

T2_SUBS = [k for k in t2_panel if k != "TOTAL"]
for sub in T2_SUBS + ["TOTAL"]:
    row = t2_panel[sub]
    rec = t2_recalc[sub]
    for col in ["atlas_n", "named_n(L)", "named_n_S(R14)", "named_n_S(strict)", "proved_n"]:
        pv = clean_num(row[col])
        rv = rec[col]
        if pv != str(rv):
            cls, ev = "算错", "定义明确（%s），与盘上重算不符" % col
            hits = []
            for bakname, bblocks in BACKUPS.items():
                v = bak_cell(bblocks, "named_n(L)" if col != "atlas_n" else "atlas_n", sub,
                             T2_COLS.index(col))
                if v is not None and clean_num(v) == pv:
                    hits.append(bakname)
            if hits:
                cls = "旧截面"
                ev += "；值与备份 %s 同格相同（落后于其后改动）" % ", ".join(hits[:3])
            base = panel_base.get(sub)
            flip = ""
            if base:
                fn, fs = sub_with({"named_n_S(R14)": "named_n_S(R14)", "proved_n": "proved_n",
                                   "atlas_n": "atlas_n"}.get(col, ""), rv, base)
                if fn or fs:
                    flip = "yes:翻转 %s %s" % (sub, "名义" if fn else "") + ("+严格" if fs else "")
            add_mismatch(t2_line[sub], T2_ID, sub, col, row[col], str(rv), cls, ev,
                         flip or "no")
    for pcol, src in PCT_COL.items():
        pv = row[pcol]
        n = rec[src]
        dn = rec["atlas_n"]
        raw = 100.0 * n / dn if dn else 0.0
        if not pct_ok(pv, raw):
            base = panel_base.get(sub)
            flip = ""
            if base:
                fn, fs = sub_with(src, n, base)
                flip = "yes:翻转 %s %s" % (sub, "名义" if fn else "") + ("+严格" if fs else "") if (fn or fs) else "no"
            add_mismatch(t2_line[sub], T2_ID, sub, pcol, pv,
                         "%.2f(实算 %.4f)" % (r2(raw), raw), "算错",
                         "百分数列定义明确（%s/%s，2 位小数）" % (src, "atlas_n"),
                         flip or "no")

# ---- T3 ----
for sub in T2_SUBS + ["TOTAL"]:
    row = t3_panel[sub]
    rec = t3_recalc[sub]
    # atlas_n / proved_n / proved_strict_n
    for col, rv in [("atlas_n", rec["atlas_n"]), ("proved_n", rec["proved_n"]),
                    ("proved_strict_n", rec["proved_strict_n"])]:
        pv = clean_num(row[col])
        if pv != str(rv):
            cls, ev = "算错", "定义明确（%s，卡片口径：语义串不含「未证」）" % col
            if col == "proved_strict_n" and pv == str(rec["proved_strict_br"]) and rec["proved_strict_br"] != rec["proved_strict_n"]:
                cls = "口径错"
                ev = ("面板值=「[未证]」字面排除的结果（strict_panel.py 实现），"
                      "与卡片口径（裸「未证」）不同；差异行清单见 REPORT §6")
            hits = []
            for bakname, bblocks in BACKUPS.items():
                v = bak_cell(bblocks, "proved_strict_n", sub, T3_COLS.index(col))
                if v is not None and clean_num(v) == pv:
                    hits.append(bakname)
            if hits and cls == "算错":
                cls = "旧截面"
                ev += "；值与备份 %s 同格相同（落后于其后改动）" % ", ".join(hits[:3])
            base = panel_base.get(sub)
            flip = ""
            if base and col in ("proved_n", "proved_strict_n", "atlas_n"):
                fn, fs = sub_with({"proved_n": "proved_n", "proved_strict_n": "proved_strict_n",
                                   "atlas_n": "atlas_n"}.get(col, ""), rv, base)
                if fn or fs:
                    flip = "yes:翻转 %s %s" % (sub, "名义" if fn else "") + ("+严格" if fs else "")
            add_mismatch(t3_line[sub], T3_ID, sub, col, row[col], str(rv), cls, ev,
                         flip or "yes:头条计数" if sub == "TOTAL" and col in ("proved_n", "proved_strict_n") else (flip or "no"))
    # pct
    for pcol, src, dn_col in [("proved_pct", "proved_n", "atlas_n"),
                              ("proved_strict_pct", "proved_strict_n", "atlas_n")]:
        pv = row[pcol]
        raw = 100.0 * rec[src] / rec["atlas_n"] if rec["atlas_n"] else 0.0
        if not pct_ok(pv, raw):
            add_mismatch(t3_line[sub], T3_ID, sub, pcol, pv,
                         "%.2f(实算 %.4f)" % (r2(raw), raw), "算错",
                         "百分数列定义明确", "no")
    # 门槛
    if sub != "TOTAL":
        pv = clean_num(row["门槛(50%)"])
        if pv != str(rec["thr"]):
            add_mismatch(t3_line[sub], T3_ID, sub, "门槛(50%)", row["门槛(50%)"], str(rec["thr"]),
                         "算错", "ceil(0.5n) 定义明确", "yes:门槛变化影响判定" )
    # 名义 / 严格
    if sub != "TOTAL":
        want_nom = "达标" if rec["nominal"] else "—"
        if norm_cell(row["名义"]) != want_nom:
            add_mismatch(t3_line[sub], T3_ID, sub, "名义", row["名义"], want_nom,
                         "算错", "D-38(A)/D-44 口径明确", "yes:名义达标判定本身")
        want_str = "达标" if rec["strict"] else "—"
        if norm_cell(row["严格"]) != want_str:
            add_mismatch(t3_line[sub], T3_ID, sub, "严格", row["严格"], want_str,
                         "算错", "D-44 严格口径明确", "yes:严格达标判定本身")
    else:
        pv = norm_cell(row["名义"])
        want = "%d/22" % rec["nominal_count"]
        if pv != want:
            add_mismatch(t3_line[sub], T3_ID, sub, "名义", row["名义"], want,
                         "算错", "头条计数", "yes:头条计数")
        pv = norm_cell(row["严格"])
        want = "%d/22" % rec["strict_count"]
        if pv != want:
            add_mismatch(t3_line[sub], T3_ID, sub, "严格", row["严格"], want,
                         "算错", "头条计数", "yes:头条计数")

# ---- T4（M47 时点快照表）----
def parse_t4_row(raw):
    cells = split_row(raw)
    if len(cells) > len(T4_COLS):
        cells = cells[:len(T4_COLS) - 1] + ["|".join(cells[len(T4_COLS) - 1:])]
    if len(cells) < len(T4_COLS):
        cells += [""] * (len(T4_COLS) - len(cells))
    return cells


t4_rows = []
for no, raw in T4["rows"][2:]:
    cells = parse_t4_row(raw)
    key = norm_cell(cells[0])
    t4_rows.append((no, key, {T4_COLS[i]: cells[i] for i in range(len(T4_COLS))}))

t4_current = {}
for s in S_LIST:
    t4_current[s] = dict(atlas_n=tot[s]["atlas_n"], **{
        "named_n(L)": tot[s]["named_L"], "named_n_S(R14)": tot[s]["named_S14"],
        "named_n_S(strict)": tot[s]["named_strict"], "proved_n": tot[s]["proved"]})

T4_HIST_DIFF = []   # 与现值不同、但与 M47 快照口径一致的合法历史差异
for no, key, row in t4_rows:
    sub = key
    if sub not in t4_current:
        add_mismatch(no, T4_ID, sub, "行标识", key, "S01–S21 之一", "无法判定",
                     "T4 只应有 S01–S21 行", "no")
        continue
    for col in ["atlas_n", "named_n(L)", "named_n_S(R14)", "named_n_S(strict)", "ceil(0.9n)", "ceil(0.5n)"]:
        pv = clean_num(row[col])
        if col == "ceil(0.9n)":
            rv = thr_named[sub]
        elif col == "ceil(0.5n)":
            rv = thr_proved[sub]
        else:
            rv = t4_current[sub][col]
        if pv != str(rv):
            add_mismatch(no, T4_ID, sub, col, row[col], str(rv), "算错",
                         "M47→现在 named/atlas_n 无文档化改动，快照值应与现值一致", "no")
    # proved：与 M47 快照重建值比
    pv = clean_num(row["proved_n"])
    exp47 = m47_expected.get(sub)
    if m47_reconstruction_ok and exp47 is not None:
        if pv == str(exp47):
            if pv != str(t4_current[sub]["proved_n"]):
                T4_HIST_DIFF.append((no, sub, pv, t4_current[sub]["proved_n"]))
        else:
            ev = ("M47 时点重建值=%d（PANEL L192 21 行小计 proved=1,400 + 文档化增量反推：%s）"
                  % (exp47, "; ".join(m47_evidence)))
            if pv == str(t4_current[sub]["proved_n"]):
                ev += "；面板格=当前盘上值（%s），疑被后续现值覆写" % pv
            add_mismatch(no, T4_ID, sub, "proved_n", row["proved_n"], str(exp47),
                         "算错", ev, "no")
    else:
        if pv != str(t4_current[sub]["proved_n"]):
            add_mismatch(no, T4_ID, sub, "proved_n", row["proved_n"],
                         "%d 或 M47 时点值(重建失败 sum=%d)" % (t4_current[sub]["proved_n"], m47_sum),
                         "无法判定", "M47 快照重建与 L192 小计 1,400 不符，时点真值存疑", "no")
    # 达标列
    want = "是" if nominal[sub] else "否"
    if norm_cell(row["达标"]) != want:
        add_mismatch(no, T4_ID, sub, "达标", row["达标"], want,
                     "算错", "M47 时点名义判定与当前一致（named/门槛未变，proved 变化均不跨门槛）", "no")

# ---------------------------------------------------------------- 5. 输出 recalc_all.tsv

recalc_all_path = SCRIPT_DIR / "recalc_all.tsv"
with open(recalc_all_path, "w", encoding="utf-8", newline="") as f:
    f.write("subsystem\tn\tnamed_L\tnamed_S14\tnamed_strict\tproved\tproved_strict\t"
            "thr_named\tthr_proved\tnominal_pass\tstrict_pass\n")
    for s in S_LIST:
        f.write("\t".join(str(x) for x in [
            s, tot[s]["atlas_n"], tot[s]["named_L"], tot[s]["named_S14"], tot[s]["named_strict"],
            tot[s]["proved"], tot[s]["proved_strict"], thr_named[s], thr_proved[s],
            nominal[s], strict[s]]) + "\n")
    f.write("\t".join(str(x) for x in [
        "TOTAL", sum_all["atlas_n"], sum_all["named_L"], sum_all["named_S14"],
        sum_all["named_strict"], sum_all["proved"], sum_all["proved_strict"],
        "-", "-", "%d/22" % len(nominal_set), "%d/22" % len(strict_set)]) + "\n")

# ---------------------------------------------------------------- 6. 输出 mismatches.tsv

mm_path = SCRIPT_DIR / "mismatches.tsv"
mismatches.sort(key=lambda m: (m["line"], m["col"]))
with open(mm_path, "w", encoding="utf-8", newline="") as f:
    f.write("panel_line\ttable_id\tsubsystem\tcolumn\tpanel_value\trecalc_value\tclass\taffects_dod\n")
    for m in mismatches:
        f.write("\t".join([str(m["line"]), m["tid"], m["sub"], m["col"], m["panel"],
                           m["recalc"], m["cls"], m["affects"]]) + "\n")

# ---------------------------------------------------------------- 7. REPORT.md

cls_count = Counter(m["cls"] for m in mismatches)
flip_cells = [m for m in mismatches if m["affects"].startswith("yes:翻转")]
flips = len(flip_cells)

R = []
A = R.append
A("# PANEL_CHK / REPORT — PANEL.md 全量数值一致性普查")
A("")
A("- 普查对象：`lead/next_re_20261117_r14/COVERAGE/PANEL.md`（只读，未改动）")
A("- 复跑：`python lead\\next_re_20261117_r14\\COVERAGE\\PANEL_CHK\\recalc.py`（本目录四件套全部由该脚本一次产出）")
A("- 结论速览：**不符 %d 处**（%s）；**会翻转达标判定的格子 %d 个**（详见 §7）。"
  % (len(mismatches),
     "、".join("%s %d" % (k, v) for k, v in sorted(cls_count.items())) or "无",
     flips))
A("")
A("## 一、输入与指纹")
A("")
A("| 文件 | 角色 | 指纹/规模 |")
A("|---|---|---|")
A("| COVERAGE/coverage.tsv | 行级真值 | `%s`，数据行 %d（表头 1 行）|" % (sha256(COV), cov_rows_raw))
A("| W130_atlas/function_atlas.tsv | atlas 分母 | `%s`，数据行 %d |" % (sha256(ATLAS), atlas_rows))
A("| COVERAGE/PANEL.md | 被普查对象 | `%s`，%d 行 |" % (sha256(PANEL), len(panel_lines)))
A("| P0_INITTERM/INITTERM_TABLE.tsv | B 分母前提核对 | 数据行 %d |" % len(interm_targets))
A("")
A("## 二、口径（照任务卡逐条实现）")
A("")
A("- `n` = subsystem 且 entry ∈ atlas（atlas `entry` 列为小写十六进制，比对统一 `%08X` 大写归一）")
A("- `proved` = 上述行中 grade `== [已证]`")
A("- `named_L` = name 非空且不以 `sub_` 开头")
A("- `named_S(R14)` = `named_L` 排除 `::sub_[0-9A-Fa-f]+$`（任意长度十六进制，M53 明确）")
A("- `named_strict` = `named_S(R14)` 排除 `::slotN` / `::vslotN`（实现为 `::v?slot\\d+$`，与 RULING_R15 work/strict_panel.py 一致）")
A("- `proved_strict` = proved 中语义串不含「未证」——**卡片口径（裸子串）**；"
  "同时计算「[未证]」带括号变体（= strict_panel.py 实现）作对照，差异见 §6/§8")
A("- 门槛 `ceil(0.9n)` / `ceil(0.5n)`；`nominal_pass = named_S(R14)≥ceil(0.9n) ∧ proved≥ceil(0.5n)`；"
  "`strict_pass = nominal_pass ∧ proved_strict≥ceil(0.5n)`")
A("- S22 不参与达标排名（面板规则）；其布尔值仍列出（恒 False）")
A("")
A("## 三、盘上基础核对")
A("")
A("- coverage 数据行 **%d**（面板 C 口径/行数声明 18,498：%s）；畸形行 %d" %
  (cov_rows_raw, "一致" if cov_rows_raw == 18498 else "**不一致**", cov_malformed))
A("- grade 直方图：%s" % "，".join("`%s` %d" % (k, v) for k, v in sorted(grade_hist.items(), key=lambda x: -x[1])))
A("- 第 8 列 conflict==1：%d（M52 后声明 254：%s）" % (conflict1, "一致" if conflict1 == 254 else "**变化**"))
A("- atlas 数据行 **%d**；大小写归一后唯一 entry %d，重复 %d 个%s"
  % (atlas_rows, len(atlas_set), len(atlas_dup), ("：" + ", ".join(atlas_dup)) if atlas_dup else ""))
A("- atlas entry 全部在 coverage：%s（atlas∩coverage = %d）"
  % ("是" if len(interm_missing := atlas_set - cov_entries) == 0 else "否，缺 %d 个：%s" % (len(interm_missing), sorted(interm_missing)[:5]), sum_all["atlas_n"]))
A("- coverage 在 atlas 外：%d 行（18,498−12,916=5,582 预期）；atlas 内非 S\\d\\d 的 subsystem：%s"
  % (cov_rows_raw - sum_all["atlas_n"], dict(odd_sub_atlas) if odd_sub_atlas else "无"))
A("- INITTERM target %d 个，其中在 coverage %d 个（面板声明 3,944 全在：%s）；"
  "coverage 中 `initterm_thunk_NNNN` 名 %d 行（声明 3,922）；"
  "B 重算 = %d − %d = **%d**（面板 14,554）"
  % (len(interm_targets), len(interm_in_cov),
     "一致" if len(interm_in_cov) == len(interm_targets) == 3944 else "**不符**",
     initterm_named_rows, cov_rows_raw, len(interm_in_cov), B_recalc))
A("- 全表 `[已证]` **%d**；其中 atlas 内 **%d**、atlas 外 %d" % (all_proved, all_proved_atlas, all_proved - all_proved_atlas))
A("")
A("## 四、表清单与逐行枚举（行号 = PANEL.md 1-based）")
A("")
A("| 表 | 行号范围 | 数据行 | 说明 |")
A("|---|---|---|---|")
A("| %s | L%d–L%d | %d | 三分母（A/B/C/行数/已证两数）|" % (T1_ID, T1["start"], T1["end"], len(T1["rows"]) - 2))
A("| %s | L%d–L%d | %d | 主面板 S01–S22 + TOTAL（9 数字列 + 差距说明）|" % (T2_ID, T2["start"], T2["end"], len(T2["rows"]) - 2))
A("| %s | L%d–L%d | %d | 严格双列 S01–S22 + TOTAL |" % (T3_ID, T3["start"], T3["end"], len(T3["rows"]) - 2))
A("| %s | L%d–L%d | %d | M47 全表同步快照（历史截面，S01–S21）|" % (T4_ID, T4["start"], T4["end"], len(T4["rows"]) - 2))
A("")
A("其余 PIPE 开头行块：%s（无则写「无」）。"
  % ("; ".join("L%d–L%d:%s" % (b["start"], b["end"], b["header"][0][:20]) for b in blocks
               if b not in (T1, T2, T3, T4)) or "无"))
A("")
for tid, blk, cols in ((T1_ID, T1, None), (T2_ID, T2, T2_COLS), (T3_ID, T3, T3_COLS), (T4_ID, T4, T4_COLS)):
    A("### %s 逐行" % tid)
    A("")
    for no, raw in blk["rows"][2:]:
        cells = split_row(raw)
        key = norm_cell(cells[0]) if cells else ""
        A("- L%d：%s" % (no, key))
    A("")
A("## 五、逐格比对结果")
A("")
A("### T1 三分母表")
A("")
A("| 行 | 格 | 面板值 | 重算值 | 判定 |")
A("|---|---|---:|---:|---|")
for no, col, panel_raw, panel_num, recalc_num in t1_cells:
    ok = panel_num == recalc_num
    A("| L%d | %s | %s | %d | %s |" % (no, col, panel_raw, recalc_num,
                                        "一致" if ok else "**不符（%s）**" % next(m["cls"] for m in mismatches if m["line"] == no and m["col"] == col)))
A("")
A("### T2 主面板（当前口径，格级）")
A("")
n_ok2 = 0
diff_rows2 = []
for sub in T2_SUBS + ["TOTAL"]:
    row = t2_panel[sub]
    rec = t2_recalc[sub]
    bad = []
    for col in ["atlas_n", "named_n(L)", "named_n_S(R14)", "named_n_S(strict)", "proved_n"]:
        if clean_num(row[col]) != str(rec[col]):
            bad.append((col, row[col], rec[col]))
    for pcol, src in PCT_COL.items():
        raw = 100.0 * rec[src] / rec["atlas_n"] if rec["atlas_n"] else 0.0
        if not pct_ok(row[pcol], raw):
            bad.append((pcol, row[pcol], "%.2f" % r2(raw)))
    if bad:
        diff_rows2.append((sub, t2_line[sub], bad))
    else:
        n_ok2 += 1
A("- 逐格一致 %d/%d 行；不一致行 %d 张：" % (n_ok2, len(T2_SUBS) + 1, len(diff_rows2)))
for sub, no, bad in diff_rows2:
    A("  - L%d `%s`：%s" % (no, sub, "；".join("%s 面板=%s 重算=%s" % b for b in bad)))
if not diff_rows2:
    A("  - （无）")
A("")
A("### T3 严格双列表（卡片口径）")
A("")
n_ok3 = 0
diff_rows3 = []
for sub in T2_SUBS + ["TOTAL"]:
    row = t3_panel[sub]
    rec = t3_recalc[sub]
    bad = []
    for col, rv in [("atlas_n", rec["atlas_n"]), ("proved_n", rec["proved_n"]),
                    ("proved_strict_n", rec["proved_strict_n"])]:
        if clean_num(row[col]) != str(rv):
            bad.append((col, row[col], rv))
    for pcol, src in [("proved_pct", "proved_n"), ("proved_strict_pct", "proved_strict_n")]:
        raw = 100.0 * rec[src] / rec["atlas_n"] if rec["atlas_n"] else 0.0
        if not pct_ok(row[pcol], raw):
            bad.append((pcol, row[pcol], "%.2f" % r2(raw)))
    if sub != "TOTAL":
        if clean_num(row["门槛(50%)"]) != str(rec["thr"]):
            bad.append(("门槛(50%)", row["门槛(50%)"], rec["thr"]))
        if norm_cell(row["名义"]) != ("达标" if rec["nominal"] else "—"):
            bad.append(("名义", row["名义"], "达标" if rec["nominal"] else "—"))
        if norm_cell(row["严格"]) != ("达标" if rec["strict"] else "—"):
            bad.append(("严格", row["严格"], "达标" if rec["strict"] else "—"))
    else:
        if norm_cell(row["名义"]) != "%d/22" % rec["nominal_count"]:
            bad.append(("名义", row["名义"], "%d/22" % rec["nominal_count"]))
        if norm_cell(row["严格"]) != "%d/22" % rec["strict_count"]:
            bad.append(("严格", row["严格"], "%d/22" % rec["strict_count"]))
    if bad:
        diff_rows3.append((sub, t3_line[sub], bad))
    else:
        n_ok3 += 1
A("- 逐格一致 %d/%d 行；不一致行 %d 张：" % (n_ok3, len(T2_SUBS) + 1, len(diff_rows3)))
for sub, no, bad in diff_rows3:
    A("  - L%d `%s`：%s" % (no, sub, "；".join("%s 面板=%s 重算=%s" % b for b in bad)))
if not diff_rows3:
    A("  - （无）")
A("")
A("### T4 M47 同步快照表（历史截面，按 M47 时点口径核对）")
A("")
A("- M47 时点重建：现值 − 文档化增量（%s）＝逐行 M47 应有值；"
  "重建 S01–S21 proved 合计 = %d，与该节自记小计 1,400 %s → 重建%s"
  % ("；".join(m47_evidence), m47_sum,
     "一致" if m47_reconstruction_ok else "不一致", "可信" if m47_reconstruction_ok else "不可信"))
A("- 与现值不同、但与 M47 时点一致的合法历史差异（**不计不符**）：%s"
  % ("；".join("L%d %s proved %s(快照) vs %s(现值)" % h for h in T4_HIST_DIFF) or "无"))
A("")
A("## 六、不符清单（= mismatches.tsv，含依据）")
A("")
if mismatches:
    A("| 行 | 表 | 子系统 | 列 | 面板值 | 重算值 | 类别 | 依据 | 影响 |")
    A("|---|---|---|---|---:|---:|---|---|---|")
    for m in mismatches:
        A("| L%d | %s | %s | %s | %s | %s | **%s** | %s | %s |"
          % (m["line"], m["tid"].split("@")[0], m["sub"], m["col"], m["panel"], m["recalc"],
             m["cls"], m["evidence"], m["affects"]))
else:
    A("（无不符）")
A("")
A("类别计数：%s；总计 **%d**。"
  % ("、".join("%s=%d" % (k, v) for k, v in sorted(cls_count.items())) or "无", len(mismatches)))
A("")
if any(m["cls"] == "口径错" for m in mismatches):
    A("**口径错差异行清单**（面板按「[未证]」字面排除、卡片口径为裸「未证」）：")
    for s in S_LIST:
        b = tot[s]["proved_strict_br"] - tot[s]["proved_strict"]
        if b:
            A("- %s：两种口径差 %d 行" % (s, b))
    A("")
A("## 七、达标判定影响（会翻转的格子）")
A("")
if flips:
    A("会翻转达标判定的格子 **%d 个**：" % flips)
    for m in flip_cells:
        A("- L%d `%s` %s：%s" % (m["line"], m["sub"], m["col"], m["affects"]))
else:
    A("**0 个**——没有任何一格的更正会翻转任何子系统的名义/严格达标判定或头条计数。")
A("")
A("判定边缘（余量 ≤5）供参考：")
A("")
A("| 子系统 | named_S/门槛 | proved/门槛 | proved_strict/门槛 | 名义 | 严格 |")
A("|---|---|---|---|---|---|")
for s in S_LIST:
    if s == "S22":
        continue
    m_n = tot[s]["named_S14"] - thr_named[s]
    m_p = tot[s]["proved"] - thr_proved[s]
    m_s = tot[s]["proved_strict"] - thr_proved[s]
    if min(m_n, m_p, m_s) <= 5:
        A("| %s | %d/%d（%+d） | %d/%d（%+d） | %d/%d（%+d） | %s | %s |"
          % (s, tot[s]["named_S14"], thr_named[s], m_n, tot[s]["proved"], thr_proved[s], m_p,
             tot[s]["proved_strict"], thr_proved[s], m_s,
             "达标" if nominal[s] else "否", "达标" if strict[s] else "否"))
A("")
A("## 八、头条核对")
A("")
A("| 口径 | 重算 | 面板 TOTAL 行现记 | 一致？ |")
A("|---|---|---|---|")
A("| 名义达标（named_S(R14)≥ceil(0.9n) ∧ proved≥ceil(0.5n)） | **%d/22：%s** | 3/22（S15/S16/S17） | %s |"
  % (len(nominal_set), "/".join(nominal_set) or "无", "一致" if len(nominal_set) == 3 and nominal_set == ["S15", "S16", "S17"] else "**不一致**"))
A("| 严格达标（再加 proved_strict≥ceil(0.5n)，卡片口径） | **%d/22：%s** | 1/22（仅 S17） | %s |"
  % (len(strict_set), "/".join(strict_set) or "无", "一致" if len(strict_set) == 1 and strict_set == ["S17"] else "**不一致**"))
A("| 对照：proved_strict 用「[未证]」字面口径 | %d/22：%s | — | — |"
  % (len(strict_br_set), "/".join(strict_br_set) or "无"))
A("")
A("TOTAL 重算：atlas_n %d、named_L %d、named_S(R14) %d、named_strict %d、proved %d、"
  "proved_strict %d（[未证] 字面口径 %d）"
  % (sum_all["atlas_n"], sum_all["named_L"], sum_all["named_S14"], sum_all["named_strict"],
     sum_all["proved"], sum_all["proved_strict"], sum_all["proved_strict_br"]))
A("")
A("## 九、结论")
A("")
A("- PANEL.md 四张含数值表共 %d 个数据行全部枚举；可由 coverage.tsv + atlas 推导的格子逐格重算。"
  % (len(T1["rows"]) - 2 + len(T2["rows"]) - 2 + len(T3["rows"]) - 2 + len(T4["rows"]) - 2))
A("- 不符 %d 处（%s）；会翻转达标判定的格子 %d 个；对外头条影响：%s。"
  % (len(mismatches),
     "、".join("%s %d" % (k, v) for k, v in sorted(cls_count.items())) or "无",
     flips,
     ("；".join(sorted(set(m["affects"] for m in mismatches if m["affects"].startswith("yes:")))) or "无")))
A("- T4 的 S02/S13/S17/S19 proved 与现值不同属 M47 时点合法快照（重建验证），不计不符；"
  "T4 的 S09/S15/S16 proved 被后续现值覆写属快照污染。")
A("- 本卡未改 PANEL.md / coverage.tsv / R14_COMMON.md / 台账；只写 PANEL_CHK\\ 四件。")
A("")

(SCRIPT_DIR / "REPORT.md").write_text("\n".join(R), encoding="utf-8")

# ---------------------------------------------------------------- 8. 控制台摘要
print("coverage 行数=%d atlas 行数=%d atlas∩cov=%d" % (cov_rows_raw, atlas_rows, sum_all["atlas_n"]))
print("grade:", dict(grade_hist))
print("全表[已证]=%d atlas内[已证]=%d conflict1=%d" % (all_proved, all_proved_atlas, conflict1))
print("B 重算=%d (interm targets %d, in cov %d)" % (B_recalc, len(interm_targets), len(interm_in_cov)))
print("M47 重建 sum(S01-S21 proved)=%d vs prose 1400 -> %s" % (m47_sum, m47_reconstruction_ok))
print("nominal:", nominal_set, "strict:", strict_set, "strict_br:", strict_br_set)
print("TOTAL proved_strict 卡片口径=%d / [未证]字面=%d" % (sum_all["proved_strict"], sum_all["proved_strict_br"]))
print("mismatches=%d %s" % (len(mismatches), dict(cls_count)))
for m in mismatches:
    print("  L%-4d %-14s %-5s %-18s %s -> %s [%s] %s" % (
        m["line"], m["tid"].split("@")[0], m["sub"], m["col"], m["panel"], m["recalc"], m["cls"], m["affects"]))
print("flips=%d" % flips)
print("T4 hist diff:", T4_HIST_DIFF)
