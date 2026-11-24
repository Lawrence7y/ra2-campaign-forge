# -*- coding: utf-8 -*-
"""_rv2_probe_20261109.py — A/B 裁决修订稿取证探针（零写入被核域；本脚本只读）。

不 import 候选模块；对 classify_except_freshness 的 if 链做受限 AST 求值
（只支持该函数实际用到的节点形态，遇不支持节点即中止报错）。
矩阵 claimant 按「耦合件 MATRIX_ROW5_COUPLING.md:67 匹配键 = preState 字段 +
condition 前件」（STRICT）与「condition 文本承载路由、preState=登记示例」
（LOOSE）两种口径分别仿真；处方后（B 文案）按同一双口径重算。
对照批评点：上轮 _ab_probe.py:220-230 的 after-B 路由为硬编码期望值；
本探针的 claimant 覆盖域亦为手工编码（自然语言 condition 无法机器化），
但在输出中逐条注明编码依据，且 actual 路由全部来自候选自身 AST 求值。
"""
import ast
import hashlib
import json
import os
import sys

BASE = "D:/Project/ra2-campaign-forge"
P_JSON = os.path.join(BASE, "lead/b2b_design_20261106/STATE_MATRIX.json")
P_DESIGN = os.path.join(BASE, "lead/b2b_design_20261106/B2B_DESIGN.md")
P_CAND = os.path.join(BASE, "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py")
P_RULING = os.path.join(BASE, "lead/matrix_ab_ruling_20261109/_ab_RULING_MATRIX_AB_20261109.md")

fails = []

def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (("  || " + str(detail)) if detail else ""))
    if not ok:
        fails.append(name)

# ---------- 0 指纹 ----------
print("== F0 fingerprints (hashlib, read-only) ==")
for p in (P_JSON, P_DESIGN, P_CAND):
    b = open(p, "rb").read()
    print("  %s  %d  %s" % (hashlib.sha256(b).hexdigest(), len(b), os.path.basename(p)))

# ---------- 1 矩阵行 ----------
rows = json.loads(open(P_JSON, encoding="utf-8").read())
check("F1 STATE_MATRIX.json = 14 data rows", len(rows) == 14, len(rows))
print("  :2 cond = %s" % rows[0]["condition"])
print("  :4 cond = %s" % rows[2]["condition"])
print("  :5 cond = %s" % rows[4]["condition"])
print("  :6 cond = %s" % rows[5]["condition"])

# ---------- 2 候选 AST：函数定位 + if 链 ----------
src = open(P_CAND, encoding="utf-8").read()
tree = ast.parse(src)
fn = None
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "classify_except_freshness":
        fn = node
check("F2 classify_except_freshness located", fn is not None,
      "%d-%d" % (fn.lineno, fn.end_lineno) if fn else "")
states_const = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "FRESHNESS_SNAPSHOT_STATES" for t in node.targets):
        states_const = ast.literal_eval(node.value)
check("F3 FRESHNESS_SNAPSHOT_STATES = 4-tuple", states_const == ("unknown", "absent_confirmed", "present", "error"), states_const)

chain = [s for s in fn.body if isinstance(s, ast.If)]
chain_lines = [s.lineno for s in chain]
check("F4 if-chain lines", chain_lines == [4637, 4643, 4648, 4652, 4657, 4666, 4673, 4678, 4681, 4686, 4690, 4693],
      chain_lines)

# ---------- 3 受限求值器 ----------
class Unsupported(Exception):
    pass

def ev(node, env):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise Unsupported("Name %s" % node.id)
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(ev(e, env) for e in node.elts)
    if isinstance(node, ast.BoolOp):
        vals = [ev(v, env) for v in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not ev(node.operand, env)
    if isinstance(node, ast.Compare):
        left = ev(node.left, env)
        for op, comp in zip(node.ops, node.comparators):
            r = ev(comp, env)
            if isinstance(op, ast.Eq):
                ok = left == r
            elif isinstance(op, ast.NotEq):
                ok = left != r
            elif isinstance(op, ast.In):
                ok = left in r
            elif isinstance(op, ast.NotIn):
                ok = left not in r
            elif isinstance(op, ast.Is):
                ok = left is r
            elif isinstance(op, ast.Lt):
                ok = left < r
            elif isinstance(op, ast.LtE):
                ok = left <= r
            else:
                raise Unsupported("cmp op %r" % op)
            if not ok:
                return False
            left = r
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub):
        return ev(node.left, env) - ev(node.right, env)
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr == "get":
            obj = ev(f.value, env)
            args = [ev(a, env) for a in node.args]
            return obj.get(*args)
        if isinstance(f, ast.Name) and f.id in ("float", "abs", "bool"):
            return {"float": float, "abs": abs, "bool": bool}[f.id](ev(node.args[0], env))
        raise Unsupported("call %r" % ast.dump(f))
    raise Unsupported("%s" % type(node).__name__)

