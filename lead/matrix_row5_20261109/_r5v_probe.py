# -*- coding: utf-8 -*-
# _r5v_probe.py — 复核员独立验证：
#  (P1) 候选顶层副作用 AST 扫描（import 安全性自证）
#  (P2) classify_except_freshness 分支码序（AST 顶层 if 链独立排序）
#  (P3) 标准隔离加载真实 classify_except_freshness，9 pre × 8 post = 72 格
#  (P4) make_pre_freshness_snapshot 运行期探针（临时件在写域内，纯只读函数）
#  (P5) STATE_MATRIX 逐行 claimant 交叉表（read_error 格的登记归属）
import ast, importlib.util, json, shutil, sys, os

WRITE = r"D:\Project\ra2-campaign-forge\lead\matrix_row5_20261109"
CAND = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"
MATRIX = r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\STATE_MATRIX.json"

src = open(CAND, "rb").read().decode("utf-8")
tree = ast.parse(src)
print("== P1 top-level side-effect scan ==")
ALLOWED_CALLS = {"SetProcessDPIAware"}
for node in tree.body:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        f = node.value.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "?")
        tag = "OK" if name in ALLOWED_CALLS else "REVIEW"
        print(f"  top-level call line {node.lineno}: {name} [{tag}]")
guarded = any(isinstance(n, ast.If) and
              isinstance(n.test, ast.Compare) and
              getattr(n.test.left, "id", "") == "__name__"
              for n in tree.body)
print(f"  __main__ guard present: {guarded}")

print("== P2 classify_except_freshness branch order (AST, own implementation) ==")
fn = None
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name == "classify_except_freshness":
        fn = n
if fn is None:
    print("  !! function not found"); sys.exit(1)

def verdicts_in(node):
    out = []
    for sub in ast.walk(node):
        if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                and sub.func.id == "_finish" and sub.args
                and isinstance(sub.args[0], ast.Constant)):
            out.append((sub.lineno, sub.args[0].value))
    return out

print(f"  func span {fn.lineno}-{fn.end_lineno}")
for stmt in fn.body:
    if isinstance(stmt, ast.If):
        cond = ast.unparse(stmt.test)
        vs = verdicts_in(stmt)
        print(f"  line {stmt.lineno:5d} if {cond}")
        for vln, v in vs:
            print(f"          -> {v} (line {vln})")

print("== P3 isolated import + 72-cell probe ==")
spec = importlib.util.spec_from_file_location("r5v_cand", CAND)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except SystemExit as e:
    print(f"  !! SystemExit at import: {e!r}"); sys.exit(1)
cls = mod.classify_except_freshness
states = mod.FRESHNESS_SNAPSHOT_STATES
print(f"  FRESHNESS_SNAPSHOT_STATES = {states}")

pres = {
    "None":        None,
    "emptydict":   {},
    "missing_st":  {"sha256": "x"},                    # 缺 state
    "dirty":       {"state": 123},                     # 脏值
    "expl_unknown":{"state": "unknown"},               # 显式 unknown
    "absent_conf": {"state": "absent_confirmed"},
    "error":       {"state": "error", "error": "boom: 1"},
    "present_sha": {"state": "present", "sha256": "A"*64, "mtime_pre": 100.0},
    "present_nosh":{"state": "present", "sha256": None, "mtime_pre": 100.0},
}
posts = {
    "re_nofile":   {"read_error": "Err: x", "exists": None},
    "re_exist_nosha": {"read_error": "Err: x", "exists": True},
    "re_exist_sha":   {"read_error": "Err: x", "exists": True, "sha256": "B"*64},
    "nore_nofile": {"read_error": None, "exists": False},
    "nore_exist_nosha": {"read_error": None, "exists": True},
    "nore_exist_difsha": {"read_error": None, "exists": True, "sha256": "B"*64},
    "nore_same_mt_same": {"read_error": None, "exists": True, "sha256": "A"*64, "mtime_post": 100.0},
    "nore_same_mt_up":   {"read_error": None, "exists": True, "sha256": "A"*64, "mtime_post": 200.0},
}
cells = {}
for pn, pv in pres.items():
    for qn, qv in posts.items():
        r = cls(pv, qv)
        cells[(pn, qn)] = (r["verdict"], r["confidence"], r["is_new"],
                           r["usable_as_crash_evidence"])
        print(f"  {pn:13s} x {qn:20s} -> verdict={r['verdict']:<22s} conf={r['confidence']:<6s} "
              f"is_new={r['is_new']!s:<5s} usable={r['usable_as_crash_evidence']}")
