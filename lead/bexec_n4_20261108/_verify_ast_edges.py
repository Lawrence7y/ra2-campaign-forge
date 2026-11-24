# -*- coding: utf-8 -*-
"""独立复核：禁止 API 调用边逐符号审查（复核员自写，不复用规格员 _n4_ast_scan.py）。

只 ast.parse 两份源码，绝不 import / exec 目标脚本。
统计口径与 N-4:49 对齐：
  call  = ast.Call 且被调名（Name 或 Attribute 链末段）命中禁止符号
  load  = ast.Name(Load) 命中禁止符号
  attr  = ast.Attribute 链末段命中禁止符号（引用，非调用）
  dyn   = getattr/__import__/eval/exec/compile/importlib.* 的字符串实参命中禁止名
  alias = Assign 右值 Name 命中禁止符号
  lit   = ast.Constant 字符串字面量恰好等于禁止名（仅作旁证，绝不代替 call）
另：subprocess / os.system / 进程创建边、ctypes 属性链、call edge 差集、import 集合。
"""
import ast
import hashlib

FORBIDDEN = [
    "MiniDumpWriteDump", "SuspendThread", "StackWalk", "StackWalk64",
    "ReadProcessMemory", "WriteProcessMemory", "VirtualAllocEx",
    "CreateRemoteThread", "SetWindowsHookEx", "OpenProcess", "TerminateProcess",
]
FSET = set(FORBIDDEN)
DYN_FUNCS = {"getattr", "__import__", "eval", "exec", "compile"}
PROC_TAIL = {"system", "popen", "spawnl", "spawnle", "spawnv", "spawnve",
             "startfile", "Popen", "check_output", "check_call",
             "CreateProcess", "ShellExecute", "WinExec", "ShellExecuteEx"}
LAUNCH = ("gamemd", "ra2loader", "yuri", "taskkill")

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py"
CAND = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"


def dotted(n):
    if isinstance(n, ast.Name):
        return n.id, True
    if isinstance(n, ast.Attribute):
        b, ok = dotted(n.value)
        if ok:
            return b + "." + n.attr, True
    return None, False


