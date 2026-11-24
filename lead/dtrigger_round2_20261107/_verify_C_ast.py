# -*- coding: utf-8 -*-
# 独立复核 C：AST 审计 + 硬编码 §7 断言逐条对文件核实 + 措辞检索
import ast, os, json, re

ROOT = r"D:/Project/ra2-campaign-forge"
SCRIPT = os.path.join(ROOT, "lead/dtrigger_round2_20261107/_dC_recompute.py")
OUT = os.path.join(ROOT, "lead/dtrigger_round2_20261107/_dC_out.txt")
src = open(SCRIPT, "r", encoding="utf-8").read()
tree = ast.parse(src)

# --- AST: imports ---
imports = []
for n in ast.walk(tree):
    if isinstance(n, ast.Import):
        imports += [a.name for a in n.names]
    elif isinstance(n, ast.ImportFrom):
        imports.append(n.module or "")
print("AST all import modules =", sorted(set(imports)))

# --- AST: open() calls and modes ---
opens = []
for n in ast.walk(tree):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open":
        modes = [a.value for a in n.args[1:2] if isinstance(a, ast.Constant)]
        kws = [(k.arg, k.value.value if isinstance(k.value, ast.Constant) else "?") for k in n.keywords]
        opens.append((n.lineno, modes, kws))
print("AST open() calls =", opens)
write_modes = [o for o in opens if any(isinstance(m, str) and any(ch in m for ch in "wax+") for m in o[1])
               or any(k[0] == "mode" and isinstance(k[1], str) and any(ch in k[1] for ch in "wax+") for k in o[2])]
print("AST write-mode open count =", len(write_modes))

# --- banned API scan ---
BANNED = ["ctypes", "OpenProcess", "ReadProcessMemory", "WriteProcessMemory", "VirtualAllocEx",
          "CreateRemoteThread", "SetWindowsHookEx", "TerminateProcess", "SuspendThread",
          "StackWalk", "MiniDump", "taskkill", "gamemd.exe", "ra2loader", "YURI.exe",
          "import _cost_quota", "importlib", "__import__", "subprocess", "os.system", "popen"]
print("--- banned token scan in _dC_recompute.py ---")
for b in BANNED:
    lines = [i for i, l in enumerate(src.split("\n"), 1) if b in l]
    if lines:
        print("  %-24s -> lines %s" % (b, lines))
print("  (only lines printed are tokens present; text mentions in docstrings are not calls)")

# --- lines mentioning _cost_quota.py / _cost_quota_check.py ---
print("--- lines containing '_cost_quota.py' or '_cost_quota_check' ---")
for i, l in enumerate(src.split("\n"), 1):
    if "_cost_quota.py" in l or "_cost_quota_check" in l:
        print("  %d| %s" % (i, l.strip()))

# --- hardcoded emit strings in §7: identify which emit() calls are pure literals ---
print("--- §7 emit calls with NO runtime variables (pure literal claims) ---")
for n in ast.walk(tree):
    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == "emit":
        arg = n.value.args[0] if n.value.args else None
        is_pure = isinstance(arg, ast.Constant)
        if is_pure and 300 <= n.lineno <= 390:
            print("  line %d: PURE LITERAL -> %s" % (n.lineno, repr(arg.value[:110])))
        elif not is_pure and 300 <= n.lineno <= 390:
            print("  line %d: computed/format -> %s" % (n.lineno, type(arg).__name__))

# --- check hardcoded claims against the actual files ---
print("--- verify hardcoded §7 claims against source files ---")
metrics = open(os.path.join(ROOT, "lead/dtrigger_compare_20261107/_dtrigger_metrics_out.txt"), "r", encoding="utf-8").read().split("\n")
supp = open(os.path.join(ROOT, "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt"), "r", encoding="utf-8").read().split("\n")
probe = open(os.path.join(ROOT, "lead/dtrigger_compare_20261107/_dtrigger_probe_out.txt"), "r", encoding="utf-8").read().split("\n")
stall = open(os.path.join(ROOT, "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md"), "r", encoding="utf-8").read().split("\n")

print("  7c-2 probe detail lines:")
for ln in (106, 128, 150, 161, 172):
    print("    probe_out.txt:%d| %s" % (ln, probe[ln-1].strip()))
print("  7d metrics_out.txt:28,30 | %s | %s" % (metrics[27].strip(), metrics[29].strip()))
print("  7e metrics_out.txt:31 | %s" % metrics[30].strip())
print("  7e probe_out.txt:171-172 | %s | %s" % (probe[170].strip(), probe[171].strip()))
print("  7f stall:190 | %s" % stall[189].strip())
print("  7f stall:191 | %s" % stall[190].strip())
print("  7g supplement:44-45 | %s | %s" % (supp[43].strip(), supp[44].strip()))
print("  7h note column (metrics 21,26-31):")
for ln in (21, 26, 27, 28, 29, 30, 31):
    print("    %d| %s" % (ln, metrics[ln-1].strip().split("|")[-1].strip()))

# --- supplement >=100 distribution for the 13 criteria ---
print("--- supplement >=100 column for the 13 zero-preempt criteria (assess '高档 >=100ms') ---")
thirteen = ["C2-N16-P95x2", "C2-P95x2", "C2-P95x3", "C2-P99x2", "C2-P99x3", "C2-abs-P95x2",
            "C3-N16-r2", "C3-r12", "C3-r2", "C3-r4", "C3-r4-clean", "C3-r8", "C3-r8-clean"]
rows = {}
for l in supp:
    if "|" not in l: continue
    f = [z.strip() for z in l.split("|")]
    if len(f) >= 12 and f[0] in thirteen and f[1].isdigit():
        rows[f[0]] = (int(f[1]), int(f[6]), int(f[8]))
for c in thirteen:
    if c in rows:
        n, g50, g100 = rows[c]
        print("  %-22s nTrig=%3d >50=%3d >=100=%3d  all>=100:%s" % (c, n, g50, g100, g100 == n))
    else:
        print("  %-22s (no supplement row)" % c)

# --- wording search in _dC_out.txt for S_hat / physical S / false-rate / feasibility ---
print("--- wording scan of _dC_out.txt ---")
out_lines = open(OUT, "r", encoding="utf-8").read().split("\n")
for kw in ["S_hat", "物理 S", "物理起点", "误报率", "误触发率", "可行", "批准", "合规", "方案", "修复", "未验", "下界"]:
    hits = [i for i, l in enumerate(out_lines, 1) if kw in l]
    print("  %-10s -> lines %s" % (kw, hits))
