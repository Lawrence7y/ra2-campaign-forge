# -*- coding: utf-8 -*-
r"""_gpv_order.py — ⑥ 顺序是否当消解手段 + §3(c)「pos 升序」声明核对。
做法：自己按 5 种不同顺序调用同一批只读谓词，构造等价 layers dict，
逐处比对 resolve_conflicts 的 (token,pos)->verdict 映射与 conflicts 集合。
若「顺序」参与消解，不同顺序会得到不同真值；否则完全一致。
另核：设计 §3(c):269 声称 conflicts[] 按 pos 升序打印，代码是否实装。
零真机、零采样。python -I -X utf8 <绝对路径>。
"""
import hashlib
import importlib.util
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_pipeline_20261109"
sys.path.insert(0, str(WD))
import _gp_pipeline as P

g7, n13, T = P.load_predicates()
REQ = ["被核对象", "SHA256", "字节数"]
texts = [
    "grep 结果：已生效 0 命中\n本笔已入账。",
    "不宣告 X 已生效，但 Y 已入账",
    "## 2 上游指纹 + 已入账 grep 结果\n本笔已入账，可应用母本",
    "并非不宣告已生效",
]


def build_layers(text, tokens, order):
    cache = {}

    def R9():
        if "R9" not in cache:
            p, w = g7.r9_check(text, REQ)
            cache["R9"] = {"problems": p, "warnings": w}
        return cache["R9"]

    def R10():
        if "R10" not in cache:
            p, w, h = g7.r10_scan(text, tokens)
            cache["R10"] = {"problems": p, "warnings": w, "hits": h}
        return cache["R10"]

    def R12():
        if "R12" not in cache:
            p, h = g7.r12_scan(text, tokens)
            cache["R12"] = {"problems": p, "hits": h}
        return cache["R12"]

    def N13():
        if "N13" not in cache:
            p, d = n13.r13_assertions(text, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
            cache["N13"] = {"problems": p, "details": d}
        return cache["N13"]

    def R11():
        if "R11" not in cache:
            p, w, b = g7.r11_scan(text, WD, root=ROOT)
            cache["R11"] = {"problems": p, "warnings": w, "bindings": b}
        return cache["R11"]

    fns = {"R9": R9, "R10": R10, "R12": R12, "N13": N13, "R11": R11}
    for k in order:                 # ★ 唯一变量：调用先后
        fns[k]()
    return {k: cache[k] for k in ("R9", "R10", "R12", "N13", "R11")}


ORDERS = [
    ("data_dependency", ["R9", "R10", "R12", "N13", "R11"]),
    ("reversed", ["R11", "N13", "R12", "R10", "R9"]),
    ("n13_first", ["N13", "R9", "R11", "R12", "R10"]),
    ("r9r11_first", ["R9", "R11", "N13", "R12", "R10"]),
    ("shuffled", ["R12", "R9", "R11", "R10", "N13"]),
]
print("===== ⑥ 顺序是否影响逐 span 裁决 =====")
all_equal = True
for ti, text in enumerate(texts):
    base = None
    print("\n[text %d] %r" % (ti, text[:60]))
    for name, order in ORDERS:
        L = build_layers(text, T, order)
        rows, conflicts, summary = P.resolve_conflicts(text, T, L, T)
        key = {(r["token"], r["pos"]): (r["verdict"], tuple(r["rules"]),
                                       r["r10"], r["r12"], r["n13"]) for r in rows}
        ck = sorted((c["token"], c["pos"], c["resolved"], c["final"]) for c in conflicts)
        sig = {"rows": sorted((k[0], k[1], v[0], v[1]) for k, v in key.items()),
               "conflicts": ck, "summary": summary}
        if base is None:
            base = sig
            eq = True
        else:
            eq = (sig == base)
        all_equal &= eq
        print("  %-16s equal_to_first=%s summary=%s" % (name, eq, summary))
        print("     rows(pos order as produced) =", [(r["token"], r["pos"], r["verdict"])
                                                    for r in rows])
print("\nALL_ORDERS_SAME_TRUTH =", all_equal)

# §3(c):269 「conflicts[] 的打印顺序按 pos 升序」是否实装
print("\n===== §3(c) 报告次序声明核对 =====")
for ti, text in enumerate(texts):
    L = build_layers(text, T, ORDERS[0][1])
    rows, conflicts, _ = P.resolve_conflicts(text, T, L, T)
    rp = [r["pos"] for r in rows]
    cp = [c["pos"] for c in conflicts]
    print("  text%d rows_pos=%s asc=%s | conflicts_pos=%s asc=%s" %
          (ti, rp, rp == sorted(rp), cp, cp == sorted(cp)))
src = (WD / "_gp_pipeline.py").read_text(encoding="utf-8")
print("  pipeline 源码含 sorted(..pos..) =", "sorted" in src and "pos" in src)
print("  pipeline 源码 tok_set 定义行 =",
      [l.strip() for l in src.splitlines() if "tok_set" in l][:4])

# 跨进程确定性（set 迭代顺序）
print("\n===== 跨进程 row 顺序确定性（set 迭代）=====")
import subprocess
cmd = [sys.executable, "-I", "-X", "utf8", "-c",
       "import sys;sys.path.insert(0,r'%s');import _gp_pipeline as P;"
       "g,n,T=P.load_predicates();"
       "r=P.gate_check('不宣告 X 已生效，但 Y 已入账',T,r'%s',g,n,T);"
       "print([(x['token'],x['pos']) for x in r['_rows']])" % (str(WD), str(WD))]
outs = []
for i in range(4):
    o = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    outs.append(o.stdout.strip())
    print("  run%d = %s" % (i, o.stdout.strip()))
print("  all_same =", len(set(outs)) == 1)
