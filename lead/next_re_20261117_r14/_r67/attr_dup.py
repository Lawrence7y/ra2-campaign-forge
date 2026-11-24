# -*- coding: utf-8 -*-
# R17-R67 附：重复侧归因的正交拆分（更正 s273 第一版的优先级口径错误）
#
# 第一版用的是 if/elif 优先级：「备份特征优先，其次 coverage」。
# 结果：兼有两特征的 18 件 / 4,552,562 B 被整段算进「备份」桶，
#       coverage 桶因此少算 4,552,562 B（29.5% 而非真值 38.82%），
#       备份桶因此多算同样字节（11.7% 而非真值 2.46% + 3.29%）。
# 本条缺陷形状：**分类不互斥却当成互斥报百分比**（与纪律 9「先分命名空间」同族但落在分类维度）。
import csv, io, re, os, sys

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
ROOT = r"D:\Project\ra2-campaign-forge\lead"
TSV = os.path.join(R14, r"_r67\unique_content_4417.tsv")

buf = []
fails = []
def P(s=""):
    print(s); buf.append(s)
def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c: fails.append(n)

rows = list(csv.DictReader(io.open(TSV, encoding="utf-8"), delimiter="\t"))
dup = [r for r in rows if r["cluster_rep"] != r["rel"]]
TOT_N, TOT_B = len(dup), sum(int(r["bytes"]) for r in dup)
P("重复侧：%d 件 / %d B" % (TOT_N, TOT_B))
ck("重复件 = 330", TOT_N == 330, str(TOT_N))
ck("重复字节 = 138,319,224", TOT_B == 138319224, str(TOT_B))

# ---- 两个维度的判据（各自独立，不预设优先级）----
RE_COV = re.compile(r"coverage", re.I)
RE_BAK = re.compile(r"(baseline|backup|_archive|SUPERSEDED|\.bak|_before|BEFORE)")
is_cov = lambda r: bool(RE_COV.search(r["rel"]))
is_bak = lambda r: bool(RE_BAK.search(r["rel"]))

buckets = {
    "仅 coverage 快照": [r for r in dup if is_cov(r) and not is_bak(r)],
    "仅 备份/基线/归档副本": [r for r in dup if is_bak(r) and not is_cov(r)],
    "两者兼有": [r for r in dup if is_cov(r) and is_bak(r)],
    "两者皆无（其它）": [r for r in dup if not is_cov(r) and not is_bak(r)],
}
P("")
P("[1] 正交拆分（四桶互斥，并集 = 全部重复）")
sn = sb = 0
for k, v in buckets.items():
    n, b = len(v), sum(int(r["bytes"]) for r in v)
    sn += n; sb += b
    P("  %-22s %4d 件  %12d B  %6.2f%%" % (k, n, b, b * 100.0 / TOT_B))
P("  %-22s %4d 件  %12d B  100.00%%" % ("合计", sn, sb))
ck("四桶件数之和 = 330", sn == TOT_N, str(sn))
ck("四桶字节之和 = 138,319,224", sb == TOT_B, str(sb))
ck("四桶两两不相交", len({r["rel"] for v in buckets.values() for r in v}) == TOT_N)

# ---- 维度边际（不看另一维）----
P("")
P("[2] 维度边际（不区分是否兼有）")
cov_all = [r for r in dup if is_cov(r)]
bak_all = [r for r in dup if is_bak(r)]
cv_n, cv_b = len(cov_all), sum(int(r["bytes"]) for r in cov_all)
bk_n, bk_b = len(bak_all), sum(int(r["bytes"]) for r in bak_all)
P("  coverage 相关（任一位置）：%3d 件 / %12d B = %.2f%%" % (cv_n, cv_b, cv_b * 100.0 / TOT_B))
P("  备份特征相关（任一位置）  ：%3d 件 / %12d B = %.2f%%" % (bk_n, bk_b, bk_b * 100.0 / TOT_B))
P("  两者兼有                  ：%s 件 / %s B" % (len(buckets["两者兼有"]),
                                                sum(int(r["bytes"]) for r in buckets["两者兼有"])))
ck("coverage 相关 = 31 件 / 53,684,710 B", (cv_n, cv_b) == (31, 53684710),
   "%d / %d" % (cv_n, cv_b))
ck("备份特征相关 = 126 件 / 7,952,136 B", (bk_n, bk_b) == (126, 7952136),
   "%d / %d" % (bk_n, bk_b))
ck("容斥：|cov| + |bak| − |cov∩bak| = 330 − 191（两者皆无）",
   cv_n + bk_n - len(buckets["两者兼有"]) == TOT_N - len(buckets["两者皆无（其它）"]),
   "%d" % (cv_n + bk_n - len(buckets["两者兼有"])))
ck("字节容斥等式成立（= 总 − 其它桶）",
   cv_b + bk_b - sum(int(r["bytes"]) for r in buckets["两者兼有"])
   == TOT_B - sum(int(r["bytes"]) for r in buckets["两者皆无（其它）"]))

