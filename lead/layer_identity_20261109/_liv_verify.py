# -*- coding: utf-8 -*-
"""_liv_verify.py — 层恒等证明独立复核探针（只读加载谓词，绝不改任何既有件）。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/layer_identity_20261109/_liv_verify.py
"""
import hashlib
import importlib.util
import json
import pathlib
import random

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
G7_PATH = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13_COPY = ROOT / "lead" / "evidence_indep_20261109" / "_ei_n13_predicates_src.py"
WD = ROOT / "lead" / "gate_pipeline_20261109"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


g7 = _load(G7_PATH, "_liv_g7")
n13 = _load(N13_COPY, "_liv_n13")
T = list(n13.DEFAULT_TOKENS)
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

print("== fingerprints ==")
for p in (G7_PATH, N13_COPY):
    b = p.read_bytes()
    print("  %s %d %s" % (hashlib.sha256(b).hexdigest(), len(b), p.name))
n13_prod = list((ROOT / "lead" / "gate_n13_20261109").glob("*_predicates.py"))
for p in n13_prod:
    b = p.read_bytes()
    print("  %s %d %s" % (hashlib.sha256(b).hexdigest(), len(b), p.name))
    print("  production == read-only copy bytes ?", b == N13_COPY.read_bytes())


R10SCAN = "r10" + "_scan"   # 与 _g7_predicates.py:113 的公开入口同名
_r10 = getattr(g7, R10SCAN)


def judge(text, toks, tokens_for_n13=T):
    """复刻 _gp_regression.py:138-143 的单层判定口径。"""
    r10 = "CATCH" if _r10(text, toks)[0] else "PASS"
    r12 = "CATCH" if g7.r12_scan(text, toks)[0] else "PASS"
    kw = {R10SCAN: _r10, "r12" + "_scan": g7.r12_scan}
    p, _ = n13.r13_assertions(text, tokens_for_n13, **kw)
    n13v = "CATCH" if p else "PASS"
    return r10, r12, n13v


def show(tag, text, toks, expect, tn=T):
    r10, r12, n13v = judge(text, toks, tn)
    A = (r10 == "PASS" and r12 == "PASS" and n13v == "PASS")
    B = (r10 == "PASS" and n13v == "PASS")
    broken = (n13v == "PASS" and r12 == "CATCH")
    print("  %-5s expect=%-5s r10=%-5s r12=%-5s n13=%-5s | inB=%-5s inA=%-5s %s | %r" %
          (tag, expect, r10, r12, n13v, B, A, "*** BROKEN ***" if broken else "holds", text))
    return dict(r10=r10, r12=r12, n13=n13v, A=A, B=B, broken=broken)


print("\n== control (should HOLD) ==")
show("C0", "并非不宣告已生效", T, "CATCH", T)
show("C0b", "不得不承认已生效", T, "CATCH", T)
show("C1", "grep 结果：已入账 0 命中", T, "PASS", T)

print("\n== X1/X2: 词表契约分叉（R12 用行 tokens，N13 恒用 T） ==")
X1 = show("X1", "不得不承认放行 N-5", BAD_BAN, "CATCH", T)
X2 = show("X2", "不得不承认可应用母本", BAD_BAN, "CATCH", T)

print("\n== X3: CRLF 位置错位（仍用 T 三词） ==")
X3 = show("X3", "第一行文字\r\n不得不承认，已入账 grep 结果", T, "CATCH", T)

print("\n== 反例是否同时破集合恒等与条件概率 ==")
for tag, r in (("X1", X1), ("X2", X2), ("X3", X3)):
    print("  %s: inB=%s inA=%s => A!=B ? %s ; n13=PASS&r12=CATCH ? %s" %
          (tag, r["B"], r["A"], r["B"] != r["A"], r["broken"]))

print("\n== r12=CATCH => r10=PASS 也不是定理 ==")
show("C2", "本笔已入账。不得不承认已生效", T, "CATCH", T)

print("\n== 受限蕴含穷举：同一 tokens=T，LF，3 token x 10 构式 x 6 前缀 = 180 ==")
DOUBLE = ["不得不", "并非不", "并不是不", "不是不", "无不", "没有不", "不无",
          "不能不", "不可不", "未曾不"]
PREFIX = ["", "审阅 ", "本件 ", "   ", "1. ", "> "]
viol = 0
n = 0
for tok in T:
    for dbl in DOUBLE:
        for pre in PREFIX:
            s = pre + dbl + "宣告" + tok
            n += 1
            r10, r12, n13v = judge(s, T, T)
            if r12 == "CATCH" and n13v != "CATCH":
                viol += 1
                print("   VIOL", repr(s), r10, r12, n13v)
print("  combos=%d broken=%d" % (n, viol))

print("\n== CRLF 系统测试：10 构式 x 1/2/3 前置行 = 30 ==")
for pl in (1, 2, 3):
    v = 0
    for dbl in DOUBLE:
        s = ("第一行文字\r\n" * pl) + dbl + "，已入账 grep 结果"
        r10, r12, n13v = judge(s, T, T)
        if r12 == "CATCH" and n13v == "PASS":
            v += 1
    print("  prior_lines=%d violations=%d/%d" % (pl, v, len(DOUBLE)))

print("\n== 随机受限测试 1200 次 ==")
random.seed(20261109)
rc = rv = 0
for _ in range(1200):
    tok = random.choice(T)
    dbl = random.choice(DOUBLE)
    pre = random.choice(PREFIX)
    s = pre + dbl + "宣告" + tok
    r10, r12, n13v = judge(s, T, T)
    if r12 == "CATCH":
        rc += 1
        if n13v != "CATCH":
            rv += 1
print("  r12=CATCH=%d violations=%d" % (rc, rv))

print("\n== 74 行里 tokens 非 T 子集计数（独立读 JSON） ==")
rows = json.loads((WD / "_gp_regression_out.json").read_text(encoding="utf-8"))["rows"]
not_subset = [r["id"] for r in rows if not set(r["tokens"]).issubset(set(T))]
print("  not_subset n=%d ids=%s" % (len(not_subset), not_subset))
print("  distinct token sets:", sorted({tuple(r["tokens"]) for r in rows}))
