# _sv_fingerprint.py — 复核员独立指纹核对（纯只读，只 print）
import hashlib, os, time
BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/PENDING_DECISIONS.md",
    "lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",
    "lead/slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md",
    "lead/slowframe_r3_20261108/_r3_recompute_gapdiff.py",
    "lead/slowframe_r3_20261108/_r3_recompute_out.txt",
    "lead/slowframe_r3_20261108/_verify_r3_gapdiff.py",
    "lead/slowframe_r3_20261108/_verify_r3_out.txt",
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
    "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
    "lead/s604_attribution_20261108/_sa_probe.py",
    "lead/s604_attribution_20261108/_sa_probe_out.txt",
]
for rel in FILES:
    p = os.path.join(BASE, rel.replace("/", os.sep))
    if not os.path.exists(p):
        print("MISSING", rel)
        continue
    with open(p, "rb") as fh:
        b = fh.read()
    nl = b.count(b"\n")
    mt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.stat(p).st_mtime))
    print("{} | bytes={} | lines={} | sha256={} | mtime={}".format(
        rel, len(b), nl, hashlib.sha256(b).hexdigest(), mt))
