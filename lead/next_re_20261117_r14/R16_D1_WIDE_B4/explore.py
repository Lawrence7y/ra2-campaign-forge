# -*- coding: utf-8 -*-
"""B4 exploration: for each of 11 entries, enumerate all vtables holding it,
their RTTI classes, install sites (from vptr_stores.tsv + raw scan), and
host-identity facts (B3 site_facts / host_rule G1-G5). Read-only on gamemd.exe.
Writes ONLY into R16_D1_WIDE_B4/.
"""
import io, os, sys, json, bisect, collections
import pefile, capstone
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

TARGETS = ["006C6680","006C9890","006CF430","006F3330","006FC0B0","006FCDB0",
           "006FFEC0","00702D40","00706640","00708C30","007730F0"]

img = F.Image(EXE); buf = img.buf
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

# atlas + function starts
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

# vptr stores
VPTR=[]
for i,ln in enumerate(io.open(os.path.join(AUD,'vptr_stores.tsv'),encoding='utf-8')):
    if i==0: continue
    c=ln.rstrip('\r\n').split('\t')
    if len(c)>=6: VPTR.append(dict(site=int(c[0],16),vt=int(c[1],16),base=c[2],disp=int(c[3],16)))
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
    body=dis1(host,min(hend-host+16,0x800)) if host else []
    bt=['%s %s'%(x.mnemonic,x.op_str) for x in body]
    ddtor=any('test byte ptr [esp' in s and ', 1' in s for s in bt) and any('0x7c8b3d' in s for s in bt)
    return dict(ins=txt, mb=mb, disp=disp, imm=imm, host=host, hsrc=hsrc,
                this=this, ddtor=ddtor,
                on_this=bool(this and mb==this and (disp or 0)==0),
                tsec=sec_of(disp) if mb=='ABS' else None,
                opbytes=ins.bytes.hex())

# ---- enumerate all tables (vt -> class)
tabs = F.enumerate_tables(img)
stop = set(tabs)
for vt in tabs: tabs[vt]['n_slots']=F.table_len(img,vt,stop)

# ---- final.tsv decisive info
fmap={}
with io.open(os.path.join(PROBE,'final.tsv'),encoding='utf-8-sig') as f:
    h=f.readline().rstrip('\r\n').split('\t')
    for ln in f:
        c=ln.rstrip('\r\n').split('\t')
        if len(c)>=len(h): fmap[c[0]]=dict(zip(h,c))

def cls_of_vt(vt):
    col=img.u32(vt-4); coff=img.u32(col+4) if col else None; td=img.u32(col+12) if col else None
    mg=img.cstr(td+8) if td else None
    return col,mg

def row_class(name):
    # name like 'TechnoClass::slot185' or 'ObjectClass::DrawWrapper(slot65);...' or 'FileStraw::slot1'
    base=name.split('(')[0]
    if ';' in base: base=base.split(';')[0]
    if '::' in base: return base.split('::')[0]
    return base

out={}
for e in TARGETS:
    ei=int(e,16); fr=fmap.get(e)
    decis_vt=int(fr['vt'],16); decis_slot=int(fr['slot']); decis_site=int(fr['install_site'],16)
    dcol,dmg=cls_of_vt(decis_vt)
    rcls=row_class(fr['name'])
    # find all tables holding entry
    holds=[]
    for vt,t in tabs.items():
        n=t['n_slots']
        for s in range(n):
            if img.u32(vt+s*4)==ei:
                holds.append((vt,s,t['cls'],t['section'])); break  # one slot per vt suffice (can be multi)
    # also find ALL slots per vt
    holds_all=[]
    for vt,t in tabs.items():
        for s in range(t['n_slots']):
            if img.u32(vt+s*4)==ei:
                holds_all.append((vt,s,t['cls'],t['section']))
    out[e]=dict(name=fr['name'],subsystem=fr['subsystem'],row_class=rcls,
                decis_vt=fr['vt'],decis_slot=decis_slot,decis_site=fr['install_site'],
                decis_cls=dmg,decis_col=('%08X'%dcol) if dcol else None,
                direct_sites=fr['direct_sites'], note=fr['note'],
                holds_all=[('%08X'%v,s,c,sec) for v,s,c,sec in holds_all])

json.dump(dict(targets=out, data_section=[('%08X'%s['va'],s['vsize']) for s in img.secs if s['name']=='.data']),
          io.open(os.path.join(HERE,'explore_holdings.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

# print compact
for e in TARGETS:
    d=out[e]
    print('%s  %s  rowcls=%s'%(e,d['name'],d['row_class']))
    print('   DECIS vt=%s slot=%d site=%s cls=%s col=%s'%(d['decis_vt'],d['decis_slot'],d['decis_site'],d['decis_cls'],d['decis_col']))
    print('   HOLDS(%d):'%len(d['holds_all']))
    for v,s,c,sec in d['holds_all']:
        print('      vt=%s slot=%-4d cls=%-45s sec=%s'%(v,s,c,sec))
    print()
