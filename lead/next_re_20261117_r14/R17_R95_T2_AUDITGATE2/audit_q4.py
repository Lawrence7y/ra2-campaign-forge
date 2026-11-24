# -*- coding: utf-8 -*-
import os, sys, io, hashlib, subprocess, shutil
from collections import Counter
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
ROOT = r"D:\Project\ra2-campaign-forge"
REPORT = os.path.join(R14, "R17_R95_T2_AUDITGATE2")
CHK = os.path.join(R14, "check_disc.py")
DR  = os.path.join(R14, "DISC_RECHECK.tsv")
def sha(p):
    with io.open(p,"rb") as f: return hashlib.sha256(f.read()).hexdigest()
def gate():
    r = subprocess.run([sys.executable, CHK], cwd=R14, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode("utf-8","replace")
def c11(out):
    return [l for l in out.splitlines() if "C11 col7" in l or "[exit" in l or "FAIL  " in l]

print("=== Q4-A expr first-token distribution ===")
cnt = Counter()
with io.open(DR, encoding="utf-8", newline="") as f:
    for ln in list(f)[1:]:
        c = ln.rstrip("\n").split("\t")
        if len(c) == 7:
            head = c[5].strip().split(" ")[0]
            key = head.split("=")[0] if "=" in head else head
            cnt[key] += 1
print("   ", dict(cnt), " bytes= rows =", cnt.get("bytes",0))

rows = {}
with io.open(DR, encoding="utf-8", newline="") as f:
    for ln in list(f)[1:]:
        c = ln.rstrip("\n").split("\t")
        if len(c) == 7: rows[c[0].strip()] = c
hC = sha(CHK)

print("")
print("=== Q4-B append compliant line to claim-NONE discipline 11 ===")
r11 = rows["11"]; prod_rel = r11[4].strip(); prod_abs = prod_rel.replace("/","\\")
if not os.path.isabs(prod_abs): prod_abs = os.path.join(ROOT, prod_abs)
print("   disc11 col7=", r11[6].strip(), " product exists=", os.path.isfile(prod_abs))
if os.path.isfile(prod_abs):
    h = hashlib.sha256(r11[3].encode("utf-8")).hexdigest()
    line = ("DISC_RECHECK discipline=11 round=R55 at=2026-11-22T17:39:19+08:00 anchors=sha256:%s conclusion=PASS\n" % h)
    bp, hp = os.path.join(REPORT,"bak_disc11_product"), sha(prod_abs)
    shutil.copy2(prod_abs, bp)
    try:
        with io.open(prod_abs,"a",encoding="utf-8",newline="") as f: f.write(line)
        rc, out = gate(); print("   after append: exit=%d" % rc)
        for l in c11(out): print("   ", l)
    finally:
        shutil.copy2(bp, prod_abs); print("   product restored=", sha(prod_abs)==hp)
rc, out = gate(); print("   after-restore exit=%d" % rc)
for l in c11(out): print("   ", l)

print("")
print("=== Q4-C change disc3 col3 to non-placeholder garbage (C9?) ===")
bp, hp = os.path.join(REPORT,"bak_DISC_RECHECK.tsv"), sha(DR)
shutil.copy2(DR, bp)
try:
    with io.open(DR, encoding="utf-8", newline="") as f: txt = f.read()
    txt2 = txt.replace(rows["3"][2], "GARBAGE-CRITERION-OTHER", 1)
    with io.open(DR,"w",encoding="utf-8",newline="") as f: f.write(txt2)
    rc, out = gate(); print("   exit=%d" % rc)
    for l in [l for l in out.splitlines() if "C9" in l or "[exit" in l or "FAIL  " in l]: print("   ", l)
finally:
    shutil.copy2(bp, DR); print("   DISC_RECHECK restored=", sha(DR)==hp)
rc, out = gate(); print("   after-restore exit=%d" % rc)
print("")
print("=== FINAL check_disc.py unchanged=", sha(CHK)==hC)