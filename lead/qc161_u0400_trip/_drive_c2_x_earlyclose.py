# -*- coding: utf-8 -*-
"""_drive_c2_x_earlyclose.py — 早窗关窗趟（菜单态·加载早期，P3 配置）。

存在性理由（10-28 重复批后离线对勘）：旧会话 MAIN 两趟（c2ab 驱动，launch+~6.6 s 关窗）
15.5 s 自然退+exitstate 闩 1；新会话 P3m 两趟（v2 驱动，窗现+35 s 就绪闸关窗≈44.5 s）不退。
两批配置相同（Guard=1+Bail=1+同 DLL），候选差异变量=**关窗时机/加载深度** 与驱动代际。
本件=单变量裁决趟之一：用 **v2 同代组件**（import 终钉模块，复用其 bind_real_ops/预检/
载体纪律/finalize/三态读/截图），但按旧 MAIN 协议**窗现后 ~6 s 即关**，其余不变。

★ 不改 _drive_c2_x_probe_v2.py 一个字节（终钉 6afe2711 保持）。
★ 发射硬闸：本件自带 EARLY_APPROVED 标志=用户 10-28「真机继续」口头授权范围
  （P3m 矛盾定因微批）；--live 缺省仍被拦，须显式 --approved。
零新 Hook；只 PostMessageW WM_CLOSE（与既有趟同）；不写状态；清理=finalize。
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _drive_c2_x_probe_v2 as V2  # 终钉模块复用（导入无副作用：main 有 __main__ 门）

TRIP_TAG = "P3e_EARLY_MENU"
HOLD_AFTER_WINDOW = 6.0     # 旧 MAIN 协议近似：窗现后 ~6 s 关窗（其 closed_at≈launch+6.6 s）
WATCH_S = 120.0


def run_trip() -> dict:
    stamp = time.strftime("%Y%m%dT%H%M%S")
    arm = {"key": "P3e", "tag": TRIP_TAG, "inject": True, "guard": 1,
           "bail_mode": "explicit1", "mode": "menu", "note": "早窗关窗趟（v2 组件+旧协议时机）"}
    # 复用 v2 的目录/命名与载体纪律
    out_dir = V2.MYCARD / ("%s_9001_%s" % (stamp, arm["tag"]))
    carrier = out_dir / "ct" / ("c" + "0" * 9)
    V2.CURRENT_CARRIER[0] = carrier
    rec = {"trip_tag": arm["tag"], "mode": arm["mode"], "note": arm["note"],
           "out_dir": str(out_dir), "verdict": "OK", "phase": "init",
           "watch_s": WATCH_S, "protocol": "early-close (window+%.1fs)" % HOLD_AFTER_WINDOW}
    proc = None
    made_carrier = False
    try:
        rec["phase"] = "precheck"
        if any(nm.lower() in ("gamemd.exe", "rc4_loader.exe") for nm in V2.OPS["list_procs"]().values()):
            raise V2.TripFail("precheck_residual_procs")
        V2._precheck_shas()
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
        rec["window_at_s"] = round(V2.OPS["now"]() - t0, 2)
        wpid, wtid = V2.OPS["window_pid"](hwnd)
        if wpid != pid:
            raise V2.TripFail("window_pid_mismatch")
        rec["hwnd"], rec["window_tid"] = hwnd, wtid

        # 早窗协议：窗现后固定 hold（不跑就绪闸×3）；hold 期 1 Hz 采样留档（观察加载早期形态）
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

        rec["phase"] = "watch"
        rows = []
        hs = V2.OPS["open_process"](0x0400 | 0x0010 | 0x100000, pid)
        if not hs:
            raise V2.TripFail("OpenProcess_watch")
        try:
            while V2.OPS["now"]() < t_close + WATCH_S:
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
                if res == V2.WAIT_OBJECT_0:
                    break
                V2.OPS["sleep"](0.1)
        finally:
            V2.OPS["close_handle"](hs)
        rec["close_rows_n"] = len(rows)
        if len(rows) == 0:
            raise V2.TripFail("zero_close_samples")
        (out_dir / "timeline.json").write_text(
            json.dumps({"hold_tl": hold_tl, "close_rows": rows}, ensure_ascii=False), encoding="utf-8")
        exited = rows[-1]["wait"] == V2.WAIT_OBJECT_0
        rec["exited"] = exited
        rec["exit_kind"] = "natural" if exited else "still_running_at_watch_end"
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--approved", action="store_true")
    a = ap.parse_args()
    if not a.live:
        print("离线：本件仅 --live 发射（早窗协议单趟）。不载 h7/探针以保零副作用。")
        return 0
    if not a.approved:
        print("!! 需 --approved（用户 10-28 真机继续授权范围=P3m 矛盾定因微批）")
        return 3
    V2.bind_real_ops()
    fails = V2.preflight()
    if fails:
        print("!! 预检拦：%s" % fails)
        return 2
    r = run_trip()
    print("%s verdict=%s exited=%s closed_at=%s exit_after=%s code=%s fail=%s" % (
        r["trip_tag"], r["verdict"], r.get("exited"), r.get("closed_at_s"),
        r.get("exit_after_close_s"), r.get("final_exitcode"), r.get("fail")))
    return 0 if r["verdict"] in ("OK", "PARTIAL") else 1


if __name__ == "__main__":
    sys.exit(main())
