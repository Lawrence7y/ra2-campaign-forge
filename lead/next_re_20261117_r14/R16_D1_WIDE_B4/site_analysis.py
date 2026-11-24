# -*- coding: utf-8 -*-
"""B4 site analysis: for each row's class-consistent vt, list every install site
from vptr_stores.tsv, run site_facts (host identity), and print. Read-only.
"""
import io, os, sys, json, bisect
import capstone
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
PROBE = os.path.join(R14, "R16_PROBE_4FINAL")
AUD = os.path.join(R14, "R16_AUDIT_D1_WIDE_B1")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
sys.path.insert(0, PROBE); sys.dont_write_bytecode = True
import final as F
IB = F.IMAGE_BASE
img = F.Image(EXE); buf = img.buf

# class-consistent vt per row (after lesson-3 class fix)
CHOICE = {
 "006C6680":("007F3EA0",33),
 "006C9890":("007E4D90",1),
 "006CF430":("007F4108",0),
 "006F3330":("007F4960",185),   # CLASS_FIX from 007E22A4 AircraftClass
 "006FC0B0":("007F4960",240),   # CLASS_FIX from 007E8C94 FootClass
 "006FCDB0":("007F4960",242),   # CLASS_FIX from 007E22A4 AircraftClass
 "006FFEC0":("007F4960",29),
 "00702D40":("007E22A4",56),
 "00706640":("007E22A4",273),
 "00708C30":("007E22A4",174),
 "007730F0":("007F73B8",8),
}
secs = [(s['name'], s['va'], s['vsize']) for s in img.secs]
def sec_of(va):
    if va is None: return None
    for nm,sva,svs in secs:
        if sva <= va < sva+svs: return nm
    return None
TX = img.section('.text'); TEXT_VA=TX['va']; TEXT_SZ=TX['vsize']
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
def dis1(va, n=24):
    o=va-IB
    if o<0 or o>=len(buf): return []
    return list(md.disasm(bytes(buf[o:o+n]), va))
atlas={}
for i,ln in enumerate(io.open(ATLAS,encoding='utf-8-sig')):
    if i==0: continue
    c=ln.rstrip('\r\n').split('\t')
    if len(c)>=2:
        try: atlas[int(c[0].strip(),16)]=int(c[1])
        except ValueError: pass
targets=set(json.load(io.open(os.path.join(AUD,'starts.json'),encoding='utf-8'))['targets'])
ALL=sorted(set(atlas)|targets)
def fn_end(s):
    if s in atlas: return s+atlas[s]
    i=bisect.bisect_right(ALL,s)
    return ALL[i] if i<len(ALL) else TEXT_VA+TEXT_SZ
def enclosing(va):
    i=bisect.bisect_right(ALL,va)-1; best=None
    for j in range(i,max(-1,i-8),-1):
        s=ALL[j]; ins=dis1(s,va-s+16)
        if not ins or not any(x.address==va for x in ins): continue
        if any(x.mnemonic in('ret','retf') for x in ins if x.address<va): continue
        best=(s,'atlas' if s in atlas else 'call-target'); break
    for back in range(1,0x41):
        s=va-back
        if s<TEXT_VA+1: break
        p=s-1; npad=0
        while p>TEXT_VA and buf[p-IB] in (0x90,0xCC): npad+=1; p-=1
        if npad==0 or buf[p-IB] not in (0xC3,0xC2,0xCC): continue
        ins=dis1(s,va-s+16)
        if not ins or not any(x.address==va for x in ins): continue
        if any(x.mnemonic in('ret','retf') for x in ins if x.address<va): continue
        if best is None or s>best[0]: best=(s,'padding')
        break
    return best if best else (None,'none')
VPTR=[]
for i,ln in enumerate(io.open(os.path.join(AUD,'vptr_stores.tsv'),encoding='utf-8')):
    if i==0: continue
    c=ln.rstrip('\r\n').split('\t')
    if len(c)>=6: VPTR.append(dict(site=int(c[0],16),vt=int(c[1],16),base=c[2],disp=int(c[3],16),insn=c[5]))
def stores_of(vt): return [v for v in VPTR if v['vt']==vt]

