# -*- coding: utf-8 -*-
"""Deliverable self-check for S06 B1."""
import os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(WORK)
sys.path.insert(0, WORK)
import recore as R

ok=True
# delta
rows=[l.rstrip("\n").split("\t") for l in open(os.path.join(BASE,"delta.tsv"),encoding="utf-8")]
hdr,body=rows[0],rows[1:]
assert hdr==["entry","subsystem","name","one_line_semantics","grade","evidence_path"],hdr
print("delta header OK; rows =",len(body))
seen=set(); sems=set()
for r in body:
    e=r[0]
    assert re.fullmatch(r"[0-9A-F]{8}",e),"entry not uppercase hex: %r"%e
    assert not e.startswith("0x")
    assert r[1]=="S06" and r[4]=="[已证]"
    p=r[5].replace("/","\\")
    assert os.path.isfile(p),"missing evidence: "+p
    assert os.path.basename(p)=="ROW_%s.txt"%e,p
    assert e not in seen; seen.add(e)
    assert r[3] not in sems,"duplicate semantics"; sems.add(r[3])
print("delta entries:",sorted(seen))
print("distinct semantics:",len(sems),"/",len(body))

# all 18 evidence files exist
ev=os.path.join(BASE,"EVIDENCE")
files=[f for f in os.listdir(ev) if f.startswith("ROW_") and f.endswith(".txt")]
print("evidence files:",len(files))
assert len(files)==18,len(files)

# key byte recheck
CHECK=[
 (0x4839FF,"e87cc9f8ff","row1 call 410380"),(0x483A06,"3bc3","row1 cmp eax,ebx"),
 (0x483A08,"0f8cf2010000","row1 jl"),(0x483C00,"5f5e5d5b59","row1 fail epilogue"),
 (0x483C22,"e8f9c6f8ff","row2 call 410320"),(0x483C27,"85c0","row2 test"),(0x483C29,"7c4e","row2 jl"),
 (0x410389,"b803400080","E_POINTER 380"),(0x41032B,"b803400080","E_POINTER 320"),
 (0x41039E,"ff500c","Read slot 0xc"),(0x410348,"ff5010","Write slot 0x10"),
 (0x5F93B5,"e816811500","row12 call Find"),(0x5F93BA,"83f8ff","row12 cmp -1"),(0x5F93BD,"7402","row12 je"),
 (0x751516,"83c8ff","Find or eax,-1"),(0x75151B,"8bc6","Find mov eax,esi"),
 (0x5FD1BB,"e8507ee8ff","row13 call"),(0x5FD1C0,"83f8ff","row13 cmp -1"),(0x5FD1C3,"7435","row13 je"),
 (0x5FDDD8,"83c8ff","row13Find or eax,-1"),(0x5FDDC1,"33c0","row13Find xor eax,eax"),(0x5FDDC8,"c3","row13Find ret0"),
 (0x47BD5C,"c706ec4e7e00","ctor cell vt write"),(0x544A42,"c70648cc7e00","ctor tiletype vt write"),
 (0x5FC38F,"c706d4f37e00","ctor overlay vt write"),(0x5FE2F1,"c70600f67e00","ctor overlaytype vt write"),
]
for a,exp,what in CHECK:
    got=R.read_va(a,len(exp)//2).hex()
    flag="OK " if got==exp else "BAD"
    if got!=exp: ok=False
    print("%s %08X %-14s got=%s exp=%s"%(flag,a,"",got,exp))
# slot values for 4 proved rows
for sva,e in [(0x7E4F00,0x4839F0),(0x7E4F04,0x483C10),(0x7ECCAC,0x5F92D0),(0x7EF4F8,0x5FC570)]:
    v=R.u32(sva); f="OK" if v==e else "BAD"
    if v!=e: ok=False
    print("%s slot %08X=%08X exp %08X"%(f,sva,v,e))
print("ALL OK" if ok else "FAILURES PRESENT")
