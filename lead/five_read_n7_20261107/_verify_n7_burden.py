# -*- coding: utf-8 -*-
"""独立复核员·hy4 的 N-7 负担复算核验脚本（不复用复算员任何实现）。

与 _n7_burden_recalc.py 的差异（刻意为之，保证独立）：
  - 文件枚举：手动两层 os.scandir，而非 os.walk + relpath 深度判定
  - 读文件：二进制 rb + json.loads(bytes)，而非文本 open(encoding)
  - 数值：Decimal + ROUND_HALF_UP 四舍五入，而非 Fraction + 手写 divmod
  - 另做「最坏窗是否真是 max(edges/samples)」与「分母是否被裁过」两项怀疑性检查
  - 所有被核数字硬编码为待核对常量，输出 PASS/FAIL 与实算值
只读；无进程/游戏/采样路径；无 ctypes / OpenProcess / RPM / hook。
"""
import json
import os
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 60

ROOT = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

# ---------- 1. 手动两层 scandir 枚举（与复算员 os.walk 不同） ----------
d1 = []          # 一级子目录内的 measure_w*.json
d0 = []          # 根直下
deeper = []      # 更深
for e0 in os.scandir(ROOT):
    if e0.is_file() and e0.name.startswith("measure_w") and e0.name.endswith(".json"):
        d0.append(e0.path)
    elif e0.is_dir():
        for e1 in os.scandir(e0.path):
            if e1.is_file() and e1.name.startswith("measure_w") and e1.name.endswith(".json"):
                d1.append((e1.path, e0.name, e1.name))
            elif e1.is_dir():
                for e2 in os.scandir(e1.path):
                    if e2.is_file() and e2.name.startswith("measure_w") and e2.name.endswith(".json"):
                        deeper.append(e2.path)
d1.sort()

print("[V1] 枚举（手动两层 scandir）")
print("    depth1 文件数 = %d ；root-direct = %d ；deeper = %d" % (len(d1), len(d0), len(deeper)))
print("    root-direct 名单 = %r" % [os.path.basename(p) for p in sorted(d0)])
print("    断言 depth1==101 & d0==3 & deeper==0 : %s" %
      ("PASS" if (len(d1), len(d0), len(deeper)) == (101, 3, 0) else "FAIL"))

# ---------- 2. 原始字节解析 + 纳排 ----------
rows = []
excluded = []
schemas = {}
hashes = set()
hzs = set()
parse_err = 0
for path, sub, fn in d1:
    try:
        raw = open(path, "rb").read()
        d = json.loads(raw.decode("utf-8"))
    except Exception as ex:
        parse_err += 1
        excluded.append((sub, fn, "PARSE_ERR %r" % ex))
        continue
    st = d.get("stats") or {}
    span = d.get("span_s")
    samples = st.get("samples")
    edges = st.get("n_edges")
    schemas[d.get("schema")] = schemas.get(d.get("schema"), 0) + 1
    if d.get("gamemd_sha256"):
        hashes.add(d.get("gamemd_sha256"))
    if d.get("hz") is not None:
        hzs.add(d.get("hz"))
    if span == 25.0 and isinstance(samples, int) and samples > 0:
        rows.append(dict(sub=sub, fn=fn, trip=d.get("trip_id"), w=d.get("window"),
                         span=span, samples=samples, edges=edges))
    else:
        excluded.append((sub, fn, "span=%r samples=%r" % (span, samples)))

print("[V2] 解析/纳排")
print("    parse_err = %d ；纳入 = %d ；排除 = %d" % (parse_err, len(rows), len(excluded)))
print("    schema = %r ；hz = %r ；gamemd_sha256 去重 = %d" % (schemas, sorted(hzs), len(hashes)))
for h in sorted(hashes):
    print("      %s" % h)
print("    断言 纳入87/排除14/parse0/schema全MEASURE_V1/hz{500}/hash1 : %s" %
      ("PASS" if (len(rows), len(excluded), parse_err, schemas, sorted(hzs), len(hashes)) ==
       (87, 14, 0, {"MEASURE_V1": 101}, [500], 1) else "FAIL"))

# 排除 14 窗的成因分布
from collections import Counter
sp = Counter()
for sub, fn, why in excluded:
    sp[why.split(" samples=")[0]] += 1
