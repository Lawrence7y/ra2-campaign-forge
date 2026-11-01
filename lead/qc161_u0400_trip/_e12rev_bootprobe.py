# -*- coding: utf-8 -*-
"""_e12rev_bootprobe.py — 复核点5：跨趟 BOOT 断言在真实（推进）时钟下的形态。

核心问题：GetTickCount64=系统**已运行毫秒数**（单调递增的 uptime），不是「本次开机时刻常量」。
main() 只捕获一次 boot_ref 且不更新 ⇒ 第二趟 run_trip 读到的 boot_ms 必然≈第一趟读数+第一趟耗时(ms)。
若第一趟耗时≈137 s，则 T2 的 boot_ms 比 boot_ref 大约 137000 ms ⇒ boot_changed 误拦。

A) 直接证明 GetTickCount64 单调跨 tick 变化（真实 OS，两次读数夹一段实测耗时）；
B) 虚拟推进时钟：按 main() 原样串行两趟（boot_ref 捕获一次不更新），st 时钟随 sleep 推进，
   boot_ms=lambda: st['t']*1000 ⇒ 复现 T1≈137s 后再跑 T2 的判据结果。
零真机、零发射、只读被复核件。
"""
import ctypes
import json
import sys
import time
from pathlib import Path

HERE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip")
sys.path.insert(0, str(HERE))

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.GetTickCount64.restype = ctypes.c_ulonglong


def part_a():
    print("=== A) 真实 OS：GetTickCount64 是单调 uptime，跨 15.6ms tick 必变 ===")
    # 取两次读数，中间睡 ~20ms（>1 tick）
    a = k32.GetTickCount64()
    time.sleep(0.02)
    b = k32.GetTickCount64()
    print("  睡 20ms 前=%d 后=%d 差=%d ms ⇒ 非零即『读数变了』" % (a, b, b - a))
    # 睡 1.37s（模拟第一趟耗时的千分之一）看增量
    c = k32.GetTickCount64()
    time.sleep(1.37)
    d = k32.GetTickCount64()
    print("  睡 1.37s 前=%d 后=%d 差=%d ms（真实一趟≈137000ms ⇒ 差≈137000）" % (c, d, d - c))
    print("  ⇒ 结论：boot_ms 随时间单调增长，只要两趟之间有任何墙钟流逝，"
          "以『相等』为『同会话』判据必假")


def part_b():
    print("=== B) 虚拟推进时钟：main() 的 boot_ref 用法串行两趟（boot_ref 不更新）===")
    import _drive_c2_x_e12_selftest as ST
    import _drive_c2_x_e12 as D

    ops = ST.make_ops(mode="hang", v2mod=ST.V2)
    st = ops["__st"]
    ops["boot_ms"] = lambda: int(st["t"] * 1000)      # uptime 同构：读数随 (虚拟) 时间推进
    saved = ST._install(ops, ST.V2)
    recs = []
    try:
        # —— 与 _drive_c2_x_e12.main():602-613 逐句同形 ——
        boot_ref = {"boot_ms": D.V2.OPS["boot_ms"]()}
        for i in range(1, 3):
            # 模拟第一趟真实耗时：第二趟前把虚拟时钟推 137s（承 part_b 无真实发射，直接推 st）
            if i == 2:
                st["t"] += 137.0
            r = D.run_trip(i, boot_ref)
            recs.append({"trip": i, "verdict": r["verdict"], "fail": r.get("fail"),
                         "boot_ms_at_start": r.get("boot_ms_at_start"),
                         "boot_ref": boot_ref["boot_ms"]})
            if r["verdict"] not in ("OK", "PARTIAL") or r.get("stop_triggered"):
                recs.append({"batch_break_at_trip": i})
                break
    finally:
        ST._uninstall(saved)
    for row in recs:
        print("  " + json.dumps(row, ensure_ascii=False)[:240])
    t2_blocked = any(x.get("trip") == 2 and "boot_changed" in str(x.get("fail", "")) for x in recs)
    print("  ⇒ 结论：T2 %s" % ("被 boot_changed 误拦（若两趟真实间隔>0 即必然）"
                               if t2_blocked else "未被拦"))


if __name__ == "__main__":
    part_a()
    print()
    part_b()
