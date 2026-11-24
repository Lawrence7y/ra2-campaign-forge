#!/usr/bin/env python3
"""Verify auditor's claim: N classes' v[6] bodies CALL 0x410320 (Save wrapper),
v[5] bodies CALL 0x410380 (Load wrapper). Cross-contamination. Also confirm
0x410320 semantics: arg2=IStream*, calls [IStream vtable+0x10]=Write.
"""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K3\work")
import k3_lib as K
b=K.Bin()

def body_calls(va, scan=0x80):
    """Return set of direct call targets in first scan bytes of a function body."""
    out=set()
    for i in K.disasm_n(b,va,scan):
        if i.id==0: continue
        if i.mnemonic=='call' and i.op_str.startswith('0x'):
            out.add(int(i.op_str,16))
            # stop after first ret for tight forwarders
        if i.mnemonic=='ret': break
    return out

c6_320=0; c6_380=0; c5_380=0; c5_320=0
examples6=[]; examples5=[]
vft_count=0
for s in [b.sec('.rdata')]:
    buf=b.data[s['raw']:s['raw']+s['rawsize']]
    for i in range(0,len(buf)-3,4):
        col=struct.unpack_from('<I',buf,i)[0]
        if not (0x7e0000<=col<0xb80000): continue
        r=K.rtti_from_col(b,col)
        if not r: continue
        vft=s['va']+i+4
        sl=[]
        for k in range(200):
            try: val=b.u32(vft+4*k)
            except Exception: break
            if not b.in_text(val): break
            sl.append(val)
        vft_count+=1
        if len(sl)>6:
            calls=body_calls(sl[6])
            if 0x410320 in calls:
                c6_320+=1
                if len(examples6)<8: examples6.append((r['name'],vft,hex(sl[6])))
            if 0x410380 in calls: c6_380+=1
        if len(sl)>5:
            calls=body_calls(sl[5])
            if 0x410380 in calls:
                c5_380+=1
                if len(examples5)<8: examples5.append((r['name'],vft,hex(sl[5])))
            if 0x410320 in calls: c5_320+=1
print(f"COL-rooted vftables scanned: {vft_count}")
print(f"v[6] body calls 0x410320 (Save wrapper): {c6_320}")
print(f"v[6] body calls 0x410380 (Load wrapper): {c6_380}  <- cross-contamination")
print(f"v[5] body calls 0x410380 (Load wrapper): {c5_380}")
print(f"v[5] body calls 0x410320 (Save wrapper): {c5_320}  <- cross-contamination")
print("examples v[6]->0x410320:", examples6)
print("examples v[5]->0x410380:", examples5)
