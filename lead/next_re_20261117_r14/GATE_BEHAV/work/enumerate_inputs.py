#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GATE-BEHAV step-1 static enumeration. READ-ONLY on gamemd.exe.
capstone 5.0.7 skipdata=True (discipline #2), pefile. No writes to target.
Enumerates every condition input that determines the branch into/out of 0x47C738.
"""
import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
_pe = pefile.PE(BIN, fast_load=True); _pe.parse_data_directories()
SEC=[]
for s in _pe.sections:
    SEC.append((s.Name.rstrip(b'\0').decode('latin-1'), IB+s.VirtualAddress,
                s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
DATA=open(BIN,'rb').read()
def va2off(va):
    for name,sva,vsz,praw,rsz in SEC:
        if sva<=va<sva+max(vsz,rsz):
            o=praw+(va-sva)
            if 0<=o<len(DATA): return o
    return None
def read(va,n):
    o=va2off(va); return DATA[o:o+n] if o is not None else b'\0'*n
def u32(va): return struct.unpack('<I',read(va,4))[0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def disasm(va,maxb):
    for i in md.disasm(read(va,maxb),va): yield i
def fmt(i): return "%08X  %-8s %s"%(i.address,i.mnemonic,i.op_str)

def mem_disp(op):
    if op.type!=X86_OP_MEM: return None
    # absolute [0xXXXXXXXX] when base/index are 0
    if op.mem.base==0 and op.mem.index==0:
        return ('ABS', op.mem.disp & 0xffffffff)
    base = op.mem.base
    bn = reg_name(base)
    return ('REG', bn, op.mem.disp)

def reg_name(r):
    try: return md.reg_name(r)
    except Exception: return 'r%d'%r

def analyze_fn(start, end, title):
    print("="*78)
    print(title, "range %08X..%08X"%(start,end))
    print("="*78)
    conds=[]
    for i in disasm(start,end-start):
        m=i.mnemonic
        # conditional jumps + cmp/test are the branch-defining ops
        if m.startswith('j') and m!='jmp':
            print("Jcc  ", fmt(i))
        elif m in ('cmp','test'):
            ops=i.operands
            memops=[o for o in ops if o.type==X86_OP_MEM]
            tag=''
            for o in memops:
                d=mem_disp(o)
                if d: tag+=" mem=%s"%str(d)
            print("COND ", fmt(i), tag)
    print()

analyze_fn(0x47C620,0x47CA7C,"0x47C620 main gate dispatcher")
analyze_fn(0x47C3D0,0x47C4CA,"0x47C3D0 bit0 existence core")
analyze_fn(0x47C4D0,0x47C520,"0x47C4D0 terrain second gate")

# Verify global access counts (absolute-form) across whole .text
print("="*78)
print("GLOBAL ACCESS COUNTS (absolute form, whole .text)")
print("="*78)
text_va=None; text_sz=None
for name,sva,vsz,praw,rsz in SEC:
    if name=='.text': text_va,text_sz=sva,max(vsz,rsz)
targets={0xA8E7AC:0,0xA8E9A0:0,0xA8ED6B:0,0xA8ED38:0,0xA8ED2C:0,0xA8022C:0,0xAA0738:0,0xA83D84:0}
counts={k:{'r':0,'w':0,'inc':0} for k in targets}
for i in disasm(text_va,text_sz):
    try:
        ops=i.operands
    except Exception:
        continue  # skipdata data pseudo-insn: no operands
    for o in ops:
        d=mem_disp(o)
        if d and d[0]=='ABS' and d[1] in targets:
            a=d[1]
            if i.mnemonic.startswith('inc') or i.mnemonic.startswith('dec'):
                counts[a]['inc']+=1
            elif i.mnemonic in ('mov','cmp','test','add','sub','and','or','xor') :
                # crude: if this op is destination of mov -> write
                if i.mnemonic=='mov' and o is i.operands[0]:
                    counts[a]['w']+=1
                else:
                    counts[a]['r']+=1
            else:
                counts[a]['r']+=1
for a in sorted(counts):
    print("%08X  r=%d w=%d incdec=%d"%(a,counts[a]['r'],counts[a]['w'],counts[a]['inc']))

# Verify unique bit0 write point: or reg8,1 -> mov [reg+0x14],reg8
print("="*78)
print("bit0 WRITE POINTS: 'or r8,1' followed within 8 insns by 'mov [reg+0x14],r8'")
print("="*78)
hits=[]
for ins in disasm(text_va,text_sz):
    try:
        iops=ins.operands
    except Exception:
        continue
    if ins.mnemonic=='or' and len(iops)==2:
        op0,op1=iops
        if op0.type==X86_OP_REG and op1.type==X86_OP_IMM and op1.imm==1:
            r=op0.reg
            seq=list(disasm(ins.address, 24))
            for j in seq[1:9]:
                try:
                    jops=j.operands
                except Exception:
                    continue
                if j.mnemonic=='mov' and len(jops)==2:
                    d=mem_disp(jops[0])
                    if d and d[0]=='REG' and d[2]==0x14 and jops[1].type==X86_OP_REG and jops[1].reg==r:
                        hits.append((ins.address,j.address,fmt(ins),fmt(j)))
                        break
for h in hits:
    print("OR@%08X -> MOV@%08X : %s | %s"%h)
print("TOTAL bit0 or->mov[+0x14] chains =",len(hits))
