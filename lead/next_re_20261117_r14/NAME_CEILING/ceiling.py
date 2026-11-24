# -*- coding: utf-8 -*-
"""NAME-CEILING — 名字天花板测量（只读测量，只写 NAME_CEILING 目录）

卡片: lead/next_re_20261117_r14/_cards/NAME-CEILING.md

问题: 每个子系统的 named_S(R14) 最多能做到多少？有没有子系统能到 ceil(0.9n)？

口径（严格照卡片 §口径定义）:
  样本集合 = coverage.tsv 中 entry 落在 function_atlas.tsv 内的行（entry 小写十六进制，
             一律 %08X 大写归一）
  n            = 该集合中该子系统的行数
  A_named      = name 非空 且 不以 'sub_' 开头 且 不匹配 '::sub_'
  B_substyle   = name 匹配 ^(sub_|.*::sub_)      （含空名以外的 sub_ 形态）
  C_slotstyle  = A_named 中形如 '::slotN' / '::vslotN' 的子集（单独统计，不另计总数）
  D_empty      = name 为空
  A + B + D = n（恒等式，脚本内断言）

名字可解三级（对 B_substyle + D_empty 的行判定）:
  L1 · 表内可解   function_atlas.tsv 的 strings 列含 RTTI 类型描述符（.?AV/.?AU …@@）
                  或限定名（Class::Method / Class.Method）形态，且能唯一对应
  L2 · 需反汇编可解 表内无线索，但 entry 可由虚表槽反查所属类（虚表地址 + 槽号 + RTTI 描述符）
                  → 可定出 Class::slotN
  L3 · 不可解     其余（含"只有 TU/断言源文件名线索"、"只有泛用词串"、"虚表归属不唯一"）

保守纪律: 拿不准一律记 L3。本卡要的是下界。

L2 的严格判定（刻意比盘上已有 slot 命名更窄）:
  只接受 vtables_rebuilt.tsv 中 primary==1（COL.col_offset==0）且 bad_kind=='next-col'
  （表在一个合法 COL 指针前结束 = 该虚表 run 覆盖完整）的虚表；class 必须是
  .?AV/.?AU 开头可解码的 RTTI 名；槽值必须落在 .text；且该函数在全表中只被
  一个 (虚表, 槽号) 唯一指认（多指认 = 归属不唯一 = L3）。
  —— 这条比盘上既有 slot 命名更窄（见 REPORT §自证），因此 L2 是下界不是上界。

输出（全部写入本目录）:
  ceiling.tsv     22 行数据
  samples_L1.tsv  L1 判定样本（L1 实际为 0，本文件给"最强近失样本"+ 拒判理由）
  samples_L2.tsv  L2 判定样本（每条给虚表地址、槽号、RTTI 描述符地址与原文）
  REPORT.md       由人工根据本脚本输出撰写
"""
import collections
import hashlib
import io
import json
import math
import os
import re
import struct
import sys

import pefile

BASE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(BASE)
PROJ = os.path.dirname(os.path.dirname(R14))
COVERAGE_TSV = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS_TSV = os.path.join(os.path.dirname(R14), "next_re_20261112_r10",
                         "W130_atlas", "function_atlas.tsv")
VT_TSV = os.path.join(os.path.dirname(R14), "next_re_20261112_r10",
                      "W130_atlas", "vtables_rebuilt.tsv")
SURVEY_TSV = os.path.join(R14, "SURVEY_3B2", "survey.tsv")
EXE = os.path.join(PROJ, "ra2youli", "gamemd.exe")
EXE_SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D      # 卡片给定的 .text 边界

SUBS = ["S%02d" % i for i in range(1, 23)]

RE_SUBSTYLE = re.compile(r"^(sub_|.*::sub_)")
RE_SLOTSTYLE = re.compile(r"::v?slot\d+$")
# L1 形态（只有这两类才算"类名/方法名线索"）：
#   ① RTTI 类型描述符 .?AVFoo@@ / .?AUIBar@@
#   ② 限定方法名 Foo::Bar
# 注意：**不许**把 `Egos.CPP` / `MOUSE.SHA` 这类文件名当限定名——那是翻译单元线索，
#       定不出方法名（本卡纪律：拿不准记 L3）。早期草稿用点分正则误收了 209 行。
RE_L1_RTTI_STRICT = re.compile(r"\.\?A[VU]")
RE_L1_QUAL = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_~]*")
RE_ASSERT_PATH = re.compile(r"[A-Za-z0-9_\\/:. -]*\.(?:CPP|cpp|Cpp)\b")


