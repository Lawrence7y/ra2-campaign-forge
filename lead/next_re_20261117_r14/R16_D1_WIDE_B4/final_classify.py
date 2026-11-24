# -*- coding: utf-8 -*-
"""DEFINITIVE classifier: complete store scan (raw capstone) + host identity G1-G5.
For each of 11 rows' class-consistent vt, list ALL mov[mem],vt sites, then for
each site determine host, this-reg, base-ctor-before, returns-this, dtor signature.
Read-only.
"""
import io, os, sys, json, bisect
import capstone
HERE=os.path.dirname(os.path.abspath(__file__)); R14=os.path.dirname(HERE)
ROOT=os.path.dirname(os.path.dirname(R14))
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
PROBE=os.path.join(R14,"R16_PROBE_4FINAL"); AUD=os.path.join(R14,"R16_AUDIT_D1_WIDE_B1")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
sys.path.insert(0,PROBE); sys.dont_write_bytecode=True
import final as F
IB=F.IMAGE_BASE; img=F.Image(EXE); buf=img.buf
text=F.Text(img)  # complete raw store scan
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
def dis(va,n):
    o=va-IB
    if o<0 or o>=len(buf): return []
    return list(md.disasm(bytes(buf[o:o+n]),va))
# atlas for host size
atlas={}
for i,ln in enumerate(io.open(ATLAS,encoding='utf-8-sig')):
    if i==0: continue
    c=ln.rstrip('\r\n').split('\t')
    if len(c)>=2:
        try: atlas[int(c[0].strip(),16)]=int(c[1])
        except ValueError: pass
targets=set(json.load(io.open(os.path.join(AUD,'starts.json'),encoding='utf-8'))['targets'])
ALL=sorted(set(atlas)|targets)
TX=img.section('.text'); TEXT_VA=TX['va']; TEXT_SZ=TX['vsize']
def fn_end(s):
    if s in atlas: return s+atlas[s]
    i=bisect.bisect_right(ALL,s); return ALL[i] if i<len(ALL) else TEXT_VA+TEXT_SZ
def enclosing(va):
    i=bisect.bisect_right(ALL,va)-1; best=None
    for j in range(i,max(-1,i-8),-1):
        s=ALL[j]; ins=dis(s,va-s+16)
        if not ins or not any(x.address==va for x in ins): continue
        if any(x.mnemonic in('ret','retf') for x in ins if x.address<va): continue
        best=(s,'atlas' if s in atlas else 'call-target'); break
    for back in range(1,0x41):
        s=va-back
        if s<TEXT_VA+1: break
        p=s-1; npad=0
        while p>TEXT_VA and buf[p-IB] in (0x90,0xCC): npad+=1; p-=1
        if npad==0 or buf[p-IB] not in (0xC3,0xC2,0xCC): continue
        ins=dis(s,va-s+16)
        if not ins or not any(x.address==va for x in ins): continue
        if any(x.mnemonic in('ret','retf') for x in ins if x.address<va): continue
        if best is None or s>best[0]: best=(s,'padding')
        break
    return best if best else (None,'none')
SEC=[(s['name'],s['va'],s['vsize']) for s in img.secs]
def sec_of(va):
    if va is None: return None
    for nm,sva,svs in SEC:
        if sva<=va<sva+svs: return nm
    return None

CHOICE={
 "006C6680":("007F3EA0",33), "006C9890":("007E4D90",1), "006CF430":("007F4108",0),
 "006F3330":("007F4960",185), "006FC0B0":("007F4960",240), "006FCDB0":("007F4960",242),
 "006FFEC0":("007F4960",29), "00702D40":("007E22A4",56), "00706640":("007E22A4",273),
 "00708C30":("007E22A4",174), "007730F0":("007F73B8",8),
}

