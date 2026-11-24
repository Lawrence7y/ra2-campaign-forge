# -*- coding: utf-8 -*-
"""Investigate multi-membership entries and ambiguous targets."""
import os,re,sys,struct,collections
import pefile
sys.stdout.reconfigure(encoding='utf-8')
HERE=os.path.dirname(os.path.abspath(__file__));PROJ=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EXE=os.path.join(PROJ,'ra2youli','gamemd.exe')
pe=pefile.PE(EXE);IB=pe.OPTIONAL_HEADER.ImageBase;SZ=pe.OPTIONAL_HEADER.SizeOfImage
def sec(n):return [s for s in pe.sections if s.Name.rstrip(b'\0').decode('latin1')==n][0]
t=sec('.text');r=sec('.rdata');TLO=IB+t.VirtualAddress;THI=TLO+t.Misc_VirtualSize;RLO=IB+r.VirtualAddress;RSZ=r.SizeOfRawData
blob=open(EXE,'rb').read()
def off(va):
    rv=va-IB
    if rv<0 or rv>=SZ:return None
    for s in pe.sections:
        sv=s.VirtualAddress;vs=max(s.Misc_VirtualSize,s.SizeOfRawData)
        if sv<=rv<sv+vs:
            o=s.PointerToRawData+(rv-sv);return o if 0<=o<len(blob) else None
def u32(va):
    o=off(va);return struct.unpack_from('<I',blob,o)[0] if o is not None and o+4<=len(blob) else None
def cs(va,cap=256):
    o=off(va)
    if o is None or o+cap>len(blob):return b''
    b=blob[o:o+cap];z=b.find(b'\0');return b[:z] if z>0 else b''
def rn(cp):
    if not(IB<=cp<IB+SZ):return None
    sig=u32(cp);td=u32(cp+0xC);cd=u32(cp+0x10)
    if sig not in(0,1) or td is None or not(IB<=td<IB+SZ):return None
    nm=cs(td+8)
    return nm.decode('latin1') if nm.startswith(b'.?AV') or nm.startswith(b'.?AU') else None
def dem(x):
    if x.startswith('.?AV') or x.startswith('.?AU'):x=x[4:]
    if x.endswith('@@'):x=x[:-2]
    return x.replace('?$','T_').replace('@','::')
rdb=blob[r.PointerToRawData:r.PointerToRawData+RSZ];nw=len(rdb)//4;w=struct.unpack_from('<%dI'%nw,rdb,0)
def it(v):return TLO<=v<THI
fmap=collections.defaultdict(list);i=0
while i<nw:
    if it(w[i]):
        j=i
        while j<nw and it(w[j]):j+=1
        cp=w[i-1] if i>=1 else 0;raw=rn(cp)
        if raw:
            c=dem(raw)
            for k in range(j-i):fmap[w[i+k]].append((c,raw,k,RLO+4*i))
        i=j
    else:i+=1
for e in [0x00410210,0x00410480,0x00410B90,0x004C9150,0x004F8440,0x006CE7C0]:
    mem=fmap.get(e)
    print('%08X -> %d memberships'%(e,len(mem) if mem else 0))
    if mem:
        for c,raw,k,vt in mem:print('    %-45s slot%-4d vt=%08X raw=%s'%(c,k,vt,raw[:50]))
