#!/usr/bin/env python3
"""S16-K3 T2: redo the 4 [已证] entries with CORRECT premises.
For each: RTTI class attribution (COL+0xC->TD+8 inline name), own-vtable slot location
(boundary from .rdata), full body disasm to ret (no truncation), semantics.
Also: verify 0x410320 is non-virtual (0 vtable occurrences), count v[6]/v[5] forwarders,
dump 0x4C9150 stub, 0x410320 / 0x410380 / 0x410410 bodies.
"""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K3\work")
import k3_lib as K
b=K.Bin()

TARGETS = [0x6CDFD0,0x6CE220,0x6CE8D0,0x6CEFE0]

def dump_body_full(va, maxb=0x500):
    """Linear disasm from va until we've passed a ret at the outer level.
    We print a generous window but mark the first ret at/after depth 0."""
    insns=K.disasm_n(b, va, maxb)
    lines=[]; end=None
    for i in insns:
        if i.id==0:
            lines.append(K.fmt(i)); continue
        lines.append(K.fmt(i))
        if i.mnemonic in ('ret','retf') and end is None:
            end=i.address+i.size
        # keep dumping a little past first ret to show it's the function end,
        # but stop after 8 more instructions to avoid walking into next func.
        if end is not None and i.address>=end+24:
            break
    return "\n".join(lines), end

print("########## A) 0x410320 virtuality check ##########")
# scan all .rdata dwords for value 0x410320 that are vtable slots (i.e. preceded by COL chain)
occ=K.find_u32(b,0x410320)
print(f"raw dword occurrences of 0x410320 in .rdata/.data: {len(occ)}")
vslot_hits=[]
for a in occ:
    # is it a vtable slot? check preceding dwords for COL pattern at a-4-4*k
    is_slot=False
    for k in range(0,120):
        base=a-4*k
        # try each candidate vft start = a-4*slot_index, with COL at vft-4
        colva=a-4*k-4
        try: col=b.u32(colva)
        except Exception: continue
        r=K.rtti_from_col(b,col)
        if r:
            is_slot=True; break
    if is_slot: vslot_hits.append(a)
print(f"vtable-slot occurrences of 0x410320: {len(vslot_hits)} -> {[hex(x) for x in vslot_hits]}")
print("Also scanning every COL-rooted vtable's slots explicitly:")
slot_count=0; details=[]
for s in [b.sec('.rdata')]:
    buf=b.data[s['raw']:s['raw']+s['rawsize']]
    for i in range(0,len(buf)-3,4):
        col=struct.unpack_from('<I',buf,i)[0]
        if not (0x7e0000<=col<0xb80000): continue
        r=K.rtti_from_col(b,col)
        if not r: continue
        vft=s['va']+i+4
        for k in range(200):
            try: val=b.u32(vft+4*k)
            except Exception: break
            if val==0x410320:
                slot_count+=1; details.append((vft,col,r['name'],k))
            if not b.in_text(val): break
print(f"0x410320 found as slot value {slot_count} times across all COL-rooted vtables")
for d in details[:20]: print("  ",hex(d[0]),hex(d[1]),d[2],"slot",d[3])

print("\n########## B) helper bodies ##########")
for va,label in [(0x4C9150,"0x4C9150 pure-virtual stub"),
                 (0x410320,"0x410320 (S16-K2 called this 'AbstractClass::Save')"),
                 (0x410380,"0x410380 (Load wrapper)"),
                 (0x410410,"0x410410 AbstractClass::Save base block (slot13)")]:
    body,end=dump_body_full(va)
    print(f"\n--- {label} ---")
    print(body)

print("\n########## C) v[6]/v[5] forwarder census (how many classes forward Save/Load wrappers) ##########")
c6=0; c5=0; names6=[]; names5=[]
for s in [b.sec('.rdata')]:
    buf=b.data[s['raw']:s['raw']+s['rawsize']]
    for i in range(0,len(buf)-3,4):
        col=struct.unpack_from('<I',buf,i)[0]
        if not (0x7e0000<=col<0xb80000): continue
        r=K.rtti_from_col(b,col)
        if not r: continue
        vft=s['va']+i+4
        slots=[]
        for k in range(200):
            try: val=b.u32(vft+4*k)
            except Exception: break
            if not b.in_text(val): break
            slots.append(val)
        if len(slots)>6 and slots[6]==0x410320:
            c6+=1; names6.append((r['name'],vft,r['off']))
        if len(slots)>5 and slots[5]==0x410380:
            c5+=1; names5.append((r['name'],vft,r['off']))
print(f"tables with v[6]==0x410320: {c6}; with v[5]==0x410380: {c5}")
print("v[6] classes sample:", names6[:12])
print("v[5] classes sample:", names5[:12])
# cross-contamination: any table v[6]==0x410380 or v[5]==0x410320?
cross6to380=0; cross5to320=0
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
        if len(sl)>6 and sl[6]==0x410380: cross6to380+=1
        if len(sl)>5 and sl[5]==0x410320: cross5to320+=1
print(f"cross: v[6]==0x410380: {cross6to380}; v[5]==0x410320: {cross5to320}")

print("\n########## D) the 4 target entries ##########")
for va in TARGETS:
    print(f"\n\n========== ENTRY {va:08X} ==========")
    # 1) RTTI class attribution: find vftable containing this slot
    hits=K.find_any_vftable_slot(b,va)
    print(f"[RTTI] vftable slots containing {va:08X}:")
    for h in hits:
        print(f"   vft={h[0]:08X} col={h[1]:08X} class='{h[2]}' slot={h[3]} off={h[4]}")
    # 2) full body
    body,end=dump_body_full(va)
    print(f"[BODY] first ret ends at {end:08X}" if end else "[BODY] no ret found!")
    print(body)
    # 3) call targets in body
    insns=K.disasm_n(b,va,0x600)
    calls=[]
    for i in insns:
        if i.id==0: continue
        if i.mnemonic in ('call','jmp') and i.op_str.startswith('0x'):
            calls.append((i.address,i.mnemonic,int(i.op_str,16)))
    print(f"[CALLS in window]: {[(hex(a),m,hex(t)) for a,m,t in calls]}")
