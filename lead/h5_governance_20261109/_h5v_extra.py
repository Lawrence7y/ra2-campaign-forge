# -*- coding: utf-8 -*-
r"""_h5v_extra.py — 补充复核：撰写人 8 条距离反例、『不得…不得』相距、根因 trace。"""
import sys, json, importlib.util, re, hashlib
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = ROOT / "lead" / "h5_governance_20261109"
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OLD = _import("_h5v_old3", RULE)
NEW = _import("_h5v_new3", HERE / "_h5v_patched.py")
P = _import("_h5v_paste3", HERE / "_h5_pasteable.py")


def run(mod, text, tok):
    p = text.find(tok)
    r = mod.classify_v12(text, p, p + len(tok), tok)
    return ("PASS" if r["verdict"] == "V1" else "CATCH"), r


def unit_pre_post(text, tok):
    p = text.find(tok)
    ls = text.rfind("\n", 0, p) + 1
    le = text.find("\n", p)
    line = text[ls:le if le >= 0 else len(text)]
    rel = p - ls
    cuts = [0] + [m.end() for m in re.finditer(r"[。！？；\n]", line)] + [len(line)]
    cuts = sorted(set(cuts))
    U = line
    for a, b in zip(cuts, cuts[1:]):
        if a <= rel < b:
            U, rel = line[a:b], rel - a
            break
    return U, U[:rel], U[rel + len(tok):]


# ---- 撰写人 §2.4 的 8 条距离反例（自己抄自己跑，不采信其输出文件） ----
DIST = [
 ("A1", "不得写成未入账的本笔已入账", "已入账", "CATCH"),
 ("A2", "不得宣告 N-4 正式绑定已生效", "已生效", "PASS"),
 ("B1", "不宣告 N-4 正式绑定已生效", "已生效", "PASS"),
 ("B2", "本笔已入账 0 命中不得写成未入账", "已入账", "CATCH"),
 ("C1", "不宣告 N-4 已生效，但本笔已入账", "已入账", "CATCH"),
 ("C2", "不宣告 N-4 已生效；本笔已入账", "已入账", "CATCH"),
 ("D1", "并非不宣告已生效", "已生效", "CATCH"),
 ("D2", "不宣告已生效", "已生效", "PASS"),
]
print("=== 撰写人 8 条距离反例（OLD / NEW / expect） ===")
dist_rows = []
for cid, text, tok, exp in DIST:
    o, _ = run(OLD, text, tok)
    n, _ = run(NEW, text, tok)
    print("%-3s exp=%-5s old=%-5s new=%-5s newOK=%s   %s" %
          (cid, exp, o, n, n == exp, text))
    dist_rows.append(dict(id=cid, expect=exp, old=o, new=n, ok=n == exp))
print("8 条 new = %d/8" % sum(x["ok"] for x in dist_rows))

# ---- 『不得…不得』相距 / 双禁止夹击 ----
SEP = [
 ("S1", "不得写成已入账，不得重复登记", "已入账", "PASS",
  "前向『不得写成』真管辖，后置第二个『不得』在 post（G1）"),
 ("S2", "不得重复登记，本笔已入账不得写成未入账", "已入账", "CATCH",
  "两个『不得』相距，token 夹在中间：第一个管辖『登记』，第二个在 post"),
 ("S3", "不得写成未入账，不得宣告本笔已入账", "已入账", "PASS",
  "第二个『不得宣告』前向真管辖"),
 ("S4", "已入账不得改写，也不得写成未入账", "已入账", "CATCH",
  "两处『不得』都在 post（后向禁止相距）"),
]
print("\n=== 『不得…不得』相距 4 条 ===")
sep_rows = []
for cid, text, tok, exp, why in SEP:
    o, _ = run(OLD, text, tok)
    n, nr = run(NEW, text, tok)
    print("%-3s exp=%-5s old=%-5s new=%-5s newOK=%-5s hard=%r ov=%r" %
          (cid, exp, o, n, n == exp, nr["hard"], nr["override"]))
    print("     %s" % why)
    sep_rows.append(dict(id=cid, expect=exp, old=o, new=n, ok=n == exp, why=why))

# ---- 根因 trace：h5_govern 对失败样本的实际内部量 ----
print("\n=== 根因 trace（h5_govern 输入/输出） ===")
TRACE = ["不得把 N-4 写成已入账", "不得把「N-4」写成已入账",
         "不得把本笔写成已入账", "不，已入账", "不，本笔已入账",
         "非写成已入账不可", "没法不宣告本件已生效",
         "不可能/未覆盖：本笔已入账不得写成未入账"]
traces = []
for text in TRACE:
    tok = "已入账" if "已入账" in text else "已生效"
    U, pre, post = unit_pre_post(text, tok)
    g = P.h5_govern(pre, post)
    d, r = run(NEW, text, tok)
    print("text=%r tok=%s" % (text, tok))
    print("   U=%r pre=%r post=%r" % (U, pre, post))
    print("   h5_govern -> adj=%s prohibit=%s double=%s dn=%r shapes=%r scope=%r" %
          (g["adj_neg"], g["prohibit_governs"], g["double_neg"], g["dn_hit"],
           g["shapes"], g["scope"]))
    print("   NEW=%s hard=%r override=%r" % (d, r["hard"], r["override"]))
    traces.append(dict(text=text, token=tok, U=U, pre=pre, post=post,
                       gov=g, new=d, hard=r["hard"], override=r["override"]))

# ---- 桥接 filler 长度阈值实测：把字宾语长度 0..8 ----
print("\n=== G3 形状b 把字补语长度敏感性（真禁止管辖，应全 PASS） ===")
len_rows = []
for k in range(0, 9):
    obj = "字" * k
    text = "不得把%s写成已入账" % obj
    tok = "已入账"
    d, r = run(NEW, text, tok)
    U, pre, post = unit_pre_post(text, tok)
    g = P.h5_govern(pre, post)
    print("  obj_len=%d new=%-5s bridge=%-5s shapes=%r  %s" %
          (k, d, g["prohibit_governs"], g["shapes"], text))
    len_rows.append(dict(obj_len=k, new=d, expect="PASS", ok=d == "PASS",
                         bridge=g["prohibit_governs"], shapes=g["shapes"]))
print("  应全 PASS，实际 %d/%d PASS；失败 obj_len = %s" %
      (sum(x["ok"] for x in len_rows), len(len_rows),
       [x["obj_len"] for x in len_rows if not x["ok"]]))

(HERE / "_h5v_extra_out.json").write_text(
    json.dumps({"dist": dist_rows, "sep": sep_rows, "traces": traces, "filler_len": len_rows},
               ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _h5v_extra_out.json")
