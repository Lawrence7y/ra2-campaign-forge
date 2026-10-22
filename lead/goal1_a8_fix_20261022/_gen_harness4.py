#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A8 补丁生成器：从 harness3_u8.py 派生 harness4.py（补丁副本制）。

母本零改动：本脚本只**读**母本，只**写**新副本到 lead/goal1_a8_fix_20261022/。

A8 缺陷（裁决 3）
-----------------
`--allow-loader` 授权趟启动的是 `ra2loader.exe`，loader 再派生 `gamemd.exe`。
收尾 `terminate_owned_process()` 只终止本趟 `Popen` 的 pid（= loader 的 pid），
⇒ **gamemd 子进程残留**。裁决 3 要求：
  1. 收尾按**进程树**终止 loader 派生的 gamemd pid；
  2. 收尾断言零 gamemd / ra2loader 残留，不满足判该趟 V-fail。

实现要点
--------
- 只在本趟 `--allow-loader` 授权趟生效（`ALLOW_LOADER_EXE` 分支），非授权趟行为**完全不变**。
- 按**可执行文件全路径落在本趟载体目录下**精确匹配（沿用 `u8_v1v2_probe.py:196-220` 先例），
  不做按名全杀。
- 每个候选进程先核 `QueryFullProcessImageNameW` 路径前缀 == 本趟载体目录（大小写不敏感、
  带分隔符边界），再 `TerminateProcess`。
- 收尾后**再枚举一次**断言零残留；不满足 ⇒ `note_cleanup_failure(EXIT_TERMINATE_FAILED)`，
  使退出码非 0（V-fail）。

用法
----
    python _gen_harness4.py            # 生成副本并自检
    python _gen_harness4.py --check    # 只自检，不写
