"""采样剖析器：从外部测出原版游戏把时间花在哪。

为什么用采样而不是插桩：`M0 基线测量` 的目的是回答"blit 占每 tick 多少时间"，
而这**不需要改游戏代码**——按固定频率抓主线程的 EIP，统计各地址区间的样本占比，
就得到时间的分布（统计意义下等价，且零侵入、可随时中止）。

一个有利条件：`gamemd.exe` **没有 `.reloc` 段**，即不可重定位，永远加载在
`0x400000`。所以 `symbols.json` 里的静态地址**就是运行时地址**，样本可以直接归因；
反过来，如果样本大量落在预期之外的地址，那就说明符号表错了——自带交叉验证。

归因分三层：
1. 模块归属（gamemd.exe / ddraw.dll / gdi32.dll …）—— 能看出"呈现与系统调用"占多少
2. 已知虚函数入口（来自 RTTI 恢复的 954 个 vtable）—— 前后 256 字节内归为该函数
3. 粗粒度区段（两簇软件 blit 的地址区间）—— 即使函数边界不准也能给出 blit 占比

局限（写清楚，避免过度解读）：
- 这是**时间占比**，不是"每 tick 的毫秒分解"；要拿 tick 边界必须插桩（改代码）。
- 单位数量没有被插桩，所以"多单位"是靠场景描述的（几个人、打了多久），不是精确计数。
"""

from __future__ import annotations

import bisect
import ctypes
import json
import os
import struct
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass, field
from pathlib import Path

# --- Win32 常量 -------------------------------------------------------------
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPTHREAD = 0x00000004
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
CONTEXT_i386 = 0x00010000
CONTEXT_CONTROL = CONTEXT_i386 | 0x00000001

INVALID_HANDLE = (None, -1, 0xFFFFFFFFFFFFFFFF)

# 已知的软件 blit 地址簇（来自 ra2re rtti 的 m1_blit_targets.txt）
BLIT_CLUSTERS = (
    ("blit:Plain/Trans 簇", 0x007BC600, 0x007BCA00),
    ("blit:Xlat/Darken/Lucent/ZRead 簇", 0x00492300, 0x00493600),
)
# MSVC 纯虚占位
PURECALL_VA = 0x004C9150
# 已知函数入口之后多少字节内算"属于该函数"（保守，避免跨函数误归因）
SYMBOL_WINDOW = 256


class FLOATING_SAVE_AREA(ctypes.Structure):
    _fields_ = [("ControlWord", wintypes.DWORD), ("StatusWord", wintypes.DWORD),
                ("TagWord", wintypes.DWORD), ("ErrorOffset", wintypes.DWORD),
                ("ErrorSelector", wintypes.DWORD), ("DataOffset", wintypes.DWORD),
                ("DataSelector", wintypes.DWORD),
                ("RegisterArea", ctypes.c_byte * 80), ("Cr0NpxState", wintypes.DWORD)]


class CONTEXT(ctypes.Structure):
    """i386 CONTEXT（只填到 Eip 之后的通用寄存器；ExtendedRegisters 保留占位）。"""

    _fields_ = [("ContextFlags", wintypes.DWORD),
                ("Dr0", wintypes.DWORD), ("Dr1", wintypes.DWORD),
                ("Dr2", wintypes.DWORD), ("Dr3", wintypes.DWORD),
                ("Dr6", wintypes.DWORD), ("Dr7", wintypes.DWORD),
                ("FloatSave", FLOATING_SAVE_AREA),
                ("SegGs", wintypes.DWORD), ("SegFs", wintypes.DWORD),
                ("SegEs", wintypes.DWORD), ("SegDs", wintypes.DWORD),
                ("Edi", wintypes.DWORD), ("Esi", wintypes.DWORD),
                ("Ebx", wintypes.DWORD), ("Edx", wintypes.DWORD),
                ("Ecx", wintypes.DWORD), ("Eax", wintypes.DWORD),
                ("Ebp", wintypes.DWORD), ("Eip", wintypes.DWORD),
                ("SegCs", wintypes.DWORD), ("EFlags", wintypes.DWORD),
                ("Esp", wintypes.DWORD), ("SegSs", wintypes.DWORD),
                ("ExtendedRegisters", ctypes.c_byte * 512)]


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_char * 260)]


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                ("th32ThreadID", wintypes.DWORD), ("th32OwnerProcessID", wintypes.DWORD),
                ("tpBasePri", ctypes.c_long), ("tpDeltaPri", ctypes.c_long),
                ("dwFlags", wintypes.DWORD)]


class MODULEENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD), ("GlblcntUsage", wintypes.DWORD),
                ("ProccntUsage", wintypes.DWORD),
                ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
                ("modBaseSize", wintypes.DWORD), ("hModule", wintypes.HMODULE),
                ("szModule", ctypes.c_char * 256), ("szExePath", ctypes.c_char * 260)]


