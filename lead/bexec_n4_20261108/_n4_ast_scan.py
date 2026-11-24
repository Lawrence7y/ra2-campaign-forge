# -*- coding: utf-8 -*-
"""N-4 静态调用边审查（本任务 2）。

用 ast 解析 母本 qc151_trip.py 与候选 qc151_trip.candidate_lf.py：
  - 禁止 API 集合逐符号统计 import / Name 引用 / 属性链 / 实际调用边
  - 动态解析：getattr / __import__ / eval / exec / compile / importlib.* 调用边
    及其字符串实参（动态查找面）
  - subprocess / os.system / ctypes 调用边与 ctypes.* 属性链
  - 包装函数（函数体内含禁止调用边或以禁止名为 getattr 字符串实参）
  - 别名赋值（x = OpenProcess 形态）
  - 两版逐符号对照与调用边差集

只 ast.parse 只读源码，不 import、不执行目标脚本；本脚本自身零采样代码。
"""
import ast
import hashlib
import sys

FORBIDDEN = [
    "MiniDumpWriteDump", "SuspendThread", "StackWalk", "StackWalk64",
    "ReadProcessMemory", "WriteProcessMemory", "VirtualAllocEx",
    "CreateRemoteThread", "SetWindowsHookEx", "OpenProcess", "TerminateProcess",
]
DYNAMIC_NAMES = {"getattr", "__import__", "eval", "exec", "compile"}
PROC_LAST = {"system", "popen", "spawnl", "spawnle", "spawnv", "spawnve",
             "startfile", "Popen", "check_output", "check_call",
             "CreateProcess", "ShellExecute", "WinExec", "ShellExecuteEx"}
LAUNCH_MARKS = ("gamemd", "ra2loader", "yuri", "taskkill", ".exe")

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py"
CAND = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"


def dotted(node):
    """把 Name/Attribute 链解析成点号串；解析不了返回 (None, False)。"""
    if isinstance(node, ast.Name):
        return node.id, True
    if isinstance(node, ast.Attribute):
        base, ok = dotted(node.value)
        if not ok:
            return None, False
        return base + "." + node.attr, True
    return None, False


def const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def analyze(path):
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8-sig")
        enc = "utf-8-sig(bom)" if raw[:3] == b"\xef\xbb\xbf" else "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("utf-8-sig", errors="replace")
        enc = "utf-8(replace)"
    tree = ast.parse(text, filename=path)
    r = {
        "path": path, "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw), "enc": enc,
        "crlf": text.count("\r\n"), "lf_total": text.count("\n"),
        "imports": [],        # (lineno, kind, target)
        "calls": [],          # (lineno, edge)
        "forbidden_calls": [],  # (lineno, edge)
        "forbidden_names": [],  # (lineno, kind, text)  kind=name-load/attr-chain
        "dyn": [],            # (lineno, edge, [str args])
        "dyn_forbidden": [],  # (lineno, edge, forbidden str arg)
        "ctypes": [],         # (lineno, chain)
        "proc_edges": [],     # (lineno, edge, [str args])
        "aliases": [],        # (lineno, target, value)
        "wrappers": [],       # (lineno, funcname, [(lineno, hit)])
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                t = a.name + (", as " + a.asname if a.asname else "")
                r["imports"].append((node.lineno, "import", t))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for a in node.names:
                t = mod + "." + a.name + (", as " + a.asname if a.asname else "")
                if node.level:
                    t += " (level=%d)" % node.level
                r["imports"].append((node.lineno, "from", t))

        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                edge = f.id
            elif isinstance(f, ast.Attribute):
                ch, ok = dotted(f)
                edge = ch if ok else "<expr>." + f.attr
            else:
                edge = "<expr-call>"
            r["calls"].append((node.lineno, edge))
            last = edge.rsplit(".", 1)[-1]
            if last in FORBIDDEN or edge in FORBIDDEN:
                r["forbidden_calls"].append((node.lineno, edge))
            arg_strs = [s for s in (const_str(a) for a in node.args) if s]
            if isinstance(f, ast.Name) and f.id in DYNAMIC_NAMES:
                r["dyn"].append((node.lineno, edge, arg_strs))
                for s in arg_strs:
                    if s in FORBIDDEN:
                        r["dyn_forbidden"].append((node.lineno, edge, s))
            elif edge.startswith("importlib."):
                r["dyn"].append((node.lineno, edge, arg_strs))
            if (last in PROC_LAST or edge.startswith("subprocess.")
                    or edge == "os.system" or edge.endswith(".system")
                    or edge.endswith(".popen")):
                r["proc_edges"].append((node.lineno, edge, arg_strs))

        elif isinstance(node, ast.Attribute):
            ch, ok = dotted(node)
            if ok:
                if ch.startswith("ctypes"):
                    r["ctypes"].append((node.lineno, ch))
                if ch.rsplit(".", 1)[-1] in FORBIDDEN:
                    r["forbidden_names"].append((node.lineno, "attr-chain", ch))

        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN and isinstance(node.ctx, ast.Load):
                r["forbidden_names"].append((node.lineno, "name-load", node.id))

        elif isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Name) and node.value.id in FORBIDDEN:
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        r["aliases"].append((node.lineno, t.id, node.value.id))

        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str) and node.value in FORBIDDEN:
                r["dyn_forbidden"].append((node.lineno, "<str-literal>", node.value))

    # 包装函数：函数体内出现禁止调用边或禁止名 getattr 字符串实参
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            hits = []
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Call):
                    f = sub.func
                    if isinstance(f, ast.Name):
                        edge = f.id
                    elif isinstance(f, ast.Attribute):
                        ch, ok = dotted(f)
                        edge = ch if ok else "<expr>." + f.attr
                    else:
                        continue
                    if edge.rsplit(".", 1)[-1] in FORBIDDEN or edge in FORBIDDEN:
                        hits.append((sub.lineno, edge))
                    if isinstance(f, ast.Name) and f.id == "getattr" and len(sub.args) >= 2:
                        s = const_str(sub.args[1])
                        if s in FORBIDDEN:
                            hits.append((sub.lineno, "getattr->" + s))
            if hits:
                r["wrappers"].append((fn.lineno, fn.name, hits))
    return r


