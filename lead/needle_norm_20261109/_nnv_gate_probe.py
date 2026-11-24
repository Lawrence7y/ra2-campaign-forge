# -*- coding: utf-8 -*-
"""_nnv_gate_probe.py — 核第五步(b)「漏了哪类自己不知道」门禁的实际有效性。
方法：往内存语料注入 1 行新变体（不改任何盘文件），看自动发现器是否列出新类、
集合差是否 FAIL、以及撰写人 W4/补充轨/L1 能否召回该新类。
只读；纯内存；python -I -X utf8。
"""
import os, re
from collections import Counter
ROOT = r"D:/Project/ra2-campaign-forge/lead"
files = {}
for dp, dn, fn in os.walk(ROOT):
    rel = os.path.relpath(dp, ROOT).replace("\\", "/")
    d = 0 if rel == "." else rel.count("/") + 1
    if d > 2:
        dn[:] = []
        continue
    for f in sorted(fn):
        if not f.lower().endswith(".md"):
            continue
        p = os.path.join(dp, f)
        r = os.path.relpath(p, ROOT).replace("\\", "/")
        if r.startswith("needle_norm_20261109/"):
            continue
        b = open(p, "rb").read()
        if b"\x00" in b:
            continue
        files[r] = b.decode("utf-8", "replace").splitlines()

DISCOVER = re.compile(r"只能判(.{0,4}?)不可复现(.{0,2})")
W4 = re.compile(r"只能判.{0,3}不可复现")
SUPP = re.compile(r"只能判[「『“(]?不可复现[」』”)]?")

def discover(fs):
    c = Counter()
    for ls in fs.values():
        for L in ls:
            for m in DISCOVER.finditer(L):
                c[(m.group(1), m.group(2))] += 1
    return set(c)

base = discover(files)
print("BEFORE injected variant: discovered classes =", len(base))

# 新变体：半角括号 + 多一个空格（编排方 6 变体清单里没有，且间隙 4 字 > W4 的 {0,3}）
new_lines = [
    "只能判（不可复现）",             # 全角括号，pre/post 都是新类，W4 可召回(间隙1)
    "只能判〔不可复现〕",             # 新包裹符，W4 可召回
    "只能判 —— 不可复现",           # 间隙 4 字：W4 {0,3} 召回不到
    "只能判『不可复现』（新类后接）",  # post=』（ 新类
]
for k, L in enumerate(new_lines):
    fs2 = dict(files)
    fs2["__INJECTED__/%d.md" % k] = [L]
    after = discover(fs2)
    diff = after - base
    w4 = bool(W4.search(L))
    supp = bool(SUPP.search(L))
    print("-- inject %r --" % L)
    print("   discovered new classes = %d ; DIFF = %s" % (len(diff), sorted(diff)))
    print("   GATE would FAIL? %s" % bool(diff))
    print("   W4 只能判.{0,3}不可复现 召回? %s ; 补充轨 只能判[...]?不可复现[...]? 召回? %s" % (w4, supp))
    print("   集合差门禁本身能否发现新类? %s" % bool(diff))
print("")
print("结论：自动发现器能列新类并让集合差 FAIL；但『发现』不等于『召回』——W4 与补充轨")
print("      对间隙>3 字 / 未列举包裹符的新变体仍召回不到，门禁只报 FAIL，不自动修召回规则。")