def sarg(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    return None


def scan(path):
    raw = open(path, "rb").read()
    text = raw.decode("utf-8-sig")
    tree = ast.parse(text, filename=path)
    out = {
        "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
        "call": {s: [] for s in FORBIDDEN},
        "load": {s: [] for s in FORBIDDEN},
        "attr": {s: [] for s in FORBIDDEN},
        "dyn": {s: [] for s in FORBIDDEN},
        "alias": {s: [] for s in FORBIDDEN},
        "lit": {s: 0 for s in FORBIDDEN},
        "proc": [], "ctypes": {}, "edges": {}, "imports": set(),
        "import_n": 0,
    }
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out["import_n"] += 1
            for a in n.names:
                out["imports"].add("import " + a.name + (" as " + a.asname if a.asname else ""))
        elif isinstance(n, ast.ImportFrom):
            out["import_n"] += 1
            mod = n.module or ""
            for a in n.names:
                out["imports"].add("from " + mod + " import " + a.name
                                   + (" as " + a.asname if a.asname else ""))

        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                edge = f.id
            elif isinstance(f, ast.Attribute):
                ch, ok = dotted(f)
                edge = ch if ok else "<expr>." + f.attr
            else:
                edge = "<expr-call>"
            out["edges"][edge] = out["edges"].get(edge, 0) + 1
            tail = edge.rsplit(".", 1)[-1]
            if tail in FSET:
                out["call"][tail].append((n.lineno, edge))
            strs = [x for x in (sarg(a) for a in n.args) if x is not None]
            is_dyn = (isinstance(f, ast.Name) and f.id in DYN_FUNCS) or edge.startswith("importlib.")
            if is_dyn:
                for s in strs:
                    if s in FSET:
                        out["dyn"][s].append((n.lineno, edge, s))
            if tail in PROC_TAIL or edge.startswith("subprocess.") or edge in ("os.system", "os.popen"):
                marks = [m for m in LAUNCH if any(m in s.lower() for s in strs)]
                out["proc"].append((n.lineno, edge, strs, marks))

        elif isinstance(n, ast.Attribute):
            ch, ok = dotted(n)
            if ok:
                if ch == "ctypes" or ch.startswith("ctypes."):
                    out["ctypes"][ch] = out["ctypes"].get(ch, 0) + 1
                if ch.rsplit(".", 1)[-1] in FSET:
                    out["attr"][ch.rsplit(".", 1)[-1]].append((n.lineno, ch))

        elif isinstance(n, ast.Name):
            if n.id in FSET and isinstance(n.ctx, ast.Load):
                out["load"][n.id].append((n.lineno, n.id))
            elif n.id in FSET and isinstance(n.ctx, ast.Store):
                pass

        elif isinstance(n, ast.Assign):
            if isinstance(n.value, ast.Name) and n.value.id in FSET:
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        out["alias"][n.value.id].append((n.lineno, t.id, n.value.id))

        elif isinstance(n, ast.Constant):
            if isinstance(n.value, str) and n.value in FSET:
                out["lit"][n.value] += 1
    return out


def cmp(a, b, label):
    print("== %s ==" % label)
    print("%-22s | %-16s | %-16s | %s" % ("symbol", "base call/load/attr/dyn/alias", "cand call/load/attr/dyn/alias", "delta"))
    print("-" * 95)
    bad = []
    for s in FORBIDDEN:
        t1 = (len(a["call"][s]), len(a["load"][s]), len(a["attr"][s]), len(a["dyn"][s]), len(a["alias"][s]))
        t2 = (len(b["call"][s]), len(b["load"][s]), len(b["attr"][s]), len(b["dyn"][s]), len(b["alias"][s]))
        d = tuple(y - x for x, y in zip(t1, t2))
        flag = "UNCHANGED" if not any(d) else "d=" + "/".join(map(str, d))
        if any(d):
            bad.append(s)
        print("%-22s | %-16s | %-16s | %s" % (s, "/".join(map(str, t1)), "/".join(map(str, t2)), flag))
    print("候选有差异的禁止符号: %s" % (bad if bad else "无"))
    print()


def main():
    a, b = scan(BASE), scan(CAND)
    print("BASE sha256=%s bytes=%d" % (a["sha256"], a["bytes"]))
    print("CAND sha256=%s bytes=%d" % (b["sha256"], b["bytes"]))
    print()
    cmp(a, b, "禁止集合逐符号（独立 ast.Call/Name/Attribute/Assign 口径）")

    print("== 禁止集合调用边明细（base / cand）==")
    for s in FORBIDDEN:
        print("  %-22s base=%s" % (s, a["call"][s]))
        print("  %-22s cand=%s" % ("", b["call"][s]))
    print()
    print("== 字符串字面量命中禁止名（仅旁证，不代替 call 边）==")
    for s in FORBIDDEN:
        if a["lit"][s] or b["lit"][s]:
            print("  %-22s base=%d cand=%d" % (s, a["lit"][s], b["lit"][s]))
    print("  （若无输出则两版均无此类字面量）")
    print()

    print("== proc / ctypes / 动态 ==")
    print("  proc_edges base=%d cand=%d" % (len(a["proc"]), len(b["proc"])))
    for tag, r in (("base", a), ("cand", b)):
        for row in r["proc"]:
            print("    %s :%d %s args=%s marks=%s" % (tag, row[0], row[1], row[2], row[3]))
    cts = set(a["ctypes"]) | set(b["ctypes"])
    print("  ctypes 链合计 base=%d cand=%d 种类 base=%d cand=%d" % (
        sum(a["ctypes"].values()), sum(b["ctypes"].values()), len(a["ctypes"]), len(b["ctypes"])))
    for k in sorted(cts):
        if a["ctypes"].get(k, 0) != b["ctypes"].get(k, 0):
            print("    DIFF %s base=%d cand=%d" % (k, a["ctypes"].get(k, 0), b["ctypes"].get(k, 0)))
    print("  import 语句数 base=%d cand=%d；目标集合差: NEW=%s GONE=%s" % (
        a["import_n"], b["import_n"], sorted(b["imports"] - a["imports"]), sorted(a["imports"] - b["imports"])))
    print()

    new = sorted(set(b["edges"]) - set(a["edges"]))
    gone = sorted(set(a["edges"]) - set(b["edges"]))
    print("== 调用边差集 ==")
    print("  新增边 %d 种 / 消失边 %d 种；总种类 base=%d cand=%d" % (
        len(new), len(gone), len(a["edges"]), len(b["edges"])))
    print("  新增边:", [(e, b["edges"][e]) for e in new])
    print("  消失边:", [(e, a["edges"][e]) for e in gone])
    print()
    # 门禁判据：禁止集合任一符号 call/load/attr/dyn/alias 增加即 FAIL
    fail = []
    for s in FORBIDDEN:
        for k in ("call", "load", "attr", "dyn", "alias"):
            if len(b[k][s]) > len(a[k][s]):
                fail.append("%s.%s %d->%d" % (s, k, len(a[k][s]), len(b[k][s])))
    print("独立判定：禁止集合新增调用/引用/动态解析/别名 = %s → %s" % (
        fail if fail else "无", "FAIL" if fail else "PASS(该项)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
