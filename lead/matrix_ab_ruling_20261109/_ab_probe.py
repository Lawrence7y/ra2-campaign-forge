# -*- coding: utf-8 -*-
# _ab_probe.py — 方案裁决员独立复核探针（A/B 裁决取证，2026-11-09）。
# 零真机、零采样：不启动 gamemd.exe/ra2loader/YURI.exe，不 taskkill，不读活进程内存；
# 无 hook/MiniDump/SuspendThread/StackWalk/注入/动态内存解析。
# 手段 = 标准 import 协议隔离加载候选真实函数（仅执行模块顶层常量/def，__main__ 有守卫）
#       + AST 静态分析 + 纯内存字典。本探针全程零文件写入（P4 三个 make_pre 调用
#       分别落在「不存在的路径 / 候选自身 / None」，均为纯只读调用，无临时件）。
# 路径安全：全部路径经 safe() 规范化并强制限定在仓库根 BASE 白名单内，拒绝任何越界。
import ast
import importlib.util
import json
import os
import sys

BASE = r"D:\Project\ra2-campaign-forge"


def safe(p):
    """规范化并校验路径必须落在 BASE 白名单内；拒绝 ../ 越界。"""
    rp = os.path.realpath(p)
    root = os.path.realpath(BASE)
    if rp != root and not rp.startswith(root + os.sep):
        raise SystemExit("path outside allowed BASE rejected: %r" % p)
    return rp


CAND = safe(os.path.join(BASE, "lead", "b2b_candidate_lf_20261107", "qc151_trip.candidate_lf.py"))
MATRIX = safe(os.path.join(BASE, "lead", "b2b_design_20261106", "STATE_MATRIX.json"))
WRITE = safe(os.path.join(BASE, "lead", "matrix_ab_ruling_20261109"))

fails = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + "  " + name + (("  || " + detail) if detail else ""))
    if not ok:
        fails.append(name)


# ---------- P0 矩阵被改行原文入档 ----------
rows = json.load(open(MATRIX, encoding="utf-8"))
print("== P0 STATE_MATRIX.json ==")
print("  data rows =", len(rows))
for i in (0, 2, 4):
    print("  :%d state=%s preState=%s" % (i + 2, rows[i]["state"], rows[i]["preState"]))
    print("      condition =", rows[i]["condition"])
    print("      verdict=%s conf=%s usable=%s" % (rows[i]["verdict"], rows[i]["confidence"],
                                                  rows[i]["usableAsCrashEvidence"]))

# ---------- P1 候选 import 安全性自证（AST 顶层副作用扫描） ----------
src = open(CAND, "rb").read().decode("utf-8")
tree = ast.parse(src)
calls = []
for node in tree.body:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        f = node.value.func
        calls.append(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "?"))
guarded = any(isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
              and getattr(n.test.left, "id", "") == "__name__" for n in tree.body)
print("== P1 candidate import-safety scan ==")
print("  top-level calls:", calls, "| __main__ guard:", guarded)
check("P1 import-safe: __main__ guard present & top-level calls subset {SetProcessDPIAware}",
      guarded and set(calls) <= {"SetProcessDPIAware"}, str(sorted(set(calls))))

# ---------- P2 classify_except_freshness 分支码序（AST 独立实现） ----------
fn = None
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name == "classify_except_freshness":
        fn = n
print("== P2 branch order (AST) ==")
print("  func span %d-%d" % (fn.lineno, fn.end_lineno))
order = []
for stmt in fn.body:
    if isinstance(stmt, ast.If):
        vs = [s.args[0].value for s in ast.walk(stmt)
              if isinstance(s, ast.Call) and getattr(s.func, "id", "") == "_finish"
              and s.args and isinstance(s.args[0], ast.Constant)]
        order.append((stmt.lineno, vs))
        print("  line %d: %s -> %s" % (stmt.lineno, ast.unparse(stmt.test)[:58], vs))
exp_lines = [4637, 4643, 4648, 4652, 4657, 4666, 4673, 4678, 4681, 4686, 4690, 4693]
check("P2 if-chain == [4637,4643,4648,4652,4657,4666,4673,4678,4681,4686,4690,4693]"
      " (:4643 read_error 先于 :4648/:4652/:4657/:4666/:4672+)",
      [o[0] for o in order] == exp_lines, str([o[0] for o in order]))

# ---------- P3 隔离 import + 9 pre x 9 post 全格实跑 ----------
spec = importlib.util.spec_from_file_location("ab_cand", CAND)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
cls = mod.classify_except_freshness
print("== P3 isolated import + full grid ==")
print("  FRESHNESS_SNAPSHOT_STATES =", mod.FRESHNESS_SNAPSHOT_STATES)

