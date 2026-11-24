# -*- coding: utf-8 -*-
"""Independent verification of R16_D1_WIDE_B3 products (does NOT import derive.py).
Re-derives all byte facts from gamemd.exe via pefile + capstone; uses audit
starts.json/vptr_stores.tsv for function boundaries; checks products A-F.
Writes only inside R16_D1_WIDE_B3/.
"""
import io, os, sys, re, json, bisect, hashlib, csv
import pefile, capstone
HERE=os.path.dirname(os.path.abspath(__file__)); R14=os.path.dirname(HERE)
ROOT=os.path.dirname(os.path.dirname(R14))
EXE=os.path.join(ROOT,'ra2youli','gamemd.exe')
COV=os.path.join(R14,'COVERAGE','coverage.tsv')
AUD=os.path.join(R14,'R16_AUDIT_D1_WIDE_B1')
IB=0x400000
def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest().upper()
pe=pefile.PE(EXE,fast_load=True)
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b'\0').decode('latin-1'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.get_data()))
end=max(va+max(vs,len(d)) for _,va,vs,d in secs)
buf=bytearray(end-IB+16)
for nm,va,vs,d in secs: buf[va-IB:va-IB+len(d)]=d
SECS=[(nm,va,vs) for nm,va,vs,_ in secs]
def sec_of(va):
    for nm,sva,svs in SECS:
        if sva<=va<sva+svs: return nm
    return None
def u32(va):
    o=va-IB
    return int.from_bytes(buf[o:o+4],'little') if 0<=o<=len(buf)-4 else None
def cstr(va,n=256):
    o=va-IB
    if o<0 or o>=len(buf): return None
    e=buf.find(b'\0',o,min(o+n,len(buf)))
    return bytes(buf[o:e]).decode('latin-1','replace') if e>0 else None
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
def dis1(va,n=24):
    o=va-IB
    return list(md.disasm(bytes(buf[o:o+n]),va)) if 0<=o<len(buf) else []
