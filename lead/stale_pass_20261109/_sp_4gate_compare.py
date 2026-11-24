# -*- coding: utf-8 -*-
# 四件门禁「基线 vs 坏针注射」对照，全部绝对路径 + python -I -X utf8
# 只读驱动：不写任何文件，结果走 stdout
import subprocess, sys, hashlib

PAIRS = [
    ("check_d27.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\check_d27_baseline.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\check_d27_injected.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox"),
    ("check_d29.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d29\check_d29_baseline.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d29\check_d29_injected.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d29"),
    ("check_d30.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d30\check_d30_baseline.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d30\check_d30_injected.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d30"),
    ("check_d28.py (NEW)",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d28x\a\b\check_d28_baseline.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d28x\a\b\check_d28_injected.py",
     r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox\d28x\a\b"),
]

def run(script, cwd):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", script],
                       cwd=cwd, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace").strip(), \
           r.stderr.decode("utf-8", errors="replace").strip()

for name, base, inj, cwd in PAIRS:
    rb, ob, eb = run(base, cwd)
    ri, oi, ei = run(inj, cwd)
    hb = hashlib.sha256(open(base, "rb").read()).hexdigest()
    hi = hashlib.sha256(open(inj, "rb").read()).hexdigest()
    print("=== %s ===" % name)
    print("BASE sha256 = %s" % hb)
    print("INJ  sha256 = %s" % hi)
    print("BASE EXIT=%d STDOUT=%r STDERR=%r" % (rb, ob, eb))
    print("INJ  EXIT=%d STDOUT=%r STDERR=%r" % (ri, oi, ei))
    print("OUTPUT_IDENTICAL = %s ; EXIT_IDENTICAL = %s" % (ob == oi, rb == ri))
    print()