"""
import hashlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u8_impl_20261021/qc151_trip.harness3_u8.py"
DST_DIR = ROOT / "lead/goal1_a8_fix_20261022"
DST = DST_DIR / "qc151_trip.harness4.py"
DIFF = DST_DIR / "a8.diff"

SRC_SHA16 = "7db3c11009b7183c"   # 母本 harness3_u8.py 的 LF sha16（台账 §324 记载）

# ---------------------------------------------------------------------------
# 补丁 1：在 terminate_owned_process 之后插入进程树清扫函数
# ---------------------------------------------------------------------------
ANCHOR_1 = '''# ===========================================================================
# §10 · ⑤ 导航链与采帧
# ===========================================================================
def find_main_window(pid: int) -> tuple:'''

PATCH_1 = '''# ===========================================================================
# [A8] 进程树清扫：终止本趟载体目录下的 gamemd / ra2loader 残留
# ===========================================================================
def _a8_query_image_path(pid: int):
    """★ 只读：取进程可执行文件全路径。失败返回 None。

    ★ 每个 ctypes 调用都声明 argtypes/restype（★ 不声明会让 HANDLE 在 64 位截断）。
    """
    k32 = ctypes.windll.kernel32
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.QueryFullProcessImageNameW.argtypes = [
        wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    k32.QueryFullProcessImageNameW.restype = wt.BOOL
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_unicode_buffer(2048)
        n = wt.DWORD(2048)
        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return buf.value
        return None
    finally:
        k32.CloseHandle(h)


def _a8_path_under_carrier(image_path: str, carrier_dir: Path) -> bool:
    """★ 路径归属判定：image_path 是否落在 carrier_dir 之下。

    ★ 必须按**目录边界**比较，不能只用 startswith：
      载体 `...\\abc` 与 `...\\abcd` 前者是后者前缀，startswith 会误判。
    """
    if not image_path:
        return False
    try:
        img = Path(image_path).resolve()
        base = Path(carrier_dir).resolve()
    except Exception:
        return False
    try:
        img.relative_to(base)
        return True
    except ValueError:
        return False


def a8_sweep_carrier_processes(rec: Recorder, carrier_dir: Path,
                               own_pid: int | None) -> dict:
    """★★ [A8] 按载体目录精确清扫 gamemd / ra2loader 残留（★ 不做按名全杀）。

    ★ 只在 `--allow-loader` 授权趟调用（loader 会派生 gamemd）。
    ★ 三轮重试：子进程退出可能滞后于父进程终止。
    ★ 返回 {"swept": [...], "remaining": [...], "rounds": n}。
    ★★ 调用方必须检查 `remaining` 非空 ⇒ 记收尾失败（V-fail）。
    """
    TARGETS = ("gamemd.exe", "ra2loader.exe")
    swept = []
    rounds = 0
    for _round in range(3):
        rounds = _round + 1
        killed = 0
        for pid in find_pids("gamemd.exe") + find_pids("ra2loader.exe"):
            if own_pid is not None and pid == own_pid:
                continue
            img = _a8_query_image_path(pid)
            if img is None or not _a8_path_under_carrier(img, carrier_dir):
                continue
            k32 = ctypes.windll.kernel32
            k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
            k32.OpenProcess.restype = wt.HANDLE
            k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
            k32.TerminateProcess.restype = wt.BOOL
            k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
            k32.WaitForSingleObject.restype = wt.DWORD
            k32.CloseHandle.argtypes = [wt.HANDLE]
            k32.CloseHandle.restype = wt.BOOL
            PROCESS_TERMINATE = 0x0001
            SYNCHRONIZE = 0x00100000
            h = k32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
            if not h:
                continue
            try:
                if k32.TerminateProcess(h, 1):
                    k32.WaitForSingleObject(h, 5000)
                    killed += 1
                    swept.append({"pid": pid, "image": img})
            finally:
                k32.CloseHandle(h)
        if killed == 0:
            break
        time.sleep(0.8)

    # ★ 收尾断言：再枚举一次，看还有没有落在我载体目录下的
    remaining = []
    for pid in find_pids("gamemd.exe") + find_pids("ra2loader.exe"):
        if own_pid is not None and pid == own_pid:
            continue
        img = _a8_query_image_path(pid)
        if img is not None and _a8_path_under_carrier(img, carrier_dir):
            remaining.append({"pid": pid, "image": img})

    rec.add("A8", "a8_sweep_enabled", True, "script:a8_sweep_carrier_processes",
            note="★★ [A8] 授权趟进程树清扫（按载体目录精确匹配，非按名全杀）")
    rec.add("A8", "a8_carrier_dir", str(carrier_dir),
            "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_swept_count", len(swept),
            "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_swept_detail", swept, "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_remaining_count", len(remaining),
            "script:a8_sweep_carrier_processes",
            note="★★ 必须为 0；非 0 ⇒ 该趟 V-fail")
    rec.add("A8", "a8_remaining_detail", remaining,
            "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_rounds", rounds, "script:a8_sweep_carrier_processes")
    return {"swept": swept, "remaining": remaining, "rounds": rounds}


# ===========================================================================
# §10 · ⑤ 导航链与采帧
# ===========================================================================
def find_main_window(pid: int) -> tuple:'''

# ---------------------------------------------------------------------------
# 补丁 2：模块级授权标志容器（★ finally 必须能读到，不能依赖 try 内局部变量）
# ---------------------------------------------------------------------------
ANCHOR_2A = '''# ★ Popen 清理令牌（★ `main()` 内建、传给 `launch_direct`；★ 见 §9 `LaunchToken`）
LAUNCH_TOKEN = None'''

PATCH_2A = '''# ★ Popen 清理令牌（★ `main()` 内建、传给 `launch_direct`；★ 见 §9 `LaunchToken`）
LAUNCH_TOKEN = None

# ★★ [A8] 授权趟标志（★ 模块级容器，★ `finally` 必须能读到）。
#   ★ 理由：`_u8_authorized` 是 `main()` try 内的局部变量；若在它赋值**之前**
#     抛异常（如母本冻结失败、预算超限），`finally` 里引用它会 `NameError`
#     ⇒ 收尾本身崩掉。用单元素 list 与既有 `FINALIZE_CODE` / `TRIP_CARRIER`
#     同范式，★ 默认 False ⇒ 非授权趟行为**逐字不变**。
A8_ALLOW_LOADER = [False]'''


# ---------------------------------------------------------------------------
# 补丁 3：在 _u8_authorized 赋值后写入模块级容器
# ---------------------------------------------------------------------------
ANCHOR_3 = '''        _u8_authorized = allow_loader_authorized(args, TRIP_ID)
        rec.add("LAUNCH", "u8_allow_loader_authorized", _u8_authorized,'''

PATCH_3 = '''        _u8_authorized = allow_loader_authorized(args, TRIP_ID)
        # ★★ [A8] 同步到模块级容器（★ 早于 launch，★ 保证 finally 一定读得到）。
        A8_ALLOW_LOADER[0] = bool(_u8_authorized)
        rec.add("LAUNCH", "u8_allow_loader_authorized", _u8_authorized,'''


# ---------------------------------------------------------------------------
# 补丁 4：main() 终止块之后插入 A8 清扫调用
# ---------------------------------------------------------------------------
ANCHOR_4 = '''        else:
            rec.add("TERM", "termination_verdict", "N/A", "script:main",
                    note="★ 未启动（Popen 未成功/未登记）⇒ 不适用"
                         "（★ 仅此情形；★ 不用于吞掉已启动后的回收责任）")'''

PATCH_4 = '''        else:
            rec.add("TERM", "termination_verdict", "N/A", "script:main",
                    note="★ 未启动（Popen 未成功/未登记）⇒ 不适用"
                         "（★ 仅此情形；★ 不用于吞掉已启动后的回收责任）")

        # ==== [A8] 授权趟：按载体目录清扫 loader 派生的 gamemd 残留 ====
        #   ★ 只在 A8_ALLOW_LOADER[0] 为真时执行（★ 读模块级容器，不读 try 局部）。
        #   ★★ 残留非 0 ⇒ note_cleanup_failure ⇒ 退出码非 0 ⇒ 该趟 V-fail。
        if A8_ALLOW_LOADER[0]:
            _a8_carrier = (Path(TRIP_CARRIER["dir"]) if TRIP_CARRIER["dir"]
                           else carrier_dir)
            try:
                _a8_res = a8_sweep_carrier_processes(
                    rec, _a8_carrier,
                    term_pid if term_pid is not None else None)
                if _a8_res["remaining"]:
                    note_cleanup_failure(
                        EXIT_TERMINATE_FAILED, "script:main:finally:a8",
                        "★ [A8] 载体目录下仍有 gamemd/ra2loader 残留 %d 个 ⇒ V-fail"
                        % len(_a8_res["remaining"]), rec)
                    rec.add("A8", "a8_verdict", "FAIL", "script:main:finally:a8",
                            note="★★ 残留未清零 ⇒ 本趟判 V-fail")
                else:
                    rec.add("A8", "a8_verdict", "PASS", "script:main:finally:a8",
                            note="★ 零残留（已断言）")
            except Exception as _a8e:
                note_cleanup_failure(
                    EXIT_TERMINATE_FAILED, "script:main:finally:a8",
                    "★ [A8] 清扫异常：%r ⇒ 视为收尾失败" % (_a8e,), rec)
                rec.add("A8", "a8_verdict", "ERROR", "script:main:finally:a8",
                        note="★★ 清扫抛异常 ⇒ V-fail：%r" % (_a8e,))
        else:
            rec.add("A8", "a8_verdict", "N/A", "script:main:finally:a8",
                    note="★ 非授权趟（直启 gamemd，无 loader 派生进程）")'''


def lf_sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def crlf_sha16(b: bytes) -> str:
    n = b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(n).hexdigest()[:16]


def main():
    check_only = "--check" in sys.argv
    raw = SRC.read_bytes()
    print(f"src   : {SRC}")
    print(f"bytes : {len(raw)}")
    print(f"LF16  : {lf_sha16(raw)}  (expect {SRC_SHA16})")
    if lf_sha16(raw) != SRC_SHA16:
        print("ABORT: mother hash mismatch (mother must stay unchanged)")
        return 1

    text = raw.decode("utf-8")
    assert "\r\n" not in text, "mother must be LF-only"

    for name, anchor in (("ANCHOR_1", ANCHOR_1), ("ANCHOR_2A", ANCHOR_2A),
                         ("ANCHOR_3", ANCHOR_3), ("ANCHOR_4", ANCHOR_4)):
        cnt = text.count(anchor)
        print(f"{name}: {cnt} occurrence(s)")
        if cnt != 1:
            print(f"ABORT: {name} not unique")
            return 1

    patched = (text.replace(ANCHOR_1, PATCH_1, 1)
                   .replace(ANCHOR_2A, PATCH_2A, 1)
                   .replace(ANCHOR_3, PATCH_3, 1)
                   .replace(ANCHOR_4, PATCH_4, 1))
    print(f"patched bytes: {len(patched.encode('utf-8'))} "
          f"(+{len(patched.encode('utf-8')) - len(raw)})")

    # ---- 自检 1：语法 ----
    import ast
    try:
        ast.parse(patched)
    except SyntaxError as e:
        print(f"ABORT: syntax error after patch: {e}")
        return 1
    print("ast.parse : OK")

    # ---- 自检 2：新增符号存在且唯一 ----
    for sym in ("def a8_sweep_carrier_processes", "def _a8_query_image_path",
                "def _a8_path_under_carrier", "a8_sweep_carrier_processes(",
                '"A8"'):
        n = patched.count(sym)
        print(f"  {sym!r}: {n}")
        if n < 1:
            print(f"ABORT: symbol {sym!r} missing")
            return 1

    # ---- 自检 3：母本关键约束仍在（未被破坏） ----
    must_keep = [
        "**不改**游戏内存、不注入、不发消息到窗口过程",
        "def terminate_owned_process(",
        "def find_pids(",
        "EXIT_TERMINATE_FAILED = 24",
        "note_cleanup_failure(",
    ]
    for m in must_keep:
        if m not in patched:
            print(f"ABORT: mother constraint missing after patch: {m[:40]!r}")
            return 1
    print("mother constraints: all present")

    # ---- 自检 5：A8 清扫块**不得**引用 try 内局部变量 ----
    #   ★ 本轮首版就是踩了这个坑：finally 里写 `if allow_loader_flag:`
    #     而该名根本不存在（真实名是 try 内的 `_u8_authorized`）⇒ 收尾必 NameError。
    #   ★ 判据：A8 块的守卫必须是模块级容器 `A8_ALLOW_LOADER[0]`。
    if "if A8_ALLOW_LOADER[0]:" not in patched:
        print("ABORT: A8 guard must read module-level A8_ALLOW_LOADER[0]")
        return 1
    for bad in ("allow_loader_flag", "if _u8_authorized:", "if allow_loader:"):
        # 只检查 finally 段内（A8 块之后）
        a8_pos = patched.find("# ==== [A8] 授权趟")
        tail = patched[a8_pos:] if a8_pos >= 0 else ""
        if bad in tail:
            print(f"ABORT: A8 block references try-local/undefined name {bad!r}")
            return 1
    print("A8 guard scope: module-level only")

    # ---- 自检 6：模块级容器声明存在且早于使用 ----
    decl = patched.find("A8_ALLOW_LOADER = [False]")
    use = patched.find("A8_ALLOW_LOADER[0] = bool(_u8_authorized)")
    guard = patched.find("if A8_ALLOW_LOADER[0]:")
    print(f"A8_ALLOW_LOADER decl@{decl} assign@{use} guard@{guard}")
    if not (0 < decl < use < guard):
        print("ABORT: A8_ALLOW_LOADER ordering wrong (decl < assign < guard)")
        return 1
    print("A8 container ordering: OK")

    # ---- 自检 4：改动只增不改（删除行数应为 0） ----
    old_lines = text.split("\n")
    new_lines = patched.split("\n")
    from collections import Counter
    c_old, c_new = Counter(old_lines), Counter(new_lines)
    gone = [ln for ln in c_old if c_new[ln] < c_old[ln]]
    print(f"lines: {len(old_lines)} -> {len(new_lines)} "
          f"(+{len(new_lines) - len(old_lines)})")
    print(f"removed lines: {len(gone)}")
    if gone:
        print("ABORT: patch must be append-only (no removed lines)")
        for g in gone[:5]:
            print(f"  gone: {g[:70]!r}")
        return 1

    if check_only:
        print("CHECK ONLY: no files written")
        return 0

    DST_DIR.mkdir(parents=True, exist_ok=True)
    DST.write_bytes(patched.encode("utf-8"))

    # ---- 生成 unified diff ----
    import difflib
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile="qc151_trip.harness3_u8.py",
        tofile="qc151_trip.harness4.py",
        lineterm="", n=3)
    DIFF.write_text("\n".join(diff) + "\n", encoding="utf-8", newline="\n")

    out = DST.read_bytes()
    print()
    print(f"dst   : {DST}")
    print(f"bytes : {len(out)}")
    print(f"LF16  : {lf_sha16(out)}")
    print(f"CRLF16: {crlf_sha16(out)}")
    print(f"diff  : {DIFF} ({DIFF.stat().st_size} bytes)")
    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
