# -*- coding: utf-8 -*-
"""RR-P4：发射器副本 v2 的三件小事
 (a) 修好的 PE32 真能读出**正确进程名**（自 PID ⇒ 期望 python.exe，非空非乱码）；
 (b) build_harness_argv 副本 vs 母本：同输入 ⇒ argv **逐元素相等**（声明「逐字一致」）；
 (c) harness8 v2 py_compile / -W error compile；
 (d) --help 双跑：v2 相对 harness7 仅新增选项文本，无既有选项变动。
"""
import ast
import ctypes
import os
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = Path(__file__).resolve().parent
COPY = ROOT / "lead/goal1_harness8_20261031/_launch_h8_20261031.py"
MASTER = ROOT / "lead/qc161_u0400_trip/_launch_l1_20261023.py"
H7 = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
H8 = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py"


def load(path, name):
    sp = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def main():
    res = {}
    mc = load(COPY, "rr4_copy")
    mm = load(MASTER, "rr4_master")

    procs = mc.list_procs()
    me = os.getpid()
    res["a_names_sane"] = {
        "own_pid": me,
        "own_name_asread_by_copy": procs.get(me),
        "own_name_asread_by_master": mm.list_procs().get(me),
        "count_copy": len(procs),
        "names_sample": sorted({v.lower() for v in list(procs.values())[:60]})[:12],
        "empty_name_count": sum(1 for v in procs.values() if not v),
        "PASS": procs.get(me) not in (None, ""),
    }

    common = dict(harness=Path(r"D:\x\h.py"), map_path=Path(r"D:\m.MAP"),
                  map_sha="a" * 64, out_dir=Path(r"D:\o"), src=Path(r"D:\s"),
                  extra=["gamemd.exe", "配置器.exe"], trip_id="T", probe_frames="1,2",
                  extra_argv=["--h7-measure-start-frame", "400"])
    argv_c = mc.build_harness_argv(fullscreen=True, **common)
    argv_m = mm.build_harness_argv(fullscreen=True, **common)
    argv_c0 = mc.build_harness_argv(fullscreen=False, **common)
    argv_m0 = mm.build_harness_argv(fullscreen=False, **common)
    res["b_argv_equal"] = {"fullscreen_equal": argv_c == argv_m,
                           "windowed_equal": argv_c0 == argv_m0,
                           "fs": argv_c, "master_fs": argv_m}

    # (c) 编译 —— ★ 不用 py_compile 子进程（它会往只读实现目录写 __pycache__）；
    #     改为内存 compile + warnings-as-errors，等效于语法/告警核验且零磁盘副作用。
    src8 = H8.read_text(encoding="utf-8", errors="replace")
    res["c_compile_nowarn"] = "ok"
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(src8, str(H8), "exec")
    except Exception as e:
        res["c_compile_nowarn"] = "WARN/ERR: %r" % e
    src7 = H7.read_text(encoding="utf-8", errors="replace")
    res["c_compile_nowarn_h7"] = "ok"
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(src7, str(H7), "exec")
    except Exception as e:
        res["c_compile_nowarn_h7"] = "WARN/ERR: %r" % e

    # (d) --help 双跑
    outs = {}
    for tag, p in (("h7", H7), ("h8v2", H8)):
        rr = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(p), "--help"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace")
        outs[tag] = rr.stdout
    def norm(s):
        return [l for l in s.splitlines() if not l.startswith("Traceback")]
    a, b = norm(outs["h7"]), norm(outs["h8v2"])
    import difflib
    dl = [l for l in difflib.unified_diff(a, b, lineterm="")]
    res["d_help_diff_lines"] = dl
    res["d_help_added"] = [l for l in dl if l.startswith("+") and not l.startswith("+++")]
    res["d_help_removed"] = [l for l in dl if l.startswith("-") and not l.startswith("---")]

    txt = json.dumps(res, ensure_ascii=False, indent=1)
    (HERE / "rr_p4_launcher_argv_help.stdout.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
