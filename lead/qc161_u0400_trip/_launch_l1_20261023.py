"""L1 基线趟发射器 · 2026-10-23 开机会话（Arm A：原版直启 + 零注入）。

★ 目的：① 的第 0 步 —— 重启后确认本开机会话能否跑 31 档。
  判据 = measure_w0.json 的 gate.pre_fps15 ≥ 25（V11-a 硬门禁，见
  lead/goal1_v11_env_gate_20261021/V11_ENV_GATE_DESIGN.md §3.1）。
★ 与 l1d_20261021 的唯一变量 = harness 版本（harness3 → harness6）。
  measure 协议常量逐字相同（WINDOWS=3 / WINDOW_S=25.0 / SETTLE_S=4.0 /
  GATE_FPS15_MIN=3.0 / GATE_SPAN_S=1.5）⇒ pre_fps15 跨代可比。
★ 同时充当 harness6 的首次真机冒烟（①-2）。缺省 --close-mode terminate
  ⇒ 控制流与 harness5 等价，不触发 WM_CLOSE 路径。
★ 副本制：本文件为新建发射器，harness6 母本零改动。
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
HARNESS = ROOT / "lead/goal1_harness6_20261022/qc151_trip.harness6.py"
# ★★ H-2 扩散修复（2026-10-23）：原本 `HARNESS` 与 `HARNESS_SHA16` 双双焊死为
#   harness6，于是「用 harness7 跑真机冒烟」这件事**连预检都过不去**（A11 报
#   MISMATCH ⇒ `return 2`），而预检文案看起来像是「母本被改坏了」。
#   改成 harness 可选：`--harness` 指定路径 / `--harness-sha16` 指定期望哈希，
#   哈希必须落在 KNOWN_HARNESS 内。
#   ★ 这不是放宽门禁：仍是**取值比对**，只是把「唯一合法值」换成
#   「显式枚举的合法集合」，集合外一律硬停。
KNOWN_HARNESS = {
    "ff8245d27b3db22a": "harness6（母本，463,219 B / 8,483 行）",
    "d019e8beecfb5fd8": "harness7（D-05 补丁副本，472,020 B / +124−0）",
}
HARNESS_BY_SHA16 = {
    "ff8245d27b3db22a": ROOT / "lead/goal1_harness6_20261022/qc151_trip.harness6.py",
    "d019e8beecfb5fd8": ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py",
}

# ★ 变体表：L1 = 标准基线（sf8 / 872 单位）；L3 = 高负载（sf10c / 1452 单位）。
#   两者的 measure 协议常量相同，V11-a 只判「档位」不判负载 ⇒ 都可用作
#   ① 的第 0 步。选 L3 的理由：战斗更长 ⇒ 测量窗更可能落在战斗内
#   （L1 在 31 档下 125 s 帧阶段就推进 ~3500 逻辑帧，战斗先结束）。
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

HARNESS_SHA16 = "ff8245d27b3db22a"   # 缺省仍是 harness6，既有趟不受影响
GAMEMD_SHA16 = "73201cc021497c95"

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
    global OUT_DIR, TRIP_ID, SRC, MANIFEST, MAP, MAP_SHA, HARNESS, HARNESS_SHA16
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="",
                    help="★ 趟后缀（如 b/c/d）；空 = 首趟原名")
    ap.add_argument("--variant", default="L1", choices=sorted(VARIANTS),
                    help="★ 载体变体（缺省 L1）")
    ap.add_argument("--probe-frames", default=PROBE_FRAMES,
                    help="★ 探针锁存帧阶梯（缺省 %s）" % PROBE_FRAMES)
    # ★ H-2 扩散修复：harness 可选（缺省 harness6，与既有趟一致）
    ap.add_argument("--harness-sha16", default=HARNESS_SHA16,
                    choices=sorted(KNOWN_HARNESS),
                    help="★ 目标 harness（用哈希选，避免传任意路径）")
    ap.add_argument("--extra-argv", default="",
                    help="★ 透传给 harness 的附加参数（空格分隔，如 "
                         "--h7-keep-rect-wait）")
    _a = ap.parse_args()
    HARNESS = HARNESS_BY_SHA16[_a.harness_sha16]
    HARNESS_SHA16 = _a.harness_sha16
    _v = VARIANTS[_a.variant]
    SRC = TRIP / _v["src"]
    MANIFEST = TRIP / (_v["src"] + "_MANIFEST.json")
    MAP = SRC / "XMP29U2.MAP"
    MAP_SHA = _v["map_sha"]
    OUT_DIR = TRIP / ("l%s_20261023%s" % (_a.variant[1:].lower(), _a.suffix))
    TRIP_ID = _v["trip_prefix"] + "-20261023" + _a.suffix.upper()
    probe_frames = _a.probe_frames
    extra_argv = [x for x in _a.extra_argv.split() if x]

    print("=" * 78)
    print("变体 = %s   载体源 = %s" % (_a.variant, SRC.name))
    print("harness = %s（%s）"
          % (HARNESS.name, KNOWN_HARNESS[HARNESS_SHA16]))
    print("L1 基线趟 · 2026-10-23 开机会话（Arm A：原版直启 + 零注入）")
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

    # ★ 载体件集：冻结清单 88 件 = 默认 5 件（脚本自动加）+ 83 件附加。
    #   83 件附加名里无空格、无逗号（唯一非 ASCII 为 `配置器.exe`，
    #   `_argv_rt_probe.py` 已验证 os.spawnv 下可原样往返）。
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
        # --carrier 只作所有权判定基准；实际载体由 create_isolated_carrier
        # 新建到 WORKDIR/ct/
        "--carrier", str(OUT_DIR / "ct"),
        "--carrier-create-from", str(SRC),
        "--carrier-create-files", ",".join(EXTRA),
        "--trip-id", TRIP_ID,
        "--out-dir", str(OUT_DIR),
        "--measure", "1",
        "--fullscreen",
        "--evid-diff",
        "--probe-frames", probe_frames,
    ]
    # ★ H-2 扩散修复：附加参数（如 harness7 对照臂的 --h7-keep-rect-wait）
    argv.extend(extra_argv)

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
