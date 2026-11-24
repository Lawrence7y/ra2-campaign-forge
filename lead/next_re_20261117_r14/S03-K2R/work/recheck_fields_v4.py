#!/usr/bin/env python3
"""S03-K2R: redo S03-K2 #7 field write/read counts, three access forms.

Method scope is RTTI/vtable-derived (no function_atlas entry+size): own virtual slots plus
vft-writing ctors/dtors. The instruction universe is a full-image capstone(skipdata=True)
linear sweep of .text; all sites are instruction-boundary validated. Three forms:
  A  absolute [imm32]
  B  register base: thiscall ecx propagated through mov reg,reg / immediate-loaded base
  C  pointer chain: [global] -> [base+idx*4] -> [obj+off]
The absolute-only baseline is form A only; missed = A-only to full (B+C).
"""
from __future__ import annotations
import os, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import Image, fmt_ins, sha256_file

IMG=Image()
OUT=[]
def p(s=""):
    OUT.append(str(s)); print(s)

p("sha256="+sha256_file())
p("imageBase=0x%X text=[0x%X,0x%X)" % (IMG.ib,IMG.text_va,IMG.text_va+len(IMG.text_bytes)))
insns=IMG.disasm_text(); idx={x['addr']:i for i,x in enumerate(insns)}
p("linear_sweep_insns=%d byte_pseudo=%d" % (len(insns),sum(1 for x in insns if x['mn']=='.byte')))

BUF_METHODS={
 0x432610:'v0_dtor',0x401940:'v1',0x431E80:'v2',0x65D150:'v3',0x65D190:'v4',
 0x431F10:'v5',0x431F30:'v6',0x431F70:'v7',0x431F50:'v8',0x4322A0:'v9',
 0x4324B0:'v10',0x4325A0:'v11',0x432050:'v12',0x4325C0:'v13',0x65D1F0:'v14',
 0x65D240:'v15',0x65CA70:'v16',0x431B20:'ctor',0x431B80:'dtor'
}
RAW_METHODS={
 0x65D3A0:'v0_dtor',0x401940:'v1',0x65CAC0:'v2',0x65D150:'v3',0x65D190:'v4',
 0x65CBF0:'v5',0x65D420:'v6',0x65CB50:'v7',0x65CB30:'v8',0x65CCE0:'v9',
 0x65CF00:'v10',0x65D0D0:'v11',0x65CDD0:'v12',0x65CCA0:'v13',0x65D1F0:'v14',
 0x65D240:'v15',0x65CA70:'v16',0x65CA00:'nondelete_dtor',0x65CA80:'ctor'
}
FIELDS=[('BufferIOFileClass',BUF_METHODS,[0x24,0x29,0x30,0x34]),
        ('RawFileClass',RAW_METHODS,[0x14,0x18,0x20,0x24])]
ALL_STARTS=set(BUF_METHODS)|set(RAW_METHODS)

def method_end(a):
    # Audit-literal lane: stop at the first ret from entry (the prior VERDICT used this convention).
    i=idx[a]
    if insns[i]['mn'] in ('ret','retf'): return a+insns[i]['size']
    # thunk entry 0x65D1F0 is itself the only instruction of this slot; keep it in range
    if any(o['type']=='mem' and o.get('disp') in (0x14,0x18,0x20,0x24,0x29,0x30,0x34) for o in insns[i]['ops']): return a+insns[i]['size']
    for x in insns[i+1:i+1200]:
        if x['mn'] in ('ret','retf'): return x['addr']+x['size']
    return insns[min(i+1199,len(insns)-1)]['addr']+16

def classify_rw(x,k):
    # vtable slot call [reg+disp] is control transfer, never a data field read.
    if x['mn'] in ('call','jmp'): return []
    mn=x['mn']
    out=[]
    if k==0 and mn not in ('cmp','test','push'): out.append('W')
    if k>0 or mn in ('cmp','test'): out.append('R')
    if mn in ('xchg','xadd','cmpxchg'): return ['W']
    return out

def form_of(op,thisregs,immbase,ptrbase):
    if op['base'] is None and op['index'] is None: return ('A_abs',0)
    b=op.get('base')
    if b in ptrbase: return ('C_ptrarray',ptrbase[b])
    if b in immbase: return ('B_regbase',immbase[b])
    if b in thisregs: return ('B_regbase',0)  # thiscall this propagated from ecx
    return (None,None)

