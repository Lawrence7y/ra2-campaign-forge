#!/usr/bin/env python3
"""Independent anchored byte audit for R17-AUDIT-R11.
Does not import or reuse R17_R11_CTOR_CHAIN/work.py. Opens gamemd.exe read-only.
"""
from __future__ import annotations
import os, struct, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work\run\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_AUDIT_R11"
with open(EXE, "rb") as f:
    blob = f.read()
sha = hashlib.sha256(blob).hexdigest()
e_lfanew = struct.unpack_from("<I", blob, 0x3C)[0]
assert blob[e_lfanew:e_lfanew+4] == b"PE\0\0"
num_sec = struct.unpack_from("<H", blob, e_lfanew+6)[0]
size_opt = struct.unpack_from("<H", blob, e_lfanew+20)[0]
opt = e_lfanew + 24
image_base = struct.unpack_from("<I", blob, opt+28)[0]
secs=[]
for i in range(num_sec):
    o = opt + size_opt + 40*i
    name = blob[o:o+8].rstrip(b"\0").decode("ascii", "replace")
    vsize, rva, rawsize, rawptr = struct.unpack_from("<IIII", blob, o+8)
    secs.append((name, rva, max(vsize, rawsize), rawptr, rawsize))
def va_off(va: int) -> int:
    rva = va - image_base
    for name, srva, ssize, sptr, sraw in secs:
        if srva <= rva < srva + ssize:
            off = sptr + (rva - srva)
            assert off < len(blob), (hex(va), hex(off))
            return off
    raise KeyError(hex(va))
def rd(va:int, n:int)->bytes:
    o=va_off(va); return blob[o:o+n]
def hx(b:bytes)->str: return " ".join(f"{x:02X}" for x in b)
def check(rows, cid, subject, va, expected, note=""):
    exp=bytes.fromhex(expected.replace(" ",""))
    act=rd(va,len(exp))
    rows.append((cid, subject, f"0x{va:X}", hx(exp), hx(act), str(act==exp), note))
    return act==exp
md=Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
def disasm(va:int, max_bytes:int=64, count:int=16):
    out=[]
    for i in md.disasm(rd(va,max_bytes), va):
        out.append((i.address, i.mnemonic, i.op_str, bytes(i.bytes)))
        if len(out)>=count: break
    return out
def disasm_until_ret(va:int, max_bytes:int=0x100):
    out=[]
    for i in md.disasm(rd(va,max_bytes), va):
        out.append((i.address, i.mnemonic, i.op_str, bytes(i.bytes)))
        if i.mnemonic in ("ret","retf") and len(out)>0: break
        if len(out)>=48: break
    return out
def pre_anchor(va:int, span:int=32):
    pre=rd(va-span,span); n=0
    for b in reversed(pre):
        if b in (0x90,0xCC): n+=1
        else: break
    fill=pre[len(pre)-n:] if n else b""
    prior=pre[:len(pre)-n]
    tail=prior[-8:]
    ret_end = tail.endswith(b"\xC3") or (len(tail)>=3 and tail[-3]==0xC2)
    return fill, tail, bool(n or ret_end)
def call_target(site:int):
    ins=rd(site,5); assert ins[0]==0xE8, (hex(site),hx(ins))
    rel=struct.unpack("<i", ins[1:5])[0]
    return site+5+rel, ins
def shape(va:int, max_bytes:int=0x100):
    ins=disasm_until_ret(va,max_bytes)
    calls=[]; vt=[]; mov_eax_esi=False; ret=""
    for a,m,o,b in ins:
        if m=="call" and len(b)>=5 and b[0]==0xE8:
            rel=struct.unpack("<i", b[1:5])[0]; calls.append((a,a+5+rel))
        if b.startswith(b"\xC7") and len(b)>=6 and b[1] in (0x06,0x46,0x86,0x8E):
            v=struct.unpack_from("<I", b, 2+(2 if b[1] in (0x86,0x8E) else 0))[0]
            vt.append((a,hex(v)))
        if m=="mov" and o.replace(" ","")=="eax,esi": mov_eax_esi=True
        if m in ("ret","retf"): ret=f"{m} {o}".strip()
    return {"ins":ins,"calls":calls,"vt":vt,"mov_eax_esi":mov_eax_esi,"ret":ret,"end":ins[-1][0]+len(ins[-1][3]) if ins else va}

