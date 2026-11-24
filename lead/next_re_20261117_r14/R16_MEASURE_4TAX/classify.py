#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R16-MEASURE-4TAX / classify.py

用途：对 COVERAGE/coverage.tsv 中 grade == "[已证]" 的全部行，按第 4 列 one_line_semantics
的「④ 已成文」形态做互斥分桶。只读 coverage.tsv，只写本卡产物目录。

用法：
  python classify.py                      # 默认输入/输出（本卡约定路径）
  python classify.py --tsv <path> --outdir <dir>
  python classify.py --dump-sample        # 额外打印 sample18 候选（供人工判读，≤18 行）

设计原则：
  * 桶互斥，优先级从高到低：B_SLOT_WITNESS > B_DIRECT_SITES > B_INSTALL_ONLY >
    B_LABEL_ONLY > B_OTHER > NONE
  * B_LABEL_ONLY 必须在所有「真 ④ 形态」桶之后判（既有真 ④ 又顺带提 ③b④ 的行不能被
    错归为标签行）
  * 不判定 grade、不写 ④ 正文、不改任何输入文件
"""
import argparse
import os
import re
import sys
from collections import Counter, OrderedDict

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_TSV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
DEFAULT_SNAPSHOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "coverage_snapshot.tsv")
DEFAULT_OUT = os.path.dirname(os.path.abspath(__file__))

GRADE_PROVED = "[已证]"

# ---------------------------------------------------------------- 最终采用的正则
# 逐条列在 REPORT.md，改动请同步。
RE_FOUR = re.compile(r"④")
RE_SLOT = re.compile(r"④\s*活表槽位见证")                      # 口径 B 的字面形态
RE_DIRECT_SITE_COUNT = re.compile(r"④\s*\d+\s*个\s*E8\s*直调站点")
RE_DIRECT_SITE_ANY = re.compile(r"④[^。；]{0,20}直调")           # 卡面建议的宽松直调判据
RE_DIRECT_E8 = re.compile(r"④\s*direct\s*E8")                  # 英文变体 "④ direct E8@..."
RE_INSTALL_KW = re.compile(r"活\s*vt|活vt|安装点|构造安装")        # 行级共现（按卡面字面）
RE_INSTALL_PROX = re.compile(r"④[^。；]{0,24}(?:活\s*vt|活vt|安装点|构造安装)")
RE_INSTALL_PROX_WIDE = re.compile(r"④[^。；]{0,48}(?:活\s*vt|活vt|安装点|构造安装)")
RE_LABEL_3B4 = re.compile(r"③b④")

# §2.3 交叉核对用的独立判据（与分桶无关）
RE_VT_EQ = re.compile(r"vt\s*=")
RE_SLOT_TABLE_POINT = re.compile(r"装表点")

# B_OTHER 内部形态（仅作报告用，不参与互斥分桶）
RE_OTHER_UPGRADE = re.compile(r"④[^。；]{0,6}升级句")
RE_OTHER_COM = re.compile(r"④[^。；]{0,6}活\s*COM\s*类对象")
RE_OTHER_DIFFSRC = re.compile(r"④[^。；]{0,6}不同源")
RE_OTHER_CLASSMATCH = re.compile(r"④[^。；]{0,6}表属类与行名类一致")
RE_OTHER_ANCHOR = re.compile(r"④[^。；]{0,12}锚点不在析构器")
RE_OTHER_VTABLEDISPATCH = re.compile(r"④[^。；]{0,12}活\s*虚表派发")

BUCKETS = [
    "B_SLOT_WITNESS",
    "B_DIRECT_SITES",
    "B_INSTALL_ONLY",
    "B_LABEL_ONLY",
    "B_OTHER",
    "NONE",
]


def classify(col4):
    """返回 (bucket, hits)。hits 记录支撑该判定的正则名，便于复核。"""
    if not RE_FOUR.search(col4):
        return "NONE", []
    if RE_SLOT.search(col4):
        return "B_SLOT_WITNESS", ["RE_SLOT"]
    hits = []
    if RE_DIRECT_SITE_COUNT.search(col4):
        hits.append("RE_DIRECT_SITE_COUNT")
    if RE_DIRECT_E8.search(col4):
        hits.append("RE_DIRECT_E8")
    if RE_DIRECT_SITE_ANY.search(col4):
        hits.append("RE_DIRECT_SITE_ANY")
    if hits:
        return "B_DIRECT_SITES", hits
    if RE_INSTALL_KW.search(col4):
        return "B_INSTALL_ONLY", ["RE_INSTALL_KW"]
    if RE_LABEL_3B4.search(col4):
        return "B_LABEL_ONLY", ["RE_LABEL_3B4"]
    return "B_OTHER", []


def other_subform(col4):
    for name, rx in [
        ("升级句", RE_OTHER_UPGRADE),
        ("活 COM 类对象", RE_OTHER_COM),
        ("不同源", RE_OTHER_DIFFSRC),
        ("表属类与行名类一致", RE_OTHER_CLASSMATCH),
        ("锚点不在析构器", RE_OTHER_ANCHOR),
        ("活虚表派发", RE_OTHER_VTABLEDISPATCH),
    ]:
        if rx.search(col4):
            return name
    return "其它自由表述"


def load_rows(tsv):
    """表头实际是逗号分隔（与卡面描述不同），数据行是 TAB 分隔 → 一律按 TAB 切、跳过第 1 行。"""
    raw = open(tsv, encoding="utf-8").read().split("\n")
    rows = []
    for i, line in enumerate(raw):
        if i == 0 or not line.strip():
            continue
        f = line.split("\t")
        if len(f) != 8:
            raise SystemExit("unexpected column count %d at data line %d" % (len(f), i))
        rows.append(f)
    return rows


def excerpt(col4, radius=60):
    """围绕第一个 ④ 取 ≤120 字上下文（前 radius 后 radius），两端加省略标记。"""
    m = RE_FOUR.search(col4)
    if not m:
        return col4[:120]
    s = max(0, m.start() - radius)
    e = min(len(col4), m.end() + radius + 20)
    out = col4[s:e].replace("\t", " ")
    return ("…" if s > 0 else "") + out + ("…" if e < len(col4) else "")


def sample_positions(n, k):
    """桶内按 entry 升序，取第 1、最后 1、中间等距 k-2 个；不足 k 全取。"""
    if n == 0:
        return []
    if n <= k:
        return list(range(n))
    idx = {0, n - 1}
    inner = k - 2
    for j in range(1, inner + 1):
        idx.add(round(j * (n - 1) / (inner + 1)))
    return sorted(idx)


SAMPLE_ALLOC = OrderedDict([
    ("B_SLOT_WITNESS", 4),
    ("B_DIRECT_SITES", 3),
    ("B_INSTALL_ONLY", 3),
    ("B_LABEL_ONLY", 4),
    ("B_OTHER", 3),
    ("NONE", 1),
])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", default=None,
                    help="输入 TSV；默认用本目录 coverage_snapshot.tsv（若有），否则用 live coverage.tsv")
    ap.add_argument("--outdir", default=DEFAULT_OUT)
    ap.add_argument("--dump-sample", action="store_true")
    ap.add_argument("--sample-only", action="store_true")
    args = ap.parse_args()

    tsv = args.tsv or (DEFAULT_SNAPSHOT if os.path.exists(DEFAULT_SNAPSHOT) else DEFAULT_TSV)
    rows = load_rows(tsv)
    proved = [r for r in rows if r[4].strip() == GRADE_PROVED]
    denom = len(proved)

    # ------------------------------------------------ 输入来源指纹（可复跑的关键）
    import hashlib
    st = os.stat(tsv)
    h = hashlib.sha256(open(tsv, "rb").read()).hexdigest()
    print("=== 输入指纹 ===")
    print("file   :", tsv)
    print("sha256 :", h)
    print("size   :", st.st_size, "bytes | mtime:", __import__("time").strftime(
        "%Y-%m-%d %H:%M:%S", __import__("time").localtime(st.st_mtime)))
    print("rows   :", len(rows), "data rows | [已证] =", denom)

    buckets_rows = OrderedDict((b, []) for b in BUCKETS)
    bucket_hits = Counter()
    for r in proved:
        entry, subsystem, col4 = r[0], r[1], r[3]
        b, hits = classify(col4)
        buckets_rows[b].append({
            "entry": entry,
            "subsystem": subsystem,
            "grade": r[4].strip(),
            "col4": col4,
            "has_slot": bool(RE_SLOT.search(col4)),
            "has_vt_eq": bool(RE_VT_EQ.search(col4)),
            "has_install": bool(RE_INSTALL_KW.search(col4)),
            "has_slot_table_point": bool(RE_SLOT_TABLE_POINT.search(col4)),
            "len": len(col4),
        })
        for h in hits:
            bucket_hits[h] += 1

    for b in BUCKETS:
        buckets_rows[b].sort(key=lambda x: x["entry"])

    # ------------------------------------------------ buckets.tsv（1,654 行全量）
    os.makedirs(args.outdir, exist_ok=True)
    bp = os.path.join(args.outdir, "buckets.tsv")
    with open(bp, "w", encoding="utf-8", newline="\n") as f:
        f.write("entry\tsubsystem\tgrade\tbucket\thas_slot_witness\thas_vt_addr\thas_install_site\tcol4_len\n")
        written = 0
        for b in BUCKETS:
            for x in buckets_rows[b]:
                f.write("%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\n" % (
                    x["entry"], x["subsystem"], x["grade"], b,
                    1 if x["has_slot"] else 0,
                    1 if x["has_vt_eq"] else 0,
                    1 if x["has_install"] else 0,
                    x["len"],
                ))
                written += 1
    assert written == denom, (written, denom)

    # ------------------------------------------------ 分桶计数
    print("=== 六桶计数（分母 %d 行 [已证]） ===" % denom)
    bstar = 0
    for b in BUCKETS:
        n = len(buckets_rows[b])
        if b != "NONE":
            bstar += n
        print("%-16s %5d  %6.2f%%" % (b, n, 100.0 * n / denom))
    print("%-16s %5d  %6.2f%%" % ("B_* 五桶合计", bstar, 100.0 * bstar / denom))
    print("%-16s %5d  %6.2f%%" % ("NONE", len(buckets_rows["NONE"]),
                                  100.0 * len(buckets_rows["NONE"]) / denom))
    print("口径 A（含 ④，即 5 个 B_* 之和） =", bstar, " 口径 B（B_SLOT_WITNESS） =",
          len(buckets_rows["B_SLOT_WITNESS"]))
    print("正则命中计数：", dict(bucket_hits))

    # ------------------------------------------------ §2.3 交叉核对
    print("\n=== §2.3 交叉核对 ===")
    slot = buckets_rows["B_SLOT_WITNESS"]
    print("B_SLOT_WITNESS n=%d，含 `vt=` = %d，含 `装表点` = %d，两者都含 = %d，两者都不含 = %d" % (
        len(slot),
        sum(1 for x in slot if x["has_vt_eq"]),
        sum(1 for x in slot if x["has_slot_table_point"]),
        sum(1 for x in slot if x["has_vt_eq"] and x["has_slot_table_point"]),
        sum(1 for x in slot if not x["has_vt_eq"] and not x["has_slot_table_point"]),
    ))
    lab = buckets_rows["B_LABEL_ONLY"]
    print("B_LABEL_ONLY n=%d，含 `vt=` = %d，含 `装表点` = %d，含 `vt=` 或 `装表点` = %d" % (
        len(lab),
        sum(1 for x in lab if x["has_vt_eq"]),
        sum(1 for x in lab if x["has_slot_table_point"]),
        sum(1 for x in lab if x["has_vt_eq"] or x["has_slot_table_point"]),
    ))
    inst = buckets_rows["B_INSTALL_ONLY"]
    print("B_INSTALL_ONLY n=%d；安装类关键字与 ④ 邻近(≤24字) = %d，≤48字 = %d，行级共现但 >48字 = %d" % (
        len(inst),
        sum(1 for x in inst if RE_INSTALL_PROX.search(x["col4"])),
        sum(1 for x in inst if RE_INSTALL_PROX_WIDE.search(x["col4"])),
        sum(1 for x in inst if not RE_INSTALL_PROX_WIDE.search(x["col4"])),
    ))
    # 敏感性：安装点词汇的三种口径（V1=卡面字面；V2=+装活/装vt；V3=+④..构造器）
    RE_V2_EXTRA = re.compile(r"装活|装\s*vt")
    RE_V3_CTOR = re.compile(r"④[^。；]{0,12}构造器")

    def bucket_with(extra_install):
        alt = Counter()
        for r in proved:
            c = r[3]
            if not RE_FOUR.search(c):
                alt["NONE"] += 1
            elif RE_SLOT.search(c):
                alt["B_SLOT_WITNESS"] += 1
            elif RE_DIRECT_SITE_COUNT.search(c) or RE_DIRECT_E8.search(c) or RE_DIRECT_SITE_ANY.search(c):
                alt["B_DIRECT_SITES"] += 1
            elif RE_INSTALL_KW.search(c) or (extra_install is not None and extra_install.search(c)):
                alt["B_INSTALL_ONLY"] += 1
            elif RE_LABEL_3B4.search(c):
                alt["B_LABEL_ONLY"] += 1
            else:
                alt["B_OTHER"] += 1
        return alt

    print("\n=== 安装点词汇口径敏感性（V1 为主口径） ===")
    for name, rx in [("V1 卡面字面(活 vt/安装点/构造安装)", None),
                     ("V2 +装活/装 vt", RE_V2_EXTRA),
                     ("V3 +④..构造器(≤12字)", re.compile(r"装活|装\s*vt|④[^。；]{0,12}构造器"))]:
        v = bucket_with(rx)
        print("%-30s %s" % (name, " ".join("%s=%d" % (b, v[b]) for b in BUCKETS)))

    # 敏感性：INSTALL 改用 24 字邻近判据
    alt = Counter()
    for r in proved:
        c = r[3]
        if not RE_FOUR.search(c):
            alt["NONE"] += 1
        elif RE_SLOT.search(c):
            alt["B_SLOT_WITNESS"] += 1
        elif RE_DIRECT_SITE_COUNT.search(c) or RE_DIRECT_E8.search(c) or RE_DIRECT_SITE_ANY.search(c):
            alt["B_DIRECT_SITES"] += 1
        elif RE_INSTALL_PROX.search(c):
            alt["B_INSTALL_ONLY"] += 1
        elif RE_LABEL_3B4.search(c):
            alt["B_LABEL_ONLY"] += 1
        else:
            alt["B_OTHER"] += 1
    print("敏感性（INSTALL 改 24 字邻近）：" +
          " ".join("%s=%d" % (b, alt[b]) for b in BUCKETS))
    # NONE 负控制
    none = buckets_rows["NONE"]
    print("NONE 负控制：n=%d，其中含 ④ 的行 = %d（应为 0）；含 `vt=` 的行 = %d" % (
        len(none), sum(1 for x in none if RE_FOUR.search(x["col4"])),
        sum(1 for x in none if x["has_vt_eq"])))

    # ------------------------------------------------ B_OTHER 内部形态（仅报告）
    print("\n=== B_OTHER 内部形态（仅报告，不计入互斥分桶） ===")
    sub = Counter(other_subform(x["col4"]) for x in buckets_rows["B_OTHER"])
    for k, v in sub.most_common():
        print("%-22s %4d" % (k, v))

    print("\n=== 其它全表参照（不参与分桶） ===")
    print("含 ③b④ 的 [已证] 行 =", sum(1 for r in proved if RE_LABEL_3B4.search(r[3])))
    print("含 ②④ 的 [已证] 行 =", sum(1 for r in proved if "②④" in r[3]))
    print("含 `升级句` 的 [已证] 行 =", sum(1 for r in proved if "升级句" in r[3]))

    # ------------------------------------------------ 结构性参照（不参与分桶）
    print("\n=== 结构性参照（不参与互斥分桶，供报告引用） ===")
    lab3 = [r for r in proved if RE_LABEL_3B4.search(r[3])]
    print("含 `③b④` 的 [已证] 行 =", len(lab3), "→ 六桶分布:",
          dict(Counter(classify(r[3])[0] for r in lab3)))
    lab2 = [r for r in proved if "②④" in r[3]]
    print("含 `②④` 的 [已证] 行 =", len(lab2), "→ 六桶分布:",
          dict(Counter(classify(r[3])[0] for r in lab2)),
          "| 其中含 `活表槽位见证` =", sum(1 for r in lab2 if "活表槽位见证" in r[3]),
          "含 `direct` =", sum(1 for r in lab2 if RE_DIRECT_E8.search(r[3])))
    up = set(r[0] for r in proved if "升级句" in r[3])
    slot_ids = set(x["entry"] for x in buckets_rows["B_SLOT_WITNESS"])
    print("含 `升级句` 的 [已证] 行 =", len(up), "| 与 B_SLOT_WITNESS 集合相等 =", up == slot_ids)
    dcombo = Counter()
    for x in buckets_rows["B_DIRECT_SITES"]:
        c = x["col4"]
        dcombo["N个E8直调站点" if RE_DIRECT_SITE_COUNT.search(c) else
               ("④ direct E8" if RE_DIRECT_E8.search(c) else "松散直调")] += 1
    print("B_DIRECT_SITES 判据来源:", dict(dcombo))
    print("④ 出现次数分布:", dict(sorted(Counter(r[3].count("④") for r in proved).items())))

    # ------------------------------------------------ sample18 候选
    picks = []
    for b, k in SAMPLE_ALLOC.items():
        lst = buckets_rows[b]
        for i in sample_positions(len(lst), k):
            picks.append((b, i, lst[i]))
    picks = picks[:18]
    print("\n=== sample 候选 %d 行（桶内按 entry 升序取首/末/等距） ===" % len(picks))
    for b, i, x in picks:
        print("%s\t%s\t[%d/%d]" % (x["entry"], b, i + 1, len(buckets_rows[b])))
        if args.dump_sample:
            print("    EXCERPT:", excerpt(x["col4"]))

    if args.sample_only:
        for b, i, x in picks:
            print("\nENTRY=%s BUCKET=%s IDX=%d/%d" % (x["entry"], b, i + 1, len(buckets_rows[b])))
            print("EXCERPT:", excerpt(x["col4"]))
            print("FULL:", x["col4"])

    print("\nwritten:", bp)


if __name__ == "__main__":
    main()
