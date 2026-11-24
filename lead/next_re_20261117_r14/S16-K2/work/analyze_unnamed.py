#!/usr/bin/env python3
"""S16-K2: analyze the 17 unnamed S16 functions: disasm, callers, string refs, RTTI refs."""
import sys, os, struct, csv, re, collections
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K2\work")
import re_lib as R

ROOT = r"D:\Project\ra2-campaign-forge"
b = R.Bin()

UNNAMED = [0x00430BA0,0x00539EB0,0x0053A0E0,0x0053A6C0,0x0053AE00,0x0053AE50,
           0x0053B410,0x0053D8E0,0x0053DDA0,0x0065E660,0x006CE240,0x006CE270,
           0x006CE280,0x006CE2C0,0x006CE2D0,0x006CE320,0x0071AB60]

# atlas for function extents
atlas_rows, hdr = R.load_atlas()
atlas_sorted = sorted([(va,sz) for va,sz,_ in atlas_rows])
import bisect
def extent(va):
    keys=[x[0] for x in atlas_sorted]
    i=bisect.bisect_right(keys,va)-1
    if i>=0 and va<atlas_sorted[i][0]+atlas_sorted[i][1]:
        return atlas_sorted[i][0], atlas_sorted[i][1]
    return va, 0x80  # guess 128 bytes

# scan all .text calls (E8 rel32) and prints, once
m = R.md(skipdata=True)
s = b.sec('.text')
data = b.data[s['raw']:s['raw']+s['rawsize']]
callers = collections.defaultdict(list)
strrefs = collections.defaultdict(list)  # target func -> [(site, string)]
codeimm = collections.defaultdict(list)
for ins in m.disasm(data, s['va']):
    if ins.id==0: continue
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        t=int(ins.op_str,16)
        callers[t].append(ins.address)
    # push imm32: look for push of an address that is printable string
    if ins.mnemonic=='push' and ins.op_str.startswith('0x'):
        v=int(ins.op_str,16)
        if 0x400000<=v<0xB00000:
            try:
                st=R.cstr(b,v,120)
                if len(st)>=3 and all(32<=ord(c)<127 for c in st):
                    strrefs[ins.address].append((v,st))  # key by site, map later
            except Exception: pass

# map site->containing function to assign string refs
def containing_fn(site):
    keys=[x[0] for x in atlas_sorted]
    i=bisect.bisect_right(keys,site)-1
    if i>=0 and site<atlas_sorted[i][0]+atlas_sorted[i][1]:
        return atlas_sorted[i][0]
    return None

site_strings = collections.defaultdict(list)
for site, lst in strrefs.items():
    fn=containing_fn(site)
    if fn is not None:
        site_strings[fn].extend(lst)

# scan .rdata/.data dword refs to unnamed functions (non-slot data references)
data_refs = collections.defaultdict(list)
for secname in ('.rdata','.data'):
    ss=b.sec(secname)
    buf=b.data[ss['raw']:ss['raw']+ss['rawsize']]
    for i in range(0,len(buf)-3,4):
        v=struct.unpack_from('<I',buf,i)[0]
        if v in UNNAMED:
            data_refs[v].append(ss['va']+i)

for va in UNNAMED:
    st,sz = extent(va)
    print("="*100)
    print(f"FUNC {va:08X}  atlas extent {st:08X}+{sz:#x}  callers={len(callers.get(va,[]))} datarefs={len(data_refs.get(va,[]))}")
    cs=callers.get(va,[])
    if cs:
        print("  callers:", " ".join(f"{c:08X}({containing_fn(c):08X})" if containing_fn(c) else f"{c:08X}(?)" for c in cs[:20]))
    dr=data_refs.get(va,[])
    if dr:
        print("  data refs:", " ".join(f"{d:08X}" for d in dr))
    ss=site_strings.get(va,[])
    if ss:
        uniq=[]
        for addr,st2 in ss:
            if (addr,st2) not in uniq: uniq.append((addr,st2))
        print("  string refs in fn:")
        for addr,st2 in uniq[:12]:
            print(f"    push {addr:08X} -> \"{st2[:90]}\"")
    # disasm first 60 insns or up to extent
    end=min(st+sz, va+0x200) if sz else va+0x100
    insns=R.disasm_range(b,va,end,skipdata=True)
    print("  --- first instructions ---")
    for ins in insns[:45]:
        annotation=""
        if ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
            t=int(ins.op_str,16)
            if t in UNNAMED: annotation=" ->UNNAMED"
        if ins.mnemonic=='push' and ins.op_str.startswith('0x'):
            t=int(ins.op_str,16)
            if 0x7e1000<=t<0x812000:
                try:
                    st2=R.cstr(b,t,60)
                    if len(st2)>=3 and all(32<=ord(c)<127 for c in st2): annotation=f' ->"{st2[:60]}"'
                except: pass
        print("   ", R.fmt(ins)+annotation)
