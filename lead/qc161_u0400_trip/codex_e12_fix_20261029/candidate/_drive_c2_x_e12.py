# -*- coding: utf-8 -*-
"""_drive_c2_x_e12.py — E1+E2 合批候选驱动（D-11 审定对象；本件=离线候选，发射永远等用户授权）。

存在性理由（D-11 条目 + B 线 LATCHED_HANG_MECHANISM_20261028.md §4/§9）：
- **E1**：P3e 同协议补样（窗现+6 s 关窗、watch=120 s、配置 Guard=1+Bail=1 全同早窗批）；
- **E2**：主循环检测到 exitstate==1（闩）后切 1 Hz 慢采样，逐秒记录四轴——
  GetProcessTimes CPU 增量（kernel+user，句柄权沿用 0x0400|0x0010|0x100000，**不申请新权**）、
  hook6=BAIL_SITE(0x6BE0E1) 六字节现读 vs 锚 e91a1f941790（三态：在位/不在位/读败显式）、
  ws_kb、可见窗口枚举（补 A 线 R1 盲区）；闩+30 s 加一张截图。
  判读分叉（§9 A4 定稿）：CPU≈1 核×hook6 在位 ⇒ P1 第一候选；×不在位 ⇒ 丁；
  CPU≈0 ⇒ 阻塞族（交 E3 另裁）；ws 仍涨 ⇒ 加载未完动摇「宿主已进入」；新窗 ⇒ 触通用停止。
  hook6 只是**读既有 6 字节**（非新 hook 点、零写入游戏内存、零扩 Hook）。

纪律复用=import 冻结件组件，不复制改冻结件：
- 母版哈希先验后 import：_drive_c2_x_probe_v2.py=6afe2711…、_drive_c2_x_earlyclose.py=2e970eec…
  （任一不符 ⇒ 本件拒绝 import，硬失败）；
- bind_real_ops/_precheck_shas/TripFail/tri_read_u32/apply_bail_mode/screenshot_best_effort/
  finalize/载体纪律/phase_sentinels/OPS seam=全部 import 复用；
- ★ 零字节改动两个终钉件；本件独立命名，TRIP_INDEX/台账/设计件均未触碰。

通用停止条件（§4 + D-11 失败条件）：
- 慢采样期发现**新可见窗**（含 #32770/确认/保存/网络类关键字命中 ⇒ 交互定性）⇒ 只留证据
  （截图+行记录）、停止采样升级动作（不点确认/不丢存档/不断网），趟标记 stop_triggered；
- except.txt 哈希中途变化 ⇒ 停；
- 趟间 BOOT 变化 ⇒ 停（同开机会话断言，承 §4 共同前提）；
- 预检 fail ⇒ 停；批次内趟非 OK ⇒ 停后续（承 v2 G-9 硬停纪律）。

授权硬闸：--live 无 --approved 恒 rc=3；--approved 单独仅透传闸值不自动跑；
--live --approved 仍须预检全过才发射；--preflight 真 OS 只读预检；--selftest 委托离线自检套件。
输出 schema：_rec.json 增 E2 段（latch_detected/slow_sample_rows/hook6_state/cpu_delta_median_s/
e2_fork_label/stop_triggered 等）；timeline.json 保持 {hold_tl, close_rows} 原形态（close_rows
行字段与早窗批逐键同形）+ 追加 "_e2" 段（判器兼容：C5/C7/C8 口径不变；C1/C6/C9 的早窗不适用
面见自证报告通道声明）。
"""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# 冻结母版哈希自验（import 之前；不符⇒RuntimeError 拒绝加载）
FROZEN_SHA256 = {
    "_drive_c2_x_earlyclose.py": "2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1",
    "_drive_c2_x_probe_v2.py": "6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9",
}


def verify_frozen_masters(want=None):
    """逐文件实读 sha256 对钉；返回 {name: sha256}。不符⇒RuntimeError（不吞）。"""
    want = want if want is not None else FROZEN_SHA256
    got = {}
    for name, exp in want.items():
        p = HERE / name
        try:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception as e:
            raise RuntimeError("frozen_master_unreadable:%s:%r" % (name, e))
        got[name] = h
        if h != exp:
            raise RuntimeError("frozen_master_mismatch:%s got=%s want=%s" % (name, h, exp))
    return got


_MAESTRO = verify_frozen_masters()   # 模块级自验：import 本件即先验哈希再谈 import

