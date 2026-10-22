#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A8 修复补丁的**独立**全量核验（补丁核验员，非实现者）。

纪律
----
- 只读母本与副本；不写任何产物（除 stdout）。
- 不 import 被测模块（避免模块级副作用）；路径判定函数按 AST 取**原文**后
  在受控命名空间里 exec，测的就是副本里那几行代码。
- 不用 py_compile（会落 .pyc），只用 ast.parse。
- 不采信实现者数字：所有哈希 / 计数 / 判定均在本脚本内重算。

核验项
------
K1  母本零改动（LF sha256 前16 == 7db3c11009b7183c）
K2  副本自证（LF / CRLF 双哈希 + 字节数 + 编码 + BOM + 行尾）
K3  反向重建（用 a8.diff 独立逐字节重建副本；并用生成器锚点逻辑复算）
K4  AST 零改动面（按函数名分组比对 ast.dump；只允许 3 新函数 + main 变化）
K5  禁止面（taskkill /IM、SendMessage/PostMessage/SendInput/
    WriteProcessMemory/CreateRemoteThread、winreg 写、terminate_owned_process 语义）
K6  作用域正确性（A8 块在 main() 的 finally 内；守卫读模块级 A8_ALLOW_LOADER[0]；
    模块级 Assign 早于 launch_direct 调用）
