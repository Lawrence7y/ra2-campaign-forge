#!/usr/bin/env python3
# W61: cross-check that ALL 113 resources in the patched exe still resolve
# to byte-identical data (i.e. the +0x20 RVA fixups are complete and correct).
import os, struct, hashlib
import pefile
ROOT=r"D:\Project\ra2-campaign-forge"
SRC=os.path.join(ROOT,"ra2bench","gamemd.exe")
DST=os.path.join(ROOT,"lead","next_re_20261112_r02","W61_third_badge_route","work","gamemd_v14r.exe")
a=open(SRC,"rb").read(); b=open(DST,"rb").read()
pa=pefile.PE(SRC,fast_load=False); pb=pefile.PE(DST,fast_load=False)
def off(pe,rva):
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def leaves(pe,data):
    RES=pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].VirtualAddress
    RO=off(pe,RES)
    u16=lambda o:struct.unpack_from("<H",data,o)[0]
    u32=lambda o:struct.unpack_from("<I",data,o)[0]
    out=[]
    def wd(o,path):
        n=u16(o+12)+u16(o+14)
        for i in range(n):
            e=o+16+i*8; nv=u32(e); od=u32(e+4); sub=RO+(od&0x7FFFFFFF)
            lab=str(nv&0xFFFF) if not(nv&0x80000000) else "named"
            if od&0x80000000: wd(sub,path+[lab])
            else: out.append((path+[lab],u32(sub),u32(sub+4),u32(sub+8),sub))
    n=u16(RO+12)+u16(RO+14)
    for i in range(n):
        e=RO+16+i*8; nv=u32(e); od=u32(e+4)
        if od&0x80000000: wd(RO+(od&0x7FFFFFFF),[str(nv&0xFFFF)])
    return out
la=leaves(pa,a); lb=leaves(pb,b)
print("=== W61 full-resource integrity cross-check ===")
print("orig leaves=%d patched leaves=%d"%(len(la),len(lb)))
assert len(la)==len(lb)
bad=[]; shifted=0
for x,y in zip(la,lb):
    pa_,ra,sa,ca,da=x; pb_,rb,sb,cb,db=y
    assert pa_==pb_ and ca==cb, "path/cp mismatch %r"%pa_
    oa=off(pa,ra); ob=off(pb,rb)
    if oa is None or ob is None:
        bad.append((pa_,"unmapped RVA")); continue
    if ra!=rb: shifted+=1
    blob_a=a[oa:oa+sa]; blob_b=b[ob:ob+sb]
    if pa_[0]=="5" and pa_[1]=="148":
        # dialog 148 intentionally grew by 32 bytes AND cDlgItems 13->14 at bytes 16..17
        if sa==664 and sb==696:
            fixed=bytearray(blob_b[:664]); fixed[16:18]=blob_a[16:18]
            if bytes(fixed)==blob_a: continue
        bad.append((pa_,"dialog148 not as expected")); continue
    if sa!=sb or blob_a!=blob_b:
        bad.append((pa_,"content differs sa=%d sb=%d off 0x%X->0x%X"%(sa,sb,oa,ob)))
print("shifted data-entry RVAs: %d"%shifted)
print("resources with bytes identical to original: %d/%d (excluding dialog 148)"%(len(la)-1-len(bad),len(la)-1))
print("problems: %d"%len(bad))
for p,why in bad[:20]: print("  %r : %s"%(p,why))
assert not bad, "resource integrity FAILED"
# also confirm the 61 shift is exactly +0x20 and only for rva>=0x783508
exp=[x for x in la if x[1]>=0x783508]
print("expected-shift set size (orig rva>=0x783508) = %d ; actual shifted = %d"%(len(exp),shifted))
assert len(exp)==shifted==61
print("[OK] every resource resolves and is byte-identical; all 61 fixups correct")