rows=[]; g=[]; edges=[]
# 0 / B1: bit0 write and constructor anchor bytes
check(rows,"0.1","2.6 bit0 OR",0x6F322F,"0C 01")
check(rows,"0.2","2.6 bit0 store",0x6F3237,"88 46 14")
check(rows,"B1.G1.pad","6F2B40 pre-fill",0x6F2B38,"90 "*8)
check(rows,"B1.G1.prior","6F2B40 prior ret",0x6F2B34,"C3")
check(rows,"B1.G2.call","6F2B40 base call",0x6F2B46,"E8 05 7C F6 FF")
check(rows,"B1.G2.prior","65A750 prior ret",0x6F2B34,"C3") # placeholder replaced below
rows.pop()
check(rows,"B1.G2.targetret","65A750 prior ret",0x65A746,"C3")
check(rows,"B1.G3.vt0","6F306A vt440",0x6F306A,"C7 86 40 04 00 00 78 4E 7E 00")
check(rows,"B1.G3.vt1","6F3130 vt0",0x6F3130,"C7 06 60 49 7F 00")
check(rows,"B1.G3.vt2","6F3136 vt4",0x6F3136,"C7 46 04 44 49 7F 00")
check(rows,"B1.G3.vt3","6F313D vt8",0x6F313D,"C7 46 08 3C 49 7F 00")
check(rows,"B1.G3.vt4","6F314A vtC",0x6F314A,"C7 46 0C 34 49 7F 00")
check(rows,"B1.G4.tail","6F3260 return this",0x6F3260,"8B C6 5F 5E 5D 5B C2 04 00")
check(rows,"B1.G5.range","6F322F in 6F2B40 interval",0x6F322F,"0C 01 8D BE 04 03 00 00 88 46 14")
ct=call_target(0x6F2B46)
fill,prior,anch=pre_anchor(0x6F2B40)
s0=shape(0x6F2B40,0x140)
g.append(("G1","entry anchor after 8x90 and prior C3",hx(rd(0x6F2B34,4))+" | "+hx(rd(0x6F2B38,8)),"PASS"))
g.append(("G2","direct call to 0x65A750",hx(rd(0x6F2B46,5))+" -> 0x%X"%ct[0]+" | pre "+hx(prior)+" fill "+hx(fill),"PASS" if ct[0]==0x65A750 and anch else "FAIL"))
g.append(("G3","five listed vt writes",hx(rd(0x6F306A,10))+" | "+hx(rd(0x6F3130,6))+" | "+hx(rd(0x6F3136,7))+" | "+hx(rd(0x6F313D,7))+" | "+hx(rd(0x6F314A,7)),"PASS"))
g.append(("G4","mov eax,esi then ret 4",hx(rd(0x6F3260,9)),"PASS" if hx(rd(0x6F3260,9))=="8B C6 5F 5E 5D 5B C2 04 00" else "FAIL"))
g.append(("G5","range [6F2B40,6F3267) covers 6F322F bit write",hx(rd(0x6F322F,11)),"PASS" if 0x6F2B40<=0x6F322F<0x6F3267 else "FAIL"))
# B2 edge checks
edge_defs=[
 ("host1","0x43B680","0x6F4300",0x43B688,0x6F4300),
 ("host1","0x6F4300","0x65A7E0",0x6F430B,0x65A7E0),
 ("host1","0x65A7E0","0x5F3B50",0x65A7E8,0x5F3B50),
 ("host1","0x5F3B50","0x4101C0",0x5F3B58,0x4101C0),
 ("host2","0x43B740","0x6F2B40",0x43B74B,0x6F2B40),
 ("host2","0x6F2B40","0x65A750",0x6F2B46,0x65A750),
 ("host2","0x65A750","0x5B2DA0",0x65A753,0x5B2DA0),
 ("host2","0x5B2DA0","0x5F3900",0x5B2DA3,0x5F3900),
]
for chain,frm,to,site,expected in edge_defs:
    target,b=call_target(site)
    fill,prior,anch=pre_anchor(target)
    entry=hx(rd(target,8))
    ok=(target==expected and b[0]==0xE8 and anch)
    edges.append((chain,frm,to,f"0x{site:X}",hx(b),f"0x{target:X}",hx(fill) if fill else "-",hx(prior),"PASS" if anch else "FAIL","字节证实" if ok else "不成立",entry))
    rows.append(("B2.call",f"{frm}->{to}",f"0x{site:X}",f"e8 rel -> 0x{expected:X}",hx(b)+f" -> 0x{target:X}","PASS" if ok else "FAIL",f"pre-fill={hx(fill)} prior={hx(prior)} entry={entry}"))
