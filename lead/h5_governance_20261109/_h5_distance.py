# -*- coding: utf-8 -*-
"""第二步(d)：证明「只检查 distance」不够的实跑反例。
四个 pair：同一/近似距离下，真值相反；再用 R12 的 24 字回看窗口径验证。
只读既有件，输出落本任务写域。"""
import sys, json
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
import importlib.util


def _imp(name, p):
    s = importlib.util.spec_from_file_location(name, str(p))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


OLD = _imp("_h5_d_old", ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py")
NEW = _imp("_h5_d_new", HERE / "_h5_v12_patched.py")
G7 = _imp("_h5_d_g7", ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")

PAIRS = [
 # (组, 文本, token, 否定/禁止词, 期望, 说明)
 ("A 同距~10字",
  "不得写成未入账的本笔已入账", "已入账", "不得", "CATCH",
  "禁止词在前且 <24 字，但它是「未入账」的定语；token 是后半句真断言"),
 ("A 同距~10字",
  "不得宣告 N-4 正式绑定已生效", "已生效", "不得", "PASS",
  "禁止词在前且 <24 字，真前向管辖"),
 ("B 长距>24字",
  "不宣告 N-4 正式绑定已生效", "已生效", "不", "PASS",
  "距离短但需「宣告→已生效」辖域路径"),
 ("B 长距>24字",
  "本笔已入账 0 命中不得写成未入账", "已入账", "不得", "CATCH",
  "距离短，但禁止词在 token【之后】，纯距离法必然误豁免"),
 ("C 跨子句",
  "不宣告 N-4 已生效，但本笔已入账", "已入账", "不", "CATCH",
  "「不」距 token 约 13 字且在 24 字窗内，但已跨「，但」另起断言"),
 ("C 跨子句",
  "不宣告 N-4 已生效；本笔已入账", "已入账", "不", "CATCH",
  "跨子句；R10 的 CLAUSE_BREAK 不含分号时同样污染"),
 ("D 双重否定",
  "并非不宣告已生效", "已生效", "不", "CATCH",
  "距 token 极近、否定词计数=2（偶数），纯距离/奇偶法误豁免"),
 ("D 双重否定",
  "不宣告已生效", "已生效", "不", "PASS",
  "同型单重否定，应豁免"),
]


def at(mod, text, tok):
    p = text.find(tok)
    r = mod.classify_v12(text, p, p + len(tok), tok)
    return "PASS" if r["verdict"] == "V1" else "CATCH", r


rows, lines = [], []
lines.append("=== 第二步(d) 只检查 distance 不够：实跑反例 ===")
for grp, text, tok, neg, expect, note in PAIRS:
    p = text.find(tok)
    dist = p - text.find(neg) if text.find(neg) >= 0 else -1
    ctx = G7.r10_context(text, p, p + len(tok))
    o, orr = at(OLD, text, tok)
    n, nrr = at(NEW, text, tok)
    r = {"group": grp, "text": text, "token": tok, "neg": neg,
         "neg_to_token_chars": dist, "r10_neg_count": ctx["neg_count"],
         "r10_kind": ctx["kind"], "r10_dbl": ctx["dbl"],
         "expect": expect, "old": o, "new": n, "note": note,
         "old_hard": orr["hard"], "new_override": nrr["override"]}
    rows.append(r)
    lines.append("[%s] dist=%-3s r10=%-12s neg_count=%d dbl=%s | exp=%-5s old=%-5s new=%-5s | %s" %
                 (grp, dist, ctx["kind"], ctx["neg_count"], ctx["dbl"],
                  expect, o, n, note))
    lines.append("     text = %s" % text)

(HERE / "_h5_distance_out.json").write_text(
    json.dumps({"rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
(HERE / "_h5_distance_out.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print("\nwritten: _h5_distance_out.json / _h5_distance_out.txt")
