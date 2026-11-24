# -*- coding: utf-8 -*-
"""_cii_hardcode9.py — 独立验证「硬编码 9」能否被 5 条不变量门槛发现。

只写 tempfile.mkdtemp(prefix="_cii_hard_")；不改既有产物/只读域；零真机、零采样代码。
CASE A: baseline 副本（plus_match 真值恰为 9）
CASE B: merged 投影（真值 18）却把 totals.plus_match 硬编码为 9 —— 真·故意改坏
CASE C: merged 投影写回正确 18（作为对照）
对 B 实跑 4 个既有 _f2w_* 消费者（沙箱副本，路径重定向）+ 本会话 _cii_checks.py。
"""
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(r"D:\Project\ra2-campaign-forge")
R11 = REPO / "lead" / "r11_f2_fix_20261109"
W = REPO / "lead" / "count_invariant_20261109"
CMP = R11 / "_f2_compare_out.json"
MERGED = pathlib.Path(r"C:\Users\Administrator\AppData\Local\Temp\_ci_merged_r8prxhqj\merged_projection.json")
PY, FLAGS = sys.executable, ["-I", "-X", "utf8"]
TMP = pathlib.Path(tempfile.mkdtemp(prefix="_cii_hard_"))
print("TEMP:", TMP)

consumers = ["_f2w_checks.py", "_f2w_pass.py", "_f2w_extract.py", "_f2w_final.py"]


def run(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def sandbox(name, doc):
    d = TMP / name
    d.mkdir(parents=True)
    (d / "_f2_compare_out.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    shutil.copy2(R11 / "_f2_repro_out.json", d / "_f2_repro_out.json")
    for c in consumers:
        t = (R11 / c).read_text(encoding="utf-8")
        t = t.replace(str(R11), str(d))
        t = t.replace(str(R11).replace("\\", "\\\\"), str(d).replace("\\", "\\\\"))
        (d / c).write_text(t, encoding="utf-8")
    return d


def consumers_on(d):
    out = []
    for c in consumers:
        rc, o = run([PY] + FLAGS + [str(d / c)])
        notable = [l.strip() for l in o.splitlines()
                   if "一致条数" in l or "R11 PASS" in l or "rows=" in l][:2]
        out.append("%s rc=%d output_has_totals=%s notable=%r"
                   % (c, rc, "totals" in o, notable))
    return out


def gate_on(d, expect_merged=False):
    cmd = [PY] + FLAGS + [str(W / "_cii_checks.py"), str(d / "_f2_compare_out.json")]
    if expect_merged:
        cmd.append("--expect-merged")
    rc, o = run(cmd)
    alerts = [l.strip() for l in o.splitlines()
              if l.strip().startswith("-") or "ALERT" in l or "OK violations=0" in l]
    return rc, alerts


print()
print("=== CASE A: baseline 副本，plus_match=9（等于真值） ===")
a = sandbox("A_baseline9", json.loads(CMP.read_text(encoding="utf-8")))
for l in consumers_on(a):
    print("  " + l)
print("  gate rc/alerts =", gate_on(a))

print()
print("=== CASE B: merged 投影（真值 18）硬编码 totals.plus_match=9 ===")
docB = json.loads(MERGED.read_text(encoding="utf-8"))
docB["totals"]["plus_match"] = 9
b = sandbox("B_merged_hard9", docB)
for l in consumers_on(b):
    print("  " + l)
rc, alerts = gate_on(b, expect_merged=True)
print("  _cii_checks --expect-merged rc=%d alerts=%r" % (rc, alerts))
rc2, alerts2 = gate_on(b, expect_merged=False)
print("  _cii_checks (baseline mode) rc=%d alerts=%r" % (rc2, alerts2))

print()
print("=== CASE C: merged 投影 totals 写回正确 18 ===")
docC = json.loads(MERGED.read_text(encoding="utf-8"))
c3 = sandbox("C_merged_correct18", docC)
for l in consumers_on(c3)[:2]:
    print("  " + l)
print("  gate --expect-merged rc/alerts =", gate_on(c3, expect_merged=True))