sites=[]
excluded=collections.defaultdict(int)
for cls,methods,offs in FIELDS:
    for fn,tag in methods.items():
        if fn not in idx:
            p("WARN not boundary %08X %s" % (fn,tag)); continue
        end=method_end(fn)
        thisregs={'ecx'}; immbase={}; ptrbase={}
        for x in insns[idx[fn]:]:
            if x['addr']>=end and not (x['addr']==fn and insns[idx[fn]]['mn']!='ret'): break
            mn=x['mn']; ops=x['ops']
            collect_this=set(thisregs); collect_imm=dict(immbase); collect_ptr=dict(ptrbase)
            # thiscall propagation and base-register setup
            if mn=='mov' and len(ops)==2 and ops[0]['type']=='reg' and ops[1]['type']=='reg':
                d,s=ops[0]['reg'],ops[1]['reg']
                if d!=s:
                    if s in thisregs: thisregs.add(d)
                    else: thisregs.discard(d)
                    if s in immbase: immbase[d]=immbase[s]
                    else: immbase.pop(d,None)
                    if s in ptrbase: ptrbase[d]=ptrbase[s]
                    else: ptrbase.pop(d,None)
            elif mn=='mov' and len(ops)==2 and ops[0]['type']=='reg' and ops[1]['type']=='imm':
                d=ops[0]['reg']; thisregs.discard(d); ptrbase.pop(d,None); immbase[d]=ops[1]['imm']
            elif mn=='mov' and len(ops)==2 and ops[0]['type']=='reg' and ops[1]['type']=='mem':
                d=ops[0]['reg']; mo=ops[1]
                if mo['base'] is None and mo['index'] is None:
                    thisregs.discard(d); ptrbase.pop(d,None); immbase[d]=mo['disp']
                elif mo['base'] and mo['index'] and mo['scale']==4:
                    if mo['base'] in thisregs or mo['base'] in immbase or mo['base'] in ptrbase:
                        thisregs.discard(d); immbase.pop(d,None); ptrbase[d]=mo['base']
                else:
                    thisregs.discard(d); immbase.pop(d,None); ptrbase.pop(d,None)
            elif mn in ('lea','pop','xor','sub','add','inc','dec','and','or') and ops and ops[0]['type']=='reg':
                d=ops[0]['reg']; thisregs.discard(d); immbase.pop(d,None); ptrbase.pop(d,None)
            # collect field accesses
            for k,op in enumerate(ops):
                if op['type']!='mem' or op.get('disp') not in offs: continue
                if x['mn']=='call':
                    excluded[(cls,op['disp'])] += 1
                    continue
                modes=classify_rw(x,k)
                if not modes: continue
                form,anchor=form_of(op,collect_this,collect_imm,collect_ptr)
                if form is None: continue
                for mode in modes:
                    sites.append(dict(cls=cls,off=op['disp'],fn=fn,tag=tag,addr=x['addr'],
                                      rw=mode,form=form,anchor=anchor,ins=x))
# dedup by unique site+mode; prefer C over B over A if multiple bases match
prio={'C_ptrarray':3,'B_regbase':2,'A_abs':1}
best={}
for r in sites:
    key=(r['cls'],r['off'],r['addr'],r['rw'])
    if key not in best or prio[r['form']]>prio[best[key]['form']]: best[key]=r
sites=sorted(best.values(),key=lambda r:(r['addr'],r['cls'],r['off']))

p("\n=== FINAL COUNTS: three forms, class-method-scoped ===")
p("class\toffset\tW\tR\tA_W\tA_R\tB_W\tB_R\tC_W\tC_R\tabs_only_W\tabs_only_R\tmissed_W\tmissed_R\tvcall_excluded")
summary={}
for cls,methods,offs in FIELDS:
    for off in offs:
        cs=[r for r in sites if r['cls']==cls and r['off']==off]
        C=lambda rw,form=None: sum(1 for r in cs if r['rw']==rw and (form is None or r['form']==form))
        W,R=C('W'),C('R')
        aw,ar=C('W','A_abs'),C('R','A_abs'); bw,br=C('W','B_regbase'),C('R','B_regbase')
        cw,cr=C('W','C_ptrarray'),C('R','C_ptrarray')
        summary[(cls,off)]=(W,R,aw,ar,bw,br,cw,cr)
        p(f"{cls}\t+0x{off:02X}\t{W}\t{R}\t{aw}\t{ar}\t{bw}\t{br}\t{cw}\t{cr}\t{aw}\t{ar}\t{W-aw}\t{R-ar}\t{excluded[(cls,off)]}")

p("\n=== ABSOLUTE-ONLY MISSES (decomposition) ===")
p("A=absolute [0x..]; B=register base (this/imm-loaded); C=global->ptr-array->object. missed=B+C.")
for (cls,off),v in summary.items():
    W,R,aw,ar,bw,br,cw,cr=v
    p(f"{cls} +0x{off:02X}: abs-only {aw}W/{ar}R; B {bw}W/{br}R; C {cw}W/{cr}R; full {W}W/{R}R; missed {bw+cw}W/{br+cr}R")

p("\n=== ALL SITES (untruncated) ===")
for (cls,off) in sorted(summary):
    cs=[r for r in sites if r['cls']==cls and r['off']==off]
    p("--- %s +0x%02X: %d sites ---" % (cls,off,len(cs)))
    p("site\tRW\tform\tmethod_tag\tmethod_entry\tanchor\tinstruction")
    for r in cs:
        p("%08X\t%s\t%s\t%s\t%08X\t%08X\t%s" % (r['addr'],r['rw'],r['form'],r['tag'],r['fn'],r['anchor'],fmt_ins(r['ins'])))

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_S03K2R_fields_v4.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT)+'\n')
print('[written EVIDENCE/E_S03K2R_fields_v4.txt]')