def _k32():
    if not sys.platform.startswith("win"):
        raise RuntimeError("采样剖析仅支持 Windows")
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    if not getattr(k, "_ra2re_typed", False):
        k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        k.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
        k.Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
        k.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
        k.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
        k.Module32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
        k.Module32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
        k.OpenThread.restype = wintypes.HANDLE
        k.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.SuspendThread.argtypes = [wintypes.HANDLE]
        k.ResumeThread.argtypes = [wintypes.HANDLE]
        k.GetThreadContext.argtypes = [wintypes.HANDLE, ctypes.POINTER(CONTEXT)]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        # 目标进程是 32 位（gamemd.exe）而本解释器是 64 位时必须走 Wow64 版本，
        # 否则 GetThreadContext 拿不到 32 位上下文。WOW64_CONTEXT 与 i386 CONTEXT 同布局。
        if hasattr(k, "Wow64GetThreadContext"):
            k.Wow64GetThreadContext.argtypes = [wintypes.HANDLE, ctypes.POINTER(CONTEXT)]
        k._ra2re_typed = True
    return k


# --- 进程/线程/模块枚举 ------------------------------------------------------

def find_pid(exe_name: str) -> int | None:
    """按可执行文件名找 pid。注意要 SNAPPROCESS——SNAPTHREAD 的句柄喂给
    Process32First 是取不到进程表的。"""
    k = _k32()
    snap = k.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap in INVALID_HANDLE:
        return None
    try:
        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
        if not k.Process32First(snap, ctypes.byref(pe)):
            return None
        while True:
            if pe.szExeFile.decode("latin-1").lower() == exe_name.lower():
                return int(pe.th32ProcessID)
            if not k.Process32Next(snap, ctypes.byref(pe)):
                return None
    finally:
        k.CloseHandle(snap)


def list_threads(pid: int) -> list:
    k = _k32()
    snap = k.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snap in INVALID_HANDLE:
        return []
    out = []
    try:
        te = THREADENTRY32()
        te.dwSize = ctypes.sizeof(THREADENTRY32)
        if k.Thread32First(snap, ctypes.byref(te)):
            while True:
                if te.th32OwnerProcessID == pid:
                    out.append(int(te.th32ThreadID))
                if not k.Thread32Next(snap, ctypes.byref(te)):
                    break
    finally:
        k.CloseHandle(snap)
    return out


def list_modules(pid: int) -> list:
    k = _k32()
    snap = k.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    if snap in INVALID_HANDLE:
        return []
    out = []
    seen = set()
    try:
        me = MODULEENTRY32()
        me.dwSize = ctypes.sizeof(MODULEENTRY32)
        if k.Module32First(snap, ctypes.byref(me)):
            while True:
                base = ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value or 0
                key = (me.szModule.decode("latin-1").lower(), int(base))
                # TH32CS_SNAPMODULE32 在 64 位进程里会同时返回 32 位与反射条目，
                # 同名同基址的会重复出现，去重以免影响占比统计
                if key not in seen:
                    seen.add(key)
                    out.append((me.szModule.decode("latin-1"),
                                int(base), int(me.modBaseSize)))
                if not k.Module32Next(snap, ctypes.byref(me)):
                    break
    finally:
        k.CloseHandle(snap)
    return out


