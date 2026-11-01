"""harness8 v3 批发射器副本 · 2026-11-01（① 早相位判据修正+轮询对照批专用）。

★ 派生：`_launch_h8_20261031.py`（v2 发射器）副本。v3 相对 v2 的差异（逐处枚举）：
  1. KNOWN_HARNESS / HARNESS_BY_SHA16 追加 harness8 v3 条目（37a7c9cdf2ca97e3；
     v2 dd5459fe 条目保留）；缺省 HARNESS_SHA16 = v3；
  2. OUT_DIR 模板 → 「l%s_1101v3%s」（短命名：6 位 pid 下 planned ≤128，根治
     C-R2 六位 pid 门禁边界）；TRIP_ID → -V3-20261101；
  3. 头部声明（本段）。预检/载体/清理逻辑与 v2 副本逐字一致（R-1 修复承继）。
★ harness8 v3 = v2（dd5459fe，冻结维持）+ 加性/块内补丁（H8-5 在局闸分档降级 /
  H8-6 --h8-wait-hz 轮询对照旋钮 / 超时支 overrun_kind / C-R3 措辞修正）；vs 母本
  harness7 仍 0 删/208 增。见 HARNESS8_V3_DESIGN_20261101.md。
★ 载体：本趟新建 → 趟后按载体路径精确终止进程 → shutil.rmtree 删除 → 复测残留。
"""
import os
import sys
import time
import hashlib
import json
import ctypes
import shutil
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
TRIP = LEAD / "qc161_u0400_trip"
SRC = TRIP / "_src_L1_sf8_20261020"
MANIFEST = TRIP / "_src_L1_sf8_20261020_MANIFEST.json"
HARNESS = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py"
# ★ 与母本一致的白名单纪律：哈希取值比对，集合外一律硬停。
#   ★ 本副本追加 harness8 条目；harness6/7 条目保留（复现旧趟仍可用）。
KNOWN_HARNESS = {
    "ff8245d27b3db22a": "harness6（母本，463,219 B / 8,483 行）",
    "d019e8beecfb5fd8": "harness7（D-05 补丁副本，472,020 B / +124−0）",
    "dd5459fe0cf3461c": "harness8 v2（H8 绑帧补丁副本，+160−0；字节冻结维持）",
    "37a7c9cdf2ca97e3": "harness8 v3（早相位判据修正+轮询对照，+208−0 vs 母本）",
}
HARNESS_BY_SHA16 = {
    "ff8245d27b3db22a": ROOT / "lead/goal1_harness6_20261022/qc151_trip.harness6.py",
    "d019e8beecfb5fd8": ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py",
    "dd5459fe0cf3461c": ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py",
    "37a7c9cdf2ca97e3": ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8_v3.py",
}

# ★ 变体表（与母本逐字一致）：L3 = 高负载满员（sf10c）＝本批目标场景。
VARIANTS = {
    "L1": {
        "src": "_src_L1_sf8_20261020",
        "map_sha": "0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc",
        "trip_prefix": "QC161-U0800-L1",
    },
    "L3": {
        "src": "_src_L3_sf10c_20261021",
        "map_sha": "f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36",
        "trip_prefix": "QC161-U0800-L3",
    },
}

DEFAULT_CARRIER_FILES = ("gamemd.exe", "ra2loader.exe", "ra2render.dll",
                         "ra2opt_play.bat", "except.txt")
MAP = SRC / "XMP29U2.MAP"
MAP_SHA = "0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc"
PROBE_FRAMES = "3900,4200,4500,4800,5100,5400,5700,6000"

HARNESS_SHA16 = "37a7c9cdf2ca97e3"   # ★ 本副本缺省 harness8 v3（母本缺省 harness6）
GAMEMD_SHA16 = "73201cc021497c95"

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class PE32(ctypes.Structure):
    # ★ R-1 修复（XVERIFY_H8 2026-10-31）：此前誊写漏掉 th32ParentProcessID 一行
    #   ⇒ sizeof 560≠内核期望 568 ⇒ Process32FirstW 恒败 ERROR_BAD_LENGTH(24)
    #   ⇒ list_procs 恒空 ⇒ A8 预检 fail-open + kill_under 静默失效。已补回，
    #   与母本 _launch_l1_20261023.py 逐字段一致（9 字段）。
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


def build_harness_argv(*, harness, map_path, map_sha, out_dir, src, extra,
                       trip_id, probe_frames, fullscreen, extra_argv):
    """★ 与母本 build_harness_argv 逐字一致（纯函数；缺省元素序不变）。"""
    argv = [
        str(harness),
        "--target-map", str(map_path),
        "--target-sha256", map_sha,
        "--carrier", str(Path(out_dir) / "ct"),
        "--carrier-create-from", str(src),
        "--carrier-create-files", ",".join(extra),
        "--trip-id", trip_id,
        "--out-dir", str(out_dir),
        "--measure", "1",
    ]
    if fullscreen:
        argv.append("--fullscreen")
    argv += ["--evid-diff", "--probe-frames", probe_frames]
    argv.extend(x for x in (extra_argv or []) if x)
    return argv


