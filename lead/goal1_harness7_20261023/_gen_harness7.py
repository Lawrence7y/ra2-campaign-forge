#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H7 补丁生成器：从 harness6.py 派生 harness7.py（修全屏矩形空等 + measure 起始硬约束）。

母本零改动：只**读** harness6 的源码文本，只**写**新副本到
`lead/goal1_harness7_20261023/`。★ 绝不 import / exec 母本
（463 KB 脚本，import 会执行顶层 `SetProcessDPIAware()` 等）。

范式照抄 `lead/goal1_harness6_20261022/_gen_harness6.py`
----------------------------------------------------
1. `ast` 解析 / 语法编译自检；
2. **唯一锚点字符串**精确替换（每处断言 `src.count(anchor) == 1`，否则 fail-closed）；
3. 生成器自检：锚点命中数、语法可编译、**零删除行**（母本行集合 ⊆ 副本行集合）；
4. 写副本 + 落 `.diff`；`--check` 只自检不写。

两项能力
--------
① 全屏矩形空等修复
   `qc151_trip.harness6.py:7979` 的采帧前等待判据是「窗口矩形 == 800×600」。
   ★ 全屏下窗口矩形恒为整屏（实测 `[0,0,2560,1440]`）⇒ 该循环**必然跑满**
     `deadline`；四趟实测 `pre_capture_wait_polls` = 251/251/244/253（×0.5 s
     ≈ 122–127 s），`stage_seconds:frame` = 122.1–126.7 s。
   ★ 而全屏抓帧走 `capture_frame_desktop`，**按构造**固定抓 800×600
     （`w, h = FRAME_W, FRAME_H`，与窗口矩形无关）⇒ 该等待在全屏下是**纯死等**。
   ★ 修法：全屏时把该循环的 `deadline` 局部重绑为 0.0（谓词立即短路），
     **母本 while 行一字不改**；`deadline` 在本点之后**零引用**（实测 grep=0）。
   ★ 窗口模式（缺省）零影响：实测窗口模式趟 `pre_capture_wait_polls` = 0、
     `stage_seconds:frame` ≈ 0.08–0.16 s（矩形本来就到 800×600）。

② measure 起始硬约束（★ 窗口必须落在开局，不得落在战斗后）
   在 nav 收口处打 `time.monotonic()` 戳，`_measure_run` 入口算
   `nav_to_measure_s`；**且仅当矩形等待短路已生效**（即 `--fullscreen` 缺省路径）
   时，超过 `H7_MEASURE_MAX_NAV_TO_W0_S` ⇒ **不采三窗**（写 w0 JSON、
   `verdict="late_start"`），并记 `late_start=true`。
   ★ 为什么必须以「短路生效」为前置：实测 2026-10-21 四趟成功趟的 nav→w0
     本来就是 126.2–130.7 s（矩形死等的必然结果）且 `verdict=ok`。
     若无条件施加本闸，`--h7-keep-rect-wait` 对照臂会被一律误判为 late_start，
     A/B 对照拿不到任何数据。短路生效后该间隔应降到 ~5 s 量级，90 s 留足余量。
   ★ fail-closed：宁可如实报「窗太晚」，也不产出一个看起来正常的战斗后 fps。
   ★ 不新增退出码（沿用既有 §5.2 纪律）；窗口模式本闸恒不启用。

用法
----
    python _gen_harness7.py            # 生成并自检
    python _gen_harness7.py --check    # 只自检不写
