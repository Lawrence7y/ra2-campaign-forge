"""L1 基线趟发射器（Arm A：原版直启 + 零注入）。

★ 依 L1_PRELAUNCH_CHECKLIST.md 装1–装8 装配命令行。
★ 用 harness3（含 failfast + carrierfix + pathlen 目录门禁 130）。
★ 趟后自动：终止进程（按载体路径精确匹配）→ 删除载体 → 复测。
★ 启动用 os.spawnv（不经 shell，参数为 argv 列表）。
"""
import os, sys, time, hashlib, json, ctypes, shutil
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
TRIP = LEAD / "qc161_u0400_trip"
SRC = TRIP / "_src_L3_sf10c_20261021"
HARNESS = LEAD / "qc151_harness_merge_20261021/qc151_trip.harness3.py"

OUT_DIR = TRIP / "l3_20261021"       # ★ L3 高负载档（sf10c ≈1452 单位）
TRIP_ID = "QC161-U0800-L3"
MANIFEST = TRIP / "_src_L3_sf10c_20261021_MANIFEST.json"
DEFAULT_CARRIER_FILES = ("gamemd.exe", "ra2loader.exe", "ra2render.dll",
                         "ra2opt_play.bat", "except.txt")
MAP = SRC / "XMP29U2.MAP"
MAP_SHA = "f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36"
PROBE_FRAMES = "3900,4200,4500,4800,5100,5400,5700,6000"

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class PE32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", wt.WCHAR * 260)]


def list_procs():
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    h = k32.CreateToolhelp32Snapshot(2, 0)
    if not h or h == ctypes.c_void_p(-1).value:
        return {}
    out = {}
    e = PE32()
    e.dwSize = ctypes.sizeof(PE32)
    k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    ok = k32.Process32FirstW(h, ctypes.byref(e))
    while ok:
        out[e.th32ProcessID] = e.szExeFile
        ok = k32.Process32NextW(h, ctypes.byref(e))
    k32.CloseHandle(h)
    return out


def game_procs():
    return [n for n in list_procs().values()
            if n.lower() in ("gamemd.exe", "ra2loader.exe")]


def kill_under(cdir):
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.QueryFullProcessImageNameW.argtypes = [
        wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    k32.QueryFullProcessImageNameW.restype = wt.BOOL
    k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
    k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
    k32.CloseHandle.argtypes = [wt.HANDLE]
    target = str(cdir).lower()
    killed = []
    for pid, nm in list(list_procs().items()):
        if nm.lower() not in ("gamemd.exe", "ra2loader.exe", "game.exe"):
            continue
        hp = k32.OpenProcess(0x0001 | 0x1000, False, pid)
        if not hp:
            continue
        try:
            buf = ctypes.create_unicode_buffer(1024)
            ln = wt.DWORD(1024)
            if k32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(ln)):
                if target in buf.value.lower():
                    k32.TerminateProcess(hp, 1)
                    k32.WaitForSingleObject(hp, 6000)
                    killed.append((pid, nm))
        finally:
            k32.CloseHandle(hp)
    return killed


def rm_carrier(cdir):
    last = None
    for i in range(8):
        time.sleep(1.0 + i * 0.5)
        try:
            shutil.rmtree(cdir)
            return True, None
        except Exception as e:
            last = e
    return False, last


