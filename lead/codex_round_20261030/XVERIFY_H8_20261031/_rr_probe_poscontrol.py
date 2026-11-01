# -*- coding: utf-8 -*-
"""RR-P6：R-1 修复的**正控**（A8 门禁真能红）+ Y-5 死常量/_H8_STATE 读写面复核。
   零真机：gamemd.exe 条目由桩注入，绝不启动游戏。
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = Path(__file__).resolve().parent
COPY = ROOT / "lead/goal1_harness8_20261031/_launch_h8_20261031.py"
MASTER = ROOT / "lead/qc161_u0400_trip/_launch_l1_20261023.py"
H8 = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py"


def load(path, name):
    sp = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def main():
    res = {}
    m = load(COPY, "rr6_copy")
    real = m.list_procs
    # 正控 1：桩入两个游戏进程 ⇒ game_procs 非空 ⇒ A8 got != "0" ⇒ 预检能红
    m.list_procs = lambda: {8801: "gamemd.exe", 8802: "RA2LOADER.EXE",
                            8803: "python.exe"}
    gp = m.game_procs()
    res["positive_control_game_procs"] = {"got": gp, "A8_value": str(len(gp)),
                                          "A8_would_fail": str(len(gp)) != "0"}
    m.list_procs = lambda: {8801: "gamemd.exe"}
    res["positive_control_single"] = {"A8_value": str(len(m.game_procs())),
                                      "A8_would_fail": str(len(m.game_procs())) != "0"}
    m.list_procs = real
    res["real_state_now"] = {"A8_value": str(len(m.game_procs())),
                             "PASS_gate_satisfied_by_no_game": len(m.game_procs()) == 0}

    # 母本对照（同一台机、同一时刻）
    mm = load(MASTER, "rr6_master")
    res["master_vs_copy_same_snapshot"] = {"master_count": len(mm.list_procs()),
                                           "copy_count": len(m.list_procs()),
                                           "fields_equal": [f[0] for f in mm.PE32._fields_] ==
                                                            [f[0] for f in m.PE32._fields_]}

    # Y-5 复核：H8_FRAME_WAIT_HZ / _H8_STATE 的读写面
    src = H8.read_text(encoding="utf-8", errors="replace")
    lines = src.splitlines()
    res["y5_H8_FRAME_WAIT_HZ"] = [
        {"line": i + 1, "text": l.strip()[:110]}
        for i, l in enumerate(lines) if "H8_FRAME_WAIT_HZ" in l]
    res["y5__H8_STATE"] = [
        {"line": i + 1, "mode": ("write" if '["frame_wait"] =' in l else "read?"),
         "text": l.strip()[:110]}
        for i, l in enumerate(lines) if "_H8_STATE" in l]
    # 是否存在 _H8_STATE 的**读取**点（写点形如 _H8_STATE["frame_wait"] = ）
    reads = [l for l in lines if "_H8_STATE" in l and '_H8_STATE["frame_wait"] =' not in l]
    res["y5__H8_STATE_nonwrite_lines"] = reads

    # H8_OFFSET_MAX_FRAMES 引用面（v2 新增，须有真实引用）
    res["H8_OFFSET_MAX_FRAMES_lines"] = [
        {"line": i + 1, "text": l.strip()[:100]}
        for i, l in enumerate(lines) if "H8_OFFSET_MAX_FRAMES" in l]

    txt = json.dumps(res, ensure_ascii=False, indent=1)
    (HERE / "rr_p6_poscontrol_y5.stdout.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