def finish_args(call_node):
    if not (isinstance(call_node, ast.Call) and isinstance(call_node.func, ast.Name)
            and call_node.func.id == "_finish"):
        raise Unsupported("return not _finish: %s" % ast.dump(call_node))
    v = ast.literal_eval(call_node.args[0])
    c = ast.literal_eval(call_node.args[1])
    n = ast.literal_eval(call_node.args[2])
    return (v, c, n)

def run_body(stmts, env):
    for s in stmts:
        if isinstance(s, ast.If):
            if ev(s.test, env):
                r = run_body(s.body, env)
                if r is not None:
                    return r
            elif s.orelse:
                r = run_body(s.orelse, env)
                if r is not None:
                    return r
        elif isinstance(s, ast.Return):
            return finish_args(s.value)
    return None

def actual_route(pre_snap, post):
    pre = pre_snap if isinstance(pre_snap, dict) else {}
    st = pre.get("state")
    if st not in states_const:
        st = "unknown"
    env = {"st": st, "pre": pre, "post": post,
           "post_exists": bool(post.get("exists")),
           "pre_sha": pre.get("sha256"), "post_sha": post.get("sha256"),
           "pre_mt": pre.get("mtime_pre"), "post_mt": post.get("mtime_post"),
           "FRESHNESS_SNAPSHOT_STATES": states_const}
    r = run_body(fn.body, env)
    return (r[0], r[1], r[2], False)  # usable 恒 False：候选 :4625 初值 + :4631 _finish 实参（本轮实读）

# ---------- 4 网格 ----------
PRE_KINDS = ["none", "empty", "missing", "dirty", "expl_unknown",
             "absent", "present_sha", "present_nosh", "error"]
def mk_pre(k):
    if k == "none":
        return None
    if k == "empty":
        return {}
    if k == "missing":
        return {"exists": True}
    if k == "dirty":
        return {"state": "bogus", "exists": True}
    if k == "expl_unknown":
        return {"state": "unknown", "exists": None}
    if k == "absent":
        return {"state": "absent_confirmed", "exists": False}
    if k == "present_sha":
        return {"state": "present", "exists": True, "sha256": "A" * 64, "mtime_pre": 100.0}
    if k == "present_nosh":
        return {"state": "present", "exists": True, "sha256": None, "mtime_pre": 100.0}
    if k == "error":
        return {"state": "error", "error": "OSError: x"}
    raise AssertionError(k)

POST_KINDS = ["re_none", "re_true", "nofile", "no_post_sha",
              "sha_diff", "mt_same", "mt_up", "mt_down", "mt_missing"]
def mk_post(k):
    base = {"exists": None, "size": None, "sha256": None, "mtime_post": None, "read_error": None}
    if k == "re_none":
        base["read_error"] = "OSError: read fail"          # read/stat 失败：exists 停在 None（:4786 前未置位）
    elif k == "re_true":
        base.update({"exists": True, "size": 5, "sha256": "B" * 64, "mtime_post": 100.0,
                     "read_error": "OSError: write fail"})  # write_bytes 失败：:4769 先置 exists=True
    elif k == "nofile":
        base["exists"] = False
    elif k == "no_post_sha":
        base.update({"exists": True, "size": 5, "mtime_post": 100.0})
    elif k == "sha_diff":
        base.update({"exists": True, "sha256": "C" * 64, "mtime_post": 100.0})
    elif k == "mt_same":
        base.update({"exists": True, "sha256": "A" * 64, "mtime_post": 100.0})
    elif k == "mt_up":
        base.update({"exists": True, "sha256": "A" * 64, "mtime_post": 200.0})
    elif k == "mt_down":
        base.update({"exists": True, "sha256": "A" * 64, "mtime_post": 50.0})
    elif k == "mt_missing":
        base.update({"exists": True, "sha256": "A" * 64, "mtime_post": None})
    return base

def prestate_key(pk):
    return {"none": "unknown", "empty": "unknown", "missing": "unknown", "dirty": "unknown",
            "expl_unknown": "unknown", "absent": "absent_confirmed",
            "present_sha": "present", "present_nosh": "present", "error": "error"}[pk]

UNCOLLECTED = ["none", "empty", "missing", "dirty"]
RE_KINDS = ["re_none", "re_true"]
EXISTS_TRUE = ["no_post_sha", "sha_diff", "mt_same", "mt_up", "mt_down", "mt_missing"]
# 「跑后在 / 在场（存在性硬证）」字面覆盖一切 exists=True 形态——含 write_bytes 失败型
# re_true（:4769 先置 exists=True 后 :4772 才可失败）：:6/:13 的前件按字面含 re_true（O1′/W3 机制）。
ET_COVER = EXISTS_TRUE + ["re_true"]