def classify_site(site, vt):
    insns=dis(site,16); ins=insns[0] if insns else None
    if not ins: return None
    txt='%s %s'%(ins.mnemonic,ins.op_str)
    mb=disp=imm=None
    if len(ins.operands)==2:
        a,b=ins.operands
        if a.type==capstone.x86.X86_OP_MEM:
            mb=md.reg_name(a.mem.base) if a.mem.base else 'ABS'; disp=a.mem.disp
        if b.type==capstone.x86.X86_OP_IMM: imm=b.imm&0xFFFFFFFF
    target_is_stack = mb in ('esp','ebp'); target_is_abs=(mb=='ABS')
    host,hsrc=enclosing(site); hend=fn_end(host) if host else None
    this=None
    if host:
        for x in dis(host,64)[:14]:
            if x.mnemonic=='mov' and len(x.operands)==2:
                d,s2=x.operands
                if d.type==capstone.x86.X86_OP_REG and s2.type==capstone.x86.X86_OP_REG and md.reg_name(s2.reg)=='ecx':
                    this=md.reg_name(d.reg); break
    body=dis(host,min(hend-host+8,0x900)) if host else []
    direct_calls_before=[x for x in body if x.mnemonic=='call' and x.operands and x.operands[0].type==capstone.x86.X86_OP_IMM and x.address<site and (x.operands[0].imm&0xFFFFFFFF)==0x431B20]
    any_call_before=[x for x in body if x.mnemonic=='call' and x.address<site]
    delete_after=[x for x in body if x.mnemonic=='call' and x.address>site and x.operands and x.operands[0].type==capstone.x86.X86_OP_IMM and (x.operands[0].imm&0xFFFFFFFF)==0x7C8B3D]
    txts=['%s %s'%(x.mnemonic,x.op_str) for x in body]
    sdd = any(t.startswith('test') and '[esp' in t and t.rstrip().endswith(', 1') for t in txts) and any('0x7c8b3d' in t for t in txts)
    # returns this: mov eax,<reg> before a ret (search last 8 insns before each ret)
    ret_this=False
    gpr=this
    idxs=[i for i,x in enumerate(body) if x.mnemonic in ('ret','retf')]
    for i in idxs:
        for x in body[max(0,i-8):i]:
            if x.mnemonic=='mov' and len(x.operands)==2 and x.op_str==('eax, %s'%gpr):
                ret_this=True
    # direct calls to host (scalar deleting wrapper detection): scan text.direct_sites
    callers_to_host = text.direct_sites.get(host,[]) if host else []
    return dict(site='%08X'%site, ins=txt, opbytes=ins.bytes.hex(), mb=mb, disp=('%08X'%(disp&0xFFFFFFFF)) if disp is not None else None,
                imm=('%08X'%imm) if imm is not None else None, stack=target_is_stack, abs=target_is_abs,
                tsec=sec_of(disp) if target_is_abs else None,
                host=('%08X'%host) if host else None, hsrc=hsrc,
                this=this, disp0=(this is not None and (disp or 0)==0 and mb==this),
                calls_before=len(any_call_before), basector_before=len(direct_calls_before),
                delete_after=len(delete_after), sdd=sdd, ret_this=ret_this,
                callers=[('%08X'%c) for c in callers_to_host[:8]], host_len=(hend-host if host else None))

report={}
for e,(vths,slot) in CHOICE.items():
    vt=int(vths,16)
    sites=text.stores.get(vt,[])  # list of (site,disp)
    facts=[classify_site(s,vt) for s,_ in sorted(sites)]
    report[e]=dict(vt=vths,slot=slot,facts=[f for f in facts if f])
json.dump(report,io.open(os.path.join(HERE,'final_sites.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

for e,(vths,slot) in CHOICE.items():
    print('===== %s vt=%s slot=%d (stores=%d) ====='%(e,vths,slot,len(report[e]['facts'])))
    for f in report[e]['facts']:
        print('  site=%s ins=%-32s mb=%-4s disp=%-8s abs=%-5s stack=%-5s tsec=%-7s'%(
            f['site'],f['ins'][:32],f['mb'],f['disp'],f['abs'],f['stack'],f['tsec']))
        print('        host=%s(%s) this=%s disp0=%s callsB=%d baseCtorB=%d delA=%d sdd=%s retThis=%s callers=%s'%(
            f['host'],f['hsrc'],f['this'],f['disp0'],f['calls_before'],f['basector_before'],f['delete_after'],f['sdd'],f['ret_this'],f['callers'][:4]))
    print()