# ---- 负控 N6：优先级口径必须与正交口径不同（证两者不能混用）----
P("")
P("[3] 负控 N6：优先级口径 vs 正交口径必须不同（这正是第一版错的地方）")
prio = {
    "备份优先": [r for r in dup if is_bak(r)],
    "其次 coverage": [r for r in dup if is_cov(r) and not is_bak(r)],
    "其它": [r for r in dup if not is_bak(r) and not is_cov(r)],
}
for k, v in prio.items():
    b = sum(int(r["bytes"]) for r in v)
    P("  优先级 %-12s %4d 件  %12d B  %6.2f%%" % (k, len(v), b, b * 100.0 / TOT_B))
p_bak = sum(int(r["bytes"]) for r in prio["备份优先"])
ck("N6 优先级「备份」桶字节 != 正交「仅备份」桶字节",
   p_bak != sb - (cv_b - sum(int(r["bytes"]) for r in buckets["两者兼有"])) - 0
   if False else p_bak != sum(int(r["bytes"]) for r in buckets["仅 备份/基线/归档副本"]),
   "prio=%d vs orth=%d" % (p_bak, sum(int(r["bytes"]) for r in buckets["仅 备份/基线/归档副本"])))
ck("N6 优先级口径把 coverage 少算了 4,552,562 B",
   p_bak - sum(int(r["bytes"]) for r in buckets["仅 备份/基线/归档副本"]) == 4552562,
   str(p_bak - sum(int(r["bytes"]) for r in buckets["仅 备份/基线/归档副本"])))
ck("N6 优先级桶之和仍 = 330（错在归属，不在总数）",
   sum(len(v) for v in prio.values()) == TOT_N)

# ---- Top15 逐簇归到 coverage / 非 coverage ----
P("")
P("[4] Top15 大件按是否 coverage 归类（同样正交，不叠算）")
import collections
cl = collections.defaultdict(list)
for r in rows:
    cl[r["sha256"]].append(r)
dups = [(s, v) for s, v in cl.items() if len(v) > 1]
w = sorted(((int(v[0]["bytes"]) * (len(v) - 1), len(v), s, v[0]["rel"]) for s, v in dups),
           reverse=True)
top = w[:15]
T15 = sum(x[0] for x in top)
tb = {
    "仅 coverage": [x for x in top if is_cov({"rel": x[3]}) and not is_bak({"rel": x[3]})],
    "仅 备份特征": [x for x in top if is_bak({"rel": x[3]}) and not is_cov({"rel": x[3]})],
    "两者兼有": [x for x in top if is_cov({"rel": x[3]}) and is_bak({"rel": x[3]})],
    "两者皆无": [x for x in top if not is_cov({"rel": x[3]}) and not is_bak({"rel": x[3]})],
}
P("  Top15 浪费合计 = %d B" % T15)
for k, v in tb.items():
    s = sum(x[0] for x in v)
    P("    %-12s %2d 簇  %12d B  %6.2f%%" % (k, len(v), s, s * 100.0 / T15))
ck("Top15 浪费合计 = 130,989,973", T15 == 130989973, str(T15))
ck("Top15 正交四桶之和 = Top15 合计",
   sum(sum(x[0] for x in v) for v in tb.values()) == T15,
   str(sum(sum(x[0] for x in v) for v in tb.values())))
ck("Top15 四桶簇数之和 = 15", sum(len(v) for v in tb.values()) == 15,
   str(sum(len(v) for v in tb.values())))
cov_top = sum(x[0] for x in top if is_cov({"rel": x[3]}))
P("  Top15 里 coverage 相关（边际，含兼有）= %d B（%.1f%%）"
  % (cov_top, cov_top * 100.0 / T15))
ck("Top15 coverage 边际 = 53,205,706 B", cov_top == 53205706, str(cov_top))

# ---- 与第一版文本的差异（诚实记录）----
P("")
P("[5] 第一版（if/elif 优先级）与正交口径的差异 —— 这就是要更正的地方")
P("  第一版报：备份/基线/归档 128 件 16,225,186 B 11.7% / coverage 11 件 40,859,098 B 29.5% / 其它 191 件")
P("  正交报  ：仅备份 108 件 3,399,574 B 2.46% / 仅 coverage 13 件 49,132,148 B 35.52% / 兼有 18 件 4,552,562 B 3.29% / 其它 191 件 81,234,940 B 58.73%")
P("  coverage 角度真值：%d 件 / %d B = %.2f%%（第一版写 29.5%%，低报 %.2f 个百分点）"
  % (cv_n, cv_b, cv_b * 100.0 / TOT_B, cv_b * 100.0 / TOT_B - 29.5))
ck("coverage 真值 38.82%（第一版 29.5%）", abs(cv_b * 100.0 / TOT_B - 38.82) < 0.01,
   "%.2f" % (cv_b * 100.0 / TOT_B))

P("")
P("RESULT " + ("ALL-PASS" if not fails else "FAIL: " + ",".join(fails)))
io.open(os.path.join(R14, r"_r67\attr_dup.log"), "w", encoding="utf-8",
        newline="\n").write("\n".join(buf) + "\n")
sys.exit(0 if not fails else 1)