sys.path.insert(0, str(HERE))
import _drive_c2_x_probe_v2 as V2            # noqa: E402  （哈希已验）
import _drive_c2_x_earlyclose as E           # noqa: E402  （哈希已验；协议常量单一来源）

# ---------------------------------------------------------------------------
# E1 协议常量（单一来源=早窗终钉件；本件不改其值）
HOLD_AFTER_WINDOW = E.HOLD_AFTER_WINDOW      # 6.0 s
WATCH_S = E.WATCH_S                          # 120 s
TRIP_TAG_E12 = "P3e_E12"

# E2 轴参数（B 线 §4-E2 + §9-A4 定稿；D-11 判读增补引注）
LATCH_VALUE = 1                              # exitstate==1 ⇒ 闩
SLOW_HZ_SLEEP = 1.0                          # 闩后 1 Hz 慢采样
FAST_SLEEP = 0.1                             # 闩前主循环节律（同早窗批 close_rows）
HOOK6_ANCHOR = "e91a1f941790"               # 六字节锚（台账 §453「hook 实况×3」；hold_tl 实测）
HOOK6_NBYTES = 6                             # BAIL_SITE=V2.BAIL_SITE(0x6BE0E1) 起读 6 字节
WATCH_ACCESS = 0x0400 | 0x0010 | 0x100000    # 沿用既有句柄权；GetProcessTimes 同权内（PROCESS_QUERY_INFORMATION）
SPIN_MIN_DELTA = 0.7                         # CPU 自旋侧阈值（每 1 s 壁钟净核秒≥0.7 ⇒ ≈1 核）——判读归 Leader，本件只落轴
BLOCK_MAX_DELTA = 0.2                        # CPU 阻塞侧阈值（≤0.2 ⇒ ≈0 核）
CPU_TICK_DIVISOR = 1e7                       # FILETIME 100ns ⇒ 秒
LATCH_SHOT_AFTER_S = 30.0                    # 闩+30 s 截图
BOOT_TOLERANCE_MS = 2000
EXCEPT_CHECK_EVERY_S = 30.0                  # 慢采样期 except 哈希巡检节拍
SRC_INI_SHA16 = "27c9a60c55a8a1b4"           # 载体源 ra2render.ini（16,496 B；2026-10-29 实算命中）
SRC_INI_SIZE = 16496
INTERACTION_KEYS = ("#32770", "＃32770", "32770", "确认", "保存", "confirm", "save", "network", "网络")

# ---------------------------------------------------------------------------
# GetProcessTimes / BOOT seam（真实现；自检套件经 V2.OPS 替身整体接管）
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class _FT(ctypes.Structure):
    _fields_ = [("lo", wt.DWORD), ("hi", wt.DWORD)]


def _ft_int(f):
    return (f.hi << 32) | f.lo


_k32.GetProcessTimes.restype = wt.BOOL
_k32.GetProcessTimes.argtypes = [wt.HANDLE, ctypes.POINTER(_FT), ctypes.POINTER(_FT),
                                 ctypes.POINTER(_FT), ctypes.POINTER(_FT)]


def _r_process_times(h):
    """契约：(dict{kernel,user} 100ns 累计 | None, err:int)。句柄=WATCH_ACCESS 既有权。"""
    c, e, k, u = _FT(), _FT(), _FT(), _FT()
    ctypes.set_last_error(0)
    if not _k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        return None, ctypes.get_last_error()
    return {"kernel": _ft_int(k), "user": _ft_int(u)}, 0


_k32.GetTickCount64.restype = ctypes.c_ulonglong
_k32.GetTickCount64.argtypes = []


def _r_boot_ms():
    return int(_k32.GetTickCount64())


def extend_ops_real():
    """真机/预检用：V2.bind_real_ops() 后追加 E2 两个 seam（不改冻结件本体）。"""
    V2.bind_real_ops()
    V2.OPS["process_times"] = _r_process_times
    V2.OPS["boot_ms"] = _r_boot_ms
    V2.OPS["wallclock_ms"] = lambda: time.time_ns() // 1_000_000