def sym_stats(r):
    """禁止集合逐符号计数：call / load / dyn-str / alias。"""
    out = {}
    for s in FORBIDDEN:
        out[s] = {"call": 0, "load": 0, "dyn": 0, "alias": 0, "edges": []}
    for ln, edge in r["forbidden_calls"]:
        s = edge.rsplit(".", 1)[-1]
        out[s]["call"] += 1
        out[s]["edges"].append("call:%d:%s" % (ln, edge))
    for ln, kind, text in r["forbidden_names"]:
        s = text.rsplit(".", 1)[-1]
        out[s]["load"] += 1
        out[s]["edges"].append("%s:%d:%s" % (kind, ln, text))
    for ln, edge, s in r["dyn_forbidden"]:
        out[s]["dyn"] += 1
        out[s]["edges"].append("dyn:%d:%s:%s" % (ln, edge, s))
    for ln, t, v in r["aliases"]:
        out[v]["alias"] += 1
        out[v]["edges"].append("alias:%d:%s=%s" % (ln, t, v))
    return out


def agg_edges(r):
    d = {}
    for ln, edge in r["calls"]:
        d[edge] = d.get(edge, 0) + 1
    return d


def main():
    b = analyze(BASE)
    c = analyze(CAND)
    for r in (b, c):
        print("=" * 100)
        print("FILE  : %s" % r["path"])
        print("SHA256= %s" % r["sha256"])
        print("bytes = %d   enc=%s   LF=%d (其中 CRLF=%d)   ast.parse=OK"
              % (r["bytes"], r["enc"], r["lf_total"], r["crlf"]))
        print("-- imports (%d) --" % len(r["imports"]))
        for ln, kind, t in sorted(r["imports"]):
            print("   :%d %s %s" % (ln, kind, t))
        print("-- 禁止集合实际调用边 forbidden_calls (%d) --" % len(r["forbidden_calls"]))
        for ln, e in r["forbidden_calls"]:
            print("   :%d %s" % (ln, e))
        print("-- 禁止集合名字/属性引用 forbidden_names (%d) --" % len(r["forbidden_names"]))
        for ln, k, t in r["forbidden_names"]:
            print("   :%d %s %s" % (ln, k, t))
        print("-- 动态解析 dyn (getattr/__import__/eval/exec/compile/importlib.*) (%d) --"
              % len(r["dyn"]))
        for ln, e, ss in r["dyn"]:
            print("   :%d %s args=%s" % (ln, e, ss))
        print("-- 动态解析命中禁止名 dyn_forbidden (%d) --" % len(r["dyn_forbidden"]))
        for ln, e, s in r["dyn_forbidden"]:
            print("   :%d %s -> %s" % (ln, e, s))
        print("-- ctypes 链 (%d) --" % len(r["ctypes"]))
        for ln, ch in r["ctypes"]:
            print("   :%d %s" % (ln, ch))
        print("-- subprocess/os.system/进程创建边 proc_edges (%d) --" % len(r["proc_edges"]))
        for ln, e, ss in r["proc_edges"]:
            marks = [m for m in LAUNCH_MARKS if any(m in s.lower() for s in ss)]
            print("   :%d %s args=%s%s" % (ln, e, ss,
                  ("  <<LAUNCH/TASKKILL标记:" + ",".join(marks)) if marks else ""))
        print("-- 别名赋值 aliases (%d) --" % len(r["aliases"]))
        for ln, t, v in r["aliases"]:
            print("   :%d %s = %s" % (ln, t, v))
        print("-- 包装函数 wrappers (%d) --" % len(r["wrappers"]))
        for ln, name, hits in r["wrappers"]:
            print("   :%d def %s hits=%s" % (ln, name, hits))

    print("=" * 100)
    print("逐符号对照（基线 -> 候选；call=实际调用边 load=名字/属性引用 dyn=动态查找字符串 alias=别名赋值）")
    sb, sc = sym_stats(b), sym_stats(c)
    hdr = "%-22s | %-15s | %-15s | %s" % ("symbol", "baseline c/l/d/a", "candidate c/l/d/a", "delta")
    print(hdr)
    print("-" * len(hdr))
    any_new = []
    for s in FORBIDDEN:
        bb, cc = sb[s], sc[s]
        bt = (bb["call"], bb["load"], bb["dyn"], bb["alias"])
        ct = (cc["call"], cc["load"], cc["dyn"], cc["alias"])
        d = tuple(y - x for x, y in zip(bt, ct))
        if any(d):
            any_new.append(s)
        print("%-22s | %-15s | %-15s | %s" % (
            s,
            "/".join(map(str, bt)),
            "/".join(map(str, ct)),
            ("UNCHANGED" if not any(d) else "d=" + "/".join(map(str, d)))))
    print()
    print("候选新增禁止边符号: %s" % (any_new if any_new else "无"))
    print()
    print("proc/ctypes/dyn 边对照：")
    def agg_keyed(r, key, idx):
        d = {}
        for row in r[key]:
            e = row[idx]
            d[e] = d.get(e, 0) + 1
        return d
    for label, key, idx in (("proc_edges", "proc_edges", 1), ("ctypes", "ctypes", 1), ("dyn", "dyn", 1)):
        db, dc = agg_keyed(b, key, idx), agg_keyed(c, key, idx)
        keys = sorted(set(db) | set(dc))
        print("  [%s]" % label)
        if not keys:
            print("    (两边均无)")
        for k in keys:
            print("    %-40s base=%-4d cand=%-4d %s" % (k[:40], db.get(k, 0), dc.get(k, 0),
                  "NEW" if k not in db else ("GONE" if k not in dc else "")))

    print()
    print("imports 差异：")
    ib = set(t for _, _, t in b["imports"])
    ic = set(t for _, _, t in c["imports"])
    for t in sorted(ic - ib):
        print("  NEW in candidate: %s" % t)
    for t in sorted(ib - ic):
        print("  REMOVED in candidate: %s" % t)
    if not (ic - ib) and not (ib - ic):
        print("  （import 目标集合完全一致）")

    print()
    eb, ec = agg_edges(b), agg_edges(c)
    new_edges = sorted((ec.keys() | set()) - set(eb))
    gone_edges = sorted(set(eb) - set(ec))
    print("调用边差集：候选新增边 %d 种，消失边 %d 种（全部调用边：基线 %d 种 / 候选 %d 种）"
          % (len(new_edges), len(gone_edges), len(eb), len(ec)))
    print("-- 候选新增边（前 120 条，edge x count）--")
    for e in new_edges[:120]:
        print("   + %s  x%d" % (e, ec[e]))
    if len(new_edges) > 120:
        print("   …（其余 %d 条省略，见完整对照需要另行输出）" % (len(new_edges) - 120))
    print("-- 候选消失边（前 60 条）--")
    for e in gone_edges[:60]:
        print("   - %s  (base x%d)" % (e, eb[e]))
    if len(gone_edges) > 60:
        print("   …（其余 %d 条省略）" % (len(gone_edges) - 60))
    print("=" * 100)
    print("判定依据（N-4）：禁止集合逐符号及调用边计数，新增调用/导入/包装/动态解析均 FAIL；"
          "删除也须解释且只许 A—D 内变动。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