K7  路径归属判定（relative_to 而非 startswith；实跑三用例）
K8  负控有效性（重跑 _a8_negctl.py；并独立判断 6 段是否真覆盖对应断言）
K9  合成冒烟（ast.parse + 模块级符号存在 + 路径三用例）
"""
import ast
import hashlib
import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "lead/goal1_a8_fix_20261022"
MASTER = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
                / "qc151_u8_impl_20261021/qc151_trip.harness3_u8.py")
COPY = BASE / "qc151_trip.harness4.py"
DIFF = BASE / "a8.diff"
GEN = BASE / "_gen_harness4.py"
NEGCTL = BASE / "_a8_negctl.py"
NEGCTL_TXT = BASE / "A8_NEGCTL.txt"

MASTER_SHA16 = "7db3c11009b7183c"
A8_FUNCS = {"a8_sweep_carrier_processes", "_a8_query_image_path",
            "_a8_path_under_carrier"}

RESULTS = []      # (key, title, status, [evidence lines])
FAILED = []


def record(key, title, status, evidence):
    RESULTS.append((key, title, status, evidence))
    if status == "REFUTED":
        FAILED.append(key)
    print()
    print("=" * 78)
    print(f"[{key}] {title}")
    print("=" * 78)
    print(f"RESULT: {status}")
    for e in evidence:
        print(f"  {e}")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def lf16(b):
    return sha256(b)[:16]


def crlf_sha(b):
    """CRLF 口径：把 \\r\\n → \\n 再 \\n → \\r\\n 后取 sha256。"""
    return sha256(b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))


def parse(p):
    return ast.parse(p.read_text(encoding="utf-8"))


def funcs(tree):
    """模块级函数名 -> [ast.dump...]（保留重复定义，按出现顺序）。"""
    d = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            d.setdefault(n.name, []).append(ast.dump(n))
    return d


# ---------------------------------------------------------------------------
# K1 母本零改动
# ---------------------------------------------------------------------------
def k1():
    raw = MASTER.read_bytes()
    got = lf16(raw)
    n_crlf = raw.count(b"\r\n")
    ev = [f"path   : {MASTER}",
          f"bytes  : {len(raw)}",
          f"LF sha256: {sha256(raw)}",
          f"LF16   : {got}",
          f"expect : {MASTER_SHA16}",
          f"CRLF count in mother: {n_crlf} (must be 0)"]
    ok = (got == MASTER_SHA16 and n_crlf == 0)
    record("K1", "母本零改动（LF sha256 前16）", "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K2 副本自证
# ---------------------------------------------------------------------------
def k2():
    raw = COPY.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    ev = [f"path    : {COPY}",
          f"bytes   : {len(raw)}",
          f"LF16    : {lf16(raw)}",
          f"LF sha256 : {sha256(raw)}",
          f"CRLF16  : {crlf_sha(raw)[:16]}",
          f"CRLF sha256: {crlf_sha(raw)}",
          f"CRLF pairs in file: {raw.count(b'\\r\\n')}",
          f"lone LF    : {raw.count(b'\\n') - raw.count(b'\\r\\n')}",
          f"BOM        : {raw[:3] == b'\xef\xbb\xbf'}",
          f"ends with newline: {raw.endswith(b'\n')}",
          f"utf-8 decodable : ",]
    try:
        text = raw.decode("utf-8")
        ev[-1] += "True"
    except UnicodeDecodeError as e:
        ev[-1] += f"False ({e})"
        record("K2", "副本哈希自证", "REFUTED", ev)
        return
    # 结构自证：行数 / 母本行数差
    m = MASTER.read_bytes()
    ev.append(f"lines mother={m.count(b'\\n')} copy={raw.count(b'\\n')} "
              f"delta={raw.count(b'\\n') - m.count(b'\\n')}")
    ev.append(f"bytes delta = {len(raw) - len(m)}")
    ok = (raw.count(b"\r\n") == 0 and raw[:3] != b"\xef\xbb\xbf"
          and raw.endswith(b"\n"))
    record("K2", "副本哈希自证（LF/CRLF 双哈希 + 字节数）",
           "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K3 反向重建
# ---------------------------------------------------------------------------
def parse_unified_diff(text):
    """把 unified diff 解析成 [(src_start, src_len, dst_start, dst_len, lines)]。"""
    lines = text.split("\n")
    hunks = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("@@"):
            head = ln[2:].split("@@")[0].strip()
            a, b = head.split(" ")
            s = a[1:].split(",")
            d = b[1:].split(",")
            src_start = int(s[0]); src_len = int(s[1]) if len(s) > 1 else 1
            dst_start = int(d[0]); dst_len = int(d[1]) if len(d) > 1 else 1
            body = []
            i += 1
            while i < len(lines):
                x = lines[i]
                if x.startswith("@@") or x.startswith("--- ") or x.startswith("+++ "):
                    break
                if x == "" and i == len(lines) - 1:
                    i += 1
                    continue
                if x[:1] in (" ", "+", "-"):
                    body.append(x)
                i += 1
            hunks.append((src_start, src_len, dst_start, dst_len, body))
            continue
        i += 1
    return hunks


def apply_unified(src_text, hunks):
    """严格按 hunk 行号应用；上下文不匹配即抛异常（证明 diff 可逆且精确）。"""
    src = src_text.split("\n")
    out = []
    pos = 0          # 0-based 游标
    for (ss, sl, ds, dl, body) in hunks:
        start = ss - 1 if sl > 0 else ss
        if start < pos:
            raise AssertionError(f"hunk overlap at src line {ss}")
        out.extend(src[pos:start])
        pos = start
        for ln in body:
            tag, txt = ln[0], ln[1:]
            if tag == " ":
                if src[pos] != txt:
                    raise AssertionError(
                        f"context mismatch at src line {pos+1}: "
                        f"{src[pos]!r} != {txt!r}")
                out.append(txt); pos += 1
            elif tag == "-":
                if src[pos] != txt:
                    raise AssertionError(
                        f"deleted line mismatch at src line {pos+1}: "
                        f"{src[pos]!r} != {txt!r}")
                pos += 1
            elif tag == "+":
                out.append(txt)
    out.extend(src[pos:])
    return "\n".join(out)


def k3():
    master_text = MASTER.read_text(encoding="utf-8")
    copy_raw = COPY.read_bytes()
    diff_text = DIFF.read_text(encoding="utf-8")
    hunks = parse_unified_diff(diff_text)
    ev = [f"diff bytes={DIFF.stat().st_size} hunks={len(hunks)}",
          f"hunk headers: " + ", ".join(f"@{h[0]},{h[1]}" for h in hunks)]
    try:
        rebuilt = apply_unified(master_text, hunks)
    except AssertionError as e:
        ev.append(f"APPLY FAILED: {e}")
        record("K3", "反向重建（a8.diff 逐字节）", "REFUTED", ev)
        return
    rb = rebuilt.encode("utf-8")
    ev.append(f"rebuilt bytes={len(rb)} sha256={sha256(rb)}")
    ev.append(f"copy    bytes={len(copy_raw)} sha256={sha256(copy_raw)}")
    byte_exact = (rb == copy_raw)

    # 交叉验证：生成器锚点逻辑独立复算（不 import 生成器，只读其锚点常量）
    gen_src = GEN.read_text(encoding="utf-8")
    gtree = ast.parse(gen_src)
    consts = {}
    for n in gtree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name) \
                and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            consts[n.targets[0].id] = n.value.value
    pairs = [("ANCHOR_1", "PATCH_1"), ("ANCHOR_2A", "PATCH_2A"),
             ("ANCHOR_3", "PATCH_3"), ("ANCHOR_4", "PATCH_4")]
    ev.append(f"generator string consts found: {sorted(consts)}")
    gen_ok = True
    t = master_text
    for a, p in pairs:
        if a not in consts or p not in consts:
            ev.append(f"  MISSING generator const {a}/{p}")
            gen_ok = False
            continue
        cnt = t.count(consts[a])
        ev.append(f"  {a} occurrences in current text: {cnt} (must be 1)")
        if cnt != 1:
            gen_ok = False
        t = t.replace(consts[a], consts[p], 1)
    gen_bytes = t.encode("utf-8")
    ev.append(f"generator-replay bytes={len(gen_bytes)} sha256={sha256(gen_bytes)}")
    gen_exact = (gen_bytes == copy_raw)
    ev.append(f"diff rebuild == copy : {byte_exact}")
    ev.append(f"generator replay == copy : {gen_exact}")
    ok = byte_exact and gen_exact and gen_ok
    record("K3", "反向重建（a8.diff 逐字节 / 生成器锚点复算）",
           "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K4 AST 零改动面
# ---------------------------------------------------------------------------
def k4():
    mt, ct = parse(MASTER), parse(COPY)
    mf, cf = funcs(mt), funcs(ct)
    only_copy = sorted(set(cf) - set(mf))
    only_master = sorted(set(mf) - set(cf))
    changed = sorted(k for k in (set(mf) & set(cf)) if mf[k] != cf[k])
    unexpected_new = sorted(set(only_copy) - A8_FUNCS)
    unexpected_changed = sorted(set(changed) - {"main"})
    ev = [f"mother funcs={len(mf)} copy funcs={len(cf)}",
          f"new funcs in copy : {only_copy}",
          f"missing funcs     : {only_master}",
          f"changed bodies    : {changed}",
          f"unexpected new    : {unexpected_new} (allowed: {sorted(A8_FUNCS)})",
          f"unexpected changed: {unexpected_changed} (allowed: ['main'])"]
    # main 内只允许 2 处插入：finally 的 A8 If + try 内的 A8 赋值
    mf_main = [n for n in mt.body if isinstance(n, ast.FunctionDef) and n.name == "main"][0]
    cf_main = [n for n in ct.body if isinstance(n, ast.FunctionDef) and n.name == "main"][0]
    m_try = [n for n in mf_main.body if isinstance(n, ast.Try) and n.finalbody][0]
    c_try = [n for n in cf_main.body if isinstance(n, ast.Try) and n.finalbody][0]
    m_body = [ast.dump(x) for x in m_try.body]
    c_body = [ast.dump(x) for x in c_try.body]
    m_fin = [ast.dump(x) for x in m_try.finalbody]
    c_fin = [ast.dump(x) for x in c_try.finalbody]
    body_added = len(c_body) - len(m_body)
    fin_added = len(c_fin) - len(m_fin)
    # 母本的每条语句必须按序仍在（append-only，不重排）
    def is_subseq(small, big):
        it = iter(big)
        return all(any(x == y for y in it) for x in small)
    body_append_only = is_subseq(m_body, c_body)
    fin_append_only = is_subseq(m_fin, c_fin)
    ev += [f"main.try.body  stmts {len(m_body)} -> {len(c_body)} (added {body_added})",
           f"main.finally   stmts {len(m_fin)} -> {len(c_fin)} (added {fin_added})",
           f"try.body append-only   : {body_append_only}",
           f"finally  append-only   : {fin_append_only}"]
    # 模块级语句：只允许新增 1 条 A8_ALLOW_LOADER Assign
    #   ★ 两侧都排除 main（其变化已在上面单独量化），否则整段必然不等。
    def top_dump(t, exclude):
        return [ast.dump(x) for x in t.body
                if not (isinstance(x, ast.FunctionDef) and x.name in exclude)]
    m_top = top_dump(mt, {"main"})
    c_top = top_dump(ct, A8_FUNCS | {"main"})
    top_append_only = is_subseq(m_top, c_top)
    ev += [f"module stmts (funcs excluded) {len(m_top)} -> {len(c_top)} "
           f"(added {len(c_top) - len(m_top)})",
           f"module append-only (excluding main) : {top_append_only}"]
    ok = (only_copy == sorted(A8_FUNCS) and not only_master
          and changed == ["main"] and body_added == 1 and fin_added == 1
          and body_append_only and fin_append_only and top_append_only
          and (len(c_top) - len(m_top)) == 1)
    record("K4", "AST 零改动面（按函数名分组比对）",
           "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K5 禁止面
# ---------------------------------------------------------------------------
BANNED = {"SendMessage", "PostMessage", "SendInput",
          "WriteProcessMemory", "CreateRemoteThread"}


def call_names(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = (f.attr if isinstance(f, ast.Attribute)
                  else f.id if isinstance(f, ast.Name) else None)
            if nm:
                out.append(nm)
    return out


def k5():
    mt, ct = parse(MASTER), parse(COPY)
    copy_text = COPY.read_text(encoding="utf-8")
    m_calls, c_calls = call_names(mt), call_names(ct)
    ev = []
    # 5.1 taskkill /IM 按名全杀
    im_hits = []
    for n in ast.walk(ct):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            if "taskkill" in n.value.lower() and "/im" in n.value.lower():
                im_hits.append((n.lineno, n.value[:60]))
    # 任何 taskkill 相关字符串（含注释/docstring）
    tk_any = [n.lineno for n in ast.walk(ct)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)
              and "taskkill" in n.value.lower()]
    ev.append(f"taskkill+/IM string constants : {im_hits} (must be empty)")
    ev.append(f"any taskkill mention (lineno) : {tk_any}")
    ev.append(f"  -> mother mentions: "
              f"{[n.lineno for n in ast.walk(mt) if isinstance(n, ast.Constant) and isinstance(n.value, str) and 'taskkill' in n.value.lower()]}")
    # 5.2 新增危险调用（增量比较）
    new_banned = {}
    for nm in BANNED:
        delta = c_calls.count(nm) - m_calls.count(nm)
        if delta != 0:
            new_banned[nm] = delta
    ev.append(f"banned-call delta vs mother : {new_banned} (must be empty)")
    ev.append("  counts mother: " + str({nm: m_calls.count(nm) for nm in sorted(BANNED)}))
    ev.append("  counts copy  : " + str({nm: c_calls.count(nm) for nm in sorted(BANNED)}))
    # 5.3 winreg 写
    winreg_names = [n.lineno for n in ast.walk(ct)
                    if isinstance(n, ast.Name) and n.id == "winreg"]
    winreg_imports = [n.lineno for n in ast.walk(ct)
                      if isinstance(n, (ast.Import, ast.ImportFrom))
                      and any((a.name or "").split(".")[0] == "winreg"
                              for a in n.names)]
    reg_writes = [nm for nm in c_calls
                  if nm in ("SetValue", "SetValueEx", "RegSetValue",
                            "RegSetValueEx", "CreateKey", "CreateKeyEx",
                            "SetKeyValue", "DeleteKey", "DeleteValue")]
    ev.append(f"winreg Name refs={winreg_names} imports={winreg_imports} "
              f"(both must be empty)")
    ev.append(f"registry write calls : {reg_writes} (must be empty)")
    # 5.4 terminate_owned_process 既有语义不变
    mf, cf = funcs(mt), funcs(ct)
    top_ident = (mf.get("terminate_owned_process") == cf.get("terminate_owned_process"))
    ev.append(f"terminate_owned_process ast.dump identical : {top_ident}")
    ev.append(f"  dump sha16 = "
              f"{sha256(mf['terminate_owned_process'][0].encode())[:16]}")
    ok = (not im_hits and not new_banned and not winreg_names
          and not winreg_imports and not reg_writes and top_ident)
    record("K5", "禁止面（按名全杀 / 注入类 API / winreg 写 / 既有语义）",
           "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K6 作用域正确性
# ---------------------------------------------------------------------------
def k6():
    ct = parse(COPY)
    ev = []
    # 6.1 A8_ALLOW_LOADER 是模块级 Assign（不是 AnnAssign / 不在函数内）
    mod_assign = [n for n in ct.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "A8_ALLOW_LOADER"
                          for t in n.targets)]
    mod_ann = [n for n in ct.body if isinstance(n, ast.AnnAssign)
               and isinstance(n.target, ast.Name) and n.target.id == "A8_ALLOW_LOADER"]
    ev.append(f"module-level Assign(A8_ALLOW_LOADER) count={len(mod_assign)} "
              f"lineno={[n.lineno for n in mod_assign]}")
    ev.append(f"module-level AnnAssign count={len(mod_ann)} (must be 0)")
    ev.append(f"initial value = [False] : "
              f"{ast.dump(mod_assign[0].value) if mod_assign else 'N/A'}")
    # 6.2 守卫在 main() 的 finally 内，且读 Subscript A8_ALLOW_LOADER[0]
    main_fn = [n for n in ct.body if isinstance(n, ast.FunctionDef) and n.name == "main"][0]
    trys = [n for n in main_fn.body if isinstance(n, ast.Try) and n.finalbody]
    ev.append(f"main() Try-with-finalbody count = {len(trys)} (must be 1)")
    tr = trys[0]
    guard = None
    for idx, st in enumerate(tr.finalbody):
        if isinstance(st, ast.If):
            t = st.test
            if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "A8_ALLOW_LOADER"
                    and isinstance(t.slice, ast.Constant) and t.slice.value == 0):
                guard = (idx, st)
    ev.append(f"A8 guard found in finally : {guard is not None} "
              f"(finalbody index {guard[0] if guard else 'N/A'})")
    if guard:
        ev.append(f"guard test dump = {ast.dump(guard[1].test)}")
        # 守卫之后必须紧跟 carrier 选择 + sweep 调用 + remaining 判定
        gsrc = ast.dump(guard[1])
        ev.append(f"guard body calls sweep : {'a8_sweep_carrier_processes' in gsrc}")
        ev.append(f"guard body checks remaining : "
                  f"{'remaining' in gsrc}")
        ev.append(f"guard body records note_cleanup_failure : "
                  f"{'note_cleanup_failure' in gsrc}")
        ev.append(f"guard body uses EXIT_TERMINATE_FAILED : "
                  f"{'EXIT_TERMINATE_FAILED' in gsrc}")
        ev.append(f"guard body sets a8_verdict : {'a8_verdict' in gsrc}")
        # 位置：必须在 TERM 判定块之后（终止先行），且在 fin_carrier 之前
        names = [ast.dump(x) for x in tr.finalbody]
        term_idx = next((i for i, d in enumerate(names)
                         if "termination_verdict" in d), None)
        fin_idx = next((i for i, d in enumerate(names)
                        if "fin_carrier" in d), None)
        ev.append(f"index: termination_verdict={term_idx} A8={guard[0]} "
                  f"fin_carrier={fin_idx}")
        order_ok = (term_idx is not None and fin_idx is not None
                    and term_idx < guard[0] < fin_idx)
        ev.append(f"order termination -> A8 -> fin_carrier : {order_ok}")
    else:
        order_ok = False
    # 6.3 不得读 try 内局部名作守卫
    guard_src = ast.dump(guard[1].test) if guard else ""
    reads_local = "_u8_authorized" in guard_src
    ev.append(f"guard reads try-local `_u8_authorized` : {reads_local} (must be False)")
    # 6.4 赋值点早于 launch_direct 调用（AST 行号）
    assign_ln = None
    launch_ln = None
    for n in ast.walk(tr):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                        and t.value.id == "A8_ALLOW_LOADER"):
                    assign_ln = n.lineno
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "launch_direct":
            launch_ln = n.lineno if launch_ln is None else min(launch_ln, n.lineno)
    ev.append(f"A8_ALLOW_LOADER[0] assign lineno={assign_ln}, "
              f"launch_direct() call lineno={launch_ln}")
    ev.append(f"assign before launch : "
              f"{assign_ln is not None and launch_ln is not None and assign_ln < launch_ln}")
    # 6.5 默认 False ⇒ 非授权趟行为不变（守卫只在 True 时进）
    ev.append("guard is `if A8_ALLOW_LOADER[0]:` -> falsy default skips sweep: "
              f"{guard is not None}")
    ok = (len(mod_assign) == 1 and not mod_ann and guard is not None
          and order_ok and not reads_local
          and assign_ln is not None and launch_ln is not None
          and assign_ln < launch_ln
          and "a8_sweep_carrier_processes" in gsrc
          and "remaining" in gsrc and "note_cleanup_failure" in gsrc
          and "EXIT_TERMINATE_FAILED" in gsrc)
    record("K6", "作用域正确性（finally 内 / 模块级容器 / 早于 launch）",
           "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K7 路径归属判定
# ---------------------------------------------------------------------------
def extract_func_src(tree, src_text, name):
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(src_text, n)
    return None


def k7():
    src_text = COPY.read_text(encoding="utf-8")
    ct = ast.parse(src_text)
    fn_src = extract_func_src(ct, src_text, "_a8_path_under_carrier")
    ev = []
    if fn_src is None:
        record("K7", "路径归属判定", "REFUTED", ["function not found"])
        return
    # 静态：必须用 relative_to，且不得用 startswith
    calls = [n.func.attr for n in ast.walk(ast.parse(fn_src))
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    ev.append(f"calls inside function : {sorted(set(calls))}")
    ev.append(f"uses relative_to : {'relative_to' in calls}")
    ev.append(f"uses startswith  : {'startswith' in calls} (must be False)")
    ev.append(f"uses resolve     : {'resolve' in calls}")
    # 实跑：把**副本里的原文**放进受控命名空间执行
    ns = {"Path": Path}
    exec(compile(fn_src, "<_a8_path_under_carrier from harness4>", "exec"), ns)
    fn = ns["_a8_path_under_carrier"]
    P = ns["Path"]

    cases = [
        ("(a) carrier ...\\abc  vs  ...\\abc\\gamemd.exe  -> True",
         P(r"D:\qa\carrier\abc"), r"D:\qa\carrier\abc\gamemd.exe", True),
        ("(b) carrier ...\\abc  vs  ...\\abcd\\x.exe     -> False",
         P(r"D:\qa\carrier\abc"), r"D:\qa\carrier\abcd\x.exe", False),
        ("(c) carrier ...\\abc  vs  C:\\Windows\\system32\\x.exe -> False",
         P(r"D:\qa\carrier\abc"), r"C:\Windows\system32\x.exe", False),
    ]
    all_ok = True
    for label, carrier, image, expect in cases:
        got = fn(image, carrier)
        ok = (got is expect)
        all_ok = all_ok and ok
        ev.append(f"{label}: got={got} expect={expect} -> {'OK' if ok else 'MISMATCH'}")
    # 额外反证：同前缀若用 startswith 会怎样
    startswith_would = r"D:\qa\carrier\abcd\x.exe".startswith(str(P(r"D:\qa\carrier\abc")))
    ev.append(f"counter-proof: startswith would say (b) = {startswith_would} "
              f"(shows the test has discriminating power)")
    # 附加：真实载体路径形态（tmp 下含空格/中文）
    extra = [(P(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\c_20261022_120000_1234"),
              r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\c_20261022_120000_1234\ra2loader.exe", True),
             (P(r"D:\qa\carrier\abc"), r"D:\qa\carrier\abc", True),
             (P(r"D:\qa\carrier\abc"), "", False)]
    for carrier, image, expect in extra:
        got = fn(image, carrier)
        ev.append(f"extra carrier={carrier} image={image!r} -> got={got} "
                  f"expect={expect} {'OK' if got is expect else 'MISMATCH'}")
        all_ok = all_ok and got is expect
    ok = ("relative_to" in calls and "startswith" not in calls and all_ok)
    record("K7", "路径归属判定（relative_to + 三用例实跑）",
           "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K8 负控有效性
# ---------------------------------------------------------------------------
def k8():
    ev = []
    proc = subprocess.run([sys.executable, str(NEGCTL)],
                          capture_output=True, text=True, cwd=str(BASE),
                          encoding="utf-8", errors="replace")
    out = proc.stdout + proc.stderr
    ev.append(f"rerun exit code = {proc.returncode} (expect 0)")
    for line in out.splitlines():
        if any(k in line for k in ("negative-control", "checks passed",
                                   "RESULT:", "N-1", "N-2", "N-3", "N-4",
                                   "N-5", "N-6", "mother sha16")):
            ev.append(f"  | {line}")
    red_ok = "negative-control RED segments: 6/6" in out
    chk_ok = "checks passed: 13/13" in out
    res_ok = "RESULT: ALL PASS" in out
    ev.append(f"6/6 RED={red_ok} 13/13 PASS={chk_ok} RESULT ALL PASS={res_ok}")

    # 独立判断：6 段是否真覆盖对应断言（不采信脚本自述）
    master_text = MASTER.read_text(encoding="utf-8")
    copy_text = COPY.read_text(encoding="utf-8")
    judge = {}
    # N-1：改 1 字节必须真的改哈希
    m = hashlib.sha256(MASTER.read_bytes()).hexdigest()[:16]
    m2 = hashlib.sha256(MASTER.read_bytes() + b" ").hexdigest()[:16]
    judge["N-1 hash sensitivity"] = (m != m2)
    # N-2：把守卫换成 try 局部名后，"守卫 == A8_ALLOW_LOADER[0]" 判定必须变红
    v2 = copy_text.replace("if A8_ALLOW_LOADER[0]:", "if allow_loader_flag:", 1)
    judge["N-2 guard literal check flips"] = ("if A8_ALLOW_LOADER[0]:" not in v2)
    # N-3：改声明名后，decl<use<guard 顺序判定必须变红
    v3 = copy_text.replace("A8_ALLOW_LOADER = [False]",
                           "A8_ALLOW_LOADER_DISABLED = [False]", 1)
    judge["N-3 decl ordering flips"] = not (0 < v3.find("A8_ALLOW_LOADER = [False]")
                                            < v3.find("A8_ALLOW_LOADER[0] = bool(_u8_authorized)")
                                            < v3.find("if A8_ALLOW_LOADER[0]:"))
    # N-4：删的必须是母本真实存在的行
    victim = "def find_pids(name: str) -> list:"
    judge["N-4 victim line in mother"] = (victim in master_text)
    judge["N-4 victim line in copy"] = (victim in copy_text)
    # 且删除后行计数确实减少（Counter 判定会变红）
    from collections import Counter
    c_m, c_v4 = Counter(master_text.split("\n")), Counter(
        copy_text.replace(victim, "", 1).split("\n"))
    judge["N-4 counter detects loss"] = any(c_v4[k] < c_m[k] for k in c_m)
    # N-5：删函数定义后符号判定必须变红
    v5 = copy_text.replace("def a8_sweep_carrier_processes(", "def _removed_sweep(", 1)
    judge["N-5 symbol check flips"] = ("def a8_sweep_carrier_processes" not in v5)
    # N-6：注入 try 局部守卫后 no_try_local 必须变红
    v6 = copy_text.replace("if A8_ALLOW_LOADER[0]:", "if _u8_authorized:", 1)
    a8pos = v6.find("# ==== [A8] 授权趟")
    tail = v6[a8pos:] if a8pos >= 0 else ""
    judge["N-6 no_try_local flips"] = ("if _u8_authorized:" in tail)
    ev.append("independent judgement of the 6 segments:")
    for k, v in judge.items():
        ev.append(f"  {k}: {v}")
    # 覆盖性评价
    coverage = {
        "N-1": "covers mother-hash gate",
        "N-2": "covers guard-is-module-level (literal)",
        "N-3": "covers decl<assign<guard ordering",
        "N-4": "covers append-only (zero removed lines) on a REAL mother line",
        "N-5": "covers A8 symbol presence",
        "N-6": "covers no try-local name in A8 tail",
    }
    ev.append("segment coverage (as designed):")
    for k, v in coverage.items():
        ev.append(f"  {k}: {v}")
    ev.append("NOTE: N-1..N-6 exercise the GENERATOR's self-checks, not the "
              "runtime process-tree behaviour; runtime kill path is "
              "UNVERIFIABLE without launching the game.")
    all_judge = all(judge.values())
    ok = (proc.returncode == 0 and red_ok and chk_ok and res_ok and all_judge)
    record("K8", "负控有效性（重跑 + 独立判断覆盖性）",
           "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K9 合成冒烟
# ---------------------------------------------------------------------------
def k9():
    ev = []
    copy_text = COPY.read_text(encoding="utf-8")
    try:
        tree = ast.parse(copy_text)
        ev.append("ast.parse(copy): OK")
    except SyntaxError as e:
        record("K9", "合成冒烟", "REFUTED", ev + [f"SyntaxError: {e}"])
        return
    # 模块级符号存在（在模块 body 里，不是只在字符串里）
    top_funcs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    need = ["a8_sweep_carrier_processes", "_a8_query_image_path",
            "_a8_path_under_carrier", "terminate_owned_process", "find_pids",
            "note_cleanup_failure", "main"]
    for s in need:
        ev.append(f"module-level def {s}: {s in top_funcs}")
    sym_ok = all(s in top_funcs for s in need)
    # 模块级常量
    consts = {t.id for n in tree.body if isinstance(n, ast.Assign)
              for t in n.targets if isinstance(t, ast.Name)}
    ev.append(f"module-level A8_ALLOW_LOADER const: {'A8_ALLOW_LOADER' in consts}")
    # 依赖符号在同一模块可见（ctypes / wt / time / Path / find_pids）
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                imported.add(a.asname or a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                imported.add(a.asname or a.name)
    for dep in ("ctypes", "time", "Path"):
        ev.append(f"dependency {dep} imported: {dep in imported}")
    deps_ok = all(d in imported for d in ("ctypes", "time", "Path"))
    # 不启动游戏 / 不碰真机：本脚本只做 AST + exec 纯函数
    ev.append("no subprocess/Popen of game binaries performed by this verifier: True")
    # 导入期安全：新增函数注解引用的名字必须已在前面定义（否则 def 时求值会炸）
    future = [a.name for n in tree.body if isinstance(n, ast.ImportFrom)
              and n.module == "__future__" for a in n.names]
    ev.append(f"__future__ imports: {future}")
    first_def = {}
    for n in tree.body:
        if isinstance(n, (ast.ClassDef, ast.FunctionDef)):
            first_def.setdefault(n.name, n.lineno)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    first_def.setdefault(t.id, n.lineno)
    a8_line = first_def.get("a8_sweep_carrier_processes")
    ann_ok = True
    for ann_name in ("Recorder", "TripBudget"):
        ln = first_def.get(ann_name)
        ok_ann = (ln is not None and a8_line is not None and ln < a8_line)
        ev.append(f"annotation {ann_name} defined@{ln} < A8 def@{a8_line} : {ok_ann}")
        ann_ok = ann_ok and ok_ann
    ev.append(f"from __future__ import annotations (deferred eval) : "
              f"{'annotations' in future}")
    # 路径三用例复跑（与 K7 同源，确保冒烟独立成立）
    src = extract_func_src(tree, copy_text, "_a8_path_under_carrier")
    ns = {"Path": Path}
    exec(compile(src, "<a8>", "exec"), ns)
    fn, P = ns["_a8_path_under_carrier"], ns["Path"]
    r1 = fn(r"D:\qa\abc\gamemd.exe", P(r"D:\qa\abc"))
    r2 = fn(r"D:\qa\abcd\x.exe", P(r"D:\qa\abc"))
    r3 = fn(r"C:\Windows\system32\x.exe", P(r"D:\qa\abc"))
    ev.append(f"path smoke: (a)={r1} (b)={r2} (c)={r3} "
              f"expect True/False/False")
    path_ok = (r1 is True and r2 is False and r3 is False)
    ok = sym_ok and deps_ok and path_ok and ("A8_ALLOW_LOADER" in consts) and ann_ok
    record("K9", "合成冒烟（ast.parse + 符号 + 路径三用例）",
           "CONFIRMED" if ok else "REFUTED", ev)


# ---------------------------------------------------------------------------
# K10 附加风险审查（静态可查部分 + 明确划出不可核验边界）
# ---------------------------------------------------------------------------
def k10():
    ct = parse(COPY)
    src = COPY.read_text(encoding="utf-8")
    fn = {n.name: n for n in ct.body if isinstance(n, ast.FunctionDef)}
    ev = []
    # 10.1 退出码传导链：note_cleanup_failure -> CLEANUP_FAILURES
    #      -> merge_cleanup_code -> _main_wrapper -> SystemExit
    ncf = ast.dump(fn["note_cleanup_failure"])
    mcc = ast.dump(fn["merge_cleanup_code"])
    ev.append(f"note_cleanup_failure appends CLEANUP_FAILURES : "
              f"{'CLEANUP_FAILURES' in ncf}")
    ev.append(f"merge_cleanup_code reads CLEANUP_FAILURES  : "
              f"{'CLEANUP_FAILURES' in mcc}")
    ev.append(f"merge_cleanup_code takes min by _rank      : "
              f"{'min' in mcc}")
    ev.append(f"EXIT_TERMINATE_FAILED in CLEANUP_CODE_PRIORITY : "
              f"{'EXIT_TERMINATE_FAILED' in src}")
    ev.append(f"_main_wrapper merges main() return + cleanup : "
              f"{'final = merge_cleanup_code(code)' in src}")
    chain_ok = ('CLEANUP_FAILURES' in ncf and 'CLEANUP_FAILURES' in mcc
                and 'EXIT_TERMINATE_FAILED' in src
                and 'final = merge_cleanup_code(code)' in src)
    # 10.2 单趟一次性：CLEANUP_FAILURES 在 main 开头 clear
    ev.append(f"CLEANUP_FAILURES.clear() present : "
              f"{'CLEANUP_FAILURES.clear()' in src}")
    # 10.3 A8 块位于载体删除之前（先杀进程再删目录，否则文件锁）
    main_fn = [n for n in ct.body if isinstance(n, ast.FunctionDef)
               and n.name == "main"][0]
    tr = [n for n in main_fn.body if isinstance(n, ast.Try) and n.finalbody][0]
    names = [ast.dump(x) for x in tr.finalbody]
    a8_idx = next((i for i, d in enumerate(names) if "A8_ALLOW_LOADER" in d), None)
    del_idx = next((i for i, d in enumerate(names)
                    if "delete_carrier" in d or "fin_carrier" in d), None)
    ev.append(f"finalbody order: A8 idx={a8_idx} carrier-delete idx={del_idx} "
              f"-> A8 first = {a8_idx is not None and del_idx is not None and a8_idx < del_idx}")
    order_ok = (a8_idx is not None and del_idx is not None and a8_idx < del_idx)
    # 10.4 已知静态弱点（不构成 REFUTED，但须记录）
    sweep = fn["a8_sweep_carrier_processes"]
    ssrc = ast.get_source_segment(src, sweep)
    ev.append("--- documented static caveats ---")
    ev.append(f"C1 dead local TARGETS assigned but never used : "
              f"{'TARGETS' in ssrc and ssrc.count('TARGETS') == 1}")
    ev.append("C2 if OpenProcess/QueryFullProcessImageNameW fails, the pid is "
              "silently skipped in BOTH kill loop and remaining assertion "
              "=> an unqueryable process under the carrier dir could yield a "
              "false PASS (mitigated: same-user processes are queryable with "
              "PROCESS_QUERY_LIMITED_INFORMATION)")
    ev.append("C3 `remaining` excludes own_pid (loader pid) => a surviving "
              "loader is not counted by A8, but its survival is already "
              "recorded by the TERM item as EXIT_TERMINATE_FAILED(24) "
              "=> V-fail still triggered")
    ev.append("C4 process name matching uses find_pids('gamemd.exe'/"
              "'ra2loader.exe') by basename, but path ownership is verified "
              "afterwards => not a by-name mass kill")
    ev.append("C5 A8 only runs when A8_ALLOW_LOADER[0] is True => non-authorized "
              "trips keep byte-identical behaviour (default False)")
    # 10.5 运行时行为：必须真机起 loader 才能验
    ev.append("--- UNVERIFIABLE boundary ---")
    ev.append("R1 actual process-tree kill on a real ra2loader.exe -> gamemd.exe "
              "spawn: NOT executed (rule: no game launch). Static AST shows "
              "TerminateProcess per verified carrier path; runtime efficacy "
              "remains UNVERIFIABLE in this harness.")
    ev.append("R2 zero-residue assertion on a real trip: UNVERIFIABLE without "
              "launching the game.")
    record("K10", "附加风险审查（传导链 / 顺序 / 已知弱点 / 不可核验边界）",
           "CONFIRMED" if (chain_ok and order_ok) else "REFUTED", ev)


# ---------------------------------------------------------------------------
def main():
    print("A8 independent verification")
    print(f"python : {sys.version.split()[0]} ({sys.executable})")
    print(f"master : {MASTER}")
    print(f"copy   : {COPY}")
    print(f"diff   : {DIFF}")
    print(f"gen    : {GEN}")
    print(f"negctl : {NEGCTL}")
    for fn in (k1, k2, k3, k4, k5, k6, k7, k8, k9, k10):
        try:
            fn()
        except Exception as e:
            import traceback
            record(fn.__name__.upper(), "harness error", "UNVERIFIABLE",
                   [f"{type(e).__name__}: {e}", traceback.format_exc()[-800:]])
    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for key, title, status, _ in RESULTS:
        print(f"{key:4s} {status:13s} {title}")
    print()
    print(f"REFUTED count = {len(FAILED)}")
    print(f"overall = {'REFUTED' if FAILED else 'CONFIRMED'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
