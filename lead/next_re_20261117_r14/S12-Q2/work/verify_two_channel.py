#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S12-Q2 core-number two-channel verification.
Channel A: capstone linear decode (skipdata=True) via cached insns.
Channel B: independent raw-byte scan over .text (ModRM disp32 patterns) + raw RTTI parse.
Neither channel uses function_atlas.tsv entry+size for the numeric claims.
"""
import struct, re, sys
import pefile
from core_disasm import get_insns

EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); BASE=pe.OPTIONAL_HEADER.ImageBase
TEXT=None
for s in pe.sections:
    if s.Name.rstrip(b'\x00')==b'.text':
        TEXT=(BASE+s.VirtualAddress, s.get_data())
TVA,TRAW=TEXT

segs=[]
for s in pe.sections:
    va=BASE+s.VirtualAddress; segs.append((va,va+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def rd32(va):
    for lo,hi,raw,sz in segs:
        if lo<=va<lo+sz:
            with open(EXE,'rb') as f:
                f.seek(raw+(va-lo)); b=f.read(4)
            return struct.unpack('<I',b)[0] if len(b)==4 else None
    return None
def cstr(va,n=80):
    for lo,hi,raw,sz in segs:
        if lo<=va<lo+sz:
            with open(EXE,'rb') as f:
                f.seek(raw+(va-lo)); b=f.read(n)
            z=b.find(b'\x00'); return b[:z].decode('latin-1')
    return None

def chA():
    D=get_insns(); INS=D['insns']
    out={}
    # A1: writes to [reg+0x520]
    w=[(a,m,o) for a,s,m,o in INS if re.search(r'\[\w+ \+ 0x520\]',o) and
       o.split(',')[0].find('[')>=0 and m in ('mov','movzx','movsx','add','sub','and','or','xor')]
    out['w520']=sorted(set(a for a,m,o in w))
    # A2: GetCellAt call sites
    out['call_5657a0']=sorted(set(a for a,s,m,o in INS if m=='call' and '0x5657a0' in o))
    # A3: GetCellAt body key insns in [0x5657A0,0x5657D8)
    out['getcell_body']=[(a,m,o) for a,s,m,o in INS if 0x5657A0<=a<0x5657D8 and
                         (m in ('shl','mov','cmp','js','jge','ret','add'))]
    # A4: shl reg,9 count
    out['shl9']=sum(1 for a,s,m,o in INS if m=='shl' and o.strip().endswith(', 9'))
    return out

def chB():
    out={}
    raw=TRAW
    # B1: raw bytes for disp32 0x520 preceded by 89 /r (mov [reg+disp32],reg) patterns.
    # We look for 4-byte LE 20 05 00 00 anywhere and count; then A-channel decodes refine.
    needle=struct.pack('<I',0x520)
    cnt=0; addrs=[]
    i=raw.find(needle)
    while i!=-1:
        cnt+=1; addrs.append(TVA+i); i=raw.find(needle,i+1)
    out['disp520_raw_count']=cnt
    out['disp520_raw_first']=addrs[:20]
    # B2: E8 rel32 call to 0x5657A0 : target = next_ip + rel; byte pattern search
    calls=[]
    for i in range(len(raw)-4):
        if raw[i]==0xE8:
            rel=struct.unpack('<i',raw[i+1:i+5])[0]
            ip=TVA+i
            if ip+5+rel==0x5657A0: calls.append(ip)
    out['call_5657a0_E8']=sorted(set(calls))
    # B3: RTTI raw parse for vtables
    def rtti(vt):
        col=rd32(vt-4)
        if not col: return None
        td=rd32(col+0xC)
        if not td: return None
        return cstr(td+8)
    out['rtti_7E4570']=rtti(0x7E4570)
    out['rtti_7E3EBC']=rtti(0x7E3EBC)
    return out

if __name__=="__main__":
    A=chA(); B=chB()
    print("=== CHANNEL A (capstone skipdata=True) ===")
    print("write sites [reg+0x520] count:",len(A['w520']))
    print("  ",[hex(x) for x in A['w520']])
    print("call 0x5657A0 count:",len(A['call_5657a0']))
    print("shl reg,9 count:",A['shl9'])
    print("\n=== CHANNEL B (raw bytes + RTTI) ===")
    print("raw disp32 0x520 byte occurrences:",B['disp520_raw_count'])
    print("E8 rel32 call->0x5657A0 count:",len(B['call_5657a0_E8']))
    print("  first:",[hex(x) for x in B['call_5657a0_E8'][:10]])
    print("RTTI 0x7E4570:",B['rtti_7E4570'])
    print("RTTI 0x7E3EBC:",B['rtti_7E3EBC'])
    print("\n=== CROSS-CHECK ===")
    print("call sites A vs B equal:", set(A['call_5657a0'])==set(B['call_5657a0_E8']),
          "A=",len(A['call_5657a0']),"B=",len(B['call_5657a0_E8']))
