# -*- coding: utf-8 -*-
"""A8 路径归属判定的独立边界测试。

做法：用 importlib 加载补丁副本模块，直接调用 `_a8_path_under_carrier`。
不 import 母本（母本模块级有 `ctypes.windll` 调用，且会解析环境变量）。
补丁副本同样有模块级 `ctypes` 调用，但都是**只读声明**（argtypes 赋值），
不启动进程、不写盘，可安全加载。

为什么必须测
------------
`_a8_path_under_carrier` 决定「哪些进程算本趟的」：
判宽 ⇒ **杀别人的进程**；判窄 ⇒ **漏杀残留**。这是 A8 唯一的安全关键点。
"""
import importlib.util
import sys
from pathlib import Path

DST = Path(r"D:\Project\ra2-campaign-forge\lead\goal1_a8_fix_20261022\qc151_trip.harness4.py")

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


def main():
    print(f"loading: {DST}")
    spec = importlib.util.spec_from_file_location("harness4_under_test", DST)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"ABORT: module import failed: {e!r}")
        return 1
    print("module loaded OK")

    under = getattr(mod, "_a8_path_under_carrier", None)
    if under is None:
        print("ABORT: _a8_path_under_carrier not found")
        return 1

    # ---- 正例 ----
    chk("(a) carrier C:\\t\\abc , proc C:\\t\\abc\\gamemd.exe -> True",
        under(r"C:\t\abc\gamemd.exe", Path(r"C:\t\abc")) is True)

    # ---- 关键反例：startswith 会误判 True 的经典陷阱 ----
    chk("(b) carrier C:\\t\\abc , proc C:\\t\\abcd\\x.exe -> False (startswith trap)",
        under(r"C:\t\abcd\x.exe", Path(r"C:\t\abc")) is False)

    chk("(c) carrier C:\\t\\abc , proc C:\\Windows\\system32\\x.exe -> False",
        under(r"C:\Windows\system32\x.exe", Path(r"C:\t\abc")) is False)

    # ---- 更多边界 ----
    chk("(d) empty image path -> False", under("", Path(r"C:\t\abc")) is False)
    chk("(e) None image path -> False", under(None, Path(r"C:\t\abc")) is False)

    chk("(f) forward-slash variant -> True",
        under("C:/t/abc/gamemd.exe", Path(r"C:\t\abc")) is True)

    chk("(g) sibling dir with same prefix+sep -> False",
        under(r"C:\t\abc-x\y.exe", Path(r"C:\t\abc")) is False)

    # 大小写：win32 上 Path 是 WindowsPath，relative_to 内部用 _str_normcase
    # （等价 os.path.normcase）比较 ⇒ **大小写不敏感**，与 NTFS 语义一致。
    # ★ 本节首版误记为"大小写敏感"，已被异族核验实跑纠正。
    r_upper = under(r"C:\T\ABC\gamemd.exe", Path(r"C:\t\abc"))
    print(f"  [INFO] case-variant result = {r_upper} "
          f"(WindowsPath.relative_to 大小写不敏感，符合 NTFS 语义)")
    chk("(h) case-variant matches (NTFS semantics, case-insensitive)",
        r_upper is True, str(r_upper))

    # ---- 核心：确认实现用的是 relative_to 而不是 startswith ----
    #   ★ 判据要看**代码行**，不能看整段源码：docstring 里为了说明陷阱
    #     本身就写了 "startswith" 这个词（本轮首版因此假红）。
    import inspect
    src_fn = inspect.getsource(under)
    code_lines = [ln.split("#", 1)[0] for ln in src_fn.split("\n")]
    code_only = "\n".join(code_lines)
    # 去掉 docstring 三引号块
    in_doc = False
    kept = []
    for ln in code_lines:
        q = ln.count('"""') + ln.count("'''")
        if q % 2 == 1:
            in_doc = not in_doc
            continue
        if not in_doc:
            kept.append(ln)
    code_only = "\n".join(kept)
    chk("implementation uses relative_to in CODE, not startswith",
        "relative_to" in code_only and "startswith" not in code_only,
        f"relative_to={'relative_to' in code_only} "
        f"startswith={'startswith' in code_only}")

    # ---- 确认清扫函数确实按载体路径过滤，且不按名全杀 ----
    sweep = getattr(mod, "a8_sweep_carrier_processes", None)
    if sweep is None:
        chk("a8_sweep_carrier_processes exists", False, "missing")
    else:
        sw_src = inspect.getsource(sweep)
        chk("a8_sweep_carrier_processes exists", True, "found")
        chk("sweep calls _a8_path_under_carrier before killing",
            "_a8_path_under_carrier(" in sw_src, "present")
        chk("sweep does NOT use taskkill /IM (no name-wide kill)",
            "taskkill" not in sw_src, "no taskkill")
        chk("sweep excludes the trip's own pid",
            "own_pid" in sw_src and "pid == own_pid" in sw_src, "own_pid guard")
        chk("sweep re-enumerates to assert zero remaining",
            "remaining" in sw_src and "find_pids" in sw_src, "remaining check")

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