def main():
    print("=" * 78)
    print("L1 基线趟（Arm A：原版直启 + 零注入）")
    print("=" * 78)

    checks = [
        ("A1 gamemd sha", hashlib.sha256((SRC / "gamemd.exe").read_bytes()).hexdigest()[:16],
         "73201cc021497c95"),
        ("A2 map sha", hashlib.sha256(MAP.read_bytes()).hexdigest()[:16], MAP_SHA[:16]),
        ("A11 harness3 sha", hashlib.sha256(HARNESS.read_bytes()).hexdigest()[:16],
         "5c56dac5c17a2ba4"),
        ("A8 游戏进程数", str(len(game_procs())), "0"),
    ]
    ok_all = True
    for name, got, want in checks:
        good = got == want
        ok_all &= good
        print("  %-18s got=%-20s want=%-20s %s"
              % (name, got, want, "OK" if good else "MISMATCH"))
    if not ok_all:
        print("!! 预检不过，不发射")
        return 2

    planned = OUT_DIR / "ct" / ("c_" + "0" * 12 + "_12345")
    plen = len(str(planned))
    print("  %-18s len=%d (门禁 130) %s"
          % ("out-dir 预演", plen, "OK" if plen <= 130 else "BLOCK"))
    if plen > 130:
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ★★ 载体件集：冻结清单 88 件 = 默认 5 件（脚本自动加）+ 83 件附加。
    #
    #   ★★ l1b 首趟（18:42）错在**整个丢掉了 --carrier-create-files** ⇒ 载体只有
    #     默认 5 件 ⇒ gamemd 缺 ddraw.dll / *.mix ⇒ 加载期即亡
    #     （wait_returncode=3221225781 = 0xC0000135 STATUS_DLL_NOT_FOUND）
    #     ⇒ 主窗永不出现 ⇒ rc=22 EXIT_WINDOW_NOT_FOUND。★ 22 是下游症状，
    #     不是导航失败。同类先例：T6 六件载体缺 ddraw.dll 启动即亡 0xC0000135。
    #
    #   ★ 当时弃用的理由是「整串含空格项 RA2MD Update.ico 会被 argv 拆开」——
    #     该理由已被 `_argv_rt_probe.py` 证伪：os.spawnv 下整串加引号可原样送达
    #     （含逗号/非 ASCII/空格 均逐字节相等）。
    #   ★ 但 `RA2MD Update.ico` 根本**不在** L1 源变体内（只在 ra2youli/ra2bench/），
    #     冻结清单 88 条里也没有它 ⇒ 清单 A12 的「89 件」是错的，88 才是真值。
    #   ★ 因此本趟按冻结清单 88 件执行：83 件附加名里**无空格、无逗号**
    #     （唯一非 ASCII 为 `配置器.exe`，已由探针验证可原样往返）⇒ 无需引号。
    _mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _all_names = sorted(_mf["files"].keys())
    EXTRA = [n for n in _all_names if n not in DEFAULT_CARRIER_FILES]
    print("  载体件集: 清单 %d 件 = 默认 %d + 附加 %d"
          % (len(_all_names), len(DEFAULT_CARRIER_FILES), len(EXTRA)))
    assert len(_all_names) == 88, "冻结清单应为 88 条，实得 %d" % len(_all_names)
    assert len(EXTRA) == 83, "附加件应为 83 条，实得 %d" % len(EXTRA)
    for _n in EXTRA:
        assert "," not in _n, "件名含逗号会破坏整串切分: %r" % _n

    argv = [
        str(HARNESS),
        "--target-map", str(MAP),
        "--target-sha256", MAP_SHA,
        # ★ --carrier 是必填项：在本模式下只作所有权判定基准，
        #   实际载体由 create_isolated_carrier 新建到 WORKDIR/ct/
        "--carrier", str(OUT_DIR / "ct"),
        "--carrier-create-from", str(SRC),
        "--carrier-create-files", ",".join(EXTRA),
        "--trip-id", TRIP_ID,
        "--out-dir", str(OUT_DIR),
        "--measure", "1",
        "--fullscreen",
        "--evid-diff",
        "--probe-frames", PROBE_FRAMES,
    ]

    # ★★ os.spawnv 在 Windows 上会把 argv 重新拼成**命令行字符串**，
    #   含空格的元素（如 "RA2MD Update.ico"）必须自己加引号，否则被拆开。
    #   判据：脚本自己按 "," 切分 --carrier-create-files 的**值**，
    #   所以只能给整串加引号（不能改内部的逗号）。
    spawn_argv = [sys.executable]
    for a in argv:
        spawn_argv.append('"%s"' % a if (" " in a and not a.startswith('"')) else a)
    print()
    print("[发射] python " + " ".join(argv))
    print()

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.monotonic()
    # ★ os.spawnv：不经 shell，argv[0] 是解释器路径，argv[1:] 是脚本+参数
    pid = os.spawnv(os.P_WAIT, sys.executable, spawn_argv)
    dur = time.monotonic() - t0
    print()
    print("[退出] pid=%s rc=%s  用时 %.1fs" % (pid, pid, dur))

    print()
    print("[清理]")
    ctroot = OUT_DIR / "ct"
    cts = sorted(ctroot.glob("c_*")) if ctroot.is_dir() else []
    all_del = True
    for ct in cts:
        killed = kill_under(ct)
        if killed:
            print("  终止:", killed)
        ok, err = rm_carrier(ct)
        all_del &= ok
        print("  删除 %-42s %s%s" % (ct.name, ok, "" if ok else "  ERR=" + str(err)))

    left = game_procs()
    print("  残留进程:", left or "无")
    print("  载体残留:", [p.name for p in cts if p.exists()] or "无")

    result = {"rc": pid, "duration_s": round(dur, 1), "argv": argv,
              "out_dir": str(OUT_DIR), "trip_id": TRIP_ID,
              "carriers_deleted": all_del, "leftover_procs": left}
    (OUT_DIR / "_launch_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("[结果]", OUT_DIR / "_launch_result.json")
    return pid


if __name__ == "__main__":
    sys.exit(main())