TX_VA=IB+pe.sections[0].VirtualAddress; TX_SZ=pe.sections[0].Misc_VirtualSize
atlas={}
for i,ln in enumerate(io.open(os.path.join(ROOT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv'),encoding='utf-8-sig')):
    if i==0: continue
    c=ln.rstrip('\r\n').split('\t')
    if len(c)>=2:
        try: atlas[int(c[0].strip(),16)]=int(c[1])
        except ValueError: pass
tg=set(json.load(io.open(os.path.join(AUD,'starts.json'),encoding='utf-8'))['targets'])
ALL=sorted(set(atlas)|tg)
def fn_end(s):
    if s in atlas: return s+atlas[s]
    i=bisect.bisect_right(ALL,s)
    return ALL[i] if i<len(ALL) else TX_VA+TX_SZ
def enclosing(va):
    i=bisect.bisect_right(ALL,va)-1; best=None
    for j in range(i,max(-1,i-8),-1):
        s=ALL[j]
        ins=list(md.disasm(bytes(buf[s-IB:va-IB+16]),s))
        if not any(x.address==va for x in ins): continue
        if any(x.mnemonic in('ret','retf') for x in ins if x.address<va): continue
        best=s; break
    for back in range(1,0x41):
        s=va-back
        if s<TX_VA+1: break
        p=s-1; npad=0
        while p>TX_VA and buf[p-IB] in (0x90,0xCC): npad+=1; p-=1
        if npad==0 or buf[p-IB] not in (0xC3,0xC2,0xCC): continue
        ins=list(md.disasm(bytes(buf[s-IB:va-IB+16]),s))
        if not any(x.address==va for x in ins): continue
        if any(x.mnemonic in('ret','retf') for x in ins if x.address<va): continue
        if best is None or s>best: best=s
        break
    return best
VPTR=[]
for i,ln in enumerate(io.open(os.path.join(AUD,'vptr_stores.tsv'),encoding='utf-8')):
    if i==0: continue
    c=ln.rstrip('\r\n').split('\t')
    if len(c)>=6: VPTR.append((int(c[0],16),int(c[1],16),c[2],int(c[3],16)))
# load products
cov={}
with io.open(COV,encoding='utf-8-sig',newline='') as f:
    f.readline()
    for ln in f:
        c=ln.rstrip('\r\n').split('\t')
        if len(c)>=8: cov[c[0].strip().upper()]=c
def rd_tsv(p):
    L=io.open(p,encoding='utf-8-sig').read().splitlines()
    h=L[0].split('\t'); return h,[dict(zip(h,ln.split('\t'))) for ln in L[1:] if ln.strip()]
_,delta=rd_tsv(os.path.join(HERE,'delta.tsv'))
fh,fields=rd_tsv(os.path.join(HERE,'fields.tsv'))
FLD={r['entry']:r for r in fields}
with io.open(os.path.join(R14,'R16_SIEVE_D1_WIDE','sieve_all.tsv'),encoding='utf-8') as f:
    sr=list(csv.DictReader(f,delimiter='\t'))
no=sorted([r for r in sr if r['has_ring4_on_disk(是/否)'].strip()=='否'],key=lambda x:int(x['entry'],16))
b3=no[36:54]; B3E=[r['entry'].strip().upper() for r in b3]
DE=[r['entry'].strip().upper() for r in delta]
assert DE==B3E, ('delta order/set mismatch', DE, B3E)

RING='④ 活表槽位见证'; DISC='§12.6'
res=[]
for r in delta:
    e=r['entry'].strip().upper(); ei=int(e,16); c=cov[e]; f=FLD[e]
    A=[]
    A.append(('prefix', r['one_line_semantics'].startswith(c[3]) and len(r['one_line_semantics'])>len(c[3])))
    A.append(('cols', all(r[k]==c[i] for i,k in ((0,'entry'),(1,'subsystem'),(2,'name'),(4,'grade'),(5,'evidence_path'),(6,'n_sources'),(7,'conflict')))))
    A.append(('grade_unchanged', r['grade']==c[4]))
    A.append(('pre_no_ring4', RING not in c[3]))
    tail=r['one_line_semantics'][len(c[3]):]
    D=[]
    D.append(('disc_§12.6', DISC in tail and '§12.4' not in tail))
    D.append(('form_declared', ('装配方式='+f['install_form(ctor_body|mov_abs|reg|other)']) in tail))
    insn=f.get('note','')
    D.append(('entry_体外', 'entry 体外' in tail))
    # byte facts from fields
    vt=int(f['vt'],16); slot=int(f['slot']); site=int(f['install_site'],16); host=int(f['install_host'],16)
    sv=u32(vt+slot*4); col=u32(vt-4); coff=u32(col+4); td=u32(col+12); mg=cstr(td+8) if td else None
    ins=dis1(site,24); ins0=ins[0] if ins else None
    itxt='%s %s'%(ins0.mnemonic,ins0.op_str) if ins0 else '?'
    mb=md_=imm=None
    if ins0 and len(ins0.operands)==2:
        a,b=ins0.operands
        if a.type==capstone.x86.X86_OP_MEM:
            mb=ins0.reg_name(a.mem.base) if a.mem.base else 'ABS'; md_=a.mem.disp
        if b.type==capstone.x86.X86_OP_IMM: imm=b.imm&0xFFFFFFFF
    eh=enclosing(site)
    B=[]
    B.append(('slot',sv==ei)); B.append(('col_sig',col is not None and u32(col)==0)); B.append(('offset',coff==0))
    B.append(('mangled',(mg or '').startswith('.?A'))); B.append(('imm==vt',imm==vt)); B.append(('site_outside_entry',not (ei<=site<ei+atlas.get(ei,0))))
    B.append(('host_matches',eh==host)); B.append(('insn_in_note',itxt in insn))
    # host identity
    form=f['install_form(ctor_body|mov_abs|reg|other)']
    this=None
    if eh:
        for x in dis1(eh,64)[:14]:
            if x.mnemonic=='mov' and len(x.operands)==2:
                d,s2=x.operands
                if d.type==capstone.x86.X86_OP_REG and s2.type==capstone.x86.X86_OP_REG and ins0 and ins0.reg_name(s2.reg)=='ecx':
                    this=ins0.reg_name(d.reg); break
    body=dis1(eh,min(fn_end(eh)-eh+16,0x800)) if eh else []
    bt=['%s %s'%(x.mnemonic,x.op_str) for x in body]
    ddtor=any('test byte ptr [esp' in s and ', 1' in s for s in bt) and any('0x7c8b3d' in s for s in bt)
    stores=[v for v in VPTR if eh and eh<=v[0]<fn_end(eh)]
    on=[v for v in stores if this and v[2]==this and v[3]==0]
    if form=='mov_abs': C=[('abs',mb=='ABS'),('data',sec_of(md_)=='.data'),('imm',imm==vt),('no_this_needed',True)]
    elif form=='ctor_body': C=[('this',bool(this and mb==this and md_==0)),('primary',len(on)>0),('no_ddtor',not ddtor),('imm',imm==vt)]
    elif form=='reg': C=[('this',bool(this and mb==this)),('imm',imm==vt)]
    else: C=[('unknown_form',False)]
    res.append(dict(entry=e,sem=c[3][:28],form=form,
        A_fail=[k for k,v in A if not v],B_fail=[k for k,v in B if not v],
        C_fail=[k for k,v in C if not v],D_fail=[k for k,v in D if not v],
        insn=itxt,vt='%08X'%vt,slot=slot,site='%08X'%site,host='%08X'%host,mb=mb,disp=('%08X'%md_) if md_ is not None else None))
# distinct
full=[r['one_line_semantics'] for r in delta]; norm=[re.sub(r'[0-9A-Fa-f]{8}','ENTRY',s) for s in full]
print('INDEPENDENT VERIFY: rows=%d'%len(res))
print('A_fail rows=%d'%sum(1 for r in res if r['A_fail']))
print('B_fail rows=%d'%sum(1 for r in res if r['B_fail']))
print('C_fail rows=%d'%sum(1 for r in res if r['C_fail']))
print('D_fail rows=%d'%sum(1 for r in res if r['D_fail']))
print('full_distinct=%d norm_distinct=%d'%(len(set(full)),len(set(norm))))
for r in res:
    if r['A_fail'] or r['B_fail'] or r['C_fail'] or r['D_fail']:
        print(' FAIL',r['entry'],'A=',r['A_fail'],'B=',r['B_fail'],'C=',r['C_fail'],'D=',r['D_fail'])
out=dict(n=len(res),A_fail=sum(1 for r in res if r['A_fail']),B_fail=sum(1 for r in res if r['B_fail']),
         C_fail=sum(1 for r in res if r['C_fail']),D_fail=sum(1 for r in res if r['D_fail']),
         full_distinct=len(set(full)),norm_distinct=len(set(norm)),
         cov_sha=sha256(COV),exe_sha=sha256(EXE),detail=res)
json.dump(out,io.open(os.path.join(HERE,'verify_independent.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