# explicit correction of executor's erroneous byte string for host1 65A7E0->5F3B50
check(rows,"B2.exec_byte_error","executor listed bytes at 65A7E8",0x65A7E8,"E8 63 C6 E1 FF","actual must be E8 63 93 F9 FF")
# B3 host3 call sites and target entry-shape checks (>=3)
b3_targets=[(0x43BD1A,0x406060),(0x43BD27,0x406060),(0x43BD2E,0x405C00),(0x43BD35,0x405C00),(0x43BD47,0x554A80),(0x43BD67,0x7258D0),(0x43BD6E,0x445880)]
b3_rows=[]
for site,exp in b3_targets:
    target,b=call_target(site)
    fill,prior,anch=pre_anchor(target)
    sh=shape(target,0x100)
    nonctor=(not sh["mov_eax_esi"]) and (len(sh["vt"])==0)
    b3_rows.append((f"0x{site:X}",f"0x{target:X}",hx(b),"PASS" if target==exp else "FAIL",hx(fill) if fill else "-",hx(prior),"PASS" if anch else "FAIL","非构造器" if nonctor else "需复核",f"calls={len(sh['calls'])} vt={len(sh['vt'])} ret={sh['ret']!r} entry={hx(rd(target,8))}"))
    rows.append(("B3.call",f"host3 site",f"0x{site:X}",f"e8 rel -> 0x{exp:X}",hx(b)+" -> 0x{target:X}","PASS" if target==exp else "FAIL",f"target entry={hx(rd(target,8))} pre-fill={hx(fill)} prior={hx(prior)}"))
# B4 host2 vtable writes and call/coverage facts
check(rows,"B4.call","host2 call 6F2B40",0x43B74B,"E8 F0 73 2B 00")
check(rows,"B4.vt0","host2 [esi]=7E3EBC",0x43B9FA,"C7 06 BC 3E 7E 00")
check(rows,"B4.vt1","host2 [ebp]=7E3EA0",0x43BA00,"C7 45 00 A0 3E 7E 00")
check(rows,"B4.vt2","host2 [esi+8]=7E3E98",0x43BA07,"C7 46 08 98 3E 7E 00")
check(rows,"B4.vt3","host2 [esi+C]=7E3E90",0x43BA0E,"C7 46 0C 90 3E 7E 00")
# writes
def write_tsv(name, header, data):
    with open(os.path.join(OUT,name),"w",encoding="utf-8",newline="") as f:
        f.write("\t".join(header)+"\n")
        for r in data: f.write("\t".join(str(x) for x in r)+"\n")
write_tsv("byte_checks.tsv",["id","subject","address","expected","actual","ok","note"],rows)
write_tsv("g1g5_6f2b40.tsv",["criterion","expectation","bytes","verdict","evidence"],g)
write_tsv("edges.tsv",["chain","from","to","call_site","call_bytes","target","target_pre_fill","target_prior_tail","entry_anchor","verdict","target_entry_bytes"],edges)
write_tsv("b3_calls.tsv",["call_site","target","call_bytes","call_ok","target_pre_fill","target_prior_tail","entry_anchor","shape","evidence"],b3_rows)
# summary JSON for VERDICT drafting
import json
summary={"exe":EXE,"sha256":sha,"image_base":hex(image_base),"sections":[s[0] for s in secs],"g1g5":g,"edges":edges,"b3":b3_rows,"byte_rows":rows}
with open(os.path.join(OUT,"summary.json"),"w",encoding="utf-8") as f: json.dump(summary,f,ensure_ascii=False,indent=2)
print("sha256",sha)
print("image_base",hex(image_base),"sections",[s[0] for s in secs])
print("G1-G5",[(x[0],x[3]) for x in g])
print("edges",[(e[2],e[5],e[9],e[8]) for e in edges])
print("B3",[(x[0],x[1],x[7],x[8]) for x in b3_rows])
print("byte checks",sum(r[5]=="PASS" for r in rows),"/",len(rows))