print("    排除成因分布 = %r" % dict(sp))
print("    排除逐窗：")
for sub, fn, why in excluded:
    print("      %s/%s  %s" % (sub, fn, why))

# ---------- 3. 分母与沿数 ----------
S = sum(r["samples"] for r in rows)
E = sum(r["edges"] for r in rows)
T = sum(max(0, r["edges"] - 1) for r in rows)
print("[V3] 分母与沿数")
print("    S=Σsamples = %d ；E=Σn_edges = %d ；T=Σmax(0,n_edges-1) = %d" % (S, E, T))
print("    E - 87 = %d（应等于 T）" % (E - 87))
print("    断言 (S,E,T)==(1080975,28309,28222) : %s" %
      ("PASS" if (S, E, T) == (1080975, 28309, 28222) else "FAIL"))

# 逐窗 samples 分布（核对「65×12501 + 19×12502 + 三个异值」）
dist = Counter(r["samples"] for r in rows)
print("[V3b] 逐窗 samples 分布 = %r" % dict(sorted(dist.items())))
odd = sorted([(r["sub"], r["fn"], r["samples"], r["edges"]) for r in rows
              if not (12501 <= r["samples"] <= 12502)], key=lambda x: x[2])
print("    非 [12501,12502] 窗 = %d ：" % len(odd))
for o in odd:
    print("      %s/%s samples=%d edges=%d" % o)
print("    断言 65×12501 + 19×12502 + 12452 + 12471 + 5949 = S : %s" %
      ("PASS" if (dist.get(12501, 0), dist.get(12502, 0),
                  len(odd), 65 * 12501 + 19 * 12502 + 12452 + 12471 + 5949) ==
       (65, 19, 3, S) else "FAIL"))
print("    ★ 三个异值窗是否被计入分母：%s（计入则 S=1080975，剔除则 S=%d）" %
      ("是（未裁分母）" if S == 1080975 else "否",
       65 * 12501 + 19 * 12502))

# ---------- 4. 最坏窗：按 n_edges 最大（历史定义） vs 按 edges/samples 最大（怀疑性检查） ----------
max_e = max(r["edges"] for r in rows)
worst_by_e = [r for r in rows if r["edges"] == max_e]
max_ratio = rows[max(range(len(rows)),
                      key=lambda i: Decimal(rows[i]["edges"]) / Decimal(rows[i]["samples"]))]
print("[V4] 最坏窗")
for r in worst_by_e:
    print("    max(n_edges) 窗：%s w%s edges=%d samples=%d ratio=%.9f" %
          (r["trip"], r["w"], r["edges"], r["samples"],
           float(Decimal(r["edges"]) / Decimal(r["samples"]))))
print("    并列数 = %d" % len(worst_by_e))
print("    按 edges/samples 最大的窗：%s w%s edges=%d samples=%d ratio=%.9f" %
      (max_ratio["trip"], max_ratio["w"], max_ratio["edges"], max_ratio["samples"],
       float(Decimal(max_ratio["edges"]) / Decimal(max_ratio["samples"]))))
same = (worst_by_e[0]["sub"], worst_by_e[0]["fn"]) == (max_ratio["sub"], max_ratio["fn"])
print("    ★ 两种定义是否同一窗：%s" % ("是" if same else "否 —— 历史「最坏窗」并非负担率最大窗，需登记"))
print("    断言 worst=(QC161-U0800-L3-20261023R,window=0,784,12502) : %s" %
      ("PASS" if (worst_by_e[0]["trip"], worst_by_e[0]["w"],
                  worst_by_e[0]["edges"], worst_by_e[0]["samples"]) ==
       ("QC161-U0800-L3-20261023R", 0, 784, 12502) else "FAIL"))

# ---------- 5. 百分比：Decimal 独立四舍五入 ----------
def dec_pct(n, edges, samples):
    return Decimal(100) * Decimal(n) * Decimal(edges) / Decimal(samples)

def rnd(fr, dp):
    q = Decimal(1).scaleb(-dp)
    return fr.quantize(q, rounding=ROUND_HALF_UP)

print("[V5] 87 窗整体（Decimal/ROUND_HALF_UP）")
ctx = {(4, "E"): "+10.475%", (4, "T"): "+10.443%",
       (5, "E"): "+13.094%", (5, "T"): "+13.054%",
       (6, "E"): "+15.713%", (6, "T"): "+15.665%"}
