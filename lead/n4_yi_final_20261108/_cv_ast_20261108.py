# -*- coding: utf-8 -*-
# _cv_ast_20261108.py — 自写 AST 静态提取：_finish 定义/调用、值域常量、调用点计数、禁符号计数（只读，不 import 不执行候选）
import ast, json

BASE = "D:/Project/ra2-campaign-forge/"
CAND   = BASE + "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
MASTER = BASE + "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
MATRIX = BASE + "lead/b2b_design_20261106/STATE_MATRIX.json"

raw = open(CAND, "rb").read()
ctext = raw.decode("utf-8")
clines = ctext.split("\n")
mtree_raw = open(MASTER, "rb").read()
mtext = mtree_raw.decode("utf-8")

tree = ast.parse(raw)
mtree = ast.parse(mtree_raw)

print("== A. FRESHNESS 常量（模块级） ==")
consts = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id.startswith("FRESHNESS"):
                try: consts.setdefault(t.id, (node.lineno, ast.literal_eval(node.value)))
                except Exception: consts.setdefault(t.id, (node.lineno, "<nonliteral>"))
for k in sorted(consts):
    ln, v = consts[k]
    print("  %s @cand:%d = %r" % (k, ln, v))

print("== B. _finish 定义 ==")
fdefs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and "_finish" in n.name]
for n in fdefs:
    print("  def %s @cand:%d..%d, args=%s" % (n.name, n.lineno, n.end_lineno, [a.arg for a in n.args.args]))
print("  source cand:4628-4632:")
for i in range(4628, 4633):
    print("    %d| %s" % (i, clines[i-1][:120]))

print("== C. classify_except_freshness 定义与归一/出口 ==")
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef) and n.name == "classify_except_freshness":
        print("  def @cand:%d..%d" % (n.lineno, n.end_lineno))
print("  source cand:4634-4652:")
for i in range(4634, 4653):
    print("    %d| %s" % (i, clines[i-1][:150]))

print("== D. 全部 _finish 调用（lineno + 关键字字面量） ==")
calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        f = node.func
        nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
        if nm and "_finish" in nm:
            kws = {}
            for kw in node.keywords:
                try: kws[kw.arg] = ast.literal_eval(kw.value)
                except Exception: kws[kw.arg] = "<expr>"
            posv = []
            for a in node.args:
                try: posv.append(ast.literal_eval(a))
                except Exception: posv.append("<expr>")
            calls.append((node.lineno, kws, posv))
calls.sort()
print("  _finish call count:", len(calls))
for ln, kws, posv in calls:
    print("    :%d  pos=%s kw=%s" % (ln, posv, kws))

print("== E. 调用对 vs 矩阵对（互为充要；位置实参 ver=第1位 conf=第2位 is_new=第3位） ==")
data = json.loads(open(MATRIX, "rb").read().decode("utf-8"))
mpairs = sorted({(r["verdict"], r["confidence"]) for r in data})
cpairs = sorted({(p[0], p[1]) for _, _, p in calls
                 if len(p) >= 2 and isinstance(p[0], str) and isinstance(p[1], str)})
print("  matrix pairs (%d):" % len(mpairs), mpairs)
print("  code pairs   (%d):" % len(cpairs), cpairs)
print("  code-not-matrix:", sorted(set(cpairs) - set(mpairs)))
print("  matrix-not-code:", sorted(set(mpairs) - set(cpairs)))
us = sorted({str(p[2]) for _, _, p in calls if len(p) >= 3})
print("  is_new（第3位实参）values at call sites:", us)
print("  usable_as_crash_evidence：非调用实参，_finish 体内硬编码（见 B 段 :4631 = False）")

print("== F. 行号↔(verdict,confidence) 映射（核对审阅员 matrixRows 的码点） ==")
for ln, kws, p in calls:
    print("    :%d -> %s/%s is_new=%r" % (ln, p[0] if len(p) > 0 else "?",
                                          p[1] if len(p) > 1 else "?",
                                          p[2] if len(p) > 2 else "?"))

print("== G. copy_post_except_evidence / finalize_trip / make_pre_freshness_snapshot ==")
for nm in ("copy_post_except_evidence", "finalize_trip", "make_pre_freshness_snapshot"):
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            n2 = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if n2 == nm:
                sites.append((node.lineno, [k.arg for k in node.keywords]))
    print("  %s call sites: %s" % (nm, sites))
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef) and n.name in ("copy_post_except_evidence", "finalize_trip", "make_pre_freshness_snapshot"):
        dfl = [ast.literal_eval(d) if isinstance(d, ast.Constant) else "<expr>" for d in n.args.defaults]
        print("  def %s @cand:%d args=%s defaults=%s" % (n.name, n.lineno, [a.arg for a in n.args.args], dfl))

print("== H. 关键落点源文（抽查实读） ==")
for a, b in ((220, 230), (4656, 4698), (6165, 6169), (6525, 6530), (6620, 6631), (7363, 7369)):
    print("  --- cand %d-%d ---" % (a, b))
    for i in range(a, b + 1):
        print("    %d| %s" % (i, clines[i-1][:150]))

print("== I. import 集合 master vs cand ==")
def imports(t):
    s = set()
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            for a2 in n.names: s.add(a2.name)
        elif isinstance(n, ast.ImportFrom):
            s.add((n.module or "") + "#" + ",".join(a2.name for a2 in n.names))
    return s
mi, ci = imports(mtree), imports(tree)
print("  equal:", mi == ci)
print("  cand imports:", sorted(ci))

print("== J. 禁止符号/字符串计数（文本子串，master vs cand） ==")
for sym in ("gamemd", "ra2loader", "taskkill", "YURI", "os.system", "subprocess.Popen",
            "MiniDumpWriteDump", "SuspendThread", "StackWalk", "StackWalk64",
            "ReadProcessMemory", "WriteProcessMemory", "VirtualAllocEx",
            "CreateRemoteThread", "SetWindowsHookEx", "OpenProcess", "TerminateProcess"):
    print("  %-18s master=%d cand=%d equal=%s" % (sym, mtext.count(sym), ctext.count(sym), mtext.count(sym) == ctext.count(sym)))
def ctypes_attrs(t):
    return sum(1 for n in ast.walk(t) if isinstance(n, ast.Attribute)
               and isinstance(n.value, ast.Name) and n.value.id == "ctypes")
print("  ctypes attr refs: master=%d cand=%d equal=%s" % (ctypes_attrs(mtree), ctypes_attrs(tree), ctypes_attrs(mtree) == ctypes_attrs(tree)))

print("== K. 甲残留关键词（候选全文） ==")
for kw in ("B2_FIX_DESIGN", "absent_both, n/a", "'n/a'", '"n/a"'):
    print("  %-16s cand=%d master=%d" % (repr(kw), ctext.count(kw), mtext.count(kw)))