# ---------------------------------------------------------------------------
# E2 纯函数（自检套件分臂直测）
def capture_boot():
    """Read both clocks at each boundary; keep the batch reference immutable.

    Wall-clock corrections beyond the tolerance conservatively stop the batch.
    This is a session guard, not an authentication-quality boot identifier.
    """
    wall = V2.OPS["wallclock_ms"]()
    uptime = V2.OPS["boot_ms"]()
    if (isinstance(wall, bool) or isinstance(uptime, bool)
            or not isinstance(wall, (int, float)) or not isinstance(uptime, (int, float))
            or not math.isfinite(wall) or not math.isfinite(uptime) or uptime < 0):
        raise V2.TripFail("boot_clock_invalid")
    return {"boot_ms": uptime, "wallclock_ms": wall,
            "boot_wallclock_ms": wall - uptime}


def assert_same_boot(current, reference):
    if (not isinstance(reference, dict) or "boot_wallclock_ms" not in reference
            or not isinstance(reference["boot_wallclock_ms"], (int, float))
            or isinstance(reference["boot_wallclock_ms"], bool)
            or not math.isfinite(reference["boot_wallclock_ms"])):
        raise V2.TripFail("boot_reference_invalid")
    if abs(current["boot_wallclock_ms"] - reference["boot_wallclock_ms"]) > BOOT_TOLERANCE_MS:
        raise V2.TripFail("stop_condition:boot_changed_between_trips(%s!=%s)"
                          % (current["boot_wallclock_ms"], reference["boot_wallclock_ms"]))


def cpu_delta(prev, cur):
    """(kernel+user)100ns 增量⇒秒；任一侧缺⇒None（不造数）。prev/cur={"kernel","user"} 或 None。"""
    if not prev or not cur:
        return None
    try:
        return ((cur["kernel"] - prev["kernel"]) + (cur["user"] - prev["user"])) / CPU_TICK_DIVISOR
    except (KeyError, TypeError):
        return None


def hook6_tri(h):
    """BAIL_SITE 六字节现读三态：present/absent/read_fail（读败带 rpm/vquery 细节，不得吞、不得冒充不在位）。"""
    raw, err = V2.OPS["read_mem"](h, V2.BAIL_SITE, HOOK6_NBYTES)
    if raw is None:
        try:
            mbi, verr = V2.OPS["vquery"](h, V2.BAIL_SITE)
            detail = {"rpm_err": err, "vquery_err": verr, "mbi_state": mbi[0] if mbi else None}
        except Exception as e:
            detail = {"rpm_err": err, "vquery_exc": repr(e)}
        return {"state": "read_fail", "detail": detail}
    hx = raw.hex()
    return {"state": "present" if hx == HOOK6_ANCHOR else "absent", "hex": hx}


def interaction_hits(wins, baseline):
    """新可见窗（相对基线 hwnd 集）与交互关键字命中。返回 (new_wins, hit_wins)。"""
    base_ids = {w.get("hwnd") for w in (baseline or [])}
    new_wins = [w for w in wins if w.get("hwnd") not in base_ids]
    hits = []
    for w in new_wins:
        blob = ((w.get("class") or "") + "|" + (w.get("title") or "")).lower()
        if any(k.lower() in blob for k in INTERACTION_KEYS):
            hits.append(w)
    return new_wins, hits


