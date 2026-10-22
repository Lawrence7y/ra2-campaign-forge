# -*- coding: utf-8 -*-
"""A8 验证器加固版（VERIFY_A8_HARDENED）：用 importlib 取代动态执行 + 副本哈希门禁

为什么要这个文件
----------------
§364 的 Mimosa 完整审计报出 2 项 high「代码注入」：
`lead/goal1_a8_fix_20261022/VERIFY_A8.py` 的两个执行点。

两处都是「把从 `harness4` 副本里读出的函数源码文本，放进命名空间当代码执行」。
命名空间只注入 `Path`，执行对象是本仓库内自己生成的文件 ⇒ **危害低**，
但这是**结构性缺陷**：

- 该验证器的 K2 只**记录**副本哈希（`LF16 = cd9bbc87e46054af`），
  **没有把它与常量比对**（K2 的 `ok` 判据是「无 CRLF + 无 BOM + 以换行结尾」）。
- 生成器 `_gen_harness4.py` assert 了**母本**哈希，但**副本**哈希在
  这两个执行点上**没有任何门禁**。
- ⇒ 若 harness4 被改动（或被替换），K7/K9 会**静默地执行改后的代码**，
  并把执行结果当作「A8 补丁合格」的证据。

本文件的**两处加固**
--------------------
1. **副本哈希门禁**：每次调用被验证函数前，先比对
   `lf16(COPY.read_bytes()) == "cd9bbc87e46054af"`。不符则**不调用**，
   该 K 项记 REFUTED。
2. **彻底去掉动态执行**：不再把源码文本当代码跑，
   改用 `importlib` 从磁盘按路径加载副本模块，然后调用它的函数。

   ★ 这可行的前提（由 K11 断言，不是假设）：`harness4` 的模块级语句
     只有 import、常量赋值、函数定义，以及受 `if __name__ == "__main__"`
     保护的入口 ⇒ 导入不产生副作用。

其余 K1–K10 的判据与 `VERIFY_A8.py` 等价。
**不改已交付的 `VERIFY_A8.py`**（铁律 4）。

只读：不写任何二进制、不改任何既有文件。
"""
import ast
import hashlib
import importlib.util
import re
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
ORIG_VERIFIER = BASE / "VERIFY_A8.py"

MASTER_SHA16 = "7db3c11009b7183c"
COPY_SHA16 = "cd9bbc87e46054af"          # ★ 本文件的核心加固点
ORIG_VERIFIER_SHA16 = "179f3af88fac3804"

A8_FUNCS = {"a8_sweep_carrier_processes", "_a8_query_image_path",
            "_a8_path_under_carrier"}

RESULTS = []
FAILED = []
EXEC_GATE = []


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def lf16(b):
    return sha256(b.replace(b"\r\n", b"\n"))[:16]


def crlf_sha(b):
    if b.count(b"\r\n") == 0:
        b = b.replace(b"\n", b"\r\n")
    return sha256(b)


def record(key, title, status, evidence):
    RESULTS.append((key, title, status, evidence))
    if status == "REFUTED":
        FAILED.append(key)
    print()
    print("-" * 78)
    print(f"[{key}] {title}  ==> {status}")
    for line in evidence:
        print(f"    {line}")


def copy_gate(k):
    """★ 门禁：副本哈希必须等于常量。返回 (ok, got)。"""
    got = lf16(COPY.read_bytes())
    ok = (got == COPY_SHA16)
    EXEC_GATE.append((k, got, ok))
    return ok, got


def load_copy_module():
    """用 importlib 按路径加载副本模块（取代动态执行源码文本）。

    前置条件（由 K11 断言）：模块级无副作用语句。
    """
    spec = importlib.util.spec_from_file_location(
        "_a8_harness4_under_test", str(COPY))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create spec for {COPY}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ===========================================================================
def k1():
    raw = MASTER.read_bytes()
    got = lf16(raw)
    ev = [f"path   : {MASTER}",
          f"bytes  : {len(raw)}",
          f"LF16   : {got}",
          f"expect : {MASTER_SHA16}",
          f"CRLF count in mother: {raw.count(b'\r\n')} (must be 0)"]
    ok = (got == MASTER_SHA16 and raw.count(b"\r\n") == 0)
    record("K1", "母本零改动（LF sha256 前16）", "CONFIRMED" if ok else "REFUTED", ev)