"""
import ast
import hashlib
import py_compile
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "lead/goal1_harness6_20261022/qc151_trip.harness6.py"
DST_DIR = ROOT / "lead/goal1_harness7_20261023"
DST = DST_DIR / "qc151_trip.harness7.py"
DIFF = DST_DIR / "h7.diff"

SRC_SHA16 = "ff8245d27b3db22a"   # harness6 的 LF sha16（★ 动手前必须实测等于此值）

# ---------------------------------------------------------------------------
# 补丁 A：H7 常量（紧跟既有 measure 协议常量之后）
# ---------------------------------------------------------------------------
ANCHOR_A = 'MEASURE_TICK_MISS_FACTOR = 1.5       # tick_miss：间隔 >1.5×p50（bench 同口径）\n'

PATCH_A = ANCHOR_A + '''
# >>> H7-BEGIN const（★ 缺省 off ⇒ 锚路径零行为差；删本块即还原 harness6 语义）
# ★★ [H7-②] measure 起始硬约束：nav 收口 → measure 入口的允许最大间隔（秒）。
#   ★★ 该闸**只在 `fs_rect_wait_skipped` 生效时才判定**（见补丁 D 的条件）——
#      理由与标定如下：
#   - 实测（2026-10-21 四趟，`nav_end=stage_begin:frame`，`w0=stage_begin:measure_w0`）：
#     nav→w0 = **130.688 / 127.704 / 130.704 / 126.187 s**，全部 >120 s，
#     但这四趟 `verdict=ok`（测到了 9–15 fps）。⇒ **长间隔本身不是失败判据**，
#     它只是「矩形死等仍在」的必然结果。
#   - 所以：`--h7-keep-rect-wait`（A/B 对照臂）下**不得**启用本闸，
#     否则对照臂会被一律判 late_start，A/B 拿不到任何数据。
#   - 短路生效时（`--fullscreen` 缺省），nav→w0 应降到 ~5 s 量级
#     （frame 段只剩采帧本身 ≈0.1 s + nav 收尾），取 90 s 留足一个数量级余量。
#   - 窗口模式（无 `--fullscreen`）本闸恒不启用，行为与 harness6 逐字节一致。
H7_MEASURE_MAX_NAV_TO_W0_S = 90.0
# ★★ [H7-①] 全屏矩形等待跳过开关容器（模块级；main 装载）。
#   ★ 仅当 `--fullscreen` 且未显式 `--h7-keep-rect-wait` 时为 True。
_H7_STATE = {"fs_rect_wait_skipped": False,
             "nav_end_t": None,
             "nav_to_measure_s": None,
             "late_start": None}
# <<< H7-END const'''

# ---------------------------------------------------------------------------
# 补丁 B：nav 收口打时间戳（供 H7-② 计算 nav→measure 间隔）
# ---------------------------------------------------------------------------
ANCHOR_B = ('        if _nav_failed_at:\n'
            '            rec.add("NAV", "failed_at", _nav_failed_at, "script:nav")\n')

PATCH_B = ANCHOR_B + '''        # >>> H7-BEGIN nav-end（★ 只打戳，不改任何既有语义）
        # ★★ [H7-②] nav 收口时刻（monotonic；与 `budget.stage_t0` 同钟源）。
        #   ★ 仅作 measure 起始硬约束的分子，不参与导航判定。
        _H7_STATE["nav_end_t"] = time.monotonic()
        rec.add("NAV", "h7_nav_end_t", round(_H7_STATE["nav_end_t"], 6),
                "time.monotonic",
                note="★ H7-②：nav 收口时刻（monotonic 原始值；供 "
                     "nav_to_measure_s 计算，不参与导航判定）")
        # <<< H7-END nav-end
'''

# ---------------------------------------------------------------------------
# 补丁 C：全屏 ⇒ 短路采帧前矩形等待（母本 while 行一字不改）
# ---------------------------------------------------------------------------
ANCHOR_C = ('        _cap_rect = rect_of(hwnd)\n'
            '        _cap_wait = 0\n')

PATCH_C = ANCHOR_C + '''        # >>> H7-BEGIN rect-wait-skip（★ 缺省 off ⇒ `deadline` 原值，逐字节同锚）
        # ★★ [H7-①] 全屏下「窗口矩形 == 800×600」**永不成立**（实测恒
        #   `[0,0,2560,1440]`）⇒ 下面母本 while 必然跑满 `deadline`（实测
        #   251/251/244/253 轮 × 0.5 s ≈ 122–127 s）。
        #   ★ 但全屏抓帧走 `capture_frame_desktop`，其 `w, h = FRAME_W, FRAME_H`
        #     **按构造**固定 800×600，与窗口矩形无关 ⇒ 该等待是纯死等。
        #   ★ 修法=把 `deadline` 局部重绑为 0.0，令母本 while 谓词立即短路；
        #     **母本 while 行一字未改**（零删除行纪律）。
        #   ★ 安全性：`deadline` 在本点之后**零引用**（生成器自检 #8 实测）；
        #     它此前唯一用途是「等主窗出现」（`:7553`）与 window 稳定循环
        #     （`:7607` 起改用 `_stab_deadline`），两者都已走完。
        if _H7_STATE["fs_rect_wait_skipped"]:
            _h7_deadline_orig = deadline
            deadline = 0.0
            rec.add("FRAME", "h7_fs_rect_wait_skipped", {
                "skipped": True,
                "deadline_orig_was_set": bool(_h7_deadline_orig),
                "rect_at_skip": list(_cap_rect),
                "capture_fixed_wh": [FRAME_W, FRAME_H],
                "reason": "全屏窗口矩形恒为整屏 ≠ 800×600；全屏抓帧按构造固定 "
                          "800×600 ⇒ 原等待是纯死等（实测 122–127 s）",
            }, "argv:--fullscreen",
                note="★ H7-①：全屏矩形等待已短路（母本 while 行未改；"
                     "`deadline` 局部重绑 0.0，此后零引用）")
        # <<< H7-END rect-wait-skip
'''

# ---------------------------------------------------------------------------
# 补丁 D：measure 入口硬约束（nav→w0 过晚 ⇒ 不采三窗，fail-closed）
# ---------------------------------------------------------------------------
ANCHOR_D = ('    try:\n'
            '        # ---- settle 4 s（窗 0 前置，§3.3；同时供窗前在局闸取数）----\n')

PATCH_D = '''    try:
        # >>> H7-BEGIN late-start-gate（★ 缺省：短路未生效 ⇒ 整块零行为）
        # ★★ [H7-②] measure 起始硬约束：窗口必须落在**开局**，不得落在战斗后。
        #   ★★ 触发条件 = **短路生效** ∧ nav 收口戳存在 ∧ 间隔 > 阈值。
        #      短路未生效（`--h7-keep-rect-wait` 对照臂 / 窗口模式）⇒ 本闸**不判定**：
        #      实测 10-21 四趟的 nav→w0 本来就是 126–131 s 且 verdict=ok，
        #      对它们施加本闸会把成功趟一律误判（见常量注释的标定）。
        #   ★ 分子 = nav 收口 → 本函数入口（settle 之前）的 monotonic 间隔。
        #   ★ 超限 ⇒ 记 `late_start=true` 并**直接返回**（不 settle、不采窗），
        #     写 w0 JSON 记 `verdict="late_start"` —— 宁可如实报「窗太晚」，
        #     也不产出一个看起来正常的战斗后 fps。
        #   ★ 不新增退出码；不改进图闸语义（§5.2）。
        _h7_nav_end = _H7_STATE.get("nav_end_t")
        if _h7_nav_end is not None and _H7_STATE["fs_rect_wait_skipped"]:
            _h7_n2m = time.monotonic() - _h7_nav_end
            _H7_STATE["nav_to_measure_s"] = round(_h7_n2m, 3)
            _h7_late = bool(_h7_n2m > H7_MEASURE_MAX_NAV_TO_W0_S)
            _H7_STATE["late_start"] = _h7_late
            rec.add("MEASURE", "h7_nav_to_measure", {
                "nav_to_measure_s": round(_h7_n2m, 3),
                "limit_s": H7_MEASURE_MAX_NAV_TO_W0_S,
                "late_start": _h7_late,
                "fs_rect_wait_skipped": _H7_STATE["fs_rect_wait_skipped"],
            }, "script:_measure_run",
                note="★ H7-②：nav 收口 → measure 入口间隔（硬约束 "
                     f"{H7_MEASURE_MAX_NAV_TO_W0_S} s）；超限 ⇒ verdict=late_start"
                     "、不采三窗")
            if _h7_late:
                _h7_payload = _measure_error_payload(
                    0, TRIP_ID, map_sha256,
                    f"late_start: nav→measure {_h7_n2m:.3f}s > "
                    f"{H7_MEASURE_MAX_NAV_TO_W0_S}s（窗口已不在开局）")
                # ★★ 落盘 verdict 必须与 rec 行一致：`_measure_error_payload`
                #   默认写 "error"（那是「整窗不可测」的语义）。本支是**主动拒采**，
                #   语义不同 ⇒ 必须改写，否则 JSON 与 rec 两处互相矛盾。
                _h7_payload["verdict"] = "late_start"
                _h7_payload["h7"] = {"nav_to_measure_s": round(_h7_n2m, 3),
                                     "limit_s": H7_MEASURE_MAX_NAV_TO_W0_S,
                                     "late_start": True}
                _h7_p = _measure_write_json(out_dir, 0, _h7_payload)
                rec.add("MEASURE", "window_0_stats", _h7_payload["stats"],
                        "script:_measure_stats",
                        note=f"★ H7-②：verdict=late_start；JSON={_h7_p.name}")
                rec.add("MEASURE", "verdict", "late_start", "script:_measure_run",
                        note="★ H7-②：窗口偏晚（nav→measure 超限）⇒ 不采三窗；"
                             "不硬停趟、不加退出码（§5.2/§5.4）")
                return
        # <<< H7-END late-start-gate
        # ---- settle 4 s（窗 0 前置，§3.3；同时供窗前在局闸取数）----
'''

# ---------------------------------------------------------------------------
# 补丁 E：--fullscreen 装载 H7 状态（含 opt-out 开关）
# ---------------------------------------------------------------------------
ANCHOR_E = ('    if getattr(args, "fullscreen", False):\n'
            '        _QC151FS["on"] = True\n')

PATCH_E = ANCHOR_E + '''        # >>> H7-BEGIN main-arm（★ 仅 --fullscreen 且未 opt-out 才置位）
        # ★★ [H7-①] 全屏 ⇒ 短路采帧前矩形等待（见补丁 C）。
        #   ★ `--h7-keep-rect-wait` 显式给出 ⇒ 保持 harness6 原语义
        #     （供 A/B 对照：同一趟可复现 122–127 s 死等）。
        if not getattr(args, "h7_keep_rect_wait", False):
            _H7_STATE["fs_rect_wait_skipped"] = True
            rec.add("META", "h7_fs_rect_wait_skipped", True,
                    "argv:--fullscreen",
                    note="★ H7-①：全屏矩形等待短路已武装（对照开关 "
                         "--h7-keep-rect-wait 可恢复 harness6 原语义）")
        else:
            rec.add("META", "h7_fs_rect_wait_skipped", False,
                    "argv:--h7-keep-rect-wait",
                    note="★ H7-①：显式保持 harness6 原语义（矩形等待不短路）")
        # <<< H7-END main-arm
'''

# ---------------------------------------------------------------------------
# 补丁 F：argparse 增加 opt-out 开关（缺省 False ⇒ 零行为差）
# ---------------------------------------------------------------------------
ANCHOR_F = ('    ap.add_argument("--fullscreen", action="store_true", default=False,\n'
            '                    help="★ QC151FS：全屏模式适配（缺省 off=行为与改前逐字节"\n'
            '                         "一致；T55 显式给 on）")\n')

PATCH_F = ANCHOR_F + '''    # >>> H7-BEGIN argparse（缺省 False ⇒ 行为与 harness6 逐字节一致）
    ap.add_argument("--h7-keep-rect-wait", action="store_true", default=False,
                    help="★ H7-①：显式保持 harness6 原语义（全屏矩形等待不短路；"
                         "供 A/B 对照复现 122–127 s 死等；缺省 off=短路）")
    # <<< H7-END argparse
'''

PATCHES = [
    ("A 常量", ANCHOR_A, PATCH_A),
    ("B nav 收口打戳", ANCHOR_B, PATCH_B),
    ("C 全屏矩形等待短路", ANCHOR_C, PATCH_C),
    ("D measure 起始硬约束", ANCHOR_D, PATCH_D),
    ("E --fullscreen 装载", ANCHOR_E, PATCH_E),
    ("F argparse opt-out", ANCHOR_F, PATCH_F),
]

MARKERS = ("H7_MEASURE_MAX_NAV_TO_W0_S", "h7_fs_rect_wait_skipped",
           "h7_nav_to_measure", "h7_keep_rect_wait", "late_start")


def lf16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def crlf16(b):
    return hashlib.sha256(
        b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()[:16]


def main():
    check_only = "--check" in sys.argv
    raw = SRC.read_bytes()
    print(f"src   : {SRC}")
    print(f"bytes : {len(raw)}")
    print(f"LF16  : {lf16(raw)}  (expect {SRC_SHA16})")
    if lf16(raw) != SRC_SHA16:
        print("ABORT: source hash mismatch (harness6 must stay unchanged)")
        return 1

    text = raw.decode("utf-8")
    assert "\r\n" not in text, "source must be LF-only"

    # ---- 自检 1：每处锚点唯一（fail-closed） ----
    ok = True
    for name, anchor, _patch in PATCHES:
        cnt = text.count(anchor)
        print(f"anchor {name}: {cnt} occurrence(s)")
        if cnt != 1:
            print(f"ABORT: anchor not unique: {name}")
            ok = False
    if not ok:
        return 1

    # ---- 应用补丁（逐个替换，每个只替换 1 次） ----
    patched = text
    for name, anchor, patch in PATCHES:
        if patched.count(anchor) != 1:
            print(f"ABORT: anchor vanished after earlier patch: {name}")
            return 1
        patched = patched.replace(anchor, patch, 1)
    patched_bytes = patched.encode("utf-8")
    print(f"patched bytes: {len(patched_bytes)} "
          f"(+{len(patched_bytes) - len(raw)})")

    # ---- 自检 2：语法（ast） ----
    try:
        ast.parse(patched)
    except SyntaxError as e:
        print(f"ABORT: syntax error: {e}")
        return 1
    print("ast.parse : OK")

    # ---- 自检 3：新增符号各出现 >=1 次，且定义唯一 ----
    for sym in ("H7_MEASURE_MAX_NAV_TO_W0_S = 90.0", "_H7_STATE = {",
                '"fs_rect_wait_skipped"', '"nav_end_t"',
                '"nav_to_measure_s"', '"late_start"'):
        n = patched.count(sym)
        print(f"  {sym!r}: {n}")
        if n < 1:
            print(f"ABORT: symbol missing: {sym!r}")
            return 1

    # ---- 自检 4：标记计数 > 0 ----
    for m in MARKERS:
        n = patched.count(m)
        print(f"  marker {m!r}: {n}")
        if n < 1:
            print("ABORT: marker missing: %r" % m)
            return 1

    # ---- 自检 5：不新增退出码 ----
    def exit_codes(s):
        out = set()
        for ln in s.split("\n"):
            if ln.startswith("EXIT_") and " = " in ln:
                out.add(ln.split(" = ")[0].strip())
        return out
    added_codes = exit_codes(patched) - exit_codes(text)
    print(f"  exit codes added: {sorted(added_codes) or 'none'}")
    if added_codes:
        print("ABORT: H7 must NOT add new exit codes")
        return 1

    # ---- 自检 6：母本关键约束仍在（全屏/measure 内核零改动） ----
    for m in ("def _measure_run(", "def capture_frame_desktop(",
              "def _measure_stats(", "def _measure_write_json(",
              "MEASURE_WINDOW_S = 25.0", "MEASURE_HZ = 500",
              "MEASURE_WINDOWS = 3", "MEASURE_GATE_FPS15_MIN = 3.0",
              "w, h = FRAME_W, FRAME_H",
              "if _QC151FS[\"on\"]:\n        return capture_frame_desktop(hwnd, out_png)"):
        if m not in patched:
            print(f"ABORT: mother constraint missing: {m[:60]!r}")
            return 1
    print("mother constraints: all present")

    # ---- 自检 7：母本 while 行一字未改 ----
    WHILE_LINE = ('        while (_cap_rect[2] - _cap_rect[0], '
                  '_cap_rect[3] - _cap_rect[1]) != (FRAME_W, FRAME_H) '
                  'and time.monotonic() < deadline:\n')
    if patched.count(WHILE_LINE) != 1:
        print("ABORT: mother while line changed/duplicated")
        return 1
    print("mother rect-wait while line: byte-identical")

    # ---- 自检 8：`deadline` 在母本 while 之后（可执行行）零引用 ----
    #   ★ 只看**可执行行**（去掉注释/字符串外的说明文字）；补丁块自身的注释里
    #     提到 `deadline` 不算引用，否则检查会被自己的说明文字误导。
    _lines = patched.split("\n")
    _i_while = next(i for i, ln in enumerate(_lines) if ln == WHILE_LINE.rstrip("\n"))
    _dl_code = []
    for _ln in _lines[_i_while + 1:]:
        _s = _ln.strip()
        if not _s or _s.startswith("#"):
            continue
        if "deadline" in _s:
            _dl_code.append(_s)
    print(f"  'deadline' executable refs after mother while: {len(_dl_code)}")
    if _dl_code:
        print("ABORT: deadline is referenced after the while; "
              "short-circuit is unsafe")
        for _s in _dl_code[:5]:
            print(f"    ref: {_s[:100]}")
        return 1

    # ---- 自检 9：零删除行（母本行集合 ⊆ 副本行集合） ----
    c_old = Counter(text.split("\n"))
    c_new = Counter(patched.split("\n"))
    gone = [ln for ln in c_old if c_new[ln] < c_old[ln]]
    print(f"lines: {len(text.split(chr(10)))} -> {len(patched.split(chr(10)))}")
    print(f"removed lines: {len(gone)}")
    if gone:
        print("ABORT: patch must be append-only (no mother line may disappear)")
        for g in gone[:5]:
            print(f"  gone: {g[:80]!r}")
        return 1

    # ---- 自检 10：顺序约束（nav 打戳在 frame 段之前；短路在 while 之前） ----
    p_navend = patched.find('rec.add("NAV", "h7_nav_end_t"')
    p_skip = patched.find('if _H7_STATE["fs_rect_wait_skipped"]:')
    p_while = patched.find(WHILE_LINE)
    p_measure = patched.find("def _measure_run(")
    print(f"  navend@{p_navend} skip@{p_skip} while@{p_while} "
          f"measure@{p_measure}")
    if not (0 < p_navend < p_skip < p_while):
        print("ABORT: nav-end stamp and rect-wait skip must precede the while")
        return 1
    print("ordering: OK")

    # ---- 自检 11：py_compile（★ 编到临时目录，绝不在仓库留 .pyc） ----
    tmpdir = tempfile.mkdtemp(prefix="h7_pyc_")
    try:
        tmp_src = Path(tmpdir) / "h7_compile_check.py"
        tmp_src.write_bytes(patched_bytes)
        py_compile.compile(str(tmp_src),
                           cfile=str(Path(tmpdir) / "h7_compile_check.pyc"),
                           doraise=True)
        print("py_compile : OK")
    except py_compile.PyCompileError as e:
        print(f"ABORT: py_compile failed: {e}")
        return 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    stray = sorted(p.name for p in DST_DIR.glob("*.pyc")) if DST_DIR.is_dir() else []
    print(f"  stray .pyc in dst dir: {stray or 'none'}")
    if stray:
        print("ABORT: .pyc must not be left behind")
        return 1

    # ---- 自检 12：被修的两处函数体（除插入块外）未变 ----
    def body_of(src, name):
        m = re.search(r"^def %s\(.*?(?=^def |^# =====)" % re.escape(name),
                      src, re.S | re.M)
        return m.group(0) if m else ""

    for fn in ("_measure_stats", "_measure_write_json", "_measure_error_payload",
               "capture_frame_desktop", "_fs_arrival_poll"):
        if body_of(text, fn) != body_of(patched, fn):
            print(f"ABORT: {fn} body changed")
            return 1
    print("kernel funcs: byte-identical to mother")

    # ---- 自检 13：缺省（无 --fullscreen）时短路容器保持 False ----
    if '_H7_STATE = {"fs_rect_wait_skipped": False,' not in patched:
        print("ABORT: default state must be off")
        return 1
    if 'if _H7_STATE["fs_rect_wait_skipped"]:' not in patched:
        print("ABORT: short-circuit guard missing")
        return 1
    print("default: rect-wait short-circuit off (windowed path untouched)")

    # ---- 自检 14：late_start 落盘 verdict 与 rec 行一致 ----
    if '_h7_payload["verdict"] = "late_start"' not in patched:
        print("ABORT: late_start payload verdict not rewritten "
              "(JSON would say 'error' while rec says 'late_start')")
        return 1
    _REC_LATE = 'rec.add("MEASURE", "verdict", "late_start", "script:_measure_run"'
    if _REC_LATE not in patched:
        print("ABORT: rec-side late_start verdict missing")
        return 1
    print("late_start: payload verdict == rec verdict")

    # ---- 落盘 ----
    if check_only:
        print("CHECK ONLY: no files written")
        return 0

    DST_DIR.mkdir(parents=True, exist_ok=True)
    DST.write_bytes(patched_bytes)

    import difflib
    a = text.split("\n")
    b = patched.split("\n")
    dl = list(difflib.unified_diff(a, b, fromfile="harness6.py",
                                   tofile="harness7.py", lineterm="", n=3))
    DIFF.write_text("\n".join(dl) + "\n", encoding="utf-8")

    plus = sum(1 for x in dl if x.startswith("+") and not x.startswith("+++"))
    minus = sum(1 for x in dl if x.startswith("-") and not x.startswith("---"))
    print(f"\nwritten: {DST}")
    print(f"  bytes {len(patched_bytes)}  LF16 {lf16(patched_bytes)}  "
          f"CRLF16 {crlf16(patched_bytes)}")
    print(f"  diff   {DIFF.name}  +{plus} / -{minus}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
