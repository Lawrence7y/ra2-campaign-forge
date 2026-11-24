#!/usr/bin/env python3
"""S16-K3 T4: attempt real-evidence naming for the 7 Class::sub_XXXXXXXX entries.
Dump full body + find caller xrefs + string xrefs. Only name if body/strings give
unambiguous semantic evidence; otherwise keep Class::sub_ and report '不可定'.
"""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K3\work")
import k3_lib as K
b=K.Bin()

SUBS=[0x0053A6C0,0x0053A0E0,0x0053AE50,0x00430BA0,0x006CE280,0x006CE2C0,0x006CE2D0]

# precompute direct call sites to these targets over whole .text
def scan_direct_calls(target):
    sites=[]
    s=b.sec('.text')
    for ins in K.md(skipdata=True).disasm(b.data[s['raw']:s['raw']+s['rawsize']],s['va']):
        if ins.id==0: continue
        if ins.mnemonic=='call' and ins.op_str.startswith('0x') and int(ins.op_str,16)==target:
            sites.append(ins.address)
    return sites

def str_xrefs(va,window=0x300):
    """Find push <imm> where imm points to readable ascii in body window."""
    out=[]
    for i in K.disasm_n(b,va,window):
        if i.id==0: continue
        if i.mnemonic=='push' and i.op_str.startswith('0x'):
            x=int(i.op_str,16)
            if 0x800000<=x<0xb7a000:
                try:
                    st=K.cstr(b,x,80)
                    if st and all(32<=ord(c)<127 for c in st[:1]): out.append((i.address,x,st))
                except Exception: pass
    return out

for va in SUBS:
    print(f"\n\n========== {va:08X} ==========")
    sites=scan_direct_calls(va)
    print(f"[CALLERS] direct call sites ({len(sites)}): {[hex(x) for x in sites]}")
    # dump first 0x180 bytes
    body="\n".join(K.fmt(i) for i in K.disasm_n(b,va,0x180))
    print(body)
    sx=str_xrefs(va)
    print(f"[STRING PUSHes] {[(hex(a),hex(x),s[:60]) for a,x,s in sx]}")