PRE = {
    "None":       None,
    "empty{}":    {},
    "缺state":    {"sha256": "X", "exists": True},
    "脏值":       {"state": "garbage", "exists": True},
    "显式unknown": {"state": "unknown", "exists": None, "sha256": None, "mtime_pre": None},
    "absent_conf": {"state": "absent_confirmed", "exists": False, "size": None,
                    "sha256": None, "mtime_pre": None},
    "present":    {"state": "present", "exists": True, "size": 3,
                   "sha256": "AAA", "mtime_pre": 1000.0},
    "present缺pre_sha": {"state": "present", "exists": True, "size": 3,
                         "sha256": None, "mtime_pre": 1000.0},
    "error":      {"state": "error", "exists": None, "size": None, "sha256": None,
                   "mtime_pre": None, "error": "OSError: pre-snap boom", "traceback": "tb"},
}
POST = {
    "re(exists=None)":  {"exists": None, "size": None, "sha256": None, "mtime_post": None,
                         "captured_at_iso": "iso", "read_error": "OSError: post-read boom"},
    "re(exists=True)":  {"exists": True, "size": None, "sha256": None, "mtime_post": None,
                         "captured_at_iso": "iso", "read_error": "OSError: post-read boom"},
    "无件":             {"exists": False, "size": None, "sha256": None, "mtime_post": None,
                         "captured_at_iso": "iso", "read_error": None},
    "在场缺post_sha":   {"exists": True, "size": 3, "sha256": None, "mtime_post": 2000.0,
                         "captured_at_iso": "iso", "read_error": None},
    "在场sha异":        {"exists": True, "size": 3, "sha256": "BBB", "mtime_post": 2000.0,
                         "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt同":    {"exists": True, "size": 3, "sha256": "AAA", "mtime_post": 1000.0,
                         "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt升":    {"exists": True, "size": 3, "sha256": "AAA", "mtime_post": 1500.0,
                         "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt降":    {"exists": True, "size": 3, "sha256": "AAA", "mtime_post": 500.0,
                         "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt缺":    {"exists": True, "size": 3, "sha256": "AAA", "mtime_post": None,
                         "captured_at_iso": "iso", "read_error": None},
}
cells = {}
print("  grid (verdict|conf|is_new):")
for pn, pv in PRE.items():
    line = ("  " + pn).ljust(22)
    for qn, qv in POST.items():
        r = cls(pv, qv)
        cells[(pn, qn)] = (r["verdict"], r["confidence"], r["is_new"],
                           r["usable_as_crash_evidence"])
        line += ("%s|%s|%s" % (r["verdict"], r["confidence"], r["is_new"])).ljust(28)
    print(line)
print("  CELLS", len(cells))
check("P3 grid is 9x9=81", len(cells) == 81, str(len(cells)))

RE_Q = ["re(exists=None)", "re(exists=True)"]

# A1 W1 码侧：pre 未采集四变体 + 显式unknown × read_error → post_read_error
ok = all(cells[(pn, q)][:3] == ("post_read_error", "none", None)
         for pn in ("None", "empty{}", "缺state", "脏值", "显式unknown") for q in RE_Q)
check("A1 W1-code-side: 5 pre-uncollected/explicit-unknown x read_error -> post_read_error/none/None", ok)

# A2 W2 码侧：error × read_error → post_read_error（矩阵 :4 声称 error_pre_snapshot）
ok = all(cells[("error", q)][:3] == ("post_read_error", "none", None) for q in RE_Q)
check("A2 W2-code-side: error x read_error -> post_read_error/none/None (:4643 < :4652)", ok)

# A3 O1 码侧：absent_confirmed × read_error（exists=None 与 exists=True 两型）→ post_read_error
ok = all(cells[("absent_conf", q)][:3] == ("post_read_error", "none", None) for q in RE_Q)
check("A3 O1-code-side: absent_confirmed x read_error (both exists shapes) -> post_read_error/none/None", ok)

# A4 :5 自身格正确 + 全部 read_error 格取值卫生
ok = cells[("present", "re(exists=None)")][:3] == ("post_read_error", "none", None)
check("A4 matrix:5 own cell (present x read_error) -> post_read_error/none/None", ok)
ok = all(cells[(pn, q)][1] == "none" and cells[(pn, q)][2] is None
         and cells[(pn, q)][3] is False for pn in PRE for q in RE_Q)
check("A5 all read_error cells conf=none is_new=None usable=False", ok)

# A6 基线格标签不漂移（与矩阵 :2-:15 逐格同值）
baseline = [
    (("absent_conf", "无件"), ("absent_both", "low", False)),
    (("absent_conf", "在场sha异"), ("new_first_appearance", "high", True)),
    (("present", "无件"), ("vanished", "none", None)),
    (("present", "在场缺post_sha"), ("post_read_error", "none", None)),
    (("present", "在场sha异"), ("new_write", "high", True)),
    (("present", "在场sha同mt同"), ("leftover_unchanged", "high", False)),
    (("present", "在场sha同mt升"), ("rewritten_same_content", "medium", True)),
    (("present", "在场sha同mt降"), ("rewritten_same_content", "low", True)),
    (("present", "在场sha同mt缺"), ("leftover_unchanged", "medium", False)),
    (("present缺pre_sha", "无件"), ("vanished", "none", None)),
    (("present缺pre_sha", "在场sha异"), ("error_pre_snapshot", "none", None)),
    (("present缺pre_sha", "在场缺post_sha"), ("error_pre_snapshot", "none", None)),
    (("error", "无件"), ("error_pre_snapshot", "none", None)),
    (("error", "在场sha异"), ("error_pre_snapshot", "none", None)),
    (("显式unknown", "无件"), ("unknown", "none", None)),
    (("显式unknown", "在场sha异"), ("unknown", "none", None)),
    (("None", "在场sha异"), ("unknown", "none", None)),
]
bad = [(k, cells[k], v) for k, v in baseline if cells[k][:3] != v]
check("A6 baseline cells match matrix :2-:15 four-tuples (17 spot cells)", not bad, str(bad))
check("A7 W3: present缺pre_sha x read_error -> post_read_error (:4643 < :4673)",
      cells[("present缺pre_sha", "re(exists=None)")][:3] == ("post_read_error", "none", None))

# ---------- P4 make_pre 运行期探针（全程只读：不存在的路径 / 候选自身 / None） ----------
print("== P4 make_pre_freshness_snapshot read-only probe ==")
mp = mod.make_pre_freshness_snapshot
s_absent = mp(os.path.join(WRITE, "_ab_no_such_probe_file.xyz"))
s_present = mp(CAND)
s_err = mp(None)
states = [s_absent["state"], s_present["state"], s_err["state"]]
print("  nonexistent path -> %s | candidate file itself -> %s (sha computed: %s) | None -> %s"
      % (s_absent["state"], s_present["state"], s_present["sha256"] is not None, s_err["state"]))
check("P4 make_pre: absent->absent_confirmed, present->present(+sha), failure->error;"
      " explicit 'unknown' never produced at runtime",
      states == ["absent_confirmed", "present", "error"], str(states))

# ---------- P5 缺陷复现 + 处方后路由推演（文本层，按本裁决处方文案硬编码） ----------
print("== P5 defect reproduction (matrix literal reading vs code) & post-prescription routing ==")
# 三个活性误配格：矩阵现行 condition 字面读法声称的 verdict vs 实码 verdict
defects = [
    ("W1", "pre=None x read_error", ("None", "re(exists=None)"),
     ":2（「跑后任意文件状态」字面覆盖 read_error 格）", rows[0]["verdict"]),
    ("W2", "error x read_error", ("error", "re(exists=None)"),
     ":4（「snap.error 非空 ⇒ 独立 error 出口」无跑后限定）", rows[2]["verdict"]),
    ("O1'", "absent_confirmed x read_error(exists=True)", ("absent_conf", "re(exists=True)"),
     ":6（「跑后在场（存在性硬证）」字面被 write_bytes 失败型满足）", rows[4]["verdict"]),
]
for tag, label, key, claim_src, claimed in defects:
    actual = cells[key][0]
    print("  [%s] %-42s 矩阵声称=%s（%s） 实码=%s -> %s"
          % (tag, label, claimed, claim_src, actual,
             "MISMATCH" if claimed != actual else "match"))
    check("P5 [%s] defect reproduced (matrix claims %s, code gives %s)" % (tag, claimed, actual),
          claimed != actual)
# 处方后（B）文本层路由推演：:2 新文案把 read_error 格划出；:5 注记声明全部 pre 态落 :5
post_fix = [("W1", ("None", "re(exists=None)"), "post_read_error"),
            ("W2", ("error", "re(exists=None)"), "post_read_error"),
            ("O1'", ("absent_conf", "re(exists=True)"), "post_read_error"),
            ("O1-main", ("absent_conf", "re(exists=None)"), "post_read_error"),
            ("O3", ("None", "re(exists=True)"), "post_read_error")]
for tag, key, routed in post_fix:
    actual = cells[key][0]
    print("  [after-B] %-8s %-38s 处方路由=:5(%s) 实码=%s -> %s"
          % (tag, key[0] + " x " + key[1], routed, actual,
             "RESOLVED" if routed == actual else "STILL-BROKEN"))
    check("P5 [after-B] %s resolved (routed verdict == code verdict)" % tag, routed == actual)

print()
print("AB_PROBE_ALL_" + ("PASS" if not fails else "FAIL"))
if fails:
    print("FAILED:", fails)
    sys.exit(1)
