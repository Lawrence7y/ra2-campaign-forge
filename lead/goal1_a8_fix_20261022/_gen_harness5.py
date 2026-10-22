#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A8-b 补丁生成器：从 harness4.py 派生 harness5.py（补正控探针）。

母本零改动：只**读** harness4，只**写**新副本到 lead/goal1_a8_fix_20261022/。

要修的缺口（§353 已知残留，异族核验 C6 指出）
---------------------------------------------
`find_pids()` 在 `CreateToolhelp32Snapshot` 失败时 `return pids`（空 list）。
A8 的 `remaining` 断言把「空 list」当成「零残留」⇒ **枚举失败被误判为清扫成功**
⇒ false-PASS 通道。这会让 ① 真机趟的 V 门失去意义。

修法：**枚举器正控探针**
----------------------
清扫前先做一次「枚举器自检」：
1. 用 `find_pids` 查一个**本进程必然存在**的名字 —— 本进程自己的 exe 名；
2. 若查不到自己的 pid ⇒ 枚举器坏了 ⇒ 记 `EXIT_MODULE_ENUM_FAILED` 语义的收尾失败
   （复用既有退出码 63，语义 = 枚举失败，**不新增退出码**）；
3. 清扫后再查一次自己 ⇒ 仍须查到（否则中途坏掉）。

设计要点
--------
- **不新增退出码**：复用 `EXIT_MODULE_ENUM_FAILED = 63`（既有语义「枚举失败 ⇒ 不当未加载放行」）。
- **不改 `find_pids`**：它是母本函数，多处在用。探针在 A8 层做，不动母本语义。
- 探针失败 ⇒ 直接把 `remaining` 置为哨兵，使调用方的 V-fail 路径必然触发。

用法
----
    python _gen_harness5.py            # 生成并自检
    python _gen_harness5.py --check    # 只自检不写
