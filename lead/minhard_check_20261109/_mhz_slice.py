# _mhz_slice.py — explain §607 body SHA convention differences (this session)
import hashlib, os, sys
ROOT = r"D:\Project\ra2-campaign-forge"
def rp(rel): return os.path.join(ROOT, rel.replace("/", os.sep))
def rb(rel):
    with open(rp(rel),"rb") as f: return f.read()
O=[]
def p(s=""): O.append(str(s))

REL = "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md"
raw = rb(REL)
L = raw.decode("utf-8").splitlines()
seg = L[12:26]  # :13-26
variants = {
 "join_nl + trailing_nl": ("\n".join(seg)+"\n").encode("utf-8"),
 "join_nl no trailing": ("\n".join(seg)).encode("utf-8"),
 "each line + nl (no extra)": ("".join(x+"\n" for x in seg)).encode("utf-8"),
 "each line + nl + extra blank": ("".join(x+"\n" for x in seg)+"\n").encode("utf-8"),
 "join CRLF + trailing": ("\r\n".join(seg)+"\r\n").encode("utf-8"),
}
p(f"== {REL} :13-26 slicing variants ==")
for k,v in variants.items():
    p(f"  {k}: bytes={len(v)} sha256={hashlib.sha256(v).hexdigest()}")
p("")
p("== in-case values to compare ==")
p("  _mh_verify2_out.txt:1  a758a87b31da39e740977dff05e315333e8fb336ac0d8cdd86866244cfdaab82 / '2707 字符'")
p("  _mhv_blocks3_out.txt:52 a758a87b... / bytes=4892")
p("  bound-volume registration e9842d41f27d70b80067c5a6b89afe81ab63eb0422c7eda741d1c5983a3df698 / 4894 B")
p("")
p("== raw byte slice of the physical lines 13..26 in file bytes ==")
# find byte offsets of physical line starts
starts=[0]
for i,b in enumerate(raw):
    if b==10: starts.append(i+1)
p(f"  total physical LF count={raw.count(bytes([10]))}  line13 start={starts[12]}  line27 start={starts[26] if len(starts)>26 else 'NA'}")
if len(starts)>26:
    body=raw[starts[12]:starts[26]]
    p(f"  raw[line13:line27) bytes={len(body)} sha={hashlib.sha256(body).hexdigest()}")
    body2=raw[starts[12]:starts[25]]
    p(f"  raw[line13:line26) bytes={len(body2)} sha={hashlib.sha256(body2).hexdigest()}")
sys.stdout.write("\n".join(O)+"\n")