for n in (4, 5, 6):
    for tag, base in (("E", E), ("T", T)):
        v = dec_pct(n, base, S)
        s = "+" + str(rnd(v, 3)) + "%"
        print("    %d读 %s : %s%% (4dp %s%%, 6dp %s%%) 期望 %s [%s]" %
              (n, tag, str(rnd(v, 3)), str(rnd(v, 4)), str(rnd(v, 6)),
               ctx[(n, tag)], "PASS" if s == ctx[(n, tag)] else "FAIL"))
print("    精确分数核对（整数化简）：")
import math
def frac_str(num, den):
    g = math.gcd(num, den)
    return "%d/%d" % (num // g, den // g)
print("      5读沿表 100*5*%d/%d = %s（期望 566180/43239）" % (E, S, frac_str(100 * 5 * E, S)))
print("      5读跳变 100*5*%d/%d = %s（期望 564440/43239）" % (T, S, frac_str(100 * 5 * T, S)))

w = worst_by_e[0]
print("[V6] 最坏单窗（edges=%d samples=%d）" % (w["edges"], w["samples"]))
ctxw = {(4, "E"): "+25.0840%", (4, "T"): "+25.0520%",
        (5, "E"): "+31.3550%", (5, "T"): "+31.3150%",
        (6, "E"): "+37.6260%", (6, "T"): "+37.5780%"}
for n in (4, 5, 6):
    for tag, base in (("E", w["edges"]), ("T", w["edges"] - 1)):
        v = dec_pct(n, base, w["samples"])
        s = "+" + str(rnd(v, 4)) + "%"
        print("    %d读 %s : %s%% (6dp %s%%) 期望 %s [%s]" %
              (n, tag, str(rnd(v, 4)), str(rnd(v, 6)),
               ctxw[(n, tag)], "PASS" if s == ctxw[(n, tag)] else "FAIL"))
print("      5读沿表 100*5*%d/%d = %s（期望 28000/893）" %
      (w["edges"], w["samples"], frac_str(100 * 5 * w["edges"], w["samples"])))
print("      5读跳变 100*5*%d/%d = %s（期望 195750/6251）" %
      (w["edges"] - 1, w["samples"], frac_str(100 * 5 * (w["edges"] - 1), w["samples"])))

# ---------- 6. 字节口径 ----------
print("[V7] 字节口径（每读 4 B）")
for n in (5, 6):
    tot = 4 * n * E
    wtot = 4 * n * w["edges"]
    rate = Decimal(wtot) / Decimal(25)
    print("    %d读：每沿 %dB；87窗合计 %dB；最坏窗 %dB；最坏窗 %s B/s" %
          (n, 4 * n, tot, wtot, rnd(rate, 1)))
print("    断言 5读(20,566180,15680,627.2) 6读(24,679416,18816,752.6) : %s" %
      ("PASS" if (4 * 5 * E, 4 * 5 * w["edges"], str(rnd(Decimal(4 * 5 * w["edges"]) / 25, 1)),
                  4 * 6 * E, 4 * 6 * w["edges"], str(rnd(Decimal(4 * 6 * w["edges"]) / 25, 1))) ==
       (566180, 15680, "627.2", 679416, 18816, "752.6") else "FAIL"))

# ---------- 7. 四项主数字汇总 ----------
print("[V8] 四项主数字（被核对象结论）")
checks4 = [
    ("87窗5读沿表", dec_pct(5, E, S), 3, "+13.094%"),
    ("87窗5读跳变", dec_pct(5, T, S), 3, "+13.054%"),
    ("最坏窗5读沿表", dec_pct(5, w["edges"], w["samples"]), 4, "+31.3550%"),
    ("最坏窗5读跳变", dec_pct(5, w["edges"] - 1, w["samples"]), 4, "+31.3150%"),
]
allok = True
for name, v, dp, exp in checks4:
    s = "+" + str(rnd(v, dp)) + "%"
    ok = (s == exp)
    allok = allok and ok
    print("    %s : 实算 %s vs %s [%s]" % (name, s, exp, "PASS" if ok else "FAIL"))
print("    四项全复现 = %s" % allok)
print("V_DONE")
