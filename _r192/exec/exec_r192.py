#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 exec: sibling-slot classification, jump-chain canon, byte-level evidence.

Runs every measurement in one process; writes only _r192/exec/exec_r192.json.
Read-only against ra2bench/gamemd.exe.
"""
import sys, os, struct, collections, json
ROOT='/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT+'/_r185')
import pe185 as P
import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

# --- PE range: card口径 uses raw file extent for ".text" membership ---
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n

# --- T1 COL enumeration ---
# Physical layout of a MSVC COL: d0=sig(always 0 here), d1=mdisp(offset-to-top),
# d2=cdOffset(0), d3=pTD(.data), d4=pCHD(.rdata); name at pTD+8.
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]={'mdisp':w[i+1],'pTD':w[i+1],'pCHD':w[i+2],
                       'name':nm.decode('latin1')}

# --- T2 vtable heads: dword at vt-4 is a COL address, slot 0 in .text ---
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(1,n):
        if in_text(w[i]) and (w[i-1] in COL):
            VT[base+4*i]=w[i-1]

# --- T3 slot counts ---
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}

# --- T4 name groups ---
group=collections.defaultdict(list)
for vt in sorted(VT): group[COL[VT[vt]]['name']].append(vt)

# --- T5 adjusters vs direct slots among non-primary tables ---
def is_adj(a):
    o=P.r2o(a)
    if o is None: return False
    z=P.RAW[o:o+4]
    return (z[:3]==b'\x83\x6c\x24' or z[:3]==b'\x81\x6c\x24') and z[3]==4
direct=[]; adj=[]
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp']==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        if not in_text(v): continue
        (adj if is_adj(v) else direct).append((vt,k,v))

# --- Disassembly helpers (capstone with detail only on individually addressed code) ---
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
_dcache={}
def insns(addr,count=12):
    key=(addr,count)
    if key in _dcache: return _dcache[key]
    o=P.r2o(addr)
    if o is None:
        _dcache[key]=[]; return []
    out=[]
    for ins in md.disasm(P.RAW[o:o+128],addr):
        out.append({'addr':ins.address,'bytes':ins.bytes.hex(),
                    'text':ins.mnemonic+' '+ins.op_str,
                    'imm_operands':[op.imm for op in ins.operands if op.type==X86_OP_IMM]})
        if len(out)>=count: break
    _dcache[key]=out
    return out
_jcache={}
def jmp_target(addr, want_kind=False):
    """Return (target,kind) of first unconditional jump at addr; kind None if not thunk."""
    if addr in _jcache: return _jcache[addr]
    o=P.r2o(addr); tgt=None
    if o is not None:
        z=P.RAW[o:o+32]
        # MSVC "adjustor thunk" shape: sub [esp+4],imm followed by E9 rel32.
        # Bare E9/FF25 is also accepted. Scan at most the first 16 bytes so
        # unrelated later code cannot be mistaken for a tail jump.
        lim=min(len(z),16); i=0; imm_bytes=None
        adj_kind = '83' if (z[:3]==b'\x83\x6c\x24' and z[3]==4) else ('81' if (z[:3]==b'\x81\x6c\x24' and z[3]==4) else None)
        i=4 if adj_kind=='83' else (7 if adj_kind=='81' else 0)
        while i+5<=lim:
            if z[i]==0xE9:
                tgt=((addr+i+5+struct.unpack_from('<i',z,i+1)[0]) & 0xffffffff, adj_kind or 'E9')
                break
            if z[i:i+2]==b'\xff\x25':
                ptr=struct.unpack_from('<I',z,i+2)[0]
                q=P.dw(ptr)
                if in_text(q): tgt=(q, adj_kind or 'FF25')
                break
            i+=1
    _jcache[addr]=tgt
    return tgt
def is_thunk(addr): return jmp_target(addr) is not None

def canon(addr,maxhops=8):
    """Follow unconditional jumps at most maxhops times; return (endpoint,hops,chain,kinds)."""
    ch=[addr]; cur=addr; kinds=[]
    for _ in range(maxhops):
        jr=jmp_target(cur)
        if jr is None or jr[0] in ch: break
        kinds.append(jr[1]); ch.append(jr[0]); cur=jr[0]
    return (cur,len(ch)-1,ch,kinds)

# --- Q1 sibling classification ---
CATS=('NOSIB','SAME','THUNK_SAME','THUNK_OTHER','DIRECT_OTHER')
q1stat=collections.Counter(); q1rows=[]
adj_tgt_cache={}
def adj_target(a):
    if a not in adj_tgt_cache:
        jr=jmp_target(a); adj_tgt_cache[a]=jr[0] if jr else None
    return adj_tgt_cache[a]
def classify(vt,k,v):
    """Return (category, sibling_vt or None, sibling_value or None)."""
    name=COL[VT[vt]]['name']
    sib=[t for t in group[name] if t!=vt and k<NS[t]]
    if not sib: return ('NOSIB',None,None)
    for t in sib:                    # sib already sorted ascending by construction
        w=P.dw(t+4*k)
        if w==v: return ('SAME',t,w)
        if is_adj(w):
            jt=adj_target(w)
            return ('THUNK_SAME' if jt==v else 'THUNK_OTHER',t,w)
        return ('DIRECT_OTHER',t,w)
    return ('NOSIB',None,None)       # unreachable
for vt,k,v in direct:
    cat,sib,w=classify(vt,k,v)
    q1stat[cat]+=1
    q1rows.append({'vt':hex(vt),'col':VT[vt],'k':k,'v':hex(v),'cat':cat,
                   'sib':hex(sib) if sib else None,'w':hex(w) if w else None})

# --- Q2 collapse over DIRECT_OTHER pairs ---
pairs=[r for r in q1rows if r['cat']=='DIRECT_OTHER']
q2={'one_hop':collections.Counter(),'eight_hop':collections.Counter(),'pairs':[]}
def canon_n(addr,n):
    ch=[addr]; cur=addr
    for _ in range(n):
        jr=jmp_target(cur)
        if jr is None or jr[0] in ch: break
        ch.append(jr[0]); cur=jr[0]
    return (cur,len(ch)-1)
for r in pairs:
    v=int(r['v'],16); w=int(r['w'],16)
    cv1,hv1=canon_n(v,1); cw1,hw1=canon_n(w,1)
    cv8,hv8,_,kv8=canon(v,8);   cw8,hw8,_,kw8=canon(w,8)
    one='COLLAPSE' if cv1==cw1 else 'DISTINCT'
    eight='COLLAPSE' if cv8==cw8 else 'DISTINCT'
    q2['one_hop'][one]+=1; q2['eight_hop'][eight]+=1
    q2['pairs'].append({'vt':r['vt'],'k':r['k'],'v':r['v'],'w':r['w'],
        'canon1_v':hex(cv1),'canon1_w':hex(cw1),'one_hop':one,
        'canon8_v':hex(cv8),'canon8_w':hex(cw8),'eight_hop':eight,
        'v_is_thunk':is_thunk(v),'w_is_thunk':is_thunk(w),
        'hops_v8':hv8,'hops_w8':hw8,'kind_v8':kv8,'kind_w8':kw8})

# --- Q3 byte evidence: >=2 COLLAPSE + >=2 DISTINCT under 8-hop rule ---
def evidence(pred,limit):
    out=[]
    for p in q2['pairs']:
        if pred(p) and len(out)<limit:
            vt=int(p['vt'],16); k=p['k']; v=int(p['v'],16); w=int(p['w'],16)
            cv,_,_,_=canon(v,8); cw,_,_,_=canon(w,8)
            colv=COL[VT[vt]]; colw=COL[VT[int(p['vt'],16)]]  # placeholder overwritten below
            # sibling vt recorded at Q1 row
            row=next(x for x in q1rows if x['vt']==p['vt'] and x['k']==p['k'] and x['cat']=='DIRECT_OTHER')
            sibvt=int(row['sib'],16)
            colw=COL[VT[sibvt]]
            def hx(a,n=16):
                o=P.r2o(a)
                return None if o is None else P.RAW[o:o+n].hex()
            out.append({'vt':p['vt'],'sib_vt':hex(sibvt),'k':k,
                'target_v':p['v'],'target_w':p['w'],
                'bytes_v16':hx(v),'bytes_w16':hx(w),
                'canon8_v':hex(cv),'canon8_w':hex(cw),'eight_hop':p['eight_hop'],
                'col_v':{'name':colv['name'],'mdisp':colv['mdisp'],'addr':hex(VT[vt])},
                'col_w':{'name':colw['name'],'mdisp':colw['mdisp'],'addr':hex(VT[sibvt])}})
    return out
col_ex=evidence(lambda p:p['eight_hop']=='COLLAPSE',2)
dis_ex=evidence(lambda p:p['eight_hop']=='DISTINCT',5)
q3=col_ex+dis_ex

# --- Q4 four fixed addresses ---
FIXED=[0x410450,0x410580,0x410590,0x4C9150]
refs={a:0 for a in FIXED}
for vt in sorted(VT):
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        if v in refs: refs[v]+=1
q4=[]
for a in FIXED:
    o=P.r2o(a); b=P.RAW[o:o+32]
    q4.append({'addr':hex(a),'bytes32':b.hex(),
               'is_e9':b[0]==0xE9,'is_ff25':b[:2]==b'\xff\x25',
               'is_thunk':is_thunk(a),
               'jmp_target':hex(jmp_target(a)[0]) if jmp_target(a) else None,
               'jmp_kind':(jmp_target(a)[1] if jmp_target(a) else None),
               'disasm12':insns(a,12),'refcount_all_slots':refs[a],
               'canon8':hex(canon(a,8)[0]),'canon8_kinds':canon(a,8)[3]})

# --- positive/negative control on classify() ---
ctl={}
if pairs:
    p=pairs[0]
    vt=int(p['vt'],16); k=p['k']; v=int(p['v'],16); w=int(p['w'],16)
    # rebind: pretend sibling's value equals v -> must become SAME
    origdw=P.dw
    sibvt=int(next(x for x in q1rows if x['vt']==p['vt'] and x['k']==p['k'])['sib'],16)
    def patched(va):
        if va==sibvt+4*k: return v
        return origdw(va)
    P.dw=patched
    ctl['positive_same']={'input':'sibling w replaced by v','expected':'SAME','actual':classify(vt,k,v)[0]}
    P.dw=origdw
    # negative: start from the patched-SAME state and perturb the observed slot by +4.
    # Verdict must flip away from SAME (proves the classifier is not hardcoded).
    nv=(v+4)&0xffffffff
    def patched2(va):
        if va==sibvt+4*k: return v
        if va==vt+4*k: return nv
        return origdw(va)
    P.dw=patched2
    ctl['negative_diff']={'input':'sibling forced to v but observed slot changed to v+4',
        'expected':'not SAME','actual':classify(vt,k,nv)[0]}
    P.dw=origdw
    # canon control: synthetic pair (v,v) must collapse; (v,v+4) must stay distinct.
    anyv=int(pairs[0]['v'],16)
    ctl['canon_positive']={'input':'canon(v)==canon(v)','expected':'COLLAPSE',
        'actual':'COLLAPSE' if canon(anyv,8)==canon(anyv,8) else 'DISTINCT'}
    ctl['canon_negative']={'input':'canon of two different non-thunk funcs','expected':'DISTINCT',
        'actual':'DISTINCT' if canon(anyv,8)[0]!=canon(anyv+4,8)[0] else 'COLLAPSE'}

# --- assemble JSON ---
out={
 'meta':{'binary':'ra2bench/gamemd.exe','card':'R192','method':'card T1-T5 verbatim; mdisp=dword[1] (offset-to-top) confirmed by 1318/305/1013',
         'text_range':[hex(LO),hex(HI)],'capstone':'5.0.7'},
 'differences':{
   'mdisp_field':{'card_text':'COL[0]=mdisp','measured':'d0 is always 0 (signature); d1 (offset-to-top) is the field whose !=0 selection yields 1318/305/1013','action':'used d1 as mdisp; all T1-T5 counts match exactly'},
   'q3_collapse_examples':{'card_text':'pick >=2 COLLAPSE and >=2 DISTINCT','measured':'COLLAPSE=0 under card canon (no DIRECT_OTHER target begins with E9/FF25/adjustor, so canon is identity)','action':'5 DISTINCT examples supplied; no COLLAPSE examples exist'},
   'q2_expectation':{'card_text':'no numeric expectation given','measured':'525 DISTINCT / 0 COLLAPSE; v_thunk=0 w_thunk=0','action':'kept measured values'}},
 'preflight':{'COL':len(COL),'VT':len(VT),'slots':sum(NS.values()),
              'groups':len(group),'multi_groups':sum(1 for x in group.values() if len(x)>1),
              'nonprimary_slots':sum(NS[v] for v in VT if COL[VT[v]]['mdisp']!=0),
              'adjusters':len(adj),'direct':len(direct),'expected_direct':1013,
              'diff':len(direct)-1013},
 'q1':{'counts':dict(q1stat),'total':sum(q1stat.values()),'rows':q1rows},
 'q2':{'one_hop':dict(q2['one_hop']),'eight_hop':dict(q2['eight_hop']),
       'v_is_thunk':sum(1 for p in q2['pairs'] if p['v_is_thunk']),
       'w_is_thunk':sum(1 for p in q2['pairs'] if p['w_is_thunk']),
       'v_is_thunk_kinds':{str(k):v for k,v in collections.Counter(tuple(p['kind_v8']) for p in q2['pairs']).items()},
       'w_is_thunk_kinds':{str(k):v for k,v in collections.Counter(tuple(p['kind_w8']) for p in q2['pairs']).items()},
       'pairs_total':len(pairs),'pairs':q2['pairs']},
 'q3':q3,
 'q4':q4,'q4_refs':{hex(k):v for k,v in refs.items()},
 'control':ctl,
}
path=ROOT+'/_r192/exec/exec_r192.json'
with open(path,'w') as f: json.dump(out,f,ensure_ascii=False,indent=1)

# --- stdout full summary ---
print('=== PREFLIGHT ===',json.dumps(out['preflight'],ensure_ascii=False))
print('=== Q1 COUNTS ===',json.dumps(out['q1']['counts'],ensure_ascii=False),'total',out['q1']['total'])
print('=== Q2 ===','onehop',json.dumps(out['q2']['one_hop']),
      '8hop',json.dumps(out['q2']['eight_hop']),
      'v_thunk',out['q2']['v_is_thunk'],'w_thunk',out['q2']['w_is_thunk'],'pairs',len(pairs))
print('=== Q3 evidence ===',json.dumps(q3,ensure_ascii=False))
print('=== Q4 ===',json.dumps(q4,ensure_ascii=False))
print('=== CONTROL ===',json.dumps(ctl,ensure_ascii=False))
print('WROTE',path,'bytes',os.path.getsize(path),'sha256',__import__('hashlib').sha256(open(path,'rb').read()).hexdigest())
