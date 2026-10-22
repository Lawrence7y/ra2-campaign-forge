#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H6 补丁生成器：从 harness5.py 派生 harness6.py（合入四项能力）。

母本零改动：只**读** harness5 的源码文本，只**写**新副本到
`lead/goal1_harness6_20261022/`。★ 绝不 import / exec 母本
（427 KB 脚本，import 会执行顶层代码）。

范式照抄 `lead/goal1_a8_fix_20261022/_gen_harness5.py`
----------------------------------------------------
1. `ast` 解析 / 语法编译自检；
2. **唯一锚点字符串**精确替换（每处断言 `src.count(anchor) == 1`，否则 fail-closed）；
3. 生成器自检：锚点命中数、语法可编译、**零删除行**（母本行集合 ⊆ 副本行集合）；
4. 写副本 + 落 `.diff`；`--check` 只自检不写。

四项能力
--------
① WER 检测          → `wer_scan_new_reports()`；★★ `Sig[]` **按 `.Name=` 读值**，
                      ★ 不许按索引读（本项目 §340 实证：索引布局有三种）。
② 载体隔离计数      → `carrier_isolation_count()`；`CreateToolhelp32Snapshot(
                      TH32CS_SNAPMODULE)` 枚举模块；归属判定**只用 `Path.relative_to`**
                      （★ 不用 `str.startswith`：`C:\\a` 与 `C:\\ab` 会误配）；
                      ★ 枚举失败 ⇒ 记 `V_FAIL`，**绝不当「零越界」**。
③ near-limit WARN   → 载体**目录** 127..130 字符 ⇒ `WARN`（不改变退出码）；
                      ★ `>= 131` 的既有硬停逻辑一字不动。
④ `--close-mode`    → 缺省 `terminate`（与 harness5 逐字节等价，除新增记录字段）；
                      `close` ⇒ 先 `PostMessageW(hwnd, WM_CLOSE, 0, 0)`，
                      等 ≤20 s；超时才回落 `TerminateProcess`，并记
                      `close_fallback_terminate=true`（★ 不让回落看起来像正常退出）。
                      ★ `terminate_owned_process` 既有语义**不变**（仍在 close 之后
                      负责「确认终止」）。

用法
----
    python _gen_harness6.py            # 生成并自检
    python _gen_harness6.py --check    # 只自检不写
