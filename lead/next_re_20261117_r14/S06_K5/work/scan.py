
import sys, struct, json, csv
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06_K5'
cov_rows=K.cov_rows(); atl=K.atl_map(); cov={r['entry'].upper():r for r in cov_rows}
# S06 universe (on-disk), intersect atlas
s06=[r for r in cov_rows if r['subsystem'].strip().upper()=='S06']
s06_int=[r for r in s06 if r['entry'].upper() in atl]
print("S06 rows=%d  S06∩atlas=%d"%(len(s06),len(s06_int)))

ANCHOR_CALLS={0x5FDD20:'tiberium_type_lookup',0x487190:'IncreaseTiberium',0x4838E0:'can_spread_helper',0x483710:'grow_single',0x483780:'grow_neighbors',0x65C7E0:'map_getter',0x5657A0:'cell_getter'}
CONST_REFS={0x7E3810:'1e-5'}
FIELDS={0x44:'overlay_type_id',0x11C:'cell_state',0x11E:'cell_density',0xA0:'type_growth_chance_A0',0xB0:'type_growth_chance_B0',0xE4:'type_or_cell_E4'}
GLOBALS={0xA8B230:'rules_global',0xB0F4EC:'tiberium_type_array',0x89F688:'dir_table',0xA8E9A0:'global_a8e9a0'}

def sigs_for(va,size):
    sig={'calls':set(),'consts':set(),'fields':set(),'globals':set()}
    for i in K.dis(va,size):
        op=i.op_str.lower()
        if i.mnemonic=='call' and op.startswith('0x'):
            t=int(op,16)
            if t in ANCHOR_CALLS: sig['calls'].add(ANCHOR_CALLS[t])
        if op.startswith('0x'):
            try: imm=int(op,16)
            except: imm=None
            if imm in CONST_REFS: sig['consts'].add(CONST_REFS[imm])
            if imm in GLOBALS: sig['globals'].add(GLOBALS[imm])
        # field offsets: match [reg + 0xNN] or [reg + 0xNNn]
        import re
        m=re.findall(r'\[[^]]+0x([0-9a-f]+)\]',op)
        for hx in m:
            off=int(hx,16)
            if off in FIELDS: sig['fields'].add(FIELDS[off])
    return sig

# Channel A: atlas-driven
candA=[]
for r in s06_int:
    e=r['entry'].upper(); va=int(e,16); sz=int(atl[e]['size'])
    if r['grade'].strip()=='\u5df2\u8bc1': continue  # [已证]
    sig=sigs_for(va,min(sz,4096))
    core=bool(sig['calls'] & {'tiberium_type_lookup','IncreaseTiberium','can_spread_helper','grow_single','grow_neighbors'}) or bool(sig['consts']) or ('dir_table' in sig['globals'])
    if core:
        candA.append((e,r['grade'].strip(),r['name'].strip(),sz,sorted(sig['calls']),sorted(sig['consts']),sorted(sig['fields']),sorted(sig['globals'])))
print("\nChannel A candidates (core growth signal):",len(candA))
for c in candA: print("  ",c)

# Channel B: raw E8 scan, atlas-independent
text_start,text_end,raw_ptr,raw_sz=K.SECS[0]
data=K.DATA
call_sites={k:[] for k in ANCHOR_CALLS}
for off in range(raw_ptr, raw_ptr+raw_sz-5):
    if data[off]!=0xE8: continue
    rel=struct.unpack_from('<i',data,off+1)[0]
    va=text_start+(off-raw_ptr)
    tgt=(va+5+rel)&0xFFFFFFFF
    if tgt in ANCHOR_CALLS:
        call_sites[tgt].append(va)
print("\nChannel B raw E8 call-site counts:")
for t,sites in call_sites.items():
    print("  0x%08X %-22s %d sites"%(t,ANCHOR_CALLS[t],len(sites)))

# Attribute call sites to functions by interval containment using COVERAGE entries (not atlas)
cov_entries=sorted([(int(r['entry'],16), r['entry'].upper(), r['grade'].strip(), r['name'].strip(), r['subsystem'].strip().upper()) for r in cov_rows])
import bisect
starts=[x[0] for x in cov_entries]
def attr(site):
    idx=bisect.bisect_right(starts,site)-1
    if idx>=0:
        s,e,g,n,sub=cov_entries[idx]
        # check site within atlas size of that entry if available
        a=atl.get(e)
        if a and site < s+int(a['size']): return (e,g,n,sub)
        return (e,g,n,sub)+('(no-atlas-bound)',)
    return None
interesting={0x483710,0x483780,0x4838E0,0x487190,0x5FDD20}
print("\nCall sites for growth functions, attributed by coverage-interval containment:")
for t in [0x483710,0x483780,0x4838E0]:
    print("  TARGET 0x%08X (%s):"%(t,ANCHOR_CALLS[t]))
    for site in call_sites[t]:
        a=attr(site)
        print("    site 0x%08X -> %s"%(site,a))

# Save
res={'channelA':candA,'channelB_counts':{hex(k):len(v) for k,v in call_sites.items()},
     'callsites':{hex(k):v for k,v in call_sites.items()},
     's06_rows':len(s06),'s06_int':len(s06_int)}
json.dump(res,open(OUT+'\\work\\candidate_scan.json','w',encoding='utf-8'),indent=1,ensure_ascii=False)
print("\nsaved work/candidate_scan.json")