def norm_entry(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    return e


def sha256(path):
    h = hashlib.sha256()
    with io.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def demangle(name):
    """.?AVFoo@@ -> Foo（只做展示用；模板名保持原样）"""
    m = re.match(r"^\.\?A[VU](.+)@@$", name or "")
    return m.group(1) if m else (name or "")


# ------------------------------------------------------------------ 0. 自校验
print("[0] 输入自校验", flush=True)
exe_hash = sha256(EXE)
ok = exe_hash == EXE_SHA256
print("    gamemd.exe SHA-256 = %s  %s" % (exe_hash, "OK" if ok else "MISMATCH"))
if not ok:
    print("    !! 期望 %s" % EXE_SHA256)

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
IMG = pe.get_memory_mapped_image()
print("    ImageBase = 0x%08X" % IB)


def u32(va):
    return struct.unpack("<I", IMG[va - IB: va - IB + 4])[0]


def cstr(va, maxlen=200):
    raw = IMG[va - IB: va - IB + maxlen]
    return raw.split(b"\x00")[0]


def is_code(v):
    return TEXT_LO <= v < TEXT_HI


# ------------------------------------------------------------------ 1. 输入加载
print("[1] 加载 atlas / coverage", flush=True)
atlas = {}
with io.open(ATLAS_TSV, encoding="utf-8") as f:
    lines = f.read().splitlines()
for ln in lines[1:]:
    if not ln.strip():
        continue
    p = ln.split("\t")
    if len(p) < 9:
        continue
    try:
        atlas[norm_entry(p[0])] = {"size": int(p[1]), "n_instr": int(p[2]),
                                   "n_strings": int(p[7]), "strings": p[8]}
    except ValueError:
        pass
print("    atlas 数据行 %d（唯一 entry %d，其中 n_strings>0 的 %d）"
      % (len(lines) - 1, len(atlas), sum(1 for a in atlas.values() if a["n_strings"] > 0)))

cov = []
with io.open(COVERAGE_TSV, encoding="utf-8") as f:
    lines = f.read().splitlines()
for ln in lines[1:]:
    p = ln.split("\t")
    if len(p) < 8:
        continue
    cov.append({"entry": norm_entry(p[0]), "subsystem": p[1], "name": p[2].strip(),
                "grade": p[4]})
print("    coverage 数据行 %d" % len(cov))

# ------------------------------------------------------------------ 2. A/B/C/D 分类
print("[2] A/B/C/D 分类", flush=True)
cls = {s: collections.Counter() for s in SUBS}
rows = []
for r in cov:
    s = r["subsystem"]
    if s not in cls or r["entry"] not in atlas:
        continue
    cls[s]["n"] += 1
    nm, e = r["name"], r["entry"]
    if not nm:
        k = "D"
    elif RE_SUBSTYLE.match(nm):
        k = "B"
    else:
        k = "A"
        if RE_SLOTSTYLE.search(nm):
            cls[s]["C"] += 1
    cls[s][k] += 1
    rows.append({"entry": e, "subsystem": s, "name": nm, "kind": k,
                 "n_strings": atlas[e]["n_strings"], "strings": atlas[e]["strings"]})

for s in SUBS:
    a = cls[s]
    assert a["A"] + a["B"] + a["D"] == a["n"], (s, a)
    assert a["C"] <= a["A"], (s, a)
print("    n 合计 %d  A %d  B %d  D %d  C %d"
      % (sum(cls[s]["n"] for s in SUBS), sum(cls[s]["A"] for s in SUBS),
         sum(cls[s]["B"] for s in SUBS), sum(cls[s]["D"] for s in SUBS),
         sum(cls[s]["C"] for s in SUBS)))

# 与 SURVEY_3B2/survey.tsv 的 n / named_S14 逐格核对
drift = 0
if os.path.exists(SURVEY_TSV):
    with io.open(SURVEY_TSV, encoding="utf-8") as f:
        sl = f.read().splitlines()
    hdr = sl[0].split("\t")
    ix = {k: i for i, k in enumerate(hdr)}
    for ln in sl[1:]:
        p = ln.split("\t")
        s = p[ix["subsystem"]]
        if int(p[ix["n"]]) != cls[s]["n"] or int(p[ix["named_S14"]]) != cls[s]["A"]:
            drift += 1
            print("    DRIFT %s n=%d/%s named=%d/%s"
                  % (s, cls[s]["n"], p[ix["n"]], cls[s]["A"], p[ix["named_S14"]]))
    print("    survey.tsv 对照: %s（drift=%d）" % ("PASS" if drift == 0 else "FAIL", drift))

# ------------------------------------------------------------------ 3. L1 判定（表内）
print("[3] L1 判定（strings 列）", flush=True)
L1 = collections.Counter()
L1_slotlike = collections.Counter()   # 只有 RTTI 类名、无方法名 -> 严格口径不计
l1_detail = {}
near_miss = []
for r in rows:
    if r["kind"] == "A":
        continue
    s_txt = r["strings"] or ""
    hit = []
    if RE_L1_RTTI_STRICT.search(s_txt):
        hit.append("RTTI_DESCRIPTOR")
    if RE_L1_QUAL.search(s_txt):
        hit.append("QUALIFIED_METHOD")
    if hit:
        L1[r["subsystem"]] += 1
        if "QUALIFIED_METHOD" not in hit:
            L1_slotlike[r["subsystem"]] += 1
        l1_detail[r["entry"]] = hit
    elif RE_ASSERT_PATH.search(s_txt):
        near_miss.append((r, "ASSERT_SOURCE_PATH_ONLY",
                          RE_ASSERT_PATH.search(s_txt).group(0)))
    elif s_txt:
        near_miss.append((r, "GENERIC_STRING_ONLY", ""))
print("    L1 命中合计 %d（其中 RTTI 描述符 %d / 限定方法名 %d）"
      % (sum(L1.values()),
         sum(1 for v in l1_detail.values() if "RTTI_DESCRIPTOR" in v),
         sum(1 for v in l1_detail.values() if "QUALIFIED_METHOD" in v)))

# ------------------------------------------------------------------ 4. L2 判定（虚表槽 + RTTI）
print("[4] L2 判定（虚表槽 -> Class::slotN）", flush=True)
vt_rows = []
with io.open(VT_TSV, encoding="utf-8") as f:
    for ln in f.read().splitlines()[1:]:
        if not ln.strip():
            continue
        p = ln.split("\t")
        vt_rows.append({"vt": int(p[0], 16), "class": p[1], "primary": p[2] == "1",
                        "slots": int(p[4]), "bad_kind": p[5], "col": int(p[7], 16)})
print("    vtables_rebuilt.tsv: %d 张虚表（primary %d）"
      % (len(vt_rows), sum(1 for v in vt_rows if v["primary"])))


def build_slot_map(strict=True):
    """返回 fn_addr -> set((class_raw, slot, vt_addr))"""
    m = collections.defaultdict(set)
    for v in vt_rows:
        if strict and not (v["primary"] and v["bad_kind"] == "next-col"):
            continue
        if not re.match(r"^\.\?A[VU]", v["class"] or ""):
            continue
        for k in range(v["slots"]):
            try:
                val = u32(v["vt"] + 4 * k)
            except Exception:
                break
            if is_code(val):
                m[val].add((v["class"], k, v["vt"]))
    return m


def rtti_info(vt_addr):
    """由虚表拿 COL -> TD -> RTTI 名（用于样本可审计）"""
    try:
        col = u32(vt_addr - 4)
        td = u32(col + 0x0C)
        nb = cstr(td + 0x08)
        return col, td, nb.decode("ascii", "replace")
    except Exception:
        return None, None, ""


slot_strict = build_slot_map(True)
slot_loose = build_slot_map(False)
for tag, m in (("strict", slot_strict), ("loose", slot_loose)):
    amb = sum(1 for f, v in m.items() if len({(c, k) for c, k, _ in v}) > 1)
    print("    slot map[%s]: 槽内代码指针 %d 个 -> 唯一函数 %d（多槽指认 %d）"
          % (tag, sum(len(v) for v in m.values()), len(m), amb))

L2 = collections.Counter()
L2_amb = collections.Counter()
l2_samples = []
for r in rows:
    if r["kind"] == "A":
        continue
    f = int(r["entry"], 16)
    v = slot_strict.get(f)
    if not v:
        continue
    keys = {(c, k) for c, k, _ in v}
    if len(keys) > 1:
        L2_amb[r["subsystem"]] += 1        # 归属不唯一 -> L3（保守）
        continue
    c, k, vt = sorted(v)[0]
    L2[r["subsystem"]] += 1
    col, td, nm = rtti_info(vt)
    l2_samples.append({"entry": r["entry"], "subsystem": r["subsystem"], "name": r["name"],
                       "class": demangle(c), "class_raw": c, "slot": k,
                       "vt": vt, "col": col, "td": td, "rtti_name": nm or c})
print("    L2 合计 %d（其中归属不唯一改记 L3 的 %d）"
      % (sum(L2.values()), sum(L2_amb.values())))

# L2 方法自证：与盘上既有 ::slotN 命名比对（demangle 后按 (类, 槽号) 匹配）
# 两种口径都报：strict 明显比盘上既有命名窄，loose 与之高度吻合
selfcheck = {}
for tag, smap in (("strict", slot_strict), ("loose", slot_loose)):
    agree = disagree = 0
    for r in rows:
        if r["kind"] != "A":
            continue
        m = RE_SLOTSTYLE.search(r["name"])
        if not m:
            continue
        cname = r["name"][:m.start()]
        k = int(re.search(r"(\d+)$", r["name"]).group(1))
        v = smap.get(int(r["entry"], 16))
        if v and any(demangle(c) == cname and kk == k for c, kk, _ in v):
            agree += 1
        else:
            disagree += 1
    selfcheck[tag] = (agree, disagree)
    print("    自证[%s]: 盘上既有 slotN 名 %d 条，被推导复现 %d，未复现 %d"
          % (tag, agree + disagree, agree, disagree))

# 敏感性：loose 口径的 L2（= 盘上既有命名所用的推导，明显更宽）逐子系统重算
L2_loose = collections.Counter()
L2_loose_amb = collections.Counter()
for r in rows:
    if r["kind"] == "A":
        continue
    v = slot_loose.get(int(r["entry"], 16))
    if not v:
        continue
    if len({(c, k) for c, k, _ in v}) > 1:
        L2_loose_amb[r["subsystem"]] += 1
        continue
    L2_loose[r["subsystem"]] += 1
print("    L2(loose 敏感性) 合计 %d（归属不唯一 %d）"
      % (sum(L2_loose.values()), sum(L2_loose_amb.values())))

# ------------------------------------------------------------------ 5. 汇总
print("[5] 汇总", flush=True)
agg = {}
for s in SUBS:
    a = cls[s]
    n = a["n"]
    thr = math.ceil(0.9 * n)
    l1, l2 = L1[s], L2[s]
    l3 = a["B"] + a["D"] - l1 - l2
    ceil_off = a["A"] + l1 + l2
    # 严格口径：L1/L2 里成不了 Class::slotN 的（有真方法名的）才算；见卡片 §2
    ceil_on = a["A"] + (l1 - L1_slotlike[s])
    agg[s] = {"n": n, "A": a["A"], "C": a["C"], "B": a["B"], "D": a["D"],
              "L1": l1, "L2": l2, "L3": l3,
              "ceil_off": ceil_off, "ceil_on": ceil_on, "thr": thr,
              "reachable": ceil_off >= thr,
              "margin": ceil_off - thr,
              "L2_loose": L2_loose[s],
              "ceil_loose": a["A"] + l1 + L2_loose[s],
              "generous": a["A"] + sum(1 for r in rows
                                       if r["subsystem"] == s and r["kind"] != "A"
                                       and r["n_strings"] > 0)}

hdr = ["subsystem", "n", "A_named", "C_slotstyle", "B_substyle", "D_empty",
       "L1", "L2", "L3", "ceiling_off", "ceiling_on", "thr_named", "reachable"]
out = os.path.join(BASE, "ceiling.tsv")
with io.open(out, "w", encoding="utf-8", newline="") as f:
    f.write("\t".join(hdr) + "\n")
    for s in SUBS:
        a = agg[s]
        f.write("\t".join(str(x) for x in [
            s, a["n"], a["A"], a["C"], a["B"], a["D"], a["L1"], a["L2"], a["L3"],
            a["ceil_off"], a["ceil_on"], a["thr"],
            "True" if a["reachable"] else "False"]) + "\n")
print("    写出 %s" % out)

# 敏感性附表：三种 L2 口径 + 一种"有串即可解"的荒谬上界，看结论是否稳健
out_s = os.path.join(BASE, "sensitivity.tsv")
with io.open(out_s, "w", encoding="utf-8", newline="") as f:
    f.write("subsystem\tn\tA_named\tthr_named\tceil_strict\tceil_loose\t"
            "ceil_generous_strings\treach_strict\treach_loose\treach_generous\n")
    for s in SUBS:
        a = agg[s]
        f.write("\t".join(str(x) for x in [
            s, a["n"], a["A"], a["thr"], a["ceil_off"], a["ceil_loose"], a["generous"],
            "True" if a["ceil_off"] >= a["thr"] else "False",
            "True" if a["ceil_loose"] >= a["thr"] else "False",
            "True" if a["generous"] >= a["thr"] else "False"]) + "\n")
print("    写出 %s" % out_s)

# ------------------------------------------------------------------ 6. 样本
print("[6] 样本", flush=True)
out1 = os.path.join(BASE, "samples_L1.tsv")
with io.open(out1, "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsubsystem\tcurrent_name\tn_strings\tstrings_verbatim\t"
            "L1_verdict\treason\n")
    ordered = sorted(near_miss, key=lambda x: (x[1] != "ASSERT_SOURCE_PATH_ONLY",
                                               -x[0]["n_strings"]))
    for r, why, tok in ordered[:16]:
        txt = (r["strings"] or "").replace("\t", " ")[:240]
        reason = ("只有断言源文件名（翻译单元级线索），不能唯一确定方法名 -> L3"
                  if why == "ASSERT_SOURCE_PATH_ONLY"
                  else "只有通用串/键名，非类名或方法名 -> L3")
        f.write("\t".join([r["entry"], r["subsystem"], r["name"], str(r["n_strings"]),
                           txt, "L3", reason]) + "\n")
print("    写出 %s（L1 计数为 0，本文件为最强近失样本）" % out1)

out2 = os.path.join(BASE, "samples_L2.tsv")
with io.open(out2, "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsubsystem\tcurrent_name\tclass\tslot\tnew_name\t"
            "vtable_va\tcol_va\trtti_td_va\trtti_name_verbatim\n")
    for d in sorted(l2_samples, key=lambda x: x["entry"]):
        f.write("\t".join([
            d["entry"], d["subsystem"], d["name"], d["class"], str(d["slot"]),
            "%s::slot%d" % (d["class"], d["slot"]),
            "0x%08X" % d["vt"],
            "0x%08X" % d["col"] if d["col"] else "",
            "0x%08X" % d["td"] if d["td"] else "",
            d["rtti_name"]]) + "\n")
print("    写出 %s（%d 行）" % (out2, len(l2_samples)))

# ------------------------------------------------------------------ 7. 摘要
print("\n=== 摘要 ===")
print("%-4s %6s %6s %6s %6s %6s %6s %8s %8s %6s %s"
      % ("S", "n", "A", "B", "L1", "L2", "L3", "ceil_off", "thr", "margin", "reach"))
for s in SUBS:
    a = agg[s]
    print("%-4s %6d %6d %6d %6d %6d %6d %8d %8d %6d %s"
          % (s, a["n"], a["A"], a["B"], a["L1"], a["L2"], a["L3"],
             a["ceil_off"], a["thr"], a["margin"], a["reachable"]))
rs = [s for s in SUBS if agg[s]["reachable"]]
un = [s for s in SUBS if not agg[s]["reachable"]]
print("\n够门槛 %d 个: %s" % (len(rs), ", ".join("%s(%+d)" % (s, agg[s]["margin"]) for s in rs)))
print("够不到 %d 个: %s" % (len(un), ", ".join("%s(%+d)" % (s, agg[s]["margin"]) for s in un)))
best = max(un, key=lambda s: agg[s]["margin"])
print("最接近门槛但够不到: %s  ceiling=%d thr=%d 差 %d"
      % (best, agg[best]["ceil_off"], agg[best]["thr"], -agg[best]["margin"]))
bestr = max(rs, key=lambda s: agg[s]["margin"])
print("够门槛里余量最大: %s  ceiling=%d thr=%d 余 %+d"
      % (bestr, agg[bestr]["ceil_off"], agg[bestr]["thr"], agg[bestr]["margin"]))
g_rs = [s for s in SUBS if agg[s]["generous"] >= agg[s]["thr"]]
print("敏感性 loose-L2: 够门槛 %d 个 %s"
      % (len([s for s in SUBS if agg[s]["ceil_loose"] >= agg[s]["thr"]]),
         [s for s in SUBS if agg[s]["ceil_loose"] >= agg[s]["thr"]]))
print("敏感性 有串即可解(不可辩护上界): 够门槛 %d 个 %s" % (len(g_rs), g_rs))
print("完成。")
