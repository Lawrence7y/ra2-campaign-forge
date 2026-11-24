#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FINAL T2/T3 evidence assembly for S15-K2.
Sources of truth:
  - raw bytes of gamemd.exe (capstone skipdata=True, pefile) -- primary
  - YRpp GeneralDefinitions.h TriggerAction/AbstractType enums -- source ground truth
  - function_atlas.tsv (entry+size) -- one channel
  - coverage.tsv (current grade/name) -- baseline
Produces:
  - EVIDENCE/PROMOTIONS.tsv  (entry, oldname, newname, oldgrade, newgrade, action_id, evidence)
  - coverage_delta.tsv
Only writes inside S15-K2. Does NOT touch COVERAGE/coverage.tsv.
"""
import sys, os, csv, re, struct
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
import capstone
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
HD  = os.path.join(ROOT, r"YRpp\GeneralDefinitions.h")
CARD= os.path.join(ROOT, r"lead\next_re_20261117_r14\S15-K2")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)
b=A.Bin()
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True

# ---- parse YRpp enums ----
def parse_enum(path, name):
    txt=open(path,encoding="utf-8",errors="replace").read()
    mm=re.search(r"enum class "+re.escape(name)+r"\s*:\s*unsigned int\s*\{(.*?)\}",txt,re.S)
    d={}
    if not mm: return d
    for line in mm.group(1).splitlines():
        lm=re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(0x[0-9A-Fa-f]+|\d+)\s*,?",line)
        if lm:
            v=int(lm.group(2),16) if lm.group(2).lower().startswith("0x") else int(lm.group(2))
            d[v]=lm.group(1)
    return d
TRIG=parse_enum(HD,"TriggerAction")
ABS =parse_enum(HD,"AbstractType")
print(f"TriggerAction enum entries={len(TRIG)} max={max(TRIG):#x}({max(TRIG)})")
print(f"AbstractType  enum entries={len(ABS)} max={max(ABS)}")

# ---- baseline ----
cov=rd(COV); atl={norm(r["entry"]):r for r in rd(ATL)}
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]
by_entry={norm(r["entry"]):r for r in s15}

# ---- GetSize + WhatAmI promotions (slot12 / slot11 of 6 RTTI-confirmed classes) ----
VTSLOT = {  # class: (vtable, COL, slot11 VA, slot11 imm, slot12 VA, slot12 imm)
 "TActionClass":(0x7F443C,0x80BAF0,0x6E4640,0x2F,0x6E4630,0x94),
 "TagClass":    (0x7F44E0,0x80BBA0,0x6E58A0,0x2C,0x6E5890,0x38),
 "TagTypeClass":(0x7F45C4,0x80BCF0,0x6E6490,0x2D,0x6E64A0,0xA4),
 "TEventClass": (0x7F5578,0x80C5E0,0x71FA60,0x30,0x71FA50,0x58),
 "TriggerClass":(0x7F5858,0x80C968,0x726940,0x26,0x726930,0x48),
 "TriggerTypeClass":(0x7F5904,0x80CA20,0x727CA0,0x27,0x727CB0,0xB4),
}
promos=[]  # dict entry,old,new,oldg,newg,reason,ev
for cn,(vt,col,s11,imm11,s12,imm12) in VTSLOT.items():
    # re-verify bytes + RTTI live
    td=b.u32(col+0xC); nm=b.read(td+8,64).split(b"\x00")[0].decode(errors="replace")
    assert nm==f".?AV{cn}@@", (cn,nm)
    assert b.u32(vt-4)==col, (cn,hex(b.u32(vt-4)))
    assert b.u32(vt+11*4)==s11 and b.u32(vt+12*4)==s12, cn
    d11=b.read(s11,6); d12=b.read(s12,6)
    assert d11==bytes([0xB8])+struct.pack("<I",imm11)+b"\xc3", (cn,d11.hex())
    assert d12==bytes([0xB8])+struct.pack("<I",imm12)+b"\xc3", (cn,d12.hex())
    assert ABS[imm11] in cn, (cn,ABS.get(imm11))
    # WhatAmI slot11
    e11=f"{s11:08X}"; r11=by_entry.get(e11)
    if r11:
        promos.append(dict(entry=e11,old=r11["name"],new=f"{cn}::WhatAmI",oldg=r11["grade"],newg="[已证]",
          reason=f"vtable[{cn}] slot11={s11:#x} B8 {imm11:#x} C3; AbstractType[{imm11}]=ABS::{ABS[imm11]}; COL={col:#x}->TD->{nm}",
          ev="EVIDENCE/T2_vtable_verify.txt;EVIDENCE/T2_rtti_and_sub_callers.txt"))
    # GetSize slot12
    e12=f"{s12:08X}"; r12=by_entry.get(e12)
    if r12:
        promos.append(dict(entry=e12,old=r12["name"],new=f"{cn}::GetSize",oldg=r12["grade"],newg="[已证]",
          reason=f"vtable[{cn}] slot12={s12:#x} B8 {imm12:#x} C3 == ctor push {imm12:#x}->alloc; COL={col:#x}->TD->{nm}; shared stub 0x4C9150 not used",
          ev="EVIDENCE/T2_vtable_verify.txt;EVIDENCE/T2_alloc_sites.txt;EVIDENCE/T2_rtti_and_sub_callers.txt"))

# ---- Action implementations: parse handler region calls to sub_ rows ----
ACTION_BASE=0x6DFDEC
action=[b.u32(ACTION_BASE+4*i) for i in range(145)]
# handler order by address; each handler ends at next greater distinct target
uniq=sorted(set(action))
def handler_end(t):
    for u in uniq:
        if u>t: return u
    return 0x6DFDDB+9  # shared epilogue end
# collect direct calls inside [0x6DD8EE,0x6DFDDB+9)
region_start=min(action); region_end=0x6DFDDB+9
data=b.read(region_start, region_end-region_start)
call_sites={}  # target -> [site]
for ins in m.disasm(data,region_start):
    if ins.id==0: continue
    if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
        call_sites.setdefault(int(ins.op_str,16),[]).append(ins.address)

sub_entries={e for e,r in by_entry.items() if r["name"].strip().startswith("sub_") and r["grade"].strip()=="[未证]"}
def action_for_site(site):
    for i,t in enumerate(action):
        if t<=site<handler_end(t):
            return i
    return None

for e in sorted(sub_entries):
    va=int(e,16); sites=call_sites.get(va,[])
    acts=set()
    for s in sites:
        ai=action_for_site(s)
        if ai is not None: acts.add(ai)
    if len(acts)!=1: continue
    ai=list(acts)[0]; action_id=ai+1  # dec edx at 0x6DD8DA => 1-based
    aname=TRIG.get(action_id)
    if not aname: continue
    r=by_entry[e]
    promos.append(dict(entry=e,old=r["name"],new=f"TActionClass::{aname}",oldg=r["grade"],newg="[已证]",
      reason=f"Execute dispatch 0x6DFDEC[{ai}] (actionID={action_id}=TRIG::{aname}) handler {action[ai]:#x} contains `call {va:#x}` at {[hex(s) for s in sites]}; prologue dec edx => 1-based ID; thin-wrapper args pushed",
      ev="EVIDENCE/T2_action_map.txt;EVIDENCE/T2_action_handlers.txt;EVIDENCE/T2_action_index_verify.txt"))

# dedup by name first: if two sub_ rows map to same action name, keep only the one
# called at the handler ENTRY (first instruction of handler == call site), drop the rest.
byname={}
for p in promos:
    if p["new"].startswith("TActionClass::") and p["new"] not in ("TActionClass::GetSize","TActionClass::WhatAmI"):
        byname.setdefault(p["new"],[]).append(p)
for nm,pl in byname.items():
    if len(pl)>1:
        def is_entry_call(pp):
            # parse handler idx from reason
            m2=re.search(r"handler (\w+)",pp["reason"])
            if not m2: return False
            ht=int(m2.group(1),16)
            # check first insn at ht is a call to pp entry
            first=next((i for i in m.disasm(b.read(ht,8),ht) if i.id!=0),None)
            return first is not None and first.mnemonic=="call" and first.op_str.lower().endswith(pp["entry"].lower())
        keep=[pp for pp in pl if is_entry_call(pp)]
        keep=keep[:1] if keep else pl[:1]
        dropset={pp["entry"] for pp in pl if pp not in keep}
        promos=[p for p in promos if p["entry"] not in dropset]
        print(f"  [dedup] {nm}: kept {[k['entry'] for k in keep]}, dropped {sorted(dropset)}")
# Also drop sub_ rows whose call sites span >1 distinct action index (shared helpers, not impls).
drop2=set()
for p in promos:
    if not p["new"].startswith("TActionClass::") or p["new"] in ("TActionClass::GetSize","TActionClass::WhatAmI"): continue
    e=p["entry"]; va=int(e,16)
    acts={action_for_site(s) for s in call_sites_for(e)} if False else None
# (action_for_site/call_sites already computed above; recheck inline)
def csites(e):
    return call_sites.get(int(e,16),[])
for p in list(promos):
    if not p["new"].startswith("TActionClass::") or p["new"] in ("TActionClass::GetSize","TActionClass::WhatAmI"): continue
    acts={action_for_site(s) for s in csites(p["entry"])}
    if len(acts)!=1 or None in acts:
        print(f"  [multi-action drop] {p['entry']} {p['new']} acts={acts}")
        drop2.add(p["entry"])
promos=[p for p in promos if p["entry"] not in drop2]

seen=set(); final=[]
for p in promos:
    if p["entry"] in seen: continue
    seen.add(p["entry"]); final.append(p)

with open(os.path.join(CARD,"EVIDENCE","PROMOTIONS.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t"); w.writerow(["entry","old_name","new_name","old_grade","new_grade","reason","evidence_path"])
    for p in final: w.writerow([p["entry"],p["old"],p["new"],p["oldg"],p["newg"],p["reason"],p["ev"]])

# coverage_delta.tsv: only changed rows; full row schema per card
with open(os.path.join(CARD,"coverage_delta.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t")
    for p in sorted(final,key=lambda x:x["entry"]):
        r=by_entry[p["entry"]]
        sem=r["one_line_semantics"]
        if p["new"].endswith("::GetSize"): sem=f"{p['new']}: 返回本类对象尺寸常量 imm32; vtable槽12双点闭合"
        elif p["new"].endswith("::WhatAmI"): sem=f"{p['new']}: 返回 AbstractType 类型 ID; vtable槽11+YRPp枚举吻合"
        else: sem=f"{p['new']}: TActionClass::Execute 动作ID {p['reason'].split('actionID=')[1].split('=')[0]} 的实现体(跳表薄壳直call)"
        w.writerow([p["entry"],"S15",p["new"],sem,p["newg"],p["ev"]])

from collections import Counter
c=Counter(p["newg"] for p in final)
print(f"\nPROMOTIONS: {len(final)} rows (all -> [已证])")
for p in sorted(final,key=lambda x:x["entry"]):
    print(f"  {p['entry']} {p['old']:<28} -> {p['new']:<38}")
print(f"\nWrote EVIDENCE/PROMOTIONS.tsv and coverage_delta.tsv ({len(final)} data rows)")