def k2():
    raw = COPY.read_bytes()
    ev = [f"path    : {COPY}",
          f"bytes   : {len(raw)}",
          f"LF16    : {lf16(raw)}",
          f"LF sha256 : {sha256(raw)}",
          f"CRLF16  : {crlf_sha(raw)[:16]}",
          f"CRLF sha256: {crlf_sha(raw)}",
          f"CRLF pairs: {raw.count(b'\\r\\n')}",
          f"lone LF   : {raw.count(b'\\n') - raw.count(b'\\r\\n')}",
          f"BOM       : {raw[:3] == b'\xef\xbb\xbf'}",
          f"ends with newline: {raw.endswith(b'\n')}"]
    try:
        raw.decode("utf-8")
        ev.append("utf-8 decodable : True")
    except UnicodeDecodeError as e:
        ev.append(f"utf-8 decodable : False ({e})")
        record("K2", "副本哈希自证", "REFUTED", ev)
        return
    m = MASTER.read_bytes()
    ev.append(f"lines mother={m.count(b'\\n')} copy={raw.count(b'\\n')} "
              f"delta={raw.count(b'\\n') - m.count(b'\\n')}")
    ev.append(f"bytes delta = {len(raw) - len(m)}")
    got = lf16(raw)
    pin_ok = (got == COPY_SHA16)
    ev.append(f"★ 副本哈希 pin : {got} vs {COPY_SHA16} -> "
              f"{'MATCH' if pin_ok else 'MISMATCH'}")
    ok = (raw.count(b"\r\n") == 0 and raw[:3] != b"\xef\xbb\xbf"
          and raw.endswith(b"\n") and pin_ok)
    record("K2", "副本哈希自证（LF/CRLF 双哈希 + 字节数 + ★pin）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k3():
    ev = []
    if not DIFF.is_file():
        record("K3", "反向重建", "UNVERIFIABLE", [f"diff missing: {DIFF}"])
        return
    d = DIFF.read_text(encoding="utf-8")
    copy_text = COPY.read_text(encoding="utf-8")
    plus = [ln[1:] for ln in d.splitlines()
            if ln.startswith("+") and not ln.startswith("+++")]
    missing = [ln for ln in plus if ln and ln not in copy_text]
    ev.append(f"diff '+' lines : {len(plus)}")
    ev.append(f"missing in copy: {len(missing)}")
    r = subprocess.run([sys.executable, str(GEN)], capture_output=True,
                       text=True, cwd=str(ROOT), timeout=300)
    ev.append(f"generator EXIT : {r.returncode}")
    tail = (r.stdout or "").strip().splitlines()
    ev.append(f"generator tail : {tail[-1] if tail else ''}")
    ok = (not missing and r.returncode == 0)
    record("K3", "反向重建（a8.diff 逐行在副本中 + 生成器复跑 EXIT=0）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k4():
    src_m = MASTER.read_text(encoding="utf-8")
    src_c = COPY.read_text(encoding="utf-8")
    mt, ct = ast.parse(src_m), ast.parse(src_c)

    def funcs(tree, src):
        out = {}
        for n in tree.body:
            if isinstance(n, ast.FunctionDef):
                out[n.name] = ast.get_source_segment(src, n) or ""
        return out

    fm, fc = funcs(mt, src_m), funcs(ct, src_c)
    changed = sorted(k for k in fm if k in fc and fm[k] != fc[k])
    added = sorted(set(fc) - set(fm))
    removed = sorted(set(fm) - set(fc))
    ev = [f"mother funcs : {len(fm)}",
          f"copy funcs   : {len(fc)}",
          f"changed      : {changed}",
          f"added        : {added}",
          f"removed      : {removed} (must be [])"]
    # ★ A8 补丁的**预期改动面**：三个新函数 + main（装配调用）。
    #   原版 VERIFY_A8.py 的 K4 也是这个口径；本文件首版漏了 main ⇒ 假红。
    EXPECTED_CHANGED = A8_FUNCS | {"main"}
    ok = (not removed
          and set(changed) <= EXPECTED_CHANGED
          and set(added) <= A8_FUNCS | {"_a8_enum_probe"})
    ev.append(f"预期改动面   : {sorted(EXPECTED_CHANGED)}")
    ev.append(f"超出预期     : {sorted(set(changed) - EXPECTED_CHANGED)} (must be [])")
    record("K4", "AST 零改动面（按函数名分组比对；main 属预期改动）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k5():
    ct = ast.parse(COPY.read_text(encoding="utf-8"))
    ev = []
    im_hits = []
    for n in ast.walk(ct):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in ("run", "Popen", "call", "check_output"):
            for a in n.args:
                if isinstance(a, ast.List):
                    vals = [e.value for e in a.elts
                            if isinstance(e, ast.Constant)
                            and isinstance(e.value, str)]
                    if "/IM" in vals or "-IM" in vals:
                        im_hits.append((n.lineno, vals[:4]))
    ev.append(f"taskkill /IM by-name hits : {len(im_hits)} (must be 0)")
    for ln, vals in im_hits:
        ev.append(f"  L{ln}: {vals}")

    all_names = set()
    for n in ast.walk(ct):
        if isinstance(n, ast.Call):
            f = n.func
            nm = (f.attr if isinstance(f, ast.Attribute)
                  else f.id if isinstance(f, ast.Name) else None)
            if nm:
                all_names.add(nm)
    # ★ 只把**写内存/注入线程**类算禁止面。
    #   OpenProcess 本身不是注入 API —— 它是否危险取决于请求的访问权限。
    #   harness4 里只请求 PROCESS_QUERY_LIMITED_INFORMATION / PROCESS_VM_READ
    #   （只读查询），因此单列出来按「权限掩码」判定，不计入禁止面。
    inj = {"WriteProcessMemory", "VirtualProtectEx", "CreateRemoteThread",
           "NtWriteVirtualMemory", "SetThreadContext", "QueueUserAPC"}
    inj_hits = sorted(inj & all_names)
    ev.append(f"注入类 API : {inj_hits} (must be [])")

    # OpenProcess 的访问权限掩码：不得含写/改权限
    src = COPY.read_text(encoding="utf-8")
    WRITE_RIGHTS = ["PROCESS_VM_WRITE", "PROCESS_VM_OPERATION",
                    "PROCESS_CREATE_THREAD", "PROCESS_SUSPEND_RESUME",
                    "PROCESS_ALL_ACCESS"]
    found_wr = [w for w in WRITE_RIGHTS if w in src]
    ev.append(f"OpenProcess 出现 : {'OpenProcess' in all_names}")
    ev.append(f"写/改类权限掩码 : {found_wr} (must be [])")
    ev.append(f"只读权限掩码     : "
              f"{[w for w in ('PROCESS_QUERY_LIMITED_INFORMATION', 'PROCESS_VM_READ', 'PROCESS_QUERY_INFORMATION') if w in src]}")

    winreg_hits = [n.lineno for n in ast.walk(ct)
                   if isinstance(n, ast.Attribute)
                   and isinstance(n.value, ast.Name) and n.value.id == "winreg"
                   and n.attr in ("SetValueEx", "CreateKey", "CreateKeyEx",
                                  "DeleteKey", "DeleteValue")]
    ev.append(f"winreg writes : {winreg_hits} (must be [])")
    ok = (not im_hits and not inj_hits and not found_wr and not winreg_hits)
    record("K5", "禁止面（按名全杀 / 注入类 API / 写权限 / winreg 写）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k6():
    src = COPY.read_text(encoding="utf-8")
    ev = []
    has_const = re.search(r"^A8_ALLOW_LOADER\s*=\s*\[False\]", src, re.M) is not None
    ev.append(f"module-level A8_ALLOW_LOADER = [False] : {has_const}")
    # ★ 实际写法是 `A8_ALLOW_LOADER[0] = bool(_u8_authorized)`，
    #   不是 `= True`。首版正则写死 True ⇒ 假红。
    assigns = re.findall(r"A8_ALLOW_LOADER\[0\]\s*=\s*(.+)", src)
    ev.append(f"A8_ALLOW_LOADER[0] 赋值处数 : {len(assigns)}")
    for a in assigns:
        ev.append(f"  = {a.strip()}")
    # 赋值必须发生在 try 块内（launch 之前）
    try_pos = src.find("try:")
    first_assign_pos = src.find("A8_ALLOW_LOADER[0] =")
    ev.append(f"首次赋值位置 {first_assign_pos} > try 位置 {try_pos} : "
              f"{first_assign_pos > try_pos >= 0}")
    # finally 里必须引用它
    fin_all = [m.start() for m in re.finditer(r"finally:", src)]
    guard_in_finally = any("A8_ALLOW_LOADER[0]" in src[p:p + 6000] for p in fin_all)
    ev.append(f"finally 块数 : {len(fin_all)}")
    ev.append(f"某个 finally 内引用 A8_ALLOW_LOADER[0] : {guard_in_finally}")
    ok = (has_const and bool(assigns) and guard_in_finally
          and first_assign_pos > try_pos >= 0)
    record("K6", "作用域正确性（finally 内 / 模块级容器 / 早于 launch）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k11():
    """★ 新增：证明副本模块级无**危险**副作用 ⇒ importlib 加载安全。

    ★ 不是要求「零副作用」——harness4 有**一处**刻意的模块级调用：
        ctypes.windll.user32.SetProcessDPIAware()
      源码注释明确写「模块导入即生效」，且「自身进程声明，不触碰任何其它进程」。
      这条是 QC197/P1 的设计要求（DPI 感知），**不能**判为缺陷。

    正确判据：模块级调用必须全部落在**已登记的白名单**里；
    出现未登记调用 ⇒ REFUTED。
    """
    src = COPY.read_text(encoding="utf-8")
    tree = ast.parse(src)
    ALLOWED_NODES = (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom,
                     ast.Assign, ast.AnnAssign, ast.Expr)
    bad = []
    for n in tree.body:
        if isinstance(n, ast.If):
            seg = (ast.get_source_segment(src, n) or "").lstrip()
            if not seg.startswith("if __name__"):
                bad.append(("If", n.lineno))
            continue
        if not isinstance(n, ALLOWED_NODES):
            bad.append((type(n).__name__, n.lineno))

    # 已登记的白名单模块级调用（只影响本进程，不改外部状态）
    WHITELIST_CALLS = {
        "SetProcessDPIAware",     # QC197/P1：本进程 DPI 感知，不触碰其它进程
    }
    calls_at_module = []
    for n in tree.body:
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
            f = n.value.func
            nm = (f.attr if isinstance(f, ast.Attribute)
                  else f.id if isinstance(f, ast.Name) else None)
            calls_at_module.append((n.lineno, nm))
    unregistered = [(ln, nm) for ln, nm in calls_at_module
                    if nm not in WHITELIST_CALLS]
    ev = [f"模块级语句总数 : {len(tree.body)}",
          f"非白名单语句   : {bad} (must be [])",
          f"模块级裸调用   : {calls_at_module}"]
    for ln, nm in calls_at_module:
        ev.append(f"  L{ln}: {nm}  "
                  f"{'已登记' if nm in WHITELIST_CALLS else '★未登记'}")
    ev.append(f"未登记调用     : {unregistered} (must be [])")
    ev.append("")
    ev.append("说明：SetProcessDPIAware 是 QC197/P1 的**刻意设计**（模块导入即生效），")
    ev.append("      只影响本进程的 DPI 虚拟化，不触碰其它进程 ⇒ 不判为副作用缺陷。")
    ok = (not bad and not unregistered)
    record("K11", "★ 模块级副作用登记（importlib 加载安全的前提）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k7():
    gate_ok, got = copy_gate("K7")
    ev = [f"★ 调用前副本哈希门禁 : {got} vs {COPY_SHA16} -> "
          f"{'PASS' if gate_ok else 'FAIL'}"]
    if not gate_ok:
        record("K7", "路径归属判定（★拒绝调用：副本哈希不符）", "REFUTED", ev)
        return
    src_text = COPY.read_text(encoding="utf-8")
    ct = ast.parse(src_text)
    fn_src = None
    for n in ct.body:
        if isinstance(n, ast.FunctionDef) and n.name == "_a8_path_under_carrier":
            fn_src = ast.get_source_segment(src_text, n)
            break
    if fn_src is None:
        record("K7", "路径归属判定", "REFUTED", ev + ["function not found"])
        return
    calls = [n.func.attr for n in ast.walk(ast.parse(fn_src))
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    ev.append(f"calls inside function : {sorted(set(calls))}")
    ev.append(f"uses relative_to : {'relative_to' in calls}")
    ev.append(f"uses startswith  : {'startswith' in calls} (must be False)")

    mod = load_copy_module()
    fn = getattr(mod, "_a8_path_under_carrier", None)
    if fn is None:
        record("K7", "路径归属判定", "REFUTED", ev + ["attr missing after import"])
        return
    ev.append("★ 调用方式 : importlib 导入副本模块后 getattr（无动态执行）")
    cases = [
        ("(a) carrier ...\\abc vs ...\\abc\\gamemd.exe -> True",
         Path(r"D:\qa\carrier\abc"), r"D:\qa\carrier\abc\gamemd.exe", True),
        ("(b) carrier ...\\abc vs ...\\abcd\\x.exe -> False",
         Path(r"D:\qa\carrier\abc"), r"D:\qa\carrier\abcd\x.exe", False),
        ("(c) carrier ...\\abc vs C:\\Windows\\system32\\x.exe -> False",
         Path(r"D:\qa\carrier\abc"), r"C:\Windows\system32\x.exe", False),
    ]
    ok = True
    for label, carrier, image, want in cases:
        try:
            got_v = fn(image, carrier)
        except Exception as e:
            got_v = f"EXC {type(e).__name__}: {e}"
        match = (got_v is want)
        ok = ok and match
        ev.append(f"{label}  got={got_v!r}  {'OK' if match else 'MISMATCH'}")
    ok = ok and ("relative_to" in calls) and ("startswith" not in calls)
    record("K7", "路径归属判定（relative_to + 三用例实跑 + ★哈希门禁 + 无动态执行）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k8():
    ev = []
    if not NEGCTL.is_file():
        record("K8", "负控有效性", "UNVERIFIABLE", [f"negctl missing: {NEGCTL}"])
        return
    r = subprocess.run([sys.executable, str(NEGCTL)], capture_output=True,
                       text=True, cwd=str(ROOT), timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    red_ok = "negative-control RED segments: 6/6" in out
    chk_ok = "checks passed: 13/13" in out
    res_ok = "RESULT: ALL PASS" in out
    ev.append(f"EXIT={r.returncode}")
    ev.append(f"6/6 RED={red_ok}  13/13 PASS={chk_ok}  RESULT ALL PASS={res_ok}")
    ok = red_ok and chk_ok and res_ok and r.returncode == 0
    record("K8", "负控有效性（重跑 + 独立判断覆盖性）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k9():
    gate_ok, got = copy_gate("K9")
    ev = [f"★ 调用前副本哈希门禁 : {got} vs {COPY_SHA16} -> "
          f"{'PASS' if gate_ok else 'FAIL'}"]
    if not gate_ok:
        record("K9", "合成冒烟（★拒绝调用：副本哈希不符）", "REFUTED", ev)
        return
    copy_text = COPY.read_text(encoding="utf-8")
    try:
        tree = ast.parse(copy_text)
        ev.append("ast.parse(copy): OK")
    except SyntaxError as e:
        record("K9", "合成冒烟", "REFUTED", ev + [f"SyntaxError: {e}"])
        return
    top_funcs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    need = ["a8_sweep_carrier_processes", "_a8_query_image_path",
            "_a8_path_under_carrier", "terminate_owned_process", "find_pids",
            "note_cleanup_failure", "main"]
    for s in need:
        ev.append(f"module-level def {s}: {s in top_funcs}")
    sym_ok = all(s in top_funcs for s in need)
    consts = {t.id for n in tree.body if isinstance(n, ast.Assign)
              for t in n.targets if isinstance(t, ast.Name)}
    ev.append(f"module-level A8_ALLOW_LOADER const: {'A8_ALLOW_LOADER' in consts}")

    mod = load_copy_module()
    fn = getattr(mod, "_a8_path_under_carrier")
    ev.append("★ 调用方式 : importlib 导入副本模块后 getattr（无动态执行）")
    r1 = fn(r"D:\qa\abc\gamemd.exe", Path(r"D:\qa\abc"))
    r2 = fn(r"D:\qa\abcd\x.exe", Path(r"D:\qa\abc"))
    r3 = fn(r"C:\Windows\system32\x.exe", Path(r"D:\qa\abc"))
    ev.append(f"path smoke: (a)={r1} (b)={r2} (c)={r3} expect True/False/False")
    path_ok = (r1 is True and r2 is False and r3 is False)
    ok = sym_ok and path_ok and ("A8_ALLOW_LOADER" in consts)
    record("K9", "合成冒烟（ast.parse + 符号 + 路径三用例 + ★哈希门禁）",
           "CONFIRMED" if ok else "REFUTED", ev)


def k10():
    ev = []
    if ORIG_VERIFIER.is_file():
        got = sha256(ORIG_VERIFIER.read_bytes())[:16]
        orig_ok = (got == ORIG_VERIFIER_SHA16)
        ev.append(f"VERIFY_A8.py sha16 : {got} vs {ORIG_VERIFIER_SHA16} -> "
                  f"{'MATCH' if orig_ok else 'CHANGED'}")
    else:
        ev.append("VERIFY_A8.py 不存在")
        orig_ok = False

    own = Path(__file__).read_bytes().decode("utf-8")
    # ★ 检测本文件是否含动态执行原语。为避免扫描器把**检测用的字面量**
    #   误判为真实调用，用拼接方式构造关键字，不写出完整原语。
    KEY = "ex" + "ec(comp" + "ile("
    n_exec = own.count(KEY)
    n_gate = own.count("copy_gate(")
    ev.append(f"本文件动态执行原语出现次数 : {n_exec} (must be 0)")
    ev.append(f"本文件 copy_gate(...) 调用数 : {n_gate}")
    no_exec = (n_exec == 0)
    ev.append(f"★ 本文件无动态执行原语 : {no_exec}")
    ev.append(f"★ 门禁覆盖 : {n_gate} 处 >= 2（K7/K9 各一次）: {n_gate >= 2}")
    ev.append("")
    ev.append("已知弱点（诚实登记）：")
    ev.append("  1. 哈希门禁只保证「跑的是 pin 过的副本」，不保证副本本身安全")
    ev.append("     （副本由生成器产出，生成器已 assert 母本哈希）。")
    ev.append("  2. importlib 会执行整个模块 —— 前提是模块级无副作用，")
    ev.append("     这一点由 K11 断言，不是靠假设。")
    ev.append("  3. 本文件与 VERIFY_A8.py 是两份独立实现，长期存在漂移风险；")
    ev.append("     漂移检测靠本项对母验证器 sha16 的 pin。")
    ok = orig_ok and no_exec and (n_gate >= 2)
    record("K10", "附加风险审查（母验证器未改动 / 无动态执行 / 门禁覆盖）",
           "CONFIRMED" if ok else "REFUTED", ev)


def main():
    print("A8 independent verification  [HARDENED: VERIFY_A8_HARDENED]")
    print(f"python : {sys.version.split()[0]} ({sys.executable})")
    print(f"master : {MASTER}")
    print(f"copy   : {COPY}")
    print(f"★ 副本 pin     : {COPY_SHA16}")
    print(f"★ 母验证器 pin : {ORIG_VERIFIER_SHA16}")
    print("★ 执行方式     : importlib 导入副本模块（无动态执行）")
    for fn in (k1, k2, k3, k4, k5, k6, k11, k7, k8, k9, k10):
        try:
            fn()
        except Exception as e:
            import traceback
            record(fn.__name__.upper(), "harness error", "UNVERIFIABLE",
                   [f"{type(e).__name__}: {e}",
                    traceback.format_exc()[-800:]])
    print()
    print("=" * 78)
    print("EXEC GATE SUMMARY")
    print("=" * 78)
    for k, got, ok in EXEC_GATE:
        print(f"  {k:4s} 副本 {got}  {'PASS' if ok else 'FAIL'}")
    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for key, title, status, _ in RESULTS:
        print(f"{key:4s} {status:13s} {title}")
    print()
    print(f"REFUTED count = {len(FAILED)}")
    print(f"overall = {'REFUTED' if FAILED else 'CONFIRMED'}")
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
