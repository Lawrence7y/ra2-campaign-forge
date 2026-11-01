# -*- coding: utf-8 -*-
"""_e12rev_gates.py — 复核点3/5：母版哈希拒载门（真子进程·临时目录副本）+ 闩时枚举瞬断基线形态。

零真机、零发射：变异/篡改只发生在 tempfile 副本；被复核件与冻结母本只读。
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip")
sys.path.insert(0, str(HERE))


def test_tampered_master_gate():
    """把母版副本改 1 字节 ⇒ E12 件加载必须 RuntimeError 拒载；且不得有任何 popen/进程动作。"""
    print("=== 门1：母版哈希篡改 ⇒ 拒载（真子进程）===")
    for target in ("_drive_c2_x_probe_v2.py", "_drive_c2_x_earlyclose.py"):
        d = Path(tempfile.mkdtemp(prefix="e12rev_gate_"))
        try:
            for nm in ("_drive_c2_x_e12.py", "_drive_c2_x_probe_v2.py", "_drive_c2_x_earlyclose.py"):
                shutil.copy2(HERE / nm, d / nm)
            p = d / target
            b = bytearray(p.read_bytes())
            b[-1] ^= 0x01                      # 末字节翻转（不改语义，仅破哈希）
            p.write_bytes(bytes(b))
            r = subprocess.run([sys.executable, str(d / "_drive_c2_x_e12.py")],
                               capture_output=True, cwd=str(d), timeout=120)
            out = r.stdout.decode("utf-8", "replace")
            err = r.stderr.decode("utf-8", "replace")
            refused = r.returncode != 0 and "frozen_master_mismatch" in (err + out)
            no_launch = "gamemd" not in out and "popen" not in err.lower()
            print("  target=%s rc=%d 拒载=%s 零动作=%s" % (target, r.returncode, refused, no_launch))
            print("    err 尾行=%s" % err.strip().splitlines()[-1][:150] if err.strip() else "    (无 stderr)")
        finally:
            shutil.rmtree(d, ignore_errors=True)


def test_import_gate_via_selftest_entry():
    """--selftest 入口在母版被篡改时同样须拒载（自检件自带 rc=4 门）。"""
    print("=== 门2：篡改母版 ⇒ 自检件 rc=4 拒载 ===")
    d = Path(tempfile.mkdtemp(prefix="e12rev_gate2_"))
    try:
        for nm in ("_drive_c2_x_e12.py", "_drive_c2_x_probe_v2.py", "_drive_c2_x_earlyclose.py",
                   "_drive_c2_x_e12_selftest.py"):
            shutil.copy2(HERE / nm, d / nm)
        p = d / "_drive_c2_x_probe_v2.py"
        p.write_bytes(p.read_bytes() + b"\n#tamper\n")
        r = subprocess.run([sys.executable, str(d / "_drive_c2_x_e12_selftest.py")],
                           capture_output=True, cwd=str(d), timeout=120)
        print("  rc=%d（预期 4）stdout=%s" % (
            r.returncode, r.stdout.decode("utf-8", "replace").strip()[:120]))
        print("  零游戏动作=%s" % ("gamemd" not in r.stdout.decode("utf-8", "replace")))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_enum_transient_at_latch():
    """闩时刻枚举瞬断（基线 read_fail）+ 其后枚举恢复 ⇒ 主窗是否被误判「新可见窗」而保守停。"""
    print("=== 门3：闩时枚举瞬断⇒基线缺失形态（内存替身，不落盘）===")
    import _drive_c2_x_e12_selftest as ST
    import _drive_c2_x_e12 as D

    ops = ST.make_ops(mode="hang", v2mod=ST.V2)
    st = ops["__st"]
    inner_enum = ops["enum_windows"]

    def flaky_enum(pid):
        # 仅在「关窗已投递且尚未产慢行」的那一次（=闩行基线枚举）抛；其余恢复
        if st["t_close"] is not None and st["t"] <= st["t_close"] + 1.05:
            raise OSError("EnumWindows transient")
        return inner_enum(pid)

    ops["enum_windows"] = flaky_enum
    saved = ST._install(ops, ST.V2)
    try:
        rec = D.run_trip(trip_index=1, watch_s=10.0, slow_sleep_s=1.0,
                         latch_shot_after_s=2.0, except_check_every_s=1.0)
        try:
            tl = json.loads((Path(rec["out_dir"]) / "timeline.json").read_text(encoding="utf-8"))
        except Exception as e:
            tl = {"__unreadable": repr(e)}
    finally:
        ST._uninstall(saved)
    e2 = (tl or {}).get("_e2") or {}
    latch = e2.get("latch") or {}
    stop = rec.get("stop_triggered")
    print("  verdict=%s slow_rows=%s" % (rec.get("verdict"), rec.get("slow_rows_n")))
    print("  latch.windows_at_latch=%s" % json.dumps(latch.get("windows_at_latch"), ensure_ascii=False)[:120])
    print("  stop_triggered=%s" % json.dumps(stop, ensure_ascii=False)[:220])
    first = (e2.get("slow_sample_rows") or [{}])[0]
    print("  首慢行 new_windows_vs_baseline=%s" % json.dumps(
        first.get("new_windows_vs_baseline"), ensure_ascii=False)[:160])


if __name__ == "__main__":
    test_tampered_master_gate()
    test_import_gate_via_selftest_entry()
    test_enum_transient_at_latch()
