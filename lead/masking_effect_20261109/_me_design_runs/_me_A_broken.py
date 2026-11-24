
# --- 方案甲：逐 needle 独立跑自检，每根单独出 PASS/FAIL，再合总 -------------
import subprocess, sys, io, os
SCANNER = r"D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py"
NEEDLES = ["BROKEN_SENTINEL_NO_HIT_XYZ", "不能定位当年错误步骤"]
BASE = ["-I", "-X", "utf8", SCANNER, "--include-refuting", "--max-depth", "2", "--ext", ".md"]

def one(n):
    cp = subprocess.run([sys.executable] + BASE[:4] + ["--needle", n] + BASE[4:],
                        capture_output=True, text=True, encoding="utf-8")
    lines = cp.stdout.splitlines()
    st = next((l for l in lines if l.startswith("SELF_TEST")), "SELF_TEST = <missing>")
    scans = next((l for l in lines if l.startswith("scanned files")), "<missing>")
    return cp.returncode, st.split("=")[-1].strip(), scans

rows = [(n, *one(n)) for n in NEEDLES]
all_ok = all(ec == 0 and st == "PASS" for _, ec, st, _ in rows)
for n, ec, st, scans in rows:
    print("NEEDLE %-30r EXIT=%d SELF_TEST=%-4s | %s" % (n, ec, st, scans))
print("AGGREGATE = %s ; per-needle = %d/%d PASS ; proven_bits = %d" %
      ("PASS" if all_ok else "FAIL",
       sum(1 for _, ec, st, _ in rows if ec == 0 and st == "PASS"), len(NEEDLES), len(rows)))
sys.exit(0 if all_ok else 1)
