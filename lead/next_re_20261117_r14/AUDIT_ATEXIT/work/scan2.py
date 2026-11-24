
# -*- coding: utf-8 -*-
"""AUDIT-ATEXIT scan2 (v2): function-start model + atexit-registered set +
vptr install sites classified ctor-side vs dtor-side (imm-store and reg-mediated)."""
import pefile, capstone, json, struct, sys, os, bisect
from capstone import *
from capstone.x86 import *
from array import array

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT = os.path.dirname(os.path.abspath(__file__))
ATLAS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
pe = pefile.PE(EXE, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
blob = open(EXE,'rb').read()
secs = [dict(name=s.Name.decode().rstrip('\x00'), va=IB+s.VirtualAddress,
             vsize=s.Misc_VirtualSize, rawsize=s.SizeOfRawData, rawptr=s.PointerToRawData)
        for s in pe.sections]
def va2raw(v):
    for s in secs:
        if s['rawsize'] and s['va'] <= v < s['va']+s['rawsize']:
            return s['rawptr'] + (v - s['va'])
    return None
def read(v,n):
    r = va2raw(v)
    return None if r is None or r+n > len(blob) else blob[r:r+n]
TEXT = next(s for s in secs if s['name']=='.text')
TEXT_LO, TEXT_HI = TEXT['va'], TEXT['va']+TEXT['vsize']
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
code = read(TEXT_LO, TEXT['vsize'])

addrs=array('I'); sizes=array('B'); flags=array('B')
F_RET=1; F_PUSH=2; F_CALLI=4; F_PUSHNOP=64
pushval={}; calltgt={}; store_imm=[]; store_reg=[]; movreg={}
for ins in md.disasm(code, TEXT_LO):
    if ins.id == 0: continue
    a=ins.address; sz=ins.size; mn=ins.mnemonic; ops=ins.operands
    addrs.append(a); sizes.append(sz); fl=0
    if mn.startswith('ret'): fl|=F_RET
    if mn=='call' and ops and ops[0].type==X86_OP_IMM and TEXT_LO<=ops[0].imm<TEXT_HI:
        calltgt[a]=ops[0].imm; fl|=F_CALLI
    if mn=='push' and ops and ops[0].type==X86_OP_IMM and TEXT_LO<=ops[0].imm<TEXT_HI:
        pushval[a]=ops[0].imm; fl|=F_PUSH
    if len(ops)==2 and mn.startswith('mov'):
        o0,o1=ops
        if o0.type==X86_OP_MEM and o1.type==X86_OP_IMM and 0x400000<=o1.imm<0xC00000:
            store_imm.append((a,o1.imm,'abs' if (o0.mem.base==0 and o0.mem.index==0) else 'reg',
                              o0.mem.disp if (o0.mem.base==0 and o0.mem.index==0) else None))
        elif o0.type==X86_OP_MEM and o1.type==X86_OP_REG and o1.size==4 and o1.reg not in (0,):
            store_reg.append((a,o1.reg))
        elif o0.type==X86_OP_REG and o0.size==4 and o1.type==X86_OP_IMM and 0x400000<=o1.imm<0xC00000:
            movreg[a]=(o0.reg,o1.imm)
    flags.append(fl)
idx={a:i for i,a in enumerate(addrs)}
print('insns',len(addrs),'push',len(pushval),'call',len(calltgt),
      'store_imm',len(store_imm),'store_reg',len(store_reg),'movreg',len(movreg),file=sys.stderr)

# function starts: atlas entries + direct call targets + ret-boundary starts
atlas={}
with open(ATLAS,encoding='utf8') as f:
    next(f)
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)>=2 and p[0]: atlas[int(p[0],16)]=int(p[1])
rets=[addrs[i] for i in range(len(addrs)) if flags[i]&F_RET]
starts=set(atlas)|set(calltgt.values())
for r in rets:
    ofs=r+sizes[idx[r]]
    i=idx.get(ofs)
    while i is not None and i<len(addrs):
        b=blob[va2raw(addrs[i]):va2raw(addrs[i])+sizes[i]]
        if b in (b'\x90',b'\xcc'): i+=1; continue
        starts.add(addrs[i]); break
starts_sorted=sorted(starts)
def enclosing(a):
    j=bisect.bisect_right(starts_sorted,a)-1
    return starts_sorted[j] if j>=0 else TEXT_LO
print('fn starts',len(starts_sorted),file=sys.stderr)

# atexit registrations (push <fn> within 40 insns before call 0x7C978A)
regs=[]
for i,a in enumerate(addrs):
    if calltgt.get(a)==0x7C978A:
        for j in range(i-1,max(-1,i-41),-1):
            if addrs[j] in pushval:
                regs.append((a,addrs[j],pushval[addrs[j]]))
registered=set(r[2] for r in regs)
print('atexit calls',sum(1 for a in addrs if calltgt.get(a)==0x7C978A),
      'registrations',len(regs),'distinct pushed fns',len(registered),file=sys.stderr)

# install sites
installs=[]
for site,vt,kind,dest in store_imm:
    installs.append(dict(site=site,vt=vt,kind=kind,dest=dest,via='imm_store',fn=enclosing(site)))
# reg-mediated: mov reg,vt ; ... ; mov [mem],reg  (<=6 insns, no boundary crossing)
srg={}   # site -> list of store sites
for site,(reg,vt) in movreg.items():
    i=idx[site]
    for k in range(i+1,min(i+7,len(addrs))):
        a=addrs[k]
        if enclosing(a)!=enclosing(site): break
        if any(s==a for s,_r in store_reg):
            installs.append(dict(site=a,via='reg_move',vt=vt,kind='reg',dest=None,
                                 fn=enclosing(a),ldr=site,reg=reg))
            break
for it in installs:
    it['dtor']= it['fn'] in registered
print('installs',len(installs),'dtor-side',sum(1 for i in installs if i['dtor']),file=sys.stderr)

out=dict(text=[TEXT_LO,TEXT_HI],registered=sorted(registered),
         registrations=regs,install_count=len(installs))
with open(os.path.join(OUT,'scan2.json'),'w') as f:
    json.dump(out,f)
import csv
with open(os.path.join(OUT,'installs.tsv'),'w',newline='') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['site','vt','via','kind','dest_global','fn','dtor_side'])
    for it in installs:
        w.writerow(['%08X'%it['site'],'%08X'%it['vt'],it['via'],it['kind'],
                    '%08X'%it['dest'] if it['dest'] else '', '%08X'%it['fn'],
                    1 if it['dtor'] else 0])
print('WROTE scan2.json + installs.tsv',file=sys.stderr)
