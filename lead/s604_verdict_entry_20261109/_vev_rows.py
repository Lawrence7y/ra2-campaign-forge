# -*- coding: utf-8 -*-
# _vev_rows.py — 复核员独立实现：(b) 复跑输出 vs 台账 §604 表 15 行逐位比对；台账尾块哈希/mtime/CR 计数。只读，仅 print。
import hashlib, os, datetime, io

BASE = r"D:\Project\ra2-campaign-forge"
LEDGER = os.path.join(BASE, "lead", "GOAL_THREE_TARGETS_20261018.md")
RERUN = os.path.join(BASE, "lead", "s604_verdict_entry_20261109", "_ve_rerun_out.txt")
PRIOR = os.path.join(BASE, "lead", "s604_script_hunt_20261109", "_sh_gen512655_out.txt")

b_rerun = open(RERUN, "rb").read()
b_prior = open(PRIOR, "rb").read()
print("[0] writing-round rerun _ve_rerun_out.txt bytes=", len(b_rerun), "sha256=", hashlib.sha256(b_rerun).hexdigest())
print("    hunt capture      _sh_gen512655_out.txt bytes=", len(b_prior), "sha256=", hashlib.sha256(b_prior).hexdigest())
print("    bytes_equal =", b_rerun == b_prior)

data = open(LEDGER, "rb").read()
lines = data.split(b"\n")
print("[1] ledger LF-split parts =", len(lines), "| CR count =", data.count(b"\r"))
seg = b"\n".join(lines[9686:9757]).replace(b"\r", b"") + b"\n"
s_seg = seg.decode("utf-8")
print("    block 9687..9757(+final NL) chars =", len(s_seg), "sha256 =", hashlib.sha256(seg).hexdigest())
st = os.stat(LEDGER)
print("    ledger mtime =", datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], "size =", st.st_size)

def fnum(tok):
    tok = tok.replace("\u2212", "-").replace("**", "").replace("`", "").replace("ms", "")
    return float(tok.strip())

NUMCH = set("0123456789+-.\u2212")

rerun_rows = []
for ln in io.open(RERUN, encoding="utf-8"):
    parts = ln.split()
    if len(parts) == 6 and parts[0] != "window":
        rerun_rows.append((parts[0], [fnum(x) for x in parts[1:6]]))
print("[2] rerun rows parsed =", len(rerun_rows))

ledger_rows = []
for ln in lines[9705:9720]:
    s = ln.decode("utf-8")
    toks = [t for t in s.replace("|", " ").replace("**", "").replace("`", "").replace("ms", "").split() if t != "-"]
    toks = [t for t in toks if t and set(t) <= NUMCH]
    ledger_rows.append([fnum(t) for t in toks])
print("    ledger table rows (lines 9706..9720) parsed =", len(ledger_rows))

mismatch = 0
for i, (w, nums) in enumerate(rerun_rows):
    L = ledger_rows[i]
    ok = (len(nums) == len(L)) and all(abs(a - b2) < 1e-9 for a, b2 in zip(nums, L))
    if not ok:
        mismatch += 1
    print("    row%02d %s rerun=%s ledger=%s equal=%s" % (i + 1, w, nums, L, ok))
print("[3] 15/15 rows equal =", (mismatch == 0 and len(rerun_rows) == 15 and len(ledger_rows) == 15))

neg = [(w, nums[4]) for w, nums in rerun_rows if nums[4] < 0]
print("[4] strictly negative gapdiff cells:", neg)
raw = b_rerun.decode("utf-8").splitlines()
minus_cells = [l.split()[-1] for l in raw if l[:1] in ("l", "t") and "-" in l.split()[-1]]
print("    minus-signed cells raw text:", minus_cells)
s_rerun = b_rerun.decode("utf-8")
print("[5] rerun contains -114.820:", "-114.820" in s_rerun, "| contains 2.19 倍:", "2.19 倍" in s_rerun)
l9723 = lines[9722].decode("utf-8")
l9754 = lines[9753].decode("utf-8")
print("    ledger :9723 has 2.19 =", "2.19" in l9723)
print("    ledger :9754 =", l9754.strip()[:90])
print("    ledger :9754 has 114.8 =", "114.8" in l9754)
print("DONE")