def read_eip(tid: int) -> int | None:
    """挂起线程 → 读 EIP → 恢复。读不到返回 None。"""
    k = _k32()
    h = k.OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION,
                     False, tid)
    if not h:
        return None
    try:
        if k.SuspendThread(h) == 0xFFFFFFFF:
            return None
        try:
            ctx = CONTEXT()
            ctx.ContextFlags = CONTEXT_CONTROL
            ok = False
            if hasattr(k, "Wow64GetThreadContext"):
                ok = bool(k.Wow64GetThreadContext(h, ctypes.byref(ctx)))
            if not ok:
                ok = bool(k.GetThreadContext(h, ctypes.byref(ctx)))
            return int(ctx.Eip) if ok and ctx.Eip else None
        finally:
            k.ResumeThread(h)
    finally:
        k.CloseHandle(h)


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def process_cpu_seconds(pid: int) -> tuple | None:
    """返回进程累计 (user, kernel) CPU 秒数。用来算"占满几个核"。

    这是判断"是不是 CPU 瓶颈"的关键旁证：采样只给分布，不给总量。
    """
    k = _k32()
    h = k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        class FILETIME(ctypes.Structure):
            _fields_ = [("dwLowDateTime", wintypes.DWORD),
                        ("dwHighDateTime", wintypes.DWORD)]

        def to_s(ft):
            return ((ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 1e7

        creation, exit_, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
        if not k.GetProcessTimes(h, ctypes.byref(creation), ctypes.byref(exit_),
                                 ctypes.byref(kernel), ctypes.byref(user)):
            return None
        return to_s(user), to_s(kernel)
    finally:
        k.CloseHandle(h)


# --- 符号归因 ---------------------------------------------------------------

@dataclass
class SymbolTable:
    entries: list = field(default_factory=list)     # (va, label) 按 va 升序
    vaddrs: list = field(default_factory=list)      # 平行数组，供 bisect

    @classmethod
    def load(cls, symbols_json, *, blit_file=None) -> "SymbolTable":
        sym = cls()
        seen = {}
        p = Path(symbols_json)
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
            for name, c in data.get("classes", {}).items():
                for i, va in enumerate(c.get("vfuncs") or []):
                    va = int(va, 16)
                    seen.setdefault(va, f"{name}::v{i}")
        # 用 m1_blit_targets.txt 给 blit 函数打上更可读的名字
        if blit_file and Path(blit_file).is_file():
            for line in Path(blit_file).read_text(encoding="utf-8").splitlines():
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) < 5:
                    continue
                tmpl = parts[0]
                for i, va in enumerate(parts[4].split()):
                    seen[int(va, 16)] = f"{tmpl}::v{i}"
        for va, label in sorted(seen.items()):
            if va == PURECALL_VA:
                label = "_purecall(占位)"
            sym.entries.append((va, label))
            sym.vaddrs.append(va)
        return sym

    def attribute(self, eip: int) -> tuple:
        """返回 (类别, 标签)。类别 ∈ {sym, blit, text_unknown, symbol_unknown}"""
        i = bisect.bisect_right(self.vaddrs, eip) - 1
        if i >= 0:
            va, label = self.entries[i]
            if eip - va <= SYMBOL_WINDOW:
                kind = "blit" if "?$Blit" in label else "sym"
                return kind, label
        for name, lo, hi in BLIT_CLUSTERS:
            if lo <= eip <= hi:
                return "blit", name + "（未落在已知入口窗口内）"
        return "text_unknown", ""


# 这些模块里的样本基本等于"线程在等待"（消息循环 / 信号量 / 睡眠），不是真在干活。
# 游戏空闲时它们会占绝大多数，所以必须单独归类——否则"blit 占多少"会被稀释成没意义的数。
IDLE_MODULES = ("ntdll.dll", "win32u.dll", "kernelbase.dll")


def classify(eip: int, modules: list, sym: SymbolTable) -> tuple:
    """返回 (模块名, 类别, 标签)。类别 ∈ {blit, sym, text_unknown, idle, other_module, unmapped}"""
    mod = None
    for name, base, size in modules:
        if base <= eip < base + max(size, 0x1000):
            mod = name
            break
    if mod is None:
        return "(未映射)", "unmapped", ""
    low = mod.lower()
    if low.startswith("gamemd"):
        kind, label = sym.attribute(eip)
        return "gamemd.exe", kind, label
    if low in IDLE_MODULES:
        return mod, "idle", ""
    return mod, "other_module", ""


# --- 采样 -------------------------------------------------------------------

@dataclass
class ProfileResult:
    pid: int
    tid: int
    samples: int = 0
    seconds: float = 0.0
    hz: float = 0.0
    by_module: dict = field(default_factory=dict)
    by_class: dict = field(default_factory=dict)
    top_symbols: dict = field(default_factory=dict)
    hot_unknown: dict = field(default_factory=dict)
    image_range: tuple = (0, 0)

    def as_dict(self) -> dict:
        return {
            "pid": self.pid, "tid": self.tid, "samples": self.samples,
            "seconds": round(self.seconds, 2), "hz": round(self.hz, 1),
            "by_module": self.by_module, "by_class": self.by_class,
            "top_symbols": dict(sorted(self.top_symbols.items(),
                                       key=lambda x: -x[1])[:20]),
            "hot_unknown": dict(sorted(self.hot_unknown.items(),
                                       key=lambda x: -x[1])[:20]),
        }


def profile(exe_name: str = "gamemd.exe", *, seconds: float = 30.0, hz: float = 500.0,
            symbols_json=None, blit_file=None, log=None) -> ProfileResult:
    pid = find_pid(exe_name)
    if pid is None:
        raise RuntimeError(f"找不到进程 {exe_name}（游戏没在运行？）")
    tids = list_threads(pid)
    if not tids:
        raise RuntimeError(f"进程 {pid} 没有可枚举的线程")
    modules = list_modules(pid)
    sym = SymbolTable.load(symbols_json, blit_file=blit_file) if symbols_json else SymbolTable()

    gm = next((m for m in modules if m[0].lower().startswith("gamemd")), None)
    if gm is None:
        raise RuntimeError("进程里没找到 gamemd 模块")

    # 选主线程：先粗探每个线程，取 EIP 落在 gamemd 镜像内次数最多的那个
    probes = {tid: 0 for tid in tids}
    for _ in range(40):
        for tid in tids:
            eip = read_eip(tid)
            if eip and gm[1] <= eip < gm[1] + max(gm[2], 0x1000):
                probes[tid] += 1
    main_tid = max(probes, key=lambda t: probes[t]) if any(probes.values()) else tids[0]

    res = ProfileResult(pid=pid, tid=main_tid,
                        image_range=(gm[1], gm[1] + gm[2]))
    interval = 1.0 / max(hz, 1.0)
    t_end = time.perf_counter() + seconds
    next_at = time.perf_counter()
    while time.perf_counter() < t_end:
        eip = read_eip(main_tid)
        res.samples += 1
        if eip:
            mod, kind, label = classify(eip, modules, sym)
            res.by_module[mod] = res.by_module.get(mod, 0) + 1
            res.by_class[kind] = res.by_class.get(kind, 0) + 1
            if label:
                key = label
                res.top_symbols[key] = res.top_symbols.get(key, 0) + 1
            elif kind == "text_unknown":
                bucket = "0x%06X" % (eip & ~0xFF)
                res.hot_unknown[bucket] = res.hot_unknown.get(bucket, 0) + 1
        next_at += interval
        delay = next_at - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
        elif delay < -0.5:
            next_at = time.perf_counter()      # 落后太多就重新对齐
    res.seconds = seconds
    res.hz = res.samples / seconds if seconds else 0.0
    return res


def render_markdown(res: ProfileResult, *, scenario: str = "", note: str = "") -> str:
    total = max(res.samples, 1)
    def pct(n):
        return f"{100.0 * n / total:.1f}%"

    lines = [
        "# M0 基线测量：gamemd.exe 时间分布（采样）",
        "",
        f"- 场景：{scenario or '（未描述）'}",
        f"- 采样：{res.samples} 个样本 / {res.seconds:.0f} 秒（实际 {res.hz:.0f} Hz），"
        f"目标线程 tid={res.tid}（pid={res.pid}）",
        f"- 镜像范围：0x{res.image_range[0]:08X} – 0x{res.image_range[1]:08X}"
        "（无 .reloc → 静态地址即运行时地址）",
        "",
        "> 这是**时间占比**，不是「每 tick 毫秒分解」。要拿 tick 边界必须插桩改代码，"
        "本工具刻意不碰游戏代码。",
        "",
        "## 按模块",
        "",
        "| 模块 | 占比 | 样本 |",
        "|---|---|---|",
    ]
    for mod, n in sorted(res.by_module.items(), key=lambda x: -x[1]):
        lines.append(f"| {mod} | {pct(n)} | {n} |")

    lines += ["", "## 按类别（gamemd 内）", "", "| 类别 | 占比（全样本） | 样本 | 说明 |", "|---|---|---|---|"]
    desc = {
        "blit": "软件 blit 实现（渲染像素拷贝）",
        "sym": "已知虚函数（来自 RTTI 恢复的 vtable）",
        "text_unknown": "gamemd 代码段内、未落在已知入口窗口",
        "other_module": "系统/第三方 DLL",
        "unmapped": "未映射地址（异常）",
    }
    for kind, n in sorted(res.by_class.items(), key=lambda x: -x[1]):
        lines.append(f"| {kind} | {pct(n)} | {n} | {desc.get(kind, '')} |")

    if res.top_symbols:
        lines += ["", "## 热点函数（Top 20）", "", "| 函数 | 占比 | 样本 |", "|---|---|---|"]
        for name, n in sorted(res.top_symbols.items(), key=lambda x: -x[1])[:20]:
            lines.append(f"| `{name}` | {pct(n)} | {n} |")

    if res.hot_unknown:
        lines += ["", "## 代码段内未归因热点（Top 20，按 256 字节对齐分桶）",
                  "", "| 地址桶 | 占比 | 样本 |", "|---|---|---|"]
        for addr, n in sorted(res.hot_unknown.items(), key=lambda x: -x[1])[:20]:
            lines.append(f"| `{addr}` | {pct(n)} | {n} |")

    if note:
        lines += ["", "## 备注", "", note]
    return "\n".join(lines) + "\n"


def dump(res: ProfileResult, out_dir, *, scenario: str = "", note: str = "") -> dict:
    from ra2opt import safewrite
    import json as _json

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(res.as_dict(), ensure_ascii=False, indent=2).encode("utf-8")
    safewrite.write_bytes(out, "perf-profile.json", payload, allow_create=True)
    md = render_markdown(res, scenario=scenario, note=note)
    safewrite.write_bytes(out, "perf-profile.md", md.encode("utf-8"), allow_create=True)
    return {"json": str(out / "perf-profile.json"), "md": str(out / "perf-profile.md"),
            "result": res}