"""
import ast
import hashlib
import py_compile
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "lead/goal1_a8_fix_20261022/qc151_trip.harness5.py"
DST_DIR = ROOT / "lead/goal1_harness6_20261022"
DST = DST_DIR / "qc151_trip.harness6.py"
DIFF = DST_DIR / "h6.diff"

SRC_SHA16 = "f1e5bc7b0ff30c9c"   # harness5 的 LF sha16（★ 动手前必须实测等于此值）

# ---------------------------------------------------------------------------
# 补丁 A：near-limit 常量（紧跟既有 130 / 131 常量之后）
# ---------------------------------------------------------------------------
ANCHOR_A = (
    'CARRIER_PATH_MAX_CHARS = 130          # ★ 门禁值（硬失败线，★ 作用在载体**目录**）\n'
    'CARRIER_PATH_KNOWN_BAD_CHARS = 131    # ★ 历史实证故障阈值（★ 仅对照记录，不作门禁）'
)

PATCH_A = ANCHOR_A + '''
# ★★ [H6-③] near-limit 告警下界：载体**目录**长度 >= 127 且 <= 130 ⇒ WARN。
#   ★ 只告警、**不改变退出码**；★ `> 130` 的硬停逻辑（`carrier_pathlen_gate`）
#     一字不动（★ 本常量不参与任何硬停判据）。
#   ★ 127 取自本项目历史成功趟的最短实证余量（`l1a_20261020`=129、
#     `t55k_20261020`=130 均成功；129 距门禁仅 1 字符 ⇒ 提前一段可见）。
CARRIER_PATH_NEAR_WARN_CHARS = 127'''

# ---------------------------------------------------------------------------
# 补丁 B：carrier_pathlen_gate 内加 near-limit WARN（★ 硬停逻辑原样保留）
# ---------------------------------------------------------------------------
ANCHOR_B = '''    bad = carrier_pathlen_violations(dirs)
    if not bad:
        return'''

PATCH_B = '''    # >>> H6-③-BEGIN（near-limit WARN；★ 不改变退出码、不动硬停判据）
    # ★★ 口径同 `carrier_pathlen_violations`：★ 判的是**载体目录**字符数，
    #   ★ 不是件的完整路径。★ `>= 131` 仍走下面的硬停（本块只覆盖 127..130）。
    # ★★ 先物化 `dirs`：若调用方传的是生成器，本块遍历一次后
    #   `carrier_pathlen_violations(dirs)` 会拿到空序列 ⇒ **静默绕过硬停**。
    #   ★ 物化为 list（内容不变）⇒ 硬停判据看到与母本相同的输入。
    dirs = list(dirs)
    _near = [(str(_p), len(str(_p))) for _p in dirs
             if CARRIER_PATH_NEAR_WARN_CHARS <= len(str(_p)) <= CARRIER_PATH_MAX_CHARS]
    if _near:
        if rec is not None:
            rec.add("CARRIER", "pathlen_near_limit", {
                "max_chars": CARRIER_PATH_MAX_CHARS,
                "near_warn_chars": CARRIER_PATH_NEAR_WARN_CHARS,
                "scope": "carrier_dir_only",
                "dirs": [{"dir": _p, "chars": _n} for _p, _n in _near],
            }, f"script:{where}",
                    note="★ [H6] 载体目录接近门禁（127..130）⇒ WARN，"
                         "★ 不改变退出码（★ 硬停仍在 >130）")
        for _p, _n in _near:
            print(f"[WARN] carrier dir len={_n} near limit 130")
    # <<< H6-③-END
''' + ANCHOR_B

# ---------------------------------------------------------------------------
# 补丁 C：新增 §9-H6 段（WER / 隔离计数 / close 模式 全部新函数）
# ---------------------------------------------------------------------------
ANCHOR_C = '''# ===========================================================================
# §10 · ⑤ 导航链与采帧
# ===========================================================================
def find_main_window(pid: int) -> tuple:'''

PATCH_C = '''# ===========================================================================
# §9-H6 · [harness6 补丁副本] WER 检测 / 载体隔离计数 / close 模式
# ===========================================================================
# ★★ 本段全部是 **harness6 新增**；母本 harness5 零改动。
# ★ 段内函数只做**只读**观测：读 WER 目录、读进程模块表、向主窗投一条消息。
#   ★ 不删不改 WER 目录、不改注册表、不注入、不写其它进程内存。
#   ★ 全部观测**不改变退出码**（close 模式的回落由既有 `terminate_owned_process`
#     照旧确认终止并计入既有收尾失败语义）。
_H6_STATE = {"t0_wall": None, "close_mode": "terminate"}

H6_CLOSE_WAIT_S = 20.0          # ★ close 模式等待自发退出上限（秒）
H6_ISO_DETAIL_MAX = 20          # ★ 越界模块明细上限（条）
H6_WER_APP_NAMES = ("gamemd.exe", "ra2loader.exe")


# ---------------------------------------------------------------------------
# [H6-①] WER 检测
# ---------------------------------------------------------------------------
def _h6_wer_roots() -> list:
    r"""★ 只读：返回 `[(标签, 目录)]`（%LOCALAPPDATA%\\Microsoft\\Windows\\WER\\…）。

    ★ `LOCALAPPDATA` 缺失 ⇒ 返回空表（★ 调用方必须记「未测」，不得读成零崩溃）。
    """
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        return []
    wer = Path(base) / "Microsoft" / "Windows" / "WER"
    return [("ReportArchive", wer / "ReportArchive"),
            ("ReportQueue", wer / "ReportQueue")]


def _h6_wer_read_text(p: Path) -> str:
    """★ WER 的 `Report.wer` 常见 UTF-16LE（带 BOM），也有 ASCII/UTF-8 变体。"""
    raw = p.read_bytes()
    if raw[:2] == b"\\xff\\xfe":
        return raw.decode("utf-16-le", "replace")
    if raw[:2] == b"\\xfe\\xff":
        return raw.decode("utf-16-be", "replace")
    return raw.decode("utf-8", "replace")


def _h6_wer_parse(text: str) -> dict:
    """★★ 解析 `Report.wer` ⇒ `{"top": {...}, "sig_pairs": [...], "sig": {...}}`。

    ★★ `Sig[]` 必须**按 `.Name=` 读值**，★ **不许按索引读**：
      WER 的 `Sig[]` 是「名称/值」有序对列表，**索引只是排列位置，语义由名称
      承载**。本项目 25 份 AppCrash 实证三种布局并存（异常代码/异常偏移在
      `Sig[7]/Sig[6]` 17 份、`Sig[6]/Sig[7]` 6 份、两项都无 2 份）
      ⇒ 按索引硬编码必然读错。
      出处：`lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` §340
      （原文「WER 的 `Sig[]` 是"名称/值"有序对列表，索引只是排列位置，
      语义由名称承载」）。
    ★ `sig_pairs` 保留出现顺序**仅作留痕**；取值一律走 `sig`（名称 → 值）。
    """
    top: dict = {}
    pairs: list = []
    sig: dict = {}
    cur = None
    for line in text.splitlines():
        s = line.strip()
        if not s or "=" not in s:
            continue
        key, _, val = s.partition("=")
        key, val = key.strip(), val.strip()
        if key.startswith("Sig[") and key.endswith(".Name"):
            cur = val
            continue
        if key.startswith("Sig[") and key.endswith(".Value"):
            pairs.append((cur, val))
            if cur is not None and cur not in sig:
                sig[cur] = val
            cur = None
            continue
        if key.startswith("Sig[") or key.startswith("DynamicSig["):
            continue
        if key not in top:
            top[key] = val
    return {"top": top, "sig_pairs": pairs, "sig": sig}


def _h6_sig_first(sig: dict, names) -> str:
    """★ 按**名称**取第一个非空值（★ 中英双语名称表；★ 不按索引）。"""
    for _n in names:
        if _n in sig and sig[_n]:
            return sig[_n]
    return None


def wer_scan_new_reports(rec: Recorder, since_ts, carrier_dir=None) -> dict:
    """★★ [H6-①] 枚举本趟时段内**新增**的 WER `Report.wer`（★ 只读）。

    ★ 为什么需要：harness5 收尾只靠 `except.txt`（已知不可靠）+ 退出码，
      无法独立区分「正常退出」与「挂了/崩了」⇒ WER 报告是独立旁证。
    ★★ 解析 `EventType`（如 `AppHangB1` / `APPCRASH`）、`FriendlyEventName`、
      `AppName`、`AppPath`、以及 `Sig[]` 有序对（**按名取值**）。
    ★ `AppPath` 落在**载体目录外** ⇒ 记一条 `wer_out_of_carrier` 告警：
      这是已知的 `InstallPath` 注册表旁路（同一二进制按绝对路径加载），
      **不是污染**，但隔离边界上必须在报告里可见。
    ★★ 只读：不删、不改、不重命名 WER 目录下任何件。
    ★★ `NO_NEW_REPORT` **不等于**证明本趟没崩（报告可能未生成/被策略抑制）。
    """
    out = {"since_ts": since_ts, "roots": [], "report_count": 0,
           "reports": [], "out_of_carrier": [], "error": None,
           "verdict": "UNMEASURED"}
    rec.add("WER", "wer_scan_since_ts", since_ts, "script:wer_scan_new_reports",
            note="★ 本趟起点（epoch 秒）；只收 mtime >= 本值的新增 Report.wer")
    if since_ts is None:
        # ★★ 起点未知 ⇒ 「本趟时段」无定义 ⇒ **不扫全库**（★ 全库枚举会把
        #   历史崩溃当成本趟崩溃，正是要避免的误读）⇒ 如实记未测。
        out["error"] = "since_ts 缺失 ⇒ 本趟时段无定义"
        rec.add("WER", "wer_scan_error", out["error"],
                "script:wer_scan_new_reports",
                note="★★ 未测（★ 不得读成「无崩溃」，也不得扫全库冒充本趟）")
        rec.add("WER", "wer_verdict", "UNMEASURED",
                "script:wer_scan_new_reports")
        return out
    roots = _h6_wer_roots()
    if not roots:
        rec.add("WER", "wer_scan_error",
                "LOCALAPPDATA 缺失 ⇒ 无法定位 WER 目录",
                "script:wer_scan_new_reports",
                note="★★ 未测（★ 不得读成「无崩溃」）")
        rec.add("WER", "wer_verdict", "UNMEASURED",
                "script:wer_scan_new_reports")
        return out
    cands = []
    for _label, _d in roots:
        _exists = False
        try:
            _exists = _d.is_dir()
        except Exception:
            _exists = False
        out["roots"].append({"name": _label, "dir": str(_d),
                             "exists": _exists})
        if not _exists:
            continue
        try:
            for _p in _d.rglob("Report.wer"):
                try:
                    _mt = _p.stat().st_mtime
                except Exception:
                    continue
                if since_ts is None or _mt >= float(since_ts):
                    cands.append((_label, _p, _mt))
        except Exception as _e:
            out["error"] = f"{_label}: {_e!r}"
            rec.add("WER", f"wer_scan_error:{_label}", repr(_e),
                    "script:wer_scan_new_reports",
                    note="★ 该目录枚举失败 ⇒ 只影响该目录，如实记（★ 不当作零）")
    rec.add("WER", "wer_scan_roots", out["roots"],
            "script:wer_scan_new_reports",
            note="★ 目录存在性；★ 不存在 ≠ 无崩溃（只是本机无该队列）")
    for _label, _p, _mt in sorted(cands, key=lambda t: t[2]):
        try:
            _parsed = _h6_wer_parse(_h6_wer_read_text(_p))
        except Exception as _e:
            rec.add("WER", "wer_parse_error",
                    {"path": str(_p), "error": repr(_e)},
                    "script:wer_scan_new_reports",
                    note="★ 单份解析失败 ⇒ 只影响该份，如实记")
            continue
        _top, _sig = _parsed["top"], _parsed["sig"]
        _app_name = (_top.get("AppName")
                     or _h6_sig_first(_sig, ("AppName", "应用程序名", "应用程序名称")))
        _app_path = _top.get("AppPath") or _h6_sig_first(_sig, ("AppPath",))
        _in_carrier = None
        if _app_path and carrier_dir is not None:
            _in_carrier = _a8_path_under_carrier(_app_path, carrier_dir)
        _base_name = ""
        if _app_path:
            try:
                _base_name = Path(_app_path).name.lower()
            except Exception:
                _base_name = ""
        _item = {
            "root": _label, "path": str(_p),
            "mtime": datetime.fromtimestamp(_mt).isoformat(timespec="seconds"),
            "event_type": _top.get("EventType"),
            "friendly_event_name": _top.get("FriendlyEventName"),
            "app_name": _app_name,
            "app_path": _app_path,
            "app_path_in_carrier": _in_carrier,
            "app_relevant": bool((_app_name or "").lower() in H6_WER_APP_NAMES
                                 or _base_name in H6_WER_APP_NAMES),
            "sig_by_name": _sig,
            "sig_pairs": [[_n, _v] for _n, _v in _parsed["sig_pairs"]],
        }
        out["reports"].append(_item)
        if _in_carrier is False:
            out["out_of_carrier"].append({"path": str(_p),
                                          "app_path": _app_path})
    out["report_count"] = len(out["reports"])
    out["verdict"] = "NEW_REPORTS" if out["reports"] else "NO_NEW_REPORT"
    rec.add("WER", "wer_report_count", out["report_count"],
            "script:wer_scan_new_reports")
    rec.add("WER", "wer_reports", out["reports"],
            "script:wer_scan_new_reports",
            note="★★ 本趟时段内新增的 WER 报告：EventType / FriendlyEventName / "
                 "AppName / AppPath / Sig（★ 按 .Name= 取值，不按索引）")
    rec.add("WER", "wer_out_of_carrier", out["out_of_carrier"],
            "script:wer_scan_new_reports",
            note="★ AppPath 落在载体目录外（★ 已知 InstallPath 旁路；"
                 "不是污染，但隔离边界上必须可见）")
    rec.add("WER", "wer_verdict", out["verdict"],
            "script:wer_scan_new_reports",
            note="★★ NO_NEW_REPORT **不等于**证明本趟没崩：WER 未记录也可能是"
                 "报告未生成/被系统策略抑制 ⇒ 只作独立旁证")
    return out


# ---------------------------------------------------------------------------
# [H6-②] 载体隔离计数
# ---------------------------------------------------------------------------
def _h6_enum_module_paths(pid: int) -> tuple:
    """★ 只读：`CreateToolhelp32Snapshot(TH32CS_SNAPMODULE)` 枚举模块全路径。

    ★ 返回 `(paths, err)`；★ 任一失败 ⇒ `paths is None` 且 `err` 非空
      ⇒ 调用方**必须**判 `V_FAIL`（★ 不得把「枚举失败」当成「零越界」）。
    ★ 与母本 `s4_enum_modules`（psapi 路径）并列存在：本函数按本卡要求走
      Toolhelp 快照，两者都是**只读**枚举，互不替代。
    ★ 每处 ctypes 调用都声明 `argtypes/restype`（★ 不声明会在 64 位截断 HANDLE）。
    """
    class ME32W(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("th32ModuleID", wt.DWORD),
                    ("th32ProcessID", wt.DWORD), ("GlblcntUsage", wt.DWORD),
                    ("ProccntUsage", wt.DWORD),
                    ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
                    ("modBaseSize", wt.DWORD), ("hModule", wt.HMODULE),
                    ("szModule", wt.WCHAR * 256),
                    ("szExePath", wt.WCHAR * 260)]

    TH32CS_SNAPMODULE = 0x00000008
    TH32CS_SNAPMODULE32 = 0x00000010
    ERROR_NO_MORE_FILES = 18
    k32 = ctypes.windll.kernel32
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    k32.Module32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(ME32W)]
    k32.Module32FirstW.restype = wt.BOOL
    k32.Module32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(ME32W)]
    k32.Module32NextW.restype = wt.BOOL
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL

    snap = None
    err = None
    # ★ Windows 已知怪癖：对刚启动/正在加载的进程，SNAPMODULE 可能短暂
    #   返回 ERROR_PARTIAL_COPY ⇒ 短重试 3 次；仍失败 ⇒ 如实返回 err。
    for _try in range(3):
        snap = k32.CreateToolhelp32Snapshot(
            TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
        if snap and snap != INVALID_HANDLE_VALUE:
            break
        err = (f"CreateToolhelp32Snapshot(pid={pid}) 失败: "
               f"err={ctypes.GetLastError()}")
        snap = None
        time.sleep(0.15)
    if not snap:
        return None, err
    try:
        ent = ME32W()
        ent.dwSize = ctypes.sizeof(ME32W)
        if not k32.Module32FirstW(snap, ctypes.byref(ent)):
            return None, (f"Module32FirstW(pid={pid}) 失败: "
                          f"err={ctypes.GetLastError()}")
        paths = []
        while True:
            paths.append(ent.szExePath)
            if not k32.Module32NextW(snap, ctypes.byref(ent)):
                _e = ctypes.GetLastError()
                if _e == ERROR_NO_MORE_FILES:
                    break
                return None, (f"Module32NextW(pid={pid}) 失败: err={_e} "
                              f"⇒ 模块表**不完整** ⇒ 不能判定")
        if not paths:
            return None, f"Module32FirstW(pid={pid}): 模块表为空 ⇒ 不可判定"
        return paths, ""
    finally:
        k32.CloseHandle(snap)


def _h6_path_zone(p, carrier_root, system_root) -> str:
    r"""★ 路径归属判定 ⇒ `"inside"` / `"system"` / `"outside"`。

    ★★ **必须用 `Path.relative_to`**，★ 不许用 `str.startswith`：
      载体 `...\\abc` 与 `...\\abcd` 前者是后者前缀，`startswith` 会误判
      （本项目已实证教训）。
    ★ 相对路径 / 解析失败 ⇒ 归 `"outside"`（★ 宁可多报，不可漏报）。
    """
    try:
        _pp = Path(p)
        if not _pp.is_absolute():
            return "outside"
        _rp = _pp.resolve()
    except Exception:
        return "outside"
    for _zone, _root in (("inside", carrier_root), ("system", system_root)):
        if _root is None:
            continue
        try:
            _rp.relative_to(_root)
            return _zone
        except ValueError:
            continue
    return "outside"


def carrier_isolation_count(rec: Recorder, carrier_dir, pid) -> dict:
    r"""★★ [H6-②] 载体隔离计数：把目标进程已加载模块分三类各计数。

    ★ 背景：`HKLM\\SOFTWARE\\WOW6432Node\\Westwood\\Yuri's Revenge\\InstallPath`
      会让游戏按**绝对路径**加载载体外的 DLL（`Blowfish.dll` 等）。同一二进制
      sha 相同 ⇒ 问题在**隔离边界**，不在代码来源。
    ★★ 三类：载体内 / 系统目录（`%SystemRoot%`）/ 越界（其余）。
    ★★ 归属判定**只用 `Path.relative_to`**（见 `_h6_path_zone`）。
    ★★ **枚举失败 ⇒ `iso_verdict="V_FAIL"`**，★ 绝不当「零越界」：
      正控 = 先枚举**本进程自己**，查不到自己的 exe 名 ⇒ 枚举器坏了。
      （★ 与母本 `_a8_enum_probe` 同思路：用必然存在的自己作正控。）
    ★ 只读；★ 不改变退出码。
    """
    out = {"pid": pid, "self_probe_ok": None, "enum_ok": False,
           "n_modules": None, "inside": None, "system": None, "outside": None,
           "outside_detail": None, "system_root": None,
           "error": None, "verdict": "V_FAIL", "measured": False}
    rec.add("ISOLATION", "iso_pid", pid, "script:carrier_isolation_count")

    # ---- 正控：先枚举本进程自己（★ 必然在模块表里） ----
    self_pid = os.getpid()
    self_name = ""
    try:
        self_name = Path(sys.executable).name
    except Exception:
        self_name = "python.exe"
    self_paths, self_err = _h6_enum_module_paths(self_pid)
    self_ok = False
    if self_paths:
        for _sp in self_paths:
            try:
                if Path(_sp).name.lower() == self_name.lower():
                    self_ok = True
                    break
            except Exception:
                continue
    out["self_probe_ok"] = self_ok
    rec.add("ISOLATION", "iso_self_probe_ok", self_ok,
            "script:carrier_isolation_count",
            note="★★ 正控：枚举本进程自己（★ 查不到 ⇒ 枚举器失效 ⇒ V_FAIL）")
    rec.add("ISOLATION", "iso_self_probe", {
        "pid": self_pid, "exe": self_name,
        "n_modules": (len(self_paths) if self_paths is not None else None),
        "error": self_err or None,
    }, "script:carrier_isolation_count",
        note="★ 正控明细（★ 只在自检失败时有诊断价值）")
    if not self_ok:
        out["error"] = ("正控失败：枚举本进程自己未命中 %r（err=%r）"
                        % (self_name, self_err))
        rec.add("ISOLATION", "iso_error", out["error"],
                "script:carrier_isolation_count")
        rec.add("ISOLATION", "iso_verdict", "V_FAIL",
                "script:carrier_isolation_count",
                note="★★ 枚举器失效 ⇒ 隔离计数**不可判定**（★ 不当零越界）")
        return out

    if pid is None:
        out["error"] = "pid 缺失 ⇒ 无目标可枚举"
        rec.add("ISOLATION", "iso_error", out["error"],
                "script:carrier_isolation_count")
        rec.add("ISOLATION", "iso_verdict", "V_FAIL",
                "script:carrier_isolation_count",
                note="★ 无 pid ⇒ V_FAIL（★ 不当零越界）")
        return out

    paths, err = _h6_enum_module_paths(int(pid))
    if paths is None:
        out["error"] = err or "模块枚举失败"
        rec.add("ISOLATION", "iso_error", out["error"],
                "script:carrier_isolation_count")
        rec.add("ISOLATION", "iso_verdict", "V_FAIL",
                "script:carrier_isolation_count",
                note="★★ 模块枚举失败 ⇒ V_FAIL（★ 绝不当「零越界」）")
        return out

    # ---- 三类归属（★ 只用 Path.relative_to） ----
    carrier_root = None
    if carrier_dir is not None:
        try:
            carrier_root = Path(carrier_dir).resolve()
        except Exception:
            carrier_root = None
    system_root = None
    _sys_env = os.environ.get("SystemRoot") or os.environ.get("windir")
    if _sys_env:
        try:
            system_root = Path(_sys_env).resolve()
        except Exception:
            system_root = None
    out["system_root"] = str(system_root) if system_root is not None else None
    if carrier_root is None:
        out["error"] = "载体目录不可解析 ⇒ 三类归属无法判定"
        rec.add("ISOLATION", "iso_error", out["error"],
                "script:carrier_isolation_count")
        rec.add("ISOLATION", "iso_verdict", "V_FAIL",
                "script:carrier_isolation_count",
                note="★ 载体目录不可解析 ⇒ V_FAIL（★ 不当零越界）")
        return out

    inside, system, outside = [], [], []
    for _mp in paths:
        _zone = _h6_path_zone(_mp, carrier_root, system_root)
        if _zone == "inside":
            inside.append(_mp)
        elif _zone == "system":
            system.append(_mp)
        else:
            outside.append(_mp)
    out.update({"enum_ok": True, "measured": True, "n_modules": len(paths),
                "inside": len(inside), "system": len(system),
                "outside": len(outside),
                "outside_detail": outside[:H6_ISO_DETAIL_MAX],
                "verdict": "PASS"})
    rec.add("ISOLATION", "iso_enum_ok", True, "script:carrier_isolation_count")
    rec.add("ISOLATION", "iso_carrier_dir", str(carrier_root),
            "script:carrier_isolation_count",
            note="★ 载体目录 = 隔离基准（★ 判定用 Path.relative_to）")
    rec.add("ISOLATION", "iso_system_root", out["system_root"],
            "script:carrier_isolation_count",
            note="★ 系统目录基准（%SystemRoot%）")
    rec.add("ISOLATION", "iso_n_modules", len(paths),
            "script:carrier_isolation_count")
    rec.add("ISOLATION", "iso_inside", len(inside),
            "script:carrier_isolation_count",
            note="★ 载体内模块数")
    rec.add("ISOLATION", "iso_system", len(system),
            "script:carrier_isolation_count",
            note="★ 系统目录模块数（%SystemRoot% 之下）")
    rec.add("ISOLATION", "iso_outside", len(outside),
            "script:carrier_isolation_count",
            note="★★ 越界模块数（★ 非载体非系统；★ 已知 InstallPath 旁路来源）")
    rec.add("ISOLATION", "iso_outside_detail", outside[:H6_ISO_DETAIL_MAX],
            "script:carrier_isolation_count",
            note=f"★ 越界模块明细（最多 {H6_ISO_DETAIL_MAX} 条；★ 总数见 iso_outside）")
    rec.add("ISOLATION", "iso_verdict", "PASS",
            "script:carrier_isolation_count",
            note="★ 枚举与归属判定均完成（★ 越界数 >0 不等于污染，见载体隔离说明）")
    return out


# ---------------------------------------------------------------------------
# [H6-④] close 模式：先 WM_CLOSE，等 ≤20 s，超时才回落 TerminateProcess
# ---------------------------------------------------------------------------
def h6_close_attempt(rec: Recorder, pid: int,
                     timeout_s: float = H6_CLOSE_WAIT_S) -> dict:
    """★★ [H6-④] 向主窗投 `WM_CLOSE` 并等待进程**自行退出**（★ 只投一条消息）。

    ★★ 为什么：现行收尾用 `TerminateProcess`，**结构性绕过** RC-4 的触发条件
      （RC-4 是退出期崩溃）⇒ 需要一个「像玩家关窗」的收尾来测量它。
    ★★ 步骤：
      1. 取该 pid 的主窗 `hwnd`，并复核 `hwnd` 的属主 pid（★ 不投错窗）；
      2. 若进程已退出 ⇒ 记 `exited_s=0.0`，不投消息；
      3. `PostMessageW(hwnd, WM_CLOSE, 0, 0)`；
      4. 用**自己的** `SYNCHRONIZE` 句柄等 ≤ `timeout_s`（★ 不碰 Popen 状态，
         把「确认终止」留给 `terminate_owned_process`）；
      5. 超时 ⇒ `fallback_terminate=True`（★ 由调用方照旧走 `TerminateProcess`）。
    ★★ 返回 `{"posted", "exited_s", "fallback_terminate", ...}`；
      ★ `fallback_terminate=True` 是**关键字段**：★ 回落不得被读成正常退出。
    ★ 只读观测 + 一条窗口消息；★ 不改注册表、不注入。
    """
    WM_CLOSE = 0x0010
    SYNCHRONIZE = 0x00100000
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    out = {"posted": False, "exited_s": None, "fallback_terminate": False,
           "hwnd": None, "hwnd_owned_by_pid": None, "hwnd_source": None,
           "error": None}
    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32

    # ---- 步 1：取主窗 + 复核属主 ----
    hwnd, _info = find_main_window(int(pid))
    out["hwnd"] = hwnd
    out["hwnd_source"] = "find_main_window"
    if not hwnd:
        out["fallback_terminate"] = True
        out["error"] = "no_main_window"
        rec.add("CLOSE", "close_hwnd", None, "script:find_main_window",
                note="★★ 无主窗 ⇒ 无法投 WM_CLOSE ⇒ 回落 TerminateProcess")
        return out
    u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
    u32.GetWindowThreadProcessId.restype = wt.DWORD
    _wpid = wt.DWORD(0)
    u32.GetWindowThreadProcessId(hwnd, ctypes.byref(_wpid))
    out["hwnd_owned_by_pid"] = (_wpid.value == int(pid))
    rec.add("CLOSE", "close_hwnd", hwnd, "script:find_main_window",
            note="★ 主窗句柄 + 属主 pid 复核（★ 不向非目标进程的窗投消息）")
    rec.add("CLOSE", "close_hwnd_owned_by_pid", out["hwnd_owned_by_pid"],
            "script:GetWindowThreadProcessId")
    if not out["hwnd_owned_by_pid"]:
        out["fallback_terminate"] = True
        out["error"] = "hwnd_pid_mismatch"
        return out

    # ---- 步 2/4：自己的等待句柄（★ 不改 Popen 状态） ----
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
    k32.WaitForSingleObject.restype = wt.DWORD
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    h = k32.OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION,
                        False, int(pid))
    if not h:
        out["fallback_terminate"] = True
        out["error"] = f"OpenProcess 失败: err={ctypes.GetLastError()}"
        rec.add("CLOSE", "close_error", out["error"], "script:h6_close_attempt")
        return out
    try:
        if k32.WaitForSingleObject(h, 0) == 0:
            out["exited_s"] = 0.0
            out["error"] = "already_exited_before_close"
            rec.add("CLOSE", "close_already_exited", True,
                    "script:h6_close_attempt",
                    note="★ 投消息前进程已退出 ⇒ 本次 close 未投（★ 不是回落）")
            return out

        # ---- 步 3：投 WM_CLOSE ----
        u32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        u32.PostMessageW.restype = wt.BOOL
        _ok = bool(u32.PostMessageW(hwnd, WM_CLOSE, 0, 0))
        out["posted"] = _ok
        rec.add("CLOSE", "close_wm_close_posted", _ok,
                "script:PostMessageW:WM_CLOSE")
        if not _ok:
            out["fallback_terminate"] = True
            out["error"] = f"PostMessageW 失败: err={ctypes.GetLastError()}"
            rec.add("CLOSE", "close_error", out["error"],
                    "script:h6_close_attempt")
            return out

        # ---- 步 4：等待自行退出（≤ timeout_s） ----
        _t0 = time.monotonic()
        _rc = k32.WaitForSingleObject(h, int(float(timeout_s) * 1000))
        if _rc == 0:
            out["exited_s"] = round(time.monotonic() - _t0, 3)
            out["fallback_terminate"] = False
        else:
            out["exited_s"] = None
            out["fallback_terminate"] = True
            out["error"] = (f"WM_CLOSE 后 {timeout_s}s 未退出 "
                            f"(WaitForSingleObject rc={_rc})")
        return out
    finally:
        k32.CloseHandle(h)


# ===========================================================================
# §10 · ⑤ 导航链与采帧
# ===========================================================================
def find_main_window(pid: int) -> tuple:'''

# ---------------------------------------------------------------------------
# 补丁 D：--close-mode CLI（★ 默认 terminate）
# ---------------------------------------------------------------------------
ANCHOR_D = '''    ap.add_argument("--sg-toggle-y", type=int, default=None,
                    help="★ QC151SG：「短游戏」开关点击 y（800×600 游戏系；"
                         "缺省 None=零点击；语义同 --sg-toggle-x）")
    # <<< QC151SG-END argparse
    return ap.parse_args(argv)'''

PATCH_D = '''    ap.add_argument("--sg-toggle-y", type=int, default=None,
                    help="★ QC151SG：「短游戏」开关点击 y（800×600 游戏系；"
                         "缺省 None=零点击；语义同 --sg-toggle-x）")
    # <<< QC151SG-END argparse
    # >>> H6-CLOSE-BEGIN argparse（--close-mode 单开关；★ 缺省 terminate
    #   ⇒ 控制流与 harness5 逐字节等价，除新增 CLOSE 记录字段）
    # ★★ H6-④：收尾方式。
    #   ★ terminate（缺省）= 现行 `TerminateProcess` 路径，控制流零变化；
    #     ★ 注意：它**结构性绕过** RC-4（退出期崩溃）的触发条件 ⇒ 测不到 RC-4。
    #   ★ close = 终止前先向主窗 `PostMessageW(hwnd, WM_CLOSE, 0, 0)`，
    #     等 ≤20 s 看进程是否自行退出；★ 超时才回落 `TerminateProcess`，
    #     并记 `close_fallback_terminate=true`（★ 回落不得读成正常退出）。
    #   ★ 两种模式都仍由 `terminate_owned_process` 负责「确认终止」。
    ap.add_argument("--close-mode", choices=("terminate", "close"),
                    default="terminate",
                    help="★ H6-④：收尾方式（缺省 terminate=与改前一致；"
                         "close=先 WM_CLOSE 等 ≤20s，超时回落 TerminateProcess "
                         "并记 close_fallback_terminate=true）")
    # <<< H6-CLOSE-END argparse
    return ap.parse_args(argv)'''

# ---------------------------------------------------------------------------
# 补丁 E：main 起始处记趟起点 wall clock + close 模式（供 finally 用）
# ---------------------------------------------------------------------------
ANCHOR_E = '''    rec.add("META", "started", now_iso(), "script:main")'''

PATCH_E = ANCHOR_E + '''
    # >>> H6-STATE-BEGIN（★ 只写模块级容器 + 一行记录；不改变控制流）
    # ★★ H6-①：WER 扫描的「本趟时段」起点（★ wall clock，与文件 mtime 同钟）；
    #   ★ 早于任何启动动作 ⇒ 覆盖整个趟窗口。
    # ★★ H6-④：close 模式（★ 缺省 terminate ⇒ 下面 finally 里该块零动作）。
    _H6_STATE["t0_wall"] = time.time()
    _H6_STATE["close_mode"] = str(getattr(args, "close_mode", "terminate"))
    # <<< H6-STATE-END'''

# ---------------------------------------------------------------------------
# 补丁 F：finally 内、终止**之前**做隔离计数（要活进程）
# ---------------------------------------------------------------------------
ANCHOR_F = '''        term_ct = LAUNCH_TOKEN.ct if (LAUNCH_TOKEN is not None
                                      and LAUNCH_TOKEN.ct is not None) else launch_ct

        # ==== 第 3 项：★ 终止失败 ⇒ 进**可外达容器**，★ 并计入最终码 ===='''

PATCH_F = '''        term_ct = LAUNCH_TOKEN.ct if (LAUNCH_TOKEN is not None
                                      and LAUNCH_TOKEN.ct is not None) else launch_ct

        # >>> H6-ISOLATION-BEGIN（★ 必须在**终止之前**：要枚举活进程模块表）
        # ★★ H6-②：载体隔离计数。★ 枚举失败 ⇒ V_FAIL（★ 绝不当「零越界」）。
        #   ★ 本调用**不改变退出码**（只落盘观测值）。
        if term_pid is not None:
            try:
                _h6_iso_carrier = (Path(TRIP_CARRIER["dir"])
                                   if TRIP_CARRIER["dir"] else carrier_dir)
                carrier_isolation_count(rec, _h6_iso_carrier, term_pid)
            except Exception as _h6ie:
                rec.add("ISOLATION", "iso_error", repr(_h6ie),
                        "script:main:finally")
                rec.add("ISOLATION", "iso_verdict", "V_FAIL",
                        "script:main:finally",
                        note="★★ 隔离计数抛异常 ⇒ 不可判定（★ 不当零越界）")
        else:
            rec.add("ISOLATION", "iso_verdict", "N/A", "script:main:finally",
                    note="★ 未启动（无 pid）⇒ 未测（★ 不当作零越界；"
                         "★ 本趟无目标进程可枚举）")
        # <<< H6-ISOLATION-END

        # ==== 第 3 项：★ 终止失败 ⇒ 进**可外达容器**，★ 并计入最终码 ===='''

# ---------------------------------------------------------------------------
# 补丁 G：finally 内、调 terminate_owned_process **之前**插 close 尝试
# ---------------------------------------------------------------------------
ANCHOR_G = '''        term_ok = None            # ★ None = 不适用（未启动）；True/False = 已判定
        if term_proc is not None and term_pid is not None:
            try:
                term_ok = terminate_owned_process(rec, term_proc, term_pid, term_ct)'''

PATCH_G = '''        term_ok = None            # ★ None = 不适用（未启动）；True/False = 已判定
        if term_proc is not None and term_pid is not None:
            # >>> H6-CLOSE-BEGIN（★ 在 terminate_owned_process **之前**；
            #   ★ 不改它的既有语义：它仍负责「确认终止」）
            # ★★ H6-④：缺省 terminate ⇒ 本块零动作（控制流与 harness5 一致）。
            #   ★ close ⇒ 先 WM_CLOSE 等 ≤20 s；超时回落 TerminateProcess，
            #     并记 close_fallback_terminate=true（★ 回落 ≠ 正常退出）。
            _h6_close = {"mode": _H6_STATE.get("close_mode", "terminate"),
                         "posted": None, "exited_s": None,
                         "fallback_terminate": None, "error": None}
            if _h6_close["mode"] == "close":
                try:
                    _h6_close.update(h6_close_attempt(
                        rec, term_pid, H6_CLOSE_WAIT_S))
                except Exception as _h6ce:
                    _h6_close["posted"] = False
                    _h6_close["fallback_terminate"] = True
                    _h6_close["error"] = repr(_h6ce)
                    rec.add("CLOSE", "close_error", repr(_h6ce),
                            "script:main:finally",
                            note="★ close 尝试抛异常 ⇒ 如实记为回落 terminate")
            rec.add("CLOSE", "close_mode", _h6_close["mode"],
                    "argv:--close-mode")
            rec.add("CLOSE", "close_posted", _h6_close["posted"],
                    "script:h6_close_attempt",
                    note="★ null = 未执行（terminate 模式）")
            rec.add("CLOSE", "close_exited_s", _h6_close["exited_s"],
                    "script:h6_close_attempt",
                    note="★ 自发退出耗时（秒）；null = 未等/超时未退出")
            rec.add("CLOSE", "close_fallback_terminate",
                    _h6_close["fallback_terminate"], "script:main:finally",
                    note="★★ true = WM_CLOSE 超时后回落 TerminateProcess"
                         "（★ 不得被读成正常退出）；null = terminate 模式未尝试")
            # <<< H6-CLOSE-END
            try:
                term_ok = terminate_owned_process(rec, term_proc, term_pid, term_ct)'''

# ---------------------------------------------------------------------------
# 补丁 H：finally 内、A8 清扫之后做 WER 扫描（报告在进程退出后落盘）
# ---------------------------------------------------------------------------
ANCHOR_H = '''                    note="★ 非授权趟（直启 gamemd，无 loader 派生进程）")'''

PATCH_H = '''                    note="★ 非授权趟（直启 gamemd，无 loader 派生进程）")

        # >>> H6-WER-BEGIN（★ 在终止之后：WER 报告是进程退出/崩溃后才落盘）
        # ★★ H6-①：本趟时段内新增 WER 报告的独立旁证（★ 只读，不改退出码）。
        #   ★ 异常 ⇒ 只记「未测」，★ 绝不当成「零崩溃」。
        try:
            _h6_wer_carrier = (Path(TRIP_CARRIER["dir"])
                               if TRIP_CARRIER["dir"] else carrier_dir)
            wer_scan_new_reports(rec, _H6_STATE.get("t0_wall"), _h6_wer_carrier)
        except Exception as _h6we:
            rec.add("WER", "wer_scan_error", repr(_h6we),
                    "script:main:finally",
                    note="★★ WER 扫描异常 ⇒ 本趟 WER 判据不可用"
                         "（★ 不当作零崩溃）")
            rec.add("WER", "wer_verdict", "UNMEASURED", "script:main:finally")
        # <<< H6-WER-END'''

# 锚点 → 补丁（顺序无关：每个锚点在母本里唯一且互不重叠）
PATCHES = [
    ("A 常量 CARRIER_PATH_NEAR_WARN_CHARS", ANCHOR_A, PATCH_A),
    ("B near-limit WARN（carrier_pathlen_gate）", ANCHOR_B, PATCH_B),
    ("C §9-H6 段（WER / 隔离计数 / close 全函数）", ANCHOR_C, PATCH_C),
    ("D --close-mode CLI", ANCHOR_D, PATCH_D),
    ("E main 起点：t0_wall + close_mode", ANCHOR_E, PATCH_E),
    ("F finally：终止前隔离计数", ANCHOR_F, PATCH_F),
    ("G finally：终止前 close 尝试", ANCHOR_G, PATCH_G),
    ("H finally：A8 后 WER 扫描", ANCHOR_H, PATCH_H),
]

# 四项标记（★ 报告里要 grep -c 实测计数）
MARKERS = ("wer_scan_new_reports", "carrier_isolation_count",
           "near limit 130", "close-mode")


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
        print("ABORT: source hash mismatch (harness5 must stay unchanged)")
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
        tree = ast.parse(patched)
    except SyntaxError as e:
        print(f"ABORT: syntax error: {e}")
        return 1
    print("ast.parse : OK")

    # ---- 自检 3：新增符号各出现 >=1 次，且定义唯一 ----
    for sym in ("def wer_scan_new_reports", "def carrier_isolation_count",
                "def h6_close_attempt", "def _h6_enum_module_paths",
                "def _h6_path_zone", "def _h6_wer_parse",
                "_H6_STATE = {", "CARRIER_PATH_NEAR_WARN_CHARS = 127"):
        n = patched.count(sym)
        print(f"  {sym!r}: {n}")
        if n < 1:
            print(f"ABORT: symbol missing: {sym!r}")
            return 1
    for sym in ("def wer_scan_new_reports(", "def carrier_isolation_count(",
                "def h6_close_attempt("):
        if patched.count(sym) != 1:
            print(f"ABORT: definition not unique: {sym!r} "
                  f"({patched.count(sym)})")
            return 1

    # ---- 自检 4：四条标记计数 > 0 ----
    for m in MARKERS:
        n = patched.count(m)
        print(f"  marker {m!r}: {n}")
        if n < 1:
            print(f"ABORT: marker missing: {m!r}")
            return 1

    # ---- 自检 5：不新增退出码（★ 四项都不许加新码） ----
    def exit_codes(s):
        out = set()
        for ln in s.split("\n"):
            if ln.startswith("EXIT_") and " = " in ln:
                out.add(ln.split(" = ")[0].strip())
        return out
    added_codes = exit_codes(patched) - exit_codes(text)
    print(f"  exit codes added: {sorted(added_codes) or 'none'}")
    if added_codes:
        print("ABORT: H6 must NOT add new exit codes")
        return 1

    # ---- 自检 6：母本关键约束仍在 ----
    for m in ("def carrier_pathlen_gate(", "def terminate_owned_process(",
              "def a8_sweep_carrier_processes(", "def _a8_enum_probe(",
              "CARRIER_PATH_MAX_CHARS = 130",
              "CARRIER_PATH_KNOWN_BAD_CHARS = 131",
              '    bad = carrier_pathlen_violations(dirs)\n    if not bad:\n        return',
              "raise RuntimeError("):
        if m not in patched:
            print(f"ABORT: mother constraint missing: {m[:50]!r}")
            return 1
    print("mother constraints: all present")

    # ---- 自检 7：硬停逻辑未被改写（>130 仍 raise） ----
    if patched.count("if len(s) > CARRIER_PATH_MAX_CHARS:") != 1:
        print("ABORT: hard-stop predicate changed")
        return 1
    if "if CARRIER_PATH_NEAR_WARN_CHARS <= len(str(_p)) <= CARRIER_PATH_MAX_CHARS" not in patched:
        print("ABORT: near-limit predicate missing")
        return 1
    print("hard-stop (>=131) untouched; near-limit (127..130) added")

    # ---- 自检 8：零删除行（母本行集合 ⊆ 副本行集合） ----
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

    # ---- 自检 9：顺序约束 ----
    p_iso = patched.find(">>> H6-ISOLATION-BEGIN")
    p_close = patched.find(">>> H6-CLOSE-BEGIN（★ 在 terminate_owned_process")
    p_term = patched.find("term_ok = terminate_owned_process(rec, term_proc")
    p_wer = patched.find(">>> H6-WER-BEGIN")
    p_item1 = patched.find("# ==== 第 1 项：★ 删除链用**本趟实际载体**")
    print(f"  iso@{p_iso} close@{p_close} term@{p_term} wer@{p_wer} "
          f"item1@{p_item1}")
    if not (0 < p_iso < p_close < p_term):
        print("ABORT: isolation/close must precede terminate_owned_process")
        return 1
    if not (p_term < p_wer < p_item1):
        print("ABORT: WER scan must run after termination and before delete chain")
        return 1
    print("ordering: OK")

    # ---- 自检 10：py_compile（★ 编到临时目录，绝不在仓库留 .pyc） ----
    tmpdir = tempfile.mkdtemp(prefix="h6_pyc_")
    try:
        tmp_src = Path(tmpdir) / "h6_compile_check.py"
        tmp_src.write_bytes(patched_bytes)
        py_compile.compile(str(tmp_src),
                           cfile=str(Path(tmpdir) / "h6_compile_check.pyc"),
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

    # ---- 自检 11：close 模式不改 terminate 语义（函数体未被触碰） ----
    import re
    def body_of(src, name):
        m = re.search(r"^def %s\(.*?(?=^def |^# =====)" % re.escape(name),
                      src, re.S | re.M)
        return m.group(0) if m else ""
    if body_of(text, "terminate_owned_process") != body_of(
            patched, "terminate_owned_process"):
        print("ABORT: terminate_owned_process body changed")
        return 1
    print("terminate_owned_process: byte-identical to mother")

    # ---- 自检 12：默认 terminate 时不执行 close 分支 ----
    if 'if _h6_close["mode"] == "close":' not in patched:
        print("ABORT: close branch guard missing")
        return 1
    if 'default="terminate"' not in patched:
        print("ABORT: --close-mode default must be terminate")
        return 1
    print('close-mode default: "terminate" (guard present)')

    if check_only:
        print("CHECK ONLY: no files written")
        return 0

    # ---- 写副本 + diff ----
    DST_DIR.mkdir(parents=True, exist_ok=True)
    DST.write_bytes(patched_bytes)

    import difflib
    diff = difflib.unified_diff(
        text.split("\n"), patched.split("\n"),
        fromfile="lead/goal1_a8_fix_20261022/qc151_trip.harness5.py",
        tofile="lead/goal1_harness6_20261022/qc151_trip.harness6.py",
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
