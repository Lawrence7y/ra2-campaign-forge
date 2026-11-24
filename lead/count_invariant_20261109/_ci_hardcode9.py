# -*- coding: utf-8 -*-
"""_ci_hardcode9.py — 第四步(c)：把 plus_match 硬编码成 9，实跑现有测试看能否发现。

构造两份临时 JSON：
  A) baseline-copy 且 totals.plus_match 恰为 9（与真值相同）→ 字节与原件不同，但语义无误
  B) merged 投影（真值 18）却把 totals.plus_match 写成 9（真·故意改坏）
对两者实跑：
  1) 四个既有 JSON 消费者（_f2w_checks/_f2w_pass/_f2w_extract/_f2w_final）指向副本
  2) 三个既有指纹锁脚本（_f2d*_fpcheck.py）实跑，看 compare_out 指纹是否报 DRIFT
  3) 本任务 _ci_checks.py 跑同一份副本
所有副本落 tempfile.mkdtemp；不改既有产物。零真机、零采样代码。
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
MERGED = pathlib.Path(r"C:\Users\Administrator\AppData\Local\Temp\_ci_merged_dcdxi1lv\merged_projection.json")
PY = sys.executable
PFLAGS = ["-I", "-X", "utf8"]

tmp = pathlib.Path(tempfile.mkdtemp(prefix="_ci_hard_"))
print("TEMP:", tmp)

# 复制 4 个消费者 + 3 个指纹锁到 temp（不改原件），把里面的路径改指向 temp 副本
consumers = ["_f2w_checks.py", "_f2w_pass.py", "_f2w_extract.py", "_f2w_final.py"]
fpchecks = [REPO / "lead" / "f2d_rootcause_20261109" / "_f2d_fpcheck.py",
            REPO / "lead" / "f2d_rootcause_20261109" / "_f2dw_fpcheck.py",
            REPO / "lead" / "f2d_rootcause_20261109" / "_f2dv_fpcheck.py"]


def make_sandbox(name):
    d = tmp / name
    d.mkdir(parents=True)
    # 假 JSON 放同目录，名字必须叫 _f2_compare_out.json，消费者才能读
    return d


def run(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def consumer_sandbox(sandbox):
    """把消费者复制进 sandbox，并把 JSON 路径重定向到 sandbox/_f2_compare_out.json
    （JSON 已由调用方预先写好；此处不再 copy，避免自拷贝 WinError 32）"""
    # _f2w_extract.py 另读 _f2_repro_out.json，一并复制以便消费者能跑完
    shutil.copy2(R11 / "_f2_repro_out.json", sandbox / "_f2_repro_out.json")
    for c in consumers:
        t = (R11 / c).read_text(encoding="utf-8")
        t = t.replace(str(R11), str(sandbox))
        t = t.replace(str(R11).replace("\\", "\\\\"), str(sandbox).replace("\\", "\\\\"))
        (sandbox / c).write_text(t, encoding="utf-8")


print()
print("=== CASE A: baseline 副本，plus_match=9（与真值相同，故意改坏无从体现） ===")
a = make_sandbox("A_baseline9")
docA = json.loads(CMP.read_text(encoding="utf-8"))
docA["totals"]["plus_match"] = 9  # 硬编码 9，恰好等于真值
(a / "_f2_compare_out.json").write_text(
    json.dumps(docA, ensure_ascii=False, indent=1), encoding="utf-8")
consumer_sandbox(a)
for c in consumers:
    rc, o = run([PY] + PFLAGS + [str(a / c)])
    print("  %s rc=%d  output_has_totals=%s" % (c, rc, "totals" in o))
print("  --- 指纹锁实跑（对原件，非副本；A 副本不改原件） ---")
for fp in fpchecks:
    rc, o = run([PY] + PFLAGS + [str(fp)])
    hit = [l for l in o.splitlines() if "_f2_compare_out.json" in l]
    print("  %s rc=%d  compare_out_line=%r" % (fp.name, rc, hit[:1]))

print()
print("=== CASE B: merged 投影（真值 18），硬编码 totals.plus_match=9 ===")
b = make_sandbox("B_merged_hard9")
docB = json.loads(MERGED.read_text(encoding="utf-8"))
docB["totals"]["plus_match"] = 9  # 真·故意改坏：应为 18
(b / "_f2_compare_out.json").write_text(
    json.dumps(docB, ensure_ascii=False, indent=1), encoding="utf-8")
consumer_sandbox(b)
for c in consumers:
    rc, o = run([PY] + PFLAGS + [str(b / c)])
    print("  %s rc=%d  output_has_totals=%s  verdict_lines=%r" %
          (c, rc, "totals" in o,
           [l.strip() for l in o.splitlines() if "PASS:" in l or "一致条数" in l][:2]))
print("  --- _ci_checks.py 对 B ---")
rc, o = run([PY] + PFLAGS + [str(W / "_ci_checks.py"), str(b / "_f2_compare_out.json")])
print("  _ci_checks rc=%d" % rc)
for l in o.splitlines():
    print("   ", l)

print()
print("=== CASE C: merged 投影写回 totals=18（正确值），看现有消费者是否区分 merged/unique ===")
c3 = make_sandbox("C_merged_correct18")
shutil.copy2(MERGED, c3 / "_f2_compare_out.json")
consumer_sandbox(c3)
rc, o = run([PY] + PFLAGS + [str(c3 / "_f2w_checks.py")])
print("  _f2w_checks rc=%d  sha逐字一致条数 line = %r" %
      (rc, [l.strip() for l in o.splitlines() if "一致条数" in l]))
rc, o = run([PY] + PFLAGS + [str(c3 / "_f2w_pass.py")])
print("  _f2w_pass rc=%d  verdict line = %r" %
      (rc, [l.strip() for l in o.splitlines() if "R11 PASS" in l]))
rc, o = run([PY] + PFLAGS + [str(W / "_ci_checks.py"), str(c3 / "_f2_compare_out.json")])
print("  _ci_checks rc=%d  alerts = %r" %
      (rc, [l.strip() for l in o.splitlines() if l.strip().startswith("-") or "ALERT" in l or "OK " in l]))