def summarize_e2(latch, slow_rows):
    """§9-A4 分叉标签机（只落轴与标签，裁决权在 Leader；小样本只报并趟计数、禁比率式表述）。"""
    out = {"latch_detected": bool(latch), "slow_rows_n": len(slow_rows or [])}
    if not latch:
        out.update(e2_fork_label="not_triggered_no_latch", hook6_state="not_triggered",
                   cpu_delta_median_s=None, ws_delta_kb=None)
        return out
    hk = {"present": 0, "absent": 0, "read_fail": 0}
    for r in slow_rows:
        st = (r.get("hook6") or {}).get("state")
        if st in hk:
            hk[st] += 1
    deltas = [r["cpu"]["delta_s"] for r in slow_rows
              if (r.get("cpu") or {}).get("state") == "ok" and r["cpu"].get("delta_s") is not None]
    med = None
    if deltas:
        srt = sorted(deltas)
        n = len(srt)
        med = srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2.0
        med = round(med, 4)
    ws_ok = [r["ws_kb"] for r in slow_rows if isinstance(r.get("ws_kb"), int)]
    ws_delta = (ws_ok[-1] - ws_ok[0]) if len(ws_ok) >= 2 else None
    out["hook6_state_counts"] = hk
    if not slow_rows:
        out["hook6_state"] = "no_slow_sample_rows"
        out["cpu_ok_deltas_n"] = 0
        out["cpu_delta_median_s"] = None
        out["ws_delta_kb"] = None
        out["e2_fork_label"] = "latched_but_no_slow_rows(exit_at_latch_row?)"
        return out
    if hk["present"] and not hk["absent"] and not hk["read_fail"]:
        out["hook6_state"] = "present_stable"
    elif hk["absent"] and not hk["present"]:
        out["hook6_state"] = "absent_persistently"
    elif hk["absent"] and hk["present"]:
        out["hook6_state"] = "mixed_lost_at_some_row"
    elif hk["read_fail"] and not (hk["present"] or hk["absent"]):
        out["hook6_state"] = "all_read_fail"
    else:
        out["hook6_state"] = "present_with_read_fail_rows"
    out["cpu_ok_deltas_n"] = len(deltas)
    out["cpu_delta_median_s"] = med
    out["ws_delta_kb"] = ws_delta
    if med is None:
        out["e2_fork_label"] = "cpu_axis_unreadable"
    elif med >= SPIN_MIN_DELTA:
        if out["hook6_state"] == "present_stable":
            out["e2_fork_label"] = "spin_x_hook6_present ⇒ P1_first_candidate(§9-A4)"
        elif out["hook6_state"] == "absent_persistently":
            out["e2_fork_label"] = "spin_x_hook6_absent ⇒ 丁_first_candidate(§9-A4)"
        else:
            out["e2_fork_label"] = "spin_x_hook6_undetermined(三态未决:混合/读败)"
    elif med <= BLOCK_MAX_DELTA:
        out["e2_fork_label"] = "cpu≈0 ⇒ blocked_family(甲/乙-1尾/CRT/丙-阻塞 → E3另裁)"
    else:
        out["e2_fork_label"] = "cpu_ambiguous"
    if ws_delta is not None and ws_delta > 1024:
        out["note_ws_growing"] = "ws_kb 闩后净增 %d KB ⇒ 加载未完侧注记（动摇『宿主已进入』，§4-E2）" % ws_delta
    return out


