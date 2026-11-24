# -*- coding: utf-8 -*-
"""写盘后 pin + before_col4 自证还原性（独立脚本，只读目标文件，只写本目录 REVERSIBILITY_PROOF.txt）。"""
import os, sys, json, hashlib
sys.stdout.reconfigure(encoding="utf-8")
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT=os.path.join(ROOT,"R16_MERGE_D1_WIDE_B1")
COV=os.path.join(ROOT,"COVERAGE","coverage.tsv")
PAN=os.path.join(ROOT,"COVERAGE","PANEL.md")
def sha(b): return hashlib.sha256(b).hexdigest()

pin_cov=open(os.path.join(OUT,"_pin_coverage.tsv"),"rb").read()
pin_pan=open(os.path.join(OUT,"_pin_PANEL.md"),"rb").read()
after_cov=open(COV,"rb").read()
after_pan=open(PAN,"rb").read()
bc=json.load(open(os.path.join(OUT,"before_col4.json"),encoding="utf-8"))
log=json.load(open(os.path.join(OUT,"MERGE_LOG.json"),encoding="utf-8"))

L=[]
def w(s=""): L.append(s)

w("R16-MERGE-D1-WIDE-B1 · 写盘后 pin + before_col4 自证还原性")
w("="*76)
w()
w("[Coverage]")
w("  pin  sha256 = %s  bytes=%d" % (sha(pin_cov), len(pin_cov)))
w("  after sha256 = %s  bytes=%d" % (sha(after_cov), len(after_cov)))
# rebuild: after 的 18 行第4列换回 before_col4，其余字节保留
segs = after_cov.split(b"\n")
trail = after_cov.endswith(b"\n")
n_restored = 0
for e, info in bc.items():
    idx = info["line_number"]-1
    cols = segs[idx].split(b"\t")
    assert len(cols)==8
    cols[3] = info["value"].encode("utf-8")
    segs[idx] = b"\t".join(cols)
    n_restored += 1
rev = b"\n".join(segs) + (b"\n" if trail else b"")
w("  restored rows = %d" % n_restored)
w("  rev   sha256 = %s  bytes=%d" % (sha(rev), len(rev)))
w("  rev == pin 逐字节  = %s" % (rev==pin_cov))
w("  rev sha == pin sha = %s" % (sha(rev)==sha(pin_cov)))
assert rev == pin_cov
assert n_restored == 18
w()
w("[PANEL]")
w("  pin  sha256 = %s  bytes=%d" % (sha(pin_pan), len(pin_pan)))
w("  after sha256 = %s  bytes=%d" % (sha(after_pan), len(after_pan)))
ins_at = log["panel"]["inserted_after_line"]   # 296
ins_n  = log["panel"]["inserted_lines"]        # 8
pl = after_pan.split(b"\n")
rev_pl = pl[:ins_at] + pl[ins_at+ins_n:]
rev_pan = b"\n".join(rev_pl)
w("  removed inserted lines = %d (at 0-based %d..%d)" % (ins_n, ins_at, ins_at+ins_n-1))
w("  rev   sha256 = %s  bytes=%d" % (sha(rev_pan), len(rev_pan)))
w("  rev == pin 逐字节  = %s" % (rev_pan==pin_pan))
assert rev_pan == pin_pan
w()
w("结论：coverage.tsv 与 PANEL.md 均通过 pin + before_col4/插入位置 的逐字节还原性自证。")
w()

txt="\n".join(L)+"\n"
open(os.path.join(OUT,"REVERSIBILITY_PROOF.txt"),"w",encoding="utf-8",newline="\n").write(txt)
print(txt)
