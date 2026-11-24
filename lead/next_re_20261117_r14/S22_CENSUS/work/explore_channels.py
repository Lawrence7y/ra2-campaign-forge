#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S22-CENSUS exploratory channel counts. Read-only inputs; writes only under S22_CENSUS/work."""
import sys, os, re, struct, json, hashlib, bisect, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_INS_MOV, X86_INS_LEA, X86_INS_PUSH, X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_INVALID

ROOT = r'D:/Project/ra2-campaign-forge'
EXE = os.path.join(ROOT,'ra2youli','gamemd.exe')
COV = os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE','coverage.tsv')
ATL = os.path.join(ROOT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
WORK = os.path.join(ROOT,'lead','next_re_20261117_r14','S22_CENSUS','work')
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = pe.__data__
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\0').decode('latin1')
    secs.append(dict(nm=nm, va=IB+s.VirtualAddress, rva=s.VirtualAddress, vsize=s.Misc_VirtualSize, raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
by={s['nm']:s for s in secs}

def u32(va):
    rva=va-IB
    for s in secs:
        if s['rva'] <= rva < s['rva']+max(s['vsize'],s['rawsize']):
            off=s['raw']+(rva-s['rva'])
            if off+4 <= len(DATA) and off+4 <= s['raw']+s['rawsize']:
                return struct.unpack_from('<I',DATA,off)[0]
            break
    raise KeyError(hex(va))

def cstr(va, maxb=200):
    rva=va-IB
    for s in secs:
        if s['rva'] <= rva < s['rva']+max(s['vsize'],s['rawsize']):
            off=s['raw']+(rva-s['rva'])
            chunk=DATA[off:off+maxb]
            z=chunk.find(b'\0')
            return chunk[:z] if z>=0 else None
    return None

def demangle(nm):
    if not nm: return nm
    s=nm
    for p in ('.?AV','.?AU'):
        if s.startswith(p): s=s[4:]; break
    if s.endswith('@@'): s=s[:-2]
    return s

# TD: inline name at TD+8; fail closed on malformed
tds={}
for s in secs:
    if s['nm'] not in ('.rdata','.data'): continue
    buf=DATA[s['raw']:s['raw']+s['rawsize']]
    for off in range(0,len(buf)-16,4):
        va=s['va']+off
        if struct.unpack_from('<I',buf,off)[0] != 0x7F9594: continue
        if struct.unpack_from('<I',buf,off+4)[0] != 0: continue
        raw=cstr(va+8)
        if not raw or not raw.startswith((b'.?AV',b'.?AU')) or not raw.endswith(b'@@'): continue
        nm=raw.decode('latin1')
        cls=demangle(nm)
        if not cls: continue
        tds[va]=dict(td=va, raw=nm, cls=cls, section=s['nm'])
print('TDs',len(tds))
# COL: +0xC -> TD; sig 0, CHD pointer sanity
cols={}
for s in secs:
    if s['nm'] not in ('.rdata','.data'): continue
    buf=DATA[s['raw']:s['raw']+s['rawsize']]
    for off in range(0,len(buf)-20,4):
        va=s['va']+off
        sig, offv, cdoff = struct.unpack_from('<III',buf,off)
        ptd=struct.unpack_from('<I',buf,off+12)[0]
        chd=struct.unpack_from('<I',buf,off+16)[0]
        if sig != 0 or ptd not in tds: continue
        if not (0x400000 <= chd < 0x900000): continue
        cols[va]=dict(col=va, sig=sig, off=offv, cdoff=cdoff, td=ptd, chd=chd, raw=tds[ptd]['raw'], cls=tds[ptd]['cls'])
print('COLs',len(cols))
# vtable scan in .rdata only
r=by['.rdata']; buf=DATA[r['raw']:r['raw']+r['rawsize']]
text=by['.text']; tlo=text['va']; thi=text['va']+text['rawsize']
colset=set(cols)
vpos=[]
for off in range(0,len(buf)-4,4):
    v=struct.unpack_from('<I',buf,off)[0]
    if v in colset: vpos.append((r['va']+off,v))
vpos.sort()
vts=[]; slot_to_members=collections.defaultdict(list); vt_by_addr={}
for k,(pos,col) in enumerate(vpos):
    vt=pos+4
    hard=vpos[k+1][0] if k+1<len(vpos) else r['va']+len(buf)
    slots=[]
    va=vt
    while va < hard:
        try: fv=u32(va)
        except KeyError: break
        if not (tlo <= fv < thi): break
        slots.append((va,fv)); va+=4
    rec=dict(vt=vt, col=col, td=cols[col]['td'], cls=cols[col]['cls'], slots=slots, end=va)
    vts.append(rec); vt_by_addr[vt]=rec
    for i,(sva,fv) in enumerate(slots):
        slot_to_members[fv].append(dict(vt=vt,col=col,td=cols[col]['td'],cls=cols[col]['cls'],slot=i,sva=sva))
print('vtable tables',len(vts),'slots',sum(len(v['slots']) for v in vts))
# scope
with open(ATL,'r',encoding='utf-8',errors='replace') as f:
    ah=f.readline().rstrip('\n'); al=[ln.rstrip('\n').split('\t') for ln in f if ln.strip()]
asize={int(r[0],16): int(r[1]) for r in al}
aset=set(asize)
with open(COV,'r',encoding='utf-8',errors='replace') as f:
    ch=f.readline().rstrip('\n'); cr=[ln.rstrip('\n').split('\t') for ln in f if ln.strip()]
targets=[r for r in cr if r[1].strip().upper()=='S22' and int(r[0],16) in aset]
print('S22∩atlas',len(targets))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
coltd=set(cols)|set(tds)
counts=collections.Counter()
examples={}
for row in targets:
    e=int(row[0],16); sz=asize[e]
    # read body
    try:
        rva=e-IB
        s=next(s for s in secs if s['rva']<=rva<s['rva']+max(s['vsize'],s['rawsize']))
        off=s['raw']+(rva-s['rva'])
        body=DATA[off:off+sz]
    except Exception:
        body=b''
    ins=list(md.disasm(body,e))
    a1=slot_to_members.get(e,[])
    a2_strict=[]; a2_sem=[]; a3_imm=[]; a3_mem=[]; a3_raw=[]
    regvt=collections.defaultdict(set)
    for insn in ins:
        if insn.id == 0:
            continue
        # strict A2
        if insn.id==X86_INS_MOV and len(insn.operands)>=2:
            op0,op1=insn.operands[0],insn.operands[1]
            if op0.type==X86_OP_MEM and (op0.mem.base!=X86_REG_INVALID or op0.mem.index!=X86_REG_INVALID) and op1.type==X86_OP_IMM:
                imm=op1.imm & 0xffffffff
                if imm in vt_by_addr:
                    a2_strict.append((insn.address, insn.mnemonic+' '+insn.op_str, imm))
            # semantic A2: store from register currently holding VT
            if op0.type==X86_OP_MEM and op1.type==X86_OP_REG:
                vals=regvt.get(op1.reg,set())
                if vals and (op0.mem.base!=X86_REG_INVALID or op0.mem.index!=X86_REG_INVALID):
                    for v in sorted(vals): a2_sem.append((insn.address, insn.mnemonic+' '+insn.op_str, v))
        # A3 immediate operands
        for op in insn.operands:
            if op.type==X86_OP_IMM:
                imm=op.imm & 0xffffffff
                if imm in coltd: a3_imm.append((insn.address, insn.mnemonic+' '+insn.op_str, imm))
            elif op.type==X86_OP_MEM and op.mem.disp:
                d=op.mem.disp & 0xffffffff
                if d in coltd: a3_mem.append((insn.address, insn.mnemonic+' '+insn.op_str,d))
        # update regvt conservatively
        if insn.id==X86_INS_MOV and len(insn.operands)>=2:
            dst,src=insn.operands[0],insn.operands[1]
            if dst.type==X86_OP_REG:
                if src.type==X86_OP_IMM and (src.imm & 0xffffffff) in vt_by_addr:
                    regvt[dst.reg]={(src.imm & 0xffffffff)}
                elif src.type==X86_OP_MEM and (src.mem.disp & 0xffffffff) in vt_by_addr:
                    regvt[dst.reg]={(src.mem.disp & 0xffffffff)}
                elif src.type==X86_OP_REG:
                    regvt[dst.reg]=set(regvt.get(src.reg,set()))
                else:
                    regvt.pop(dst.reg,None)
            elif dst.type==X86_OP_MEM:
                pass
        writes=set()
        for op in insn.operands:
            if op.type==X86_OP_REG:
                # conservative: after any insn with reg operand except mov dst, invalidate (simplified)
                writes.add(op.reg)
        # more precise invalidation from capstone regs_write
        for reg in insn.regs_write:
            writes.add(reg)
        for reg in writes:
            if insn.id==X86_INS_MOV and len(insn.operands)>=2 and insn.operands[0].type==X86_OP_REG and insn.operands[0].reg==reg:
                continue
            regvt.pop(reg,None)
    # raw dword COL/TD refs inside body
    for i in range(0,max(0,len(body)-3),4):
        v=struct.unpack_from('<I',body,i)[0]
        if v in coltd: a3_raw.append((e+i,v,'raw-dword'))
    for k,seq in [('a1',a1),('a2s',a2_strict),('a2sem',a2_sem),('a3imm',a3_imm),('a3mem',a3_mem),('a3raw',a3_raw)]:
        if seq:
            counts[k]+=1
            examples.setdefault(k,(row[0],seq[:2]))
        else: counts['no_'+k]+=1
print('channel hits:',dict(counts))
for k in ['a1','a2s','a2sem','a3imm','a3mem','a3raw']:
    print(k,'example',examples.get(k))