def site_facts(site, vt):
    insns=dis1(site,24); ins=insns[0] if insns else None
    if ins is None: return None
    txt='%s %s'%(ins.mnemonic,ins.op_str)
    mb=disp=imm=None
    if len(ins.operands)==2:
        a,b=ins.operands
        if a.type==capstone.x86.X86_OP_MEM:
            mb=ins.reg_name(a.mem.base) if a.mem.base else 'ABS'; disp=a.mem.disp
        if b.type==capstone.x86.X86_OP_IMM: imm=b.imm&0xFFFFFFFF
    host,hsrc=enclosing(site); hend=fn_end(host) if host else None
    this=None
    if host:
        for x in dis1(host,64)[:14]:
            if x.mnemonic=='mov' and len(x.operands)==2:
                d,s2=x.operands
                if d.type==capstone.x86.X86_OP_REG and s2.type==capstone.x86.X86_OP_REG and ins.reg_name(s2.reg)=='ecx':
                    this=ins.reg_name(d.reg); break
    stores=[v for v in VPTR if host and v['site']>=host and v['site']<hend]
    on=[s for s in stores if this and s['base']==this]
    primary=[s for s in on if s['disp']==0]
    body=dis1(host,min(hend-host+16,0x800)) if host else []
    bt=['%s %s'%(x.mnemonic,x.op_str) for x in body]
    ddtor=any('test byte ptr [esp' in s and ', 1' in s for s in bt) and any('0x7c8b3d' in s for s in bt)
    return dict(ins=txt, mb=mb, disp=disp, imm=imm, host=host, hsrc=hsrc, this=this,
                primary=bool(primary), ddtor=ddtor,
                on_this=bool(this and mb==this and (disp or 0)==0),
                tsec=sec_of(disp) if mb=='ABS' else None,
                opbytes=ins.bytes.hex(), hsize=(hend-host if host else None))

report={}
for e,(vths,slot) in CHOICE.items():
    vt=int(vths,16); ei=int(e,16)
    sts=stores_of(vt)
    col=img.u32(vt-4); mg=None
    if col:
        td=img.u32(col+12); mg=img.cstr(td+8) if td else None
    slotval=img.u32(vt+slot*4)
    facts=[]
    for s in sts:
        f=site_facts(s['site'],vt)
        if f:
            # classify form
            if f['mb']=='ABS': form='mov_abs'
            elif f['on_this'] and f['primary'] and not f['ddtor']: form='ctor_body'
            elif f['on_this']: form='reg'
            else: form='other'
            facts.append(dict(site='%08X'%s['site'],raw=s['insn'],form=form,
                              ins=f['ins'],host=('%08X'%f['host']) if f['host'] else None,
                              hsrc=f['hsrc'],this=f['this'],on_this=f['on_this'],
                              primary=f['primary'],ddtor=f['ddtor'],tsec=f['tsec'],
                              disp=('%08X'%(f['disp']&0xFFFFFFFF)) if f['disp'] is not None else None,
                              hsize=f['hsize'],opbytes=f['opbytes']))
    report[e]=dict(vt=vths,slot=slot,cls=mg,slotval=('%08X'%slotval) if slotval else None,
                   slotval_ok=(slotval==ei),col=('%08X'%col) if col else None,facts=facts)

json.dump(report,io.open(os.path.join(HERE,'site_analysis.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

print('DATA section (VA,vsize,rsize):', [(('%08X'%s['va']),s['vsize'],s['rsize']) for s in img.secs if s['name']=='.data'])
print()
for e,(vths,slot) in CHOICE.items():
    d=report[e]
    print('%s vt=%s slot=%d cls=%s slotval=%s ok=%s'%(e,vths,slot,d['cls'],d['slotval'],d['slotval_ok']))
    print('   stores=%d'%len(d['facts']))
    for f in d['facts']:
        print('      site=%s form=%-10s host=%-8s(%s) this=%-4s onthis=%-5s prim=%-5s ddtor=%-5s tsec=%-7s ins=%s'%(
            f['site'],f['form'],f['host'],f['hsrc'],f['this'],f['on_this'],f['primary'],f['ddtor'],f['tsec'],f['ins']))
    print()