"""
import ast
import hashlib
import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "lead/goal1_a8_fix_20261022/qc151_trip.harness4.py"
DST_DIR = ROOT / "lead/goal1_a8_fix_20261022"
DST = DST_DIR / "qc151_trip.harness5.py"
DIFF = DST_DIR / "a8b.diff"

SRC_SHA16 = "cd9bbc87e46054af"   # harness4 的 LF sha16

# ---------------------------------------------------------------------------
# 补丁 1：新增枚举器正控探针函数（插在 a8_sweep_carrier_processes 之前）
# ---------------------------------------------------------------------------
ANCHOR_1 = '''def a8_sweep_carrier_processes(rec: Recorder, carrier_dir: Path,
                               own_pid: int | None) -> dict:'''

PATCH_1 = '''def _a8_enum_probe(rec: Recorder, where: str) -> dict:
    """★★ [A8-b] 枚举器正控探针：确认 `find_pids` 本身能工作。

    ★ 为什么需要：`find_pids` 在 `CreateToolhelp32Snapshot` 失败时返回**空 list**，
      与「确实没有该进程」**不可区分**。A8 的 `remaining` 断言会把前者当成后者
      ⇒ 枚举失败被误判为「零残留」⇒ false-PASS 通道（异族核验 C6）。
    ★ 做法：查**本进程自己的 exe 名**。本进程必然在进程表里 ⇒ 查不到就是枚举器坏了。
    ★ 不改 `find_pids`（母本函数，多处在用）；探针只在 A8 层做。
    ★ 返回 {"ok": bool, "self_name": str, "self_pid": int, "found": [...]}。
    """
    self_pid = os.getpid()
    self_name = ""
    try:
        self_name = Path(sys.executable).name
    except Exception:
        self_name = "python.exe"
    found = []
    err = None
    try:
        found = find_pids(self_name)
    except Exception as e:
        err = repr(e)
    ok = (self_pid in found)
    rec.add("A8", "a8_enum_probe_where", where, "script:_a8_enum_probe")
    rec.add("A8", "a8_enum_probe_self_name", self_name,
            "script:_a8_enum_probe",
            note="★ 用本进程自己的 exe 名做正控（必然存在）")
    rec.add("A8", "a8_enum_probe_self_pid", self_pid, "script:_a8_enum_probe")
    rec.add("A8", "a8_enum_probe_found", found, "script:_a8_enum_probe")
    rec.add("A8", "a8_enum_probe_ok", ok, "script:_a8_enum_probe",
            note="★★ False ⇒ 枚举器失效 ⇒ 后续 remaining 断言不可信")
    if err is not None:
        rec.add("A8", "a8_enum_probe_error", err, "script:_a8_enum_probe")
    return {"ok": ok, "self_name": self_name, "self_pid": self_pid,
            "found": found, "error": err}


def a8_sweep_carrier_processes(rec: Recorder, carrier_dir: Path,
                               own_pid: int | None) -> dict:'''

# ---------------------------------------------------------------------------
# 补丁 2：清扫前插入探针；探针失败 ⇒ remaining 置哨兵
# ---------------------------------------------------------------------------
ANCHOR_2 = '''    TARGETS = ("gamemd.exe", "ra2loader.exe")
    swept = []
    rounds = 0
    for _round in range(3):'''

PATCH_2 = '''    TARGETS = ("gamemd.exe", "ra2loader.exe")
    swept = []
    rounds = 0

    # ★★ [A8-b] 清扫前先证枚举器能工作。查不到本进程自己 ⇒ 枚举器坏了
    #   ⇒ 后续 remaining 断言不可信 ⇒ 直接返回哨兵，让调用方走 V-fail。
    probe_before = _a8_enum_probe(rec, "before_sweep")
    if not probe_before["ok"]:
        rec.add("A8", "a8_enum_verdict", "FAIL", "script:a8_sweep_carrier_processes",
                note="★★ 清扫前枚举器自检失败 ⇒ 无法判断残留 ⇒ 判 V-fail"
                     "（★ 不把「查不到」当「零残留」）")
        return {"swept": [], "remaining": [{"pid": None,
                                            "image": "<ENUM_FAILED_BEFORE_SWEEP>"}],
                "rounds": 0, "enum_probe_ok": False}

    for _round in range(3):'''

# ---------------------------------------------------------------------------
# 补丁 3：收尾断言前再验一次枚举器
# ---------------------------------------------------------------------------
ANCHOR_3 = '''    # ★ 收尾断言：再枚举一次，看还有没有落在我载体目录下的
    remaining = []'''

PATCH_3 = '''    # ★★ [A8-b] 收尾前再验一次枚举器（中途坏掉同样不可信）。
    probe_after = _a8_enum_probe(rec, "before_remaining")
    if not probe_after["ok"]:
        rec.add("A8", "a8_enum_verdict", "FAIL", "script:a8_sweep_carrier_processes",
                note="★★ 收尾断言前枚举器自检失败 ⇒ 残留不可判定 ⇒ 判 V-fail")
        return {"swept": swept,
                "remaining": [{"pid": None,
                               "image": "<ENUM_FAILED_BEFORE_REMAINING>"}],
                "rounds": rounds, "enum_probe_ok": False}

    # ★ 收尾断言：再枚举一次，看还有没有落在我载体目录下的
    remaining = []'''

# ---------------------------------------------------------------------------
# 补丁 4：返回值补 enum_probe_ok 字段
# ---------------------------------------------------------------------------
ANCHOR_4 = '''    rec.add("A8", "a8_remaining_detail", remaining,
            "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_rounds", rounds, "script:a8_sweep_carrier_processes")
    return {"swept": swept, "remaining": remaining, "rounds": rounds}'''

PATCH_4 = '''    rec.add("A8", "a8_remaining_detail", remaining,
            "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_rounds", rounds, "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_enum_verdict", "PASS", "script:a8_sweep_carrier_processes",
            note="★ 枚举器两次自检均通过 ⇒ remaining 断言可信")
    rec.add("A8", "a8_enum_probe_ok", True, "script:a8_sweep_carrier_processes")
    return {"swept": swept, "remaining": remaining, "rounds": rounds}'''


def lf16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def crlf16(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()[:16]


def main():
    check_only = "--check" in sys.argv
    raw = SRC.read_bytes()
    print(f"src   : {SRC}")
    print(f"bytes : {len(raw)}")
    print(f"LF16  : {lf16(raw)}  (expect {SRC_SHA16})")
    if lf16(raw) != SRC_SHA16:
        print("ABORT: source hash mismatch (harness4 must stay unchanged)")
        return 1

    text = raw.decode("utf-8")
    assert "\r\n" not in text, "source must be LF-only"

    for name, anchor in (("ANCHOR_1", ANCHOR_1), ("ANCHOR_2", ANCHOR_2),
                         ("ANCHOR_3", ANCHOR_3), ("ANCHOR_4", ANCHOR_4)):
        cnt = text.count(anchor)
        print(f"{name}: {cnt} occurrence(s)")
        if cnt != 1:
            print(f"ABORT: {name} not unique")
            return 1

    patched = (text.replace(ANCHOR_1, PATCH_1, 1)
                   .replace(ANCHOR_2, PATCH_2, 1)
                   .replace(ANCHOR_3, PATCH_3, 1)
                   .replace(ANCHOR_4, PATCH_4, 1))
    print(f"patched bytes: {len(patched.encode('utf-8'))} "
          f"(+{len(patched.encode('utf-8')) - len(raw)})")

    # ---- 自检 1：语法 ----
    try:
        ast.parse(patched)
    except SyntaxError as e:
        print(f"ABORT: syntax error: {e}")
        return 1
    print("ast.parse : OK")

    # ---- 自检 2：新增符号 ----
    for sym in ("def _a8_enum_probe", "_a8_enum_probe(rec,",
                "a8_enum_verdict", "enum_probe_ok"):
        n = patched.count(sym)
        print(f"  {sym!r}: {n}")
        if n < 1:
            print(f"ABORT: symbol {sym!r} missing")
            return 1

    # ---- 自检 3：不新增退出码（复用 63） ----
    old_codes = set()
    for ln in text.split("\n"):
        if ln.startswith("EXIT_") and " = " in ln:
            old_codes.add(ln.split(" = ")[0].strip())
    new_codes = set()
    for ln in patched.split("\n"):
        if ln.startswith("EXIT_") and " = " in ln:
            new_codes.add(ln.split(" = ")[0].strip())
    added = new_codes - old_codes
    print(f"  exit codes added: {sorted(added) or 'none'}")
    if added:
        print("ABORT: A8-b must NOT add new exit codes")
        return 1

    # ---- 自检 4：母本 A8 关键约束仍在 ----
    for m in ("if A8_ALLOW_LOADER[0]:", "def a8_sweep_carrier_processes(",
              "def _a8_path_under_carrier(", "note_cleanup_failure(",
              "**不改**游戏内存、不注入、不发消息到窗口过程"):
        if m not in patched:
            print(f"ABORT: constraint missing: {m[:40]!r}")
            return 1
    print("A8 constraints: all present")

    # ---- 自检 5：零删除行 ----
    c_old = Counter(text.split("\n"))
    c_new = Counter(patched.split("\n"))
    gone = [ln for ln in c_old if c_new[ln] < c_old[ln]]
    print(f"lines: {len(text.split(chr(10)))} -> {len(patched.split(chr(10)))}")
    print(f"removed lines: {len(gone)}")
    if gone:
        print("ABORT: patch must be append-only")
        for g in gone[:5]:
            print(f"  gone: {g[:70]!r}")
        return 1

    # ---- 自检 6：探针在清扫前、收尾断言前各一次 ----
    p1 = patched.find('_a8_enum_probe(rec, "before_sweep")')
    p2 = patched.find('_a8_enum_probe(rec, "before_remaining")')
    sweep_loop = patched.find("for _round in range(3):")
    rem = patched.find("remaining = []", p2 if p2 > 0 else 0)
    print(f"  probe(before_sweep)@{p1} sweep_loop@{sweep_loop} "
          f"probe(before_remaining)@{p2} remaining@{rem}")
    if not (0 < p1 < sweep_loop < p2 < rem):
        print("ABORT: probe ordering wrong")
        return 1
    print("probe ordering: OK")

    if check_only:
        print("CHECK ONLY: no files written")
        return 0

    DST_DIR.mkdir(parents=True, exist_ok=True)
    DST.write_bytes(patched.encode("utf-8"))

    import difflib
    diff = difflib.unified_diff(
        text.split("\n"), patched.split("\n"),
        fromfile="qc151_trip.harness4.py", tofile="qc151_trip.harness5.py",
        lineterm="", n=3)
    DIFF.write_text("\n".join(diff) + "\n", encoding="utf-8", newline="\n")

    out = DST.read_bytes()
    print()
    print(f"dst   : {DST}")
    print(f"bytes : {len(out)}")
    print(f"LF16  : {lf16(out)}")
    print(f"CRLF16: {crlf16(out)}")
    print(f"diff  : {DIFF} ({DIFF.stat().st_size} bytes)")
    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