# claimant 覆盖域手工编码（依据 = 各行 condition 原文，见输出注记；STRICT = 耦合件:67 合取键）
def cov(rowline, pk, qk, strict):
    u = prestate_key(pk)
    if rowline == 2:
        base = (pk in UNCOLLECTED) if strict else (u == "unknown")   # 宽键读法含显式 unknown（耦合件:112）
        return base                                                  # 原文「跑后任意文件状态」= post 任意
    if rowline == 3:
        return (pk == "expl_unknown") and (qk == "nofile")           # 「pre.state 显式 unknown + 跑后无件」
    if rowline == 4:
        return (pk == "error")                                       # 「snap.error 非空」无跑后限定
    if rowline == 5:
        if strict:
            return (u == "present") and (qk in RE_KINDS)             # 键=present 独占（耦合件:74）
        return qk in RE_KINDS                                        # 宽读法 + 处方注记「pre 任意态均落本行」
    if rowline == 6:
        return (pk == "absent") and (qk in ET_COVER)                 # 「跑后在场（存在性硬证）」=exists=True（含 re_true）
    if rowline == 7:
        return (pk == "absent") and (qk == "nofile")
    if rowline == 8:
        return (pk == "present_sha") and (qk == "mt_same")
    if rowline == 9:
        return (pk == "present_sha") and (qk == "mt_missing")
    if rowline == 10:
        return (pk == "present_sha") and (qk == "sha_diff")
    if rowline == 11:
        return (pk == "present_sha") and (qk == "mt_up")
    if rowline == 12:
        return (pk == "present_sha") and (qk == "mt_down")
    if rowline == 13:
        return (pk == "present_nosh") and (qk in ET_COVER)           # 「跑前在+跑后在+缺 pre.sha256」（含 re_true → W3 重叠）
    if rowline == 14:
        return (pk == "present_sha") and (qk == "no_post_sha")
    if rowline == 15:
        return (u == "present") and (qk == "nofile")
    raise AssertionError(rowline)

def rowvals(i):
    r = rows[i - 2]
    return (r["verdict"], r["confidence"], r["usableAsCrashEvidence"])

# 处方后 B 文案的覆盖调整（改1/改2/改3；改4-6 为镜像不改 JSON 行）
def cov_after_b(rowline, pk, qk, strict):
    if rowline == 2:                                                  # 改1：前件加「跑后读取正常」+ 分流句
        if strict:
            return (pk in UNCOLLECTED) and (qk not in RE_KINDS)
        return (prestate_key(pk) == "unknown") and (qk not in RE_KINDS)
    if rowline == 4:                                                  # 改3：随批句
        if strict:
            return pk == "error"                                      # 严格字面：注记不缩覆盖
        return (pk == "error") and (qk not in RE_KINDS)               # 宽读法：随批句把 re 格让渡给 :5
    if rowline == 5:
        return cov(5, pk, qk, strict)                                 # 改2 注记；覆盖域同上（按口径）
    return cov(rowline, pk, qk, strict)

PRIORITY = 5  # 改2 注记末句「匹配以本 condition 为准」；:4 分流句/随批句同向

def survey(strict, after_b):
    mislabel, orphan, ok = [], [], 0
    suppressed = []
    for pk in PRE_KINDS:
        for qk in POST_KINDS:
            act = actual_route(mk_pre(pk), mk_post(qk))
            act3 = (act[0], act[1], act[3])  # JSON 无 is_new 字段：可比三元 = verdict/conf/usable（实码 is_new 不入比较）
            cands = []
            for i in range(2, 16):
                f = cov_after_b if after_b else cov
                if f(i, pk, qk, strict):
                    cands.append(i)
            eff = None
            if cands and PRIORITY in cands and after_b:
                eff = PRIORITY
                suppressed.extend([c for c in cands if c != PRIORITY])
            else:
                eff = cands[0] if cands else None
            if not cands:
                orphan.append((pk, qk, act[0]))
            elif all(rowvals(i) == act3 for i in ([eff] if after_b and eff else cands)):
                ok += 1
            else:
                bad = [i for i in cands if rowvals(i) != act3]
                mislabel.append((pk, qk, act[0], bad, [rowvals(i) for i in bad]))
    return ok, mislabel, orphan, suppressed

def report(tag, strict, after_b):
    ok, mis, orph, sup = survey(strict, after_b)
    print("  [%s] OK=%d MISLABEL=%d ORPHAN=%d (81 cells) %s"
          % (tag, ok, len(mis), len(orph),
             ("suppressed-by-priority: %d" % len(set(sup))) if sup else ""))
    for m in mis:
        print("    MISLABEL %s x %s -> actual=%s ; rows %s claim %s" % m)
    for o in orph:
        print("    ORPHAN   %s x %s -> actual=%s" % o)
    return ok, mis, orph