# ---------------------------------------------------------------------------
def run_trip(trip_index=1, boot_ref=None, watch_s=WATCH_S,
             slow_sleep_s=SLOW_HZ_SLEEP, latch_shot_after_s=LATCH_SHOT_AFTER_S,
             except_check_every_s=EXCEPT_CHECK_EVERY_S) -> dict:
    """单趟：E1 协议（import 早窗件常量/纪律）+ E2 闩后慢采样轴。结构镜像 earlyclose.run_trip。
    生产缺省=终钉值（watch 120 s / 慢采 1 Hz / 闩+30 s 截图 / except 30 s 巡检）。
    自检套件传小值以在虚拟时钟下短时覆盖同一分支路径，不改生产缺省。"""
    for seam in ("process_times", "boot_ms", "wallclock_ms"):
        if seam not in V2.OPS:
            raise V2.TripFail("ops_not_bound:%s（须先 extend_ops_real 或自检替身）" % seam)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    arm = {"key": "P3e-E12", "tag": TRIP_TAG_E12, "inject": True, "guard": 1,
           "bail_mode": "explicit1", "mode": "menu",
           "note": "E1 同协议补样+E2 闩后 1Hz 慢采样（v2/早窗件组件 import 复用）"}
    out_dir = V2.MYCARD / ("%s_9001_%s_T%d" % (stamp, arm["tag"], trip_index))
    carrier = out_dir / "ct" / ("c" + "0" * 9)
    V2.CURRENT_CARRIER[0] = carrier
    rec = {"trip_tag": arm["tag"], "trip_index": trip_index, "mode": arm["mode"], "note": arm["note"],
           "out_dir": str(out_dir), "verdict": "OK", "phase": "init",
           "watch_s": watch_s,
           "protocol": "early-close (window+%.1fs)+E2-slow1Hz(latch后轴)" % HOLD_AFTER_WINDOW,
           "e2_params": {"latch_value": LATCH_VALUE, "slow_sleep_s": slow_sleep_s,
                         "watch_s": watch_s, "latch_shot_after_s": latch_shot_after_s,
                         "except_check_every_s": except_check_every_s,
                         "hook6_anchor": HOOK6_ANCHOR, "hook6_nbytes": HOOK6_NBYTES,
                         "bail_site_hex": hex(V2.BAIL_SITE), "watch_access_hex": hex(WATCH_ACCESS),
                         "spin_min_delta_s": SPIN_MIN_DELTA, "block_max_delta_s": BLOCK_MAX_DELTA,
                         "frozen_masters_sha256_at_import": _MAESTRO}}
    proc = None
    made_carrier = False
    try:
        rec["phase"] = "precheck"
        boot_current = capture_boot()
        rec["boot_ms_at_start"] = boot_current["boot_ms"]
        rec["wallclock_ms_at_start"] = boot_current["wallclock_ms"]
        rec["boot_wallclock_ms_at_start"] = boot_current["boot_wallclock_ms"]
        rec["boot_reference"] = dict(boot_ref) if isinstance(boot_ref, dict) else boot_ref
        rec["boot_tolerance_ms"] = BOOT_TOLERANCE_MS
        if boot_ref is not None:
            assert_same_boot(boot_current, boot_ref)
        if any(nm.lower() in ("gamemd.exe", "rc4_loader.exe") for nm in V2.OPS["list_procs"]().values()):
            raise V2.TripFail("precheck_residual_procs")
        V2._precheck_shas()
        ini0 = V2.GAME_SRC / "ra2render.ini"
        if V2.OPS["sha16"](ini0) != SRC_INI_SHA16 or len(V2.OPS["read_bytes"](ini0)) != SRC_INI_SIZE:
            raise V2.TripFail("precheck_src_ini:%s/%d" % (V2.OPS["sha16"](ini0),
                                                          len(V2.OPS["read_bytes"](ini0))))
        ok_id, det = V2.OPS["carrier_identity_ok"](carrier)
        if not ok_id:
            raise V2.TripFail("carrier_identity:%s" % det)

        rec["phase"] = "mkdir"
        if len(str(carrier)) > V2.CARRIER_PATH_MAX:
            raise V2.TripFail("carrier_pathlen")
        out_dir.mkdir(parents=True, exist_ok=True)
        V2.OPS["mkdir"](carrier)
        made_carrier = True
        if any(carrier.iterdir()):
            raise V2.TripFail("carrier_not_empty")

        rec["phase"] = "copy"
        for f in sorted(V2.GAME_SRC.iterdir()):
            if f.is_file():
                V2.OPS["copy_file"](f, carrier / f.name)
        ex0 = carrier / "except.txt"
        rec["except_before"] = V2.OPS["sha16"](ex0) if V2.OPS["isfile"](ex0) else "absent"
        rec["phase"] = "inject_setup"
        V2.OPS["copy_file"](V2.GUARD_DIR / "rc4_loader.exe", carrier / "rc4_loader.exe")
        V2.OPS["copy_file"](V2.C2_DIR / "ra2rc4guard_c2.dll", carrier / "ra2rc4guard_c2.dll")
        V2.apply_bail_mode(carrier / "ra2render.ini", arm["guard"], arm["bail_mode"])

        rec["phase"] = "popen"
        env = dict(__import__("os").environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = V2.OPS["popen"]([str(carrier / "rc4_loader.exe"), "ra2rc4guard_c2.dll"], str(carrier), env)
        rec["loader_pid"] = proc.pid
        t0 = V2.OPS["now"]()

        rec["phase"] = "find_pid"
        pid = None
        for _ in range(200):
            V2.OPS["sleep"](0.1)
            for p, nm in list(V2.OPS["list_procs"]().items()):
                if nm.lower() == "gamemd.exe" and V2._o_under_carrier(p):
                    pid = p
                    break
            if pid:
                break
        if pid is None:
            raise V2.TripFail("gamemd_not_found")
        rec["gamemd_pid"] = pid

        rec["phase"] = "find_window"
        hwnd = None
        while V2.OPS["now"]() - t0 < 60.0:
            hwnd = V2.OPS["find_main_window"](pid)
            if hwnd:
                break
            V2.OPS["sleep"](0.5)
        if not hwnd:
            raise V2.TripFail("no_main_window_60s")
        wpid, wtid = V2.OPS["window_pid"](hwnd)
        if wpid != pid:
            raise V2.TripFail("window_pid_mismatch")
        rec["hwnd"], rec["window_tid"] = hwnd, wtid

        rec["phase"] = "hold"
        hold_tl = []
        th = V2.OPS["now"]()
        while V2.OPS["now"]() - th < HOLD_AFTER_WINDOW:
            hold_tl.append(V2.phase_sentinels(pid))
            V2.OPS["sleep"](1.0)
        rec["hold_tl_n"] = len(hold_tl)
        V2.screenshot_best_effort(out_dir, "pre_close", rec)

        rec["phase"] = "deliver"
        ok_post, err_post = V2.OPS["post_close"](hwnd)
        rec["close_delivery"] = {"post_ok": ok_post, "post_err": err_post, "target_hwnd": hwnd,
                                 "win_pid": wpid, "win_tid": wtid, "t": round(V2.OPS["now"](), 3)}
        if not ok_post:
            raise V2.TripFail("PostMessageW_failed err=%d" % err_post)
        t_close = V2.OPS["now"]()
        rec["closed_at_s"] = round(t_close - t0, 3)

        # ---- watch（E1 主循环节律=0.1 s 同早窗批；闩后⇒1 Hz 慢采样+E2 四轴）----
        rec["phase"] = "watch"
        rows, slow = [], []
        latch = None
        just_latched = False
        win_baseline = None
        last_cpu = None
        last_except_check_t = None
        latch30_shot_done = False
        stop = None
        hs = V2.OPS["open_process"](WATCH_ACCESS, pid)
        if not hs:
            raise V2.TripFail("OpenProcess_watch")
        try:
            while V2.OPS["now"]() < t_close + watch_s:
                res = V2.OPS["wait0"](hs)
                cok, excode = V2.OPS["get_exit_code"](hs)
                row = {"t": round(V2.OPS["now"](), 3), "wait": res,
                       "code": excode if cok and res == V2.WAIT_OBJECT_0 else None, "code_read_ok": cok}
                for nm2, addr2 in (("exitstate", V2.G_EXITSTATE), ("frame", V2.G_FRAME),
                                   ("hwnd", V2.G_HWND), ("singleton", V2.G_SINGLETON),
                                   ("tick", V2.G_TICK)):
                    kind, val = V2.tri_read_u32(hs, addr2)
                    row[nm2] = val if kind == "ok" else {"state": kind}
                rows.append(row)
                if latch is None and row.get("exitstate") == LATCH_VALUE:
                    try:
                        base_cpu, perr = V2.OPS["process_times"](hs)
                        cpu_ok = base_cpu is not None
                        base = {"kernel": base_cpu["kernel"], "user": base_cpu["user"]} if cpu_ok else None
                    except Exception as e:
                        base, cpu_ok, perr = None, False, repr(e)
                    try:
                        win_baseline = [w for w in V2.OPS["enum_windows"](pid) if w["visible"]]
                    except Exception as e:
                        win_baseline = [{"state": "read_fail", "err": repr(e)}]
                    latch = {"row_index": len(rows) - 1, "t": row["t"],
                             "after_close_s": round(row["t"] - t_close, 3),
                             "cpu_baseline": base if cpu_ok else None,
                             "cpu_baseline_state": "ok" if cpu_ok else "read_fail",
                             "cpu_baseline_err": None if cpu_ok else perr,
                             "windows_at_latch": win_baseline,
                             "hook6_at_latch": hook6_tri(hs)}
                    last_cpu = base if cpu_ok else None
                    just_latched = True
                if latch is not None:
                    if not just_latched:
                        # —— E2 慢采样行（逐秒；与配对 close_row 同 t，轴失败态显式落记录）——
                        # 闩行本身不产慢行（已被 close_rows 全量覆盖，且此刻 CPU 基线=同刻⇒假零增量）；
                        # 首个慢行的增量=闩基线→下一秒真实 1 s 区间。
                        srow = {"t": row["t"], "pair_close_row_index": len(rows) - 1}
                        try:
                            cur_cpu, perr2 = V2.OPS["process_times"](hs)
                            if cur_cpu is None:
                                srow["cpu"] = {"state": "read_fail", "err": perr2, "delta_s": None}
                            else:
                                d = cpu_delta(last_cpu, cur_cpu)
                                srow["cpu"] = {"state": "ok", "kernel_100ns": cur_cpu["kernel"],
                                               "user_100ns": cur_cpu["user"], "delta_s": d}
                                last_cpu = cur_cpu
                        except Exception as e:
                            srow["cpu"] = {"state": "api_exception", "err": repr(e), "delta_s": None}
                        srow["hook6"] = hook6_tri(hs)
                        try:
                            ws = V2.OPS["working_set_kb"](hs)
                            srow["ws_kb"] = ws if isinstance(ws, int) else {"state": "read_fail"}
                        except Exception as e:
                            srow["ws_kb"] = {"state": "read_fail", "err": repr(e)}
                        try:
                            vis = [{"hwnd": w["hwnd"], "title": w["title"], "class": w["class"]}
                                   for w in V2.OPS["enum_windows"](pid) if w["visible"]]
                            srow["visible_windows"] = vis
                            new_wins, hits = interaction_hits(vis, win_baseline)
                            if new_wins:
                                srow["new_windows_vs_baseline"] = new_wins
                                srow["interaction_hits"] = hits
                                stop = {"reason": ("interaction_window" if hits else "new_visible_window"),
                                        "t": row["t"], "slow_index": len(slow),
                                        "evidence": {"new_windows": new_wins, "hits": hits}}
                        except Exception as e:
                            srow["visible_windows"] = {"state": "read_fail", "err": repr(e)}
                        if stop is None:
                            due = (last_except_check_t is None or
                                   row["t"] - (last_except_check_t or latch["t"]) >= except_check_every_s)
                            if due:
                                last_except_check_t = row["t"]
                                try:
                                    ex_now = (V2.OPS["sha16"](carrier / "except.txt")
                                              if V2.OPS["isfile"](carrier / "except.txt") else "absent")
                                    srow["except_check"] = {"sha16": ex_now,
                                                            "changed": ex_now != rec["except_before"]}
                                    if ex_now != rec["except_before"]:
                                        stop = {"reason": "except_changed", "t": row["t"],
                                                "slow_index": len(slow),
                                                "evidence": {"before": rec["except_before"], "now": ex_now}}
                                except Exception as e:
                                    srow["except_check"] = {"state": "read_fail", "err": repr(e)}
                                    rec.setdefault("evidence_errors", []).append("exceptcheck:%r" % e)
                        if (not latch30_shot_done
                                and row["t"] - latch["t"] >= latch_shot_after_s):
                            latch30_shot_done = True
                            V2.screenshot_best_effort(out_dir, "latch_plus_30", rec)
                        slow.append(srow)
                    just_latched = False
                if stop:
                    break
                if res == V2.WAIT_OBJECT_0:
                    break
                V2.OPS["sleep"](slow_sleep_s if latch is not None else FAST_SLEEP)
        finally:
            V2.OPS["close_handle"](hs)
        if stop:
            V2.screenshot_best_effort(out_dir, "stop_evidence", rec)
        rec["stop_triggered"] = stop
        rec["close_rows_n"] = len(rows)
        if len(rows) == 0:
            raise V2.TripFail("zero_close_samples")

        e2_summary = summarize_e2(latch, slow)
        (out_dir / "timeline.json").write_text(json.dumps(
            {"hold_tl": hold_tl, "close_rows": rows,
             "_e2": {"params": rec["e2_params"], "latch": latch,
                     "slow_sample_rows": slow, "summary": e2_summary,
                     "stop_triggered": stop}}, ensure_ascii=False), encoding="utf-8")
        V2.screenshot_best_effort(out_dir, "post_close_end", rec)

        # —— E2 段落 _rec（schema：E2 字段显式命名，与 close_rows 原形态隔离）——
        rec["latch_detected"] = bool(latch)
        rec["latch_row_index"] = latch["row_index"] if latch else None
        rec["latch_after_close_s"] = latch["after_close_s"] if latch else None
        rec["slow_sample_rows"] = slow
        rec["slow_rows_n"] = len(slow)
        rec["hook6_state"] = e2_summary.get("hook6_state")
        rec["hook6_state_counts"] = e2_summary.get("hook6_state_counts")
        rec["cpu_delta_median_s"] = e2_summary.get("cpu_delta_median_s")
        rec["ws_delta_kb"] = e2_summary.get("ws_delta_kb")
        rec["e2_fork_label"] = e2_summary.get("e2_fork_label")
        rec["e2_summary"] = e2_summary

        exited = rows[-1]["wait"] == V2.WAIT_OBJECT_0
        rec["exited"] = exited
        if stop:
            rec["exit_kind"] = "stopped_by_condition:" + stop["reason"]
        elif exited:
            rec["exit_kind"] = "natural"
        elif rows[-1]["wait"] == V2.WAIT_TIMEOUT:
            rec["exit_kind"] = "still_running_at_watch_end"
        else:
            # 三态补全（承 v2 fire_arm:730-732；早窗件此分支缺 wait_error 态⇒E12 对齐 v2 纪律，
            # 防 WAIT_FAILED 被误标「挂死仍活」——close_rows 原形态不变，仅标签）
            rec["exit_kind"] = "wait_error:%d" % rows[-1]["wait"]
        rec["exit_after_close_s"] = round(rows[-1]["t"] - t_close, 2) if exited else None
        rec["final_exitcode"] = rows[-1]["code"] if exited else None
    except V2.TripFail as e:
        rec["verdict"] = "FAIL"
        rec["fail"] = str(e)[:300]
    except Exception as e:
        rec["verdict"] = "FAIL"
        rec["fail"] = "unexpected@%s:%r" % (rec.get("phase"), e)
    finally:
        if made_carrier:
            try:
                V2.finalize(rec, carrier, out_dir, proc)
            except Exception as e:
                rec["finalize_leaked_error"] = repr(e)
        else:
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            except Exception:
                pass
    return rec


def extra_preflight():
    """E12 附加预检（真 OS 只读）：两终钉件哈希复验 + 源 ini sha16/size + BOOT 读数。"""
    fails = []
    try:
        verify_frozen_masters()
        print("  [OK] 终钉件 sha256 复验（6afe2711/2e970eec）")
    except Exception as e:
        print("  [RED] 终钉件 sha256：%r" % e)
        fails.append("frozen_masters")
    try:
        b = (V2.GAME_SRC / "ra2render.ini").read_bytes()
        ok = hashlib.sha256(b).hexdigest()[:16] == SRC_INI_SHA16 and len(b) == SRC_INI_SIZE
        print("  [%s] 源 ra2render.ini sha16=%s size=%d（钉 %s/16,496）"
              % ("OK" if ok else "RED", hashlib.sha256(b).hexdigest()[:16], len(b), SRC_INI_SHA16))
        if not ok:
            fails.append("src_ini")
    except Exception as e:
        print("  [RED] 源 ra2render.ini：%r" % e)
        fails.append("src_ini_unreadable")
    try:
        ms = _r_boot_ms()
        print("  [OK] UPTIME(GetTickCount64)=%d ms——批次比较开机墙钟估计，容差2000ms" % ms)
    except Exception as e:
        print("  [RED] BOOT 读数：%r" % e)
        fails.append("boot")
    return fails


def gate_decision(live: bool, approved: bool) -> int:
    """授权硬闸纯函数（发射决策；自检可直接分臂测）。
    非 live ⇒ 0（离线，含 --approved 单给：仅透传闸值不自动跑）；
    live 无 approved ⇒ 3（恒拒）；live+approved ⇒ -1 表示「闸开，交由预检后发射」。"""
    if not live:
        return 0
    if not approved:
        return 3
    return -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--approved", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--trips", type=int, default=2)   # D-11=补 2 趟（P3e 总 n=5）
    a = ap.parse_args()
    if a.selftest:
        spec = importlib.util.spec_from_file_location(
            "e12_selftest", HERE / "_drive_c2_x_e12_selftest.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.run_suite()
    if a.preflight:
        extend_ops_real()
        fails = V2.preflight() + extra_preflight()
        print("preflight: %s" % ("全过" if not fails else "红 %s" % fails))
        return 0 if not fails else 2
    g = gate_decision(a.live, a.approved)
    if g == 0:
        # ★ 离线（含 --approved 单给）：闸值透传但不自动跑
        print("离线：本件仅 --live+--approved 发射（E1+E2 合批，D-11 裁决权=用户）。"
              + (" 已收 --approved 闸值=透传，不自动跑。" if a.approved else ""))
        return 0
    if g == 3:
        print("!! 需 --approved（D-11 E1+E2 合批用户批准闸值）——--live 无授权恒拒")
        return 3
    extend_ops_real()
    fails = V2.preflight() + extra_preflight()
    if fails:
        print("!! 预检拦：%s" % fails)
        return 2
    boot_ref = capture_boot()
    last = None
    for i in range(1, a.trips + 1):
        r = run_trip(i, boot_ref)
        last = r
        print("%s T%d verdict=%s exited=%s closed_at=%s latch=%s fork=%s exit_kind=%s fail=%s" % (
            r["trip_tag"], i, r["verdict"], r.get("exited"), r.get("closed_at_s"),
            r.get("latch_detected"), r.get("e2_fork_label"), r.get("exit_kind"), r.get("fail")))
        if r["verdict"] not in ("OK", "PARTIAL") or r.get("stop_triggered"):
            print("!! 趟非 OK 或触通用停止 ⇒ 批次停（只留证据）")
            break
    return 0 if (last and last["verdict"] in ("OK", "PARTIAL")) else 1


if __name__ == "__main__":
    sys.exit(main())