def main():
    global OUT_DIR, TRIP_ID, SRC, MANIFEST, MAP, MAP_SHA, HARNESS, HARNESS_SHA16
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="",
                    help="★ 趟后缀（如 a/b）；空 = 首趟原名")
    ap.add_argument("--variant", default="L3", choices=sorted(VARIANTS),
                    help="★ 载体变体（本批缺省 L3=满员 sf10c）")
    ap.add_argument("--probe-frames", default=PROBE_FRAMES,
                    help="★ 探针锁存帧阶梯（缺省 %s）" % PROBE_FRAMES)
    ap.add_argument("--harness-sha16", default=HARNESS_SHA16,
                    choices=sorted(KNOWN_HARNESS),
                    help="★ 目标 harness（用哈希选，避免传任意路径）")
    ap.add_argument("--extra-argv", default="",
                    help="★ 透传给 harness 的附加参数（空格分隔，如 "
                         "--h7-measure-start-frame 400）")
    ap.add_argument("--no-fullscreen", action="store_true", default=False,
                    help="★ 发窗口模式趟（缺省仍是 --fullscreen，与既有趟一致）")
    _a = ap.parse_args()
    HARNESS = HARNESS_BY_SHA16[_a.harness_sha16]
    HARNESS_SHA16 = _a.harness_sha16
    _v = VARIANTS[_a.variant]
    SRC = TRIP / _v["src"]
    MANIFEST = TRIP / (_v["src"] + "_MANIFEST.json")
    MAP = SRC / "XMP29U2.MAP"
    MAP_SHA = _v["map_sha"]
    # ★ Y-6/C-R2 根治（v3）：目录名模板再缩短——「l3_1101v3a」=10 字符 ⇒ planned
    #   6 位 pid 下 ≤128 ≤130（六位 pid 边界风险消除）。
    OUT_DIR = TRIP / ("l%s_1101v3%s" % (_a.variant[1:].lower(), _a.suffix))
    TRIP_ID = _v["trip_prefix"] + "-V3-20261101" + _a.suffix.upper()
    probe_frames = _a.probe_frames
    extra_argv = [x for x in _a.extra_argv.split() if x]

    print("=" * 78)
    print("变体 = %s   载体源 = %s" % (_a.variant, SRC.name))
    print("harness = %s（%s）"
          % (HARNESS.name, KNOWN_HARNESS[HARNESS_SHA16]))
    print("harness8 绑帧批 · 2026-10-31（原版直启 + 零注入）")
    print("=" * 78)

    checks = [
        ("A1 gamemd sha", hashlib.sha256((SRC / "gamemd.exe").read_bytes()).hexdigest()[:16],
         GAMEMD_SHA16),
        ("A2 map sha", hashlib.sha256(MAP.read_bytes()).hexdigest()[:16], MAP_SHA[:16]),
        ("A11 harness sha16", hashlib.sha256(HARNESS.read_bytes()).hexdigest()[:16],
         HARNESS_SHA16),
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
        if checks[2][1] != checks[2][2]:
            print("   ★ A11 失败：目标 harness 实测 sha16=%s ≠ 期望 %s"
                  "（%s）" % (checks[2][1], checks[2][2],
                              KNOWN_HARNESS.get(checks[2][2], "未知期望值")))
        return 2

    planned = OUT_DIR / "ct" / ("c_" + "0" * 12 + "_12345")
    plen = len(str(planned))
    print("  %-18s len=%d (门禁 130) %s"
          % ("out-dir 预演", plen, "OK" if plen <= 130 else "BLOCK"))
    if plen > 130:
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    _mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _all_names = sorted(_mf["files"].keys())
    EXTRA = [n for n in _all_names if n not in DEFAULT_CARRIER_FILES]
    print("  载体件集: 清单 %d 件 = 默认 %d + 附加 %d"
          % (len(_all_names), len(DEFAULT_CARRIER_FILES), len(EXTRA)))
    assert len(_all_names) == 88, "冻结清单应为 88 条，实得 %d" % len(_all_names)
    assert len(EXTRA) == 83, "附加件应为 83 条，实得 %d" % len(EXTRA)
    for _n in EXTRA:
        assert "," not in _n, "件名含逗号会破坏整串切分: %r" % _n

    argv = build_harness_argv(
        harness=HARNESS, map_path=MAP, map_sha=MAP_SHA, out_dir=OUT_DIR,
        src=SRC, extra=EXTRA, trip_id=TRIP_ID, probe_frames=probe_frames,
        fullscreen=not _a.no_fullscreen, extra_argv=extra_argv)

    spawn_argv = [sys.executable]
    for a in argv:
        spawn_argv.append('"%s"' % a if (" " in a and not a.startswith('"')) else a)
    print()
    print("[发射] python " + " ".join(argv))
    print()

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.monotonic()
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
              "harness": str(HARNESS),
              "harness_sha16": hashlib.sha256(HARNESS.read_bytes()).hexdigest()[:16],
              "carriers_deleted": all_del, "leftover_procs": left}
    (OUT_DIR / "_launch_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("[结果]", OUT_DIR / "_launch_result.json")
    return pid


if __name__ == "__main__":
    sys.exit(main())