print(f"  CELLS {len(cells)}")

checks = []
# C1: 9 类 pre × 一切 read_error 格 -> post_read_error
re_q = ["re_nofile", "re_exist_nosha", "re_exist_sha"]
c1 = all(cells[(pn, q)][0] == "post_read_error" for pn in pres for q in re_q)
checks.append(("C1 all-9-pre x read_error -> post_read_error", c1))
# C2: 第二 post_read_error 出口（缺 post.sha256）present 独占
c2 = (cells[("present_sha", "nore_exist_nosha")][0] == "post_read_error"
      and cells[("absent_conf", "nore_exist_nosha")][0] == "new_first_appearance"
      and cells[("expl_unknown", "nore_exist_nosha")][0] == "unknown"
      and cells[("error", "nore_exist_nosha")][0] == "error_pre_snapshot")
checks.append(("C2 missing-post-sha exit present-only", c2))
# C3: read_error 格三元组恒 none / None / false
c3 = all(cells[(pn, q)][1] == "none" and cells[(pn, q)][2] is None
         and cells[(pn, q)][3] is False for pn in pres for q in re_q)
checks.append(("C3 read_error cells conf=none is_new=None usable=False", c3))
# C4: 基线格（不涉 read_error）标签不漂移
c4 = (cells[("None", "nore_nofile")][0] == "unknown"
      and cells[("error", "nore_nofile")][0] == "error_pre_snapshot"
      and cells[("expl_unknown", "nore_nofile")][0] == "unknown")
checks.append(("C4 baseline non-error labels unchanged", c4))
for name, ok in checks:
    print(f"  {name}: {'PASS' if ok else 'FAIL'}")

print("== P4 make_pre runtime probe (temp dir inside write domain) ==")
tmp = WRITE + os.sep + "_r5v_tmp_probe"
os.makedirs(tmp, exist_ok=True)
try:
    mp = mod.make_pre_freshness_snapshot
    s_absent = mp(tmp + os.sep + "absent_probe.txt")
    print(f"  absent path -> state={s_absent['state']} sha={s_absent['sha256']}")
    pfile = tmp + os.sep + "real.txt"
    with open(pfile, "wb") as fh:
        fh.write(b"hello")
    s_present = mp(pfile)
    h12 = s_present["sha256"][:12] if s_present["sha256"] else "NONE"
    print(f"  present file -> state={s_present['state']} sha12={h12} "
          f"(sha computed: {s_present['sha256'] is not None})")
    s_err = mp(None)   # Path(None) 在 try 内抛 TypeError => state=error
    err60 = repr(s_err["error"])[:60]
    print(f"  Path(None)  -> state={s_err['state']} err={err60}")
    got = [s_absent["state"], s_present["state"], s_err["state"]]
    print(f"  explicit unknown-state produced at runtime: {'unknown' in got}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("== P5 STATE_MATRIX claimant cross-tab for read_error cells ==")
rows = json.load(open(MATRIX, encoding="utf-8"))
for st in states:
    cl = [(i+2, r["state"], r["verdict"], r["condition"][:40])
          for i, r in enumerate(rows) if r["preState"] == st]
    code_v = "post_read_error"
    print(f"  preState={st:16s} read_error-cell code verdict={code_v}")
    for ln, state, verdict, cond in cl:
        mark = "MATCH" if state == code_v else "MISLABEL"
        print(f"     row:{ln:<3d} state={state:<18s} verdict={verdict:<20s} [{mark}] cond={cond}")
    other = [i+2 for i, r in enumerate(rows) if r["preState"] != st]
    print(f"     rows with other preState (cannot claim): {other}")
