# -*- coding: utf-8 -*-
"""_writer_first_needle.py — 只删第一根针的对称性（本撰写会话实跑）
编排方【复核】④ 自报已验；此处撰写员独立实跑一次，不采信报告结论。
零真机、零采样代码；只在写域 sandbox/_writer_fn/ 内生成副本并驱动。
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
SRC = REPO / "lead"
OUT = SRC / "andk_rerun_20261109" / "sandbox" / "_writer_fn"

CFG = {
    "d27": dict(dir="d27_ruling_20261106", check="check_d27.py", ruling="RULING_D27.md",
                first="外推", second="卡顿不存在", layout="cwd"),
    "d28": dict(dir="d28_ruling_20261106", check="check_d28.py", ruling="RULING_D28.md",
                first="历史数字", second="1681", layout="parents2"),
    "d29": dict(dir="d29_ruling_20261106", check="check_d29.py", ruling="RULING_D29.md",
                first="互斥", second="前提", layout="same"),
    "d30": dict(dir="d30_ruling_20261106", check="check_d30.py", ruling="RULING_D30.md",
                first="93.98", second="误报率", layout="same"),
}


def run(gate, which):
    c = CFG[gate]
    d = SRC / c["dir"]
    root = OUT / gate / which
    if root.exists():
        shutil.rmtree(root)
    if c["layout"] == "parents2":
        sdir, idir = root / "a" / "b", root / "lead" / c["dir"]
    elif c["layout"] == "cwd":
        sdir, idir = root, root / "lead" / c["dir"]
    else:
        sdir = idir = root
    sdir.mkdir(parents=True, exist_ok=True)
    idir.mkdir(parents=True, exist_ok=True)
    sb = (d / c["check"]).read_bytes()
    sp = sdir / c["check"]
    sp.write_bytes(sb)
    r = (d / c["ruling"]).read_bytes()
    f = (d / "FACTCHECK.md").read_bytes()
    removed = ""
    if which != "A":
        needle = c[which]
        n = r.decode("utf-8").count(needle)
        assert n > 0, (gate, which, needle)
        r = r.decode("utf-8").replace(needle, "").encode("utf-8")
        removed = "%s x%d" % (needle, n)
    (idir / c["ruling"]).write_bytes(r)
    (idir / "FACTCHECK.md").write_bytes(f)
    p = subprocess.run([sys.executable, "-I", "-X", "utf8", str(sp)],
                       cwd=str(root), capture_output=True)
    return dict(gate=gate, which=which, removed=removed,
                cmd='"%s" -I -X utf8 "%s"' % (sys.executable, sp),
                cwd=str(root), exit=p.returncode,
                stdout=p.stdout.decode("utf-8", "replace"),
                stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),
                script_sha256=hashlib.sha256(sb).hexdigest(),
                ruling_sha256=hashlib.sha256(r).hexdigest())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rows = []
    for g in ("d27", "d28", "d29", "d30"):
        a = run(g, "A")
        fst = run(g, "first")
        snd = run(g, "second")
        rows += [a, fst, snd]
        print("=== %s ===" % g)
        for x in (a, fst, snd):
            print("  %-6s removed=%-22s EXIT=%d stdout=%r" %
                  (x["which"], x["removed"] or "(none)", x["exit"], x["stdout"]))
        print("  A_vs_first  stdout_identical=%s ; A_vs_second stdout_identical=%s" %
              (a["stdout"] == fst["stdout"], a["stdout"] == snd["stdout"]))
        print("  first  EXIT=%d PASS_after_kill_first=%s" % (fst["exit"], fst["exit"] == 0))
        print("  second EXIT=%d PASS_after_kill_second=%s" % (snd["exit"], snd["exit"] == 0))
    import json
    (SRC / "andk_rerun_20261109" / "_writer_first_needle.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FIRST_NEEDLE_SYMMETRY_ALL_STILL_PASS = %s" %
          all(r["exit"] == 0 for r in rows if r["which"] in ("first", "second")))
