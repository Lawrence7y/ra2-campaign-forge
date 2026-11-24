# -*- coding: utf-8 -*-
import sys,pefile,capstone
sys.stdout.reconfigure(encoding='utf-8')
P=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
D=open(P,'rb').read(); pe=pefile.PE(P,fast_load=True); IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().rstrip('\x00'),IMG+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def sec_of(va):
    for n,b,vs,pt,rs in SECS:
        if b<=va<b+vs:return n,b,vs,pt,rs
def rd(va,n):
    s=sec_of(va)
    if not s:return b''
    _,b,vs,pt,rs=s; return D[pt+(va-b):pt+(va-b)+n]
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.skipdata=True
audit18='0075E510 0065BED0 0040BBC0 0040BC10 0040F8A0 0040F8F0 0040FE70 0040FEC0 0046B8C0 0046B910 0048AFD0 0048B020 0054EB50 0054EBA0 0062B330 0062B380 0065C1B0 0065C200'.split()
out=[]
for sx in audit18:
    va=int(sx,16)
    out.append('===== %s ====='%sx)
    code=rd(va,400)
    cnt=0
    for ins in MD.disasm(code,va):
        out.append('%08X  %-20s %-7s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
        cnt+=1
        if ins.mnemonic in ('ret','retf') or cnt>40: break
    out.append('')
fn=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8\EVIDENCE\bodies_audit18.txt'
open(fn,'w',encoding='utf-8').write('\n'.join(out)+'\n')
print('wrote',fn,'lines',len(out))
