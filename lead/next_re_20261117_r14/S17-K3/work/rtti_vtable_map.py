#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTTI/vtable recovery (independent byte-level evidence), fixed TD location.
Scan .rdata for dwords pointing to a COL:
  COL+0=0(sig), COL+0xC=pTD, TD+8=mangled name '.?AV...@@'
vtable[-1]=pCOL  =>  vtable base = site+4.
Map candidate function VA -> (class, slot) by scanning vtable slots.
"""
import sys, struct, os, io
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P

sections = P.sections()
rdata = [s for s in sections if s[0] == '.rdata'][0]
_, rd_va, rd_vsize, rd_praw, rd_rawsize, _ = rdata
text = [s for s in sections if s[0] == '.text'][0]
txt_lo, txt_hi = text[1], text[1] + text[4]

with open(P.EXE, 'rb') as f:
    f.seek(rd_praw)
    rd = f.read(rd_rawsize)

def cstr(va, maxn=200):
    off = P.va2off(va)
    if off is None: return None
    with open(P.EXE,'rb') as f:
        f.seek(off); b = f.read(maxn)
    z = b.find(b'\x00')
    return b[:z if z>=0 else maxn]

# find COLs
seen = {}
for i in range(0, len(rd) - 4, 4):
    p = struct.unpack_from('<I', rd, i)[0]
    if not (rd_va <= p < rd_va + rd_vsize):
        continue
    if P.u32(p) != 0:            # signature
        continue
    td = P.u32(p + 0xC)
    if td is None: continue
    nm = cstr(td + 8, 160)
    if nm is None: continue
    s = nm.decode('latin1', 'replace')
    if s.startswith('.?AV') and '@@' in s:
        seen.setdefault(p, (rd_va + i, s))

out = []
out.append(f"COLs found: {len(seen)}")
vbase_to_class = {}
for col, (site, nm) in seen.items():
    vb = site + 4
    vbase_to_class.setdefault(vb, set()).add(nm)
out.append(f"vtables (base=site+4): {len(vbase_to_class)}")

cands = [0x004068E0,0x0040E340,0x00427940,0x0042E410,0x00431B80,0x00433CF0,0x004355B0,0x0043AE50,
         0x0049F740,0x0049F8B0,0x00773450]
calib = [0x0041D6E0,0x0043A5D0,0x00410410]

def find_slots(func_va):
    res = []
    for vb, classes in vbase_to_class.items():
        for k in range(0, 600):
            sv = P.u32(vb + 4*k)
            if sv is None or not (txt_lo <= sv < txt_hi):
                break
            if sv == func_va:
                for cls in classes:
                    res.append((vb, cls, k))
                break
    return res

out.append("")
out.append("=== candidate/calibration function -> vtable slot/class ===")
for f in cands + calib:
    slots = find_slots(f)
    tag = "CALIB" if f in calib else "CAND"
    if slots:
        for vb, cls, k in slots:
            out.append(f"{tag} {f:08X}  vbase={vb:08X} slot={k} (+0x{4*k:X}) class={cls}")
    else:
        out.append(f"{tag} {f:08X}  NO vtable slot found")

# Also: for 0x431B80, dump the exact vtable it belongs to (all slots) for destructor slot check
out.append("")
out.append("=== vtable whose slot contains 0x431B80 (full listing) ===")
for vb, classes in vbase_to_class.items():
    for k in range(0, 600):
        sv = P.u32(vb + 4*k)
        if sv is None or not (txt_lo <= sv < txt_hi): break
        if sv == 0x00431B80:
            out.append(f"vbase={vb:08X} classes={classes} pCOL={vb-4:08X}={P.u32(vb-4):08X}")
            for j in range(0, 8):
                out.append(f"  slot{j} (+0x{4*j:X}) = {P.u32(vb+4*j):08X}")
            break

txt = "\n".join(out) + "\n"
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K3"
with io.open(os.path.join(CARD,"EVIDENCE","rtti_vtable_map.txt"),"w",encoding="utf-8") as fo:
    fo.write(txt)
sys.stdout.write(f"COLs={len(seen)} vtables={len(vbase_to_class)} written\n")