print("== M1 matrix claimant survey, both readings, baseline vs after-B ==")
sb = report("BASELINE-STRICT(耦合件:67 preState+前件)", True, False)
lb = report("BASELINE-LOOSE (condition 文本承载/preState=登记示例)", False, False)
sa = report("AFTER-B-STRICT", True, True)
la = report("AFTER-B-LOOSE (注记路由+优先句被消费方采纳)", False, True)

# 反对意见反例（其回件 §1）：absent_confirmed × read_error(exists=True) 严格键
print("== M2 reviewer counterexample (absent_confirmed x read_error, exists=True) ==")
act = actual_route(mk_pre("absent"), mk_post("re_true"))
print("  actual_AST = %s/%s/%s" % act[:3])
print("  strict claimants rows = %s ; values = %s"
      % ([i for i in range(2, 16) if cov(i, "absent", "re_true", True)],
         [rowvals(i) for i in range(2, 16) if cov(i, "absent", "re_true", True)]))
check("M2 strict: row:6 still claims new_first_appearance/high after B; actual=post_read_error/none",
      rowvals(6) == ("new_first_appearance", "high", False) and act[:3] == ("post_read_error", "none", None))
check("M2b after-B strict: :5 NOT eligible (preState=present != absent)",
      5 not in [i for i in range(2, 16) if cov_after_b(i, "absent", "re_true", True)])

# W2 两独立出口同现（反对意见必答三）
print("== M3 W2 distinct exits: snap.error(:4611) + post.read_error(:4786) co-occur ==")
act = actual_route(mk_pre("error"), mk_post("re_none"))
print("  error x re_none actual_AST = %s/%s/%s" % act[:3])
check("M3 error x read_error -> post_read_error (not error_pre_snapshot)",
      act[:3] == ("post_read_error", "none", None))
check("M3b after-B strict: :4 unchanged coverage -> still claims error x re (W2 open)",
      cov_after_b(4, "error", "re_none", True) and rowvals(4) == ("error_pre_snapshot", "none", False))

# ---------- 5 草案六处「原文」逐字比对 ----------
print("== V1 six original-text verbatim check vs current disk ==")
jl = open(P_JSON, encoding="utf-8").read().splitlines()
dl = open(P_DESIGN, encoding="utf-8").read().splitlines()
rl = open(P_RULING, encoding="utf-8").read().splitlines()
# 期望值 = 草案改动 1-6 的「原文」代码块逐字（草案 :92/:104/:116 与 :128/:140/:152），
# 与现盘对应行做逐字节比对。
orig = {
    ("JSON", 2): jl[1], ("JSON", 5): jl[4], ("JSON", 4): jl[3],
    ("DESIGN", 148): dl[147], ("DESIGN", 151): dl[150], ("DESIGN", 150): dl[149],
}
expect = {
    ("JSON", 2): '  {"state":"unknown","preState":"unknown","condition":"pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后任意文件状态","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},',
    ("JSON", 5): '  {"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false},',
    ("JSON", 4): '  {"state":"error","preState":"error","condition":"跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口，不降级、不静默、不给 high","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},',
    ("DESIGN", 148): dl[147],
    ("DESIGN", 151): dl[150],
    ("DESIGN", 150): dl[149],
}
# DESIGN 三行与草案引用串比对（草案 :128/:140/:152）
d_expect = {
    148: '| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |',
    151: '| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |',
    150: '| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |',
}
n_ok = 0
for (kind, ln), cur in orig.items():
    exp = d_expect[ln] if kind == "DESIGN" else expect[(kind, ln)]
    okk = (cur == exp)
    print("  %s:%d verbatim=%s" % (kind, ln, "MATCH" if okk else "MISMATCH"))
    if okk:
        n_ok += 1
    else:
        print("    disk  = %r" % cur)
        print("    draft = %r" % exp)
check("V1 ORIGINAL_EXACT_TOTAL=6/6_MATCH", n_ok == 6, n_ok)

# ---------- 6 汇总 ----------
print()
print("SUMMARY strict: baseline mislabel=%d orphan=%d ; after-B mislabel=%d orphan=%d"
      % (len(sb[1]), len(sb[2]), len(sa[1]), len(sa[2])))
print("SUMMARY loose : baseline mislabel=%d orphan=%d ; after-B mislabel=%d orphan=%d"
      % (len(lb[1]), len(lb[2]), len(la[1]), len(la[2])))
print("R2_PROBE_ALL_" + ("PASS" if not fails else "FAIL"))
if fails:
    print("FAILED:", fails)
    sys.exit(1)
