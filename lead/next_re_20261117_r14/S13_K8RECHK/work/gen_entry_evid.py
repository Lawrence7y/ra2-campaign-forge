# -*- coding: utf-8 -*-
"""Generate per-entry EVIDENCE/<entry>.txt with full untruncated disasm + write-point lists."""
import sys, json, os, capstone
sys.stdout.reconfigure(encoding='utf-8')
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK'
WORK=os.path.join(BASE,'work'); EVID=os.path.join(BASE,'EVIDENCE')
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
DATA=open(EXE,'rb').read()
import pefile
pe=pefile.PE(EXE,fast_load=True); IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1')
    SECS.append(dict(name=nm,va=IMG+s.VirtualAddress,raw=s.PointerToRawData,rs=s.SizeOfRawData,end=IMG+s.VirtualAddress+s.Misc_VirtualSize))
def sec_of(va):
    for s in SECS:
        if s['va']<=va<s['end']: return s
def rdva(va,n):
    s=sec_of(va); return b'' if s is None else DATA[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+n]
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
s2=json.load(open(os.path.join(WORK,'s2_report.json'),encoding='utf-8'))
for e in s2:
    ea=e['entry']; out=[]
    out.append('S13-K8RECHK EVIDENCE %s'%ea)
    out.append('gamemd.exe SHA-256 73201CC0...F67476; read-only; capstone 5.0.7 skipdata=True')
    out.append('vt writes: %d'%len(e['writes']))
    out.append('')
    # dtor body itself
    out.append('=== entry body @ 0x%s (128 bytes, untruncated) ==='%ea)
    for ins in MD.disasm(rdva(int(ea,16),128),int(ea,16)):
        out.append('  %08X  %-22s %-7s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    out.append('')
    # each write host
    for i,w in enumerate(e['writes']):
        f=w['func']
        cls='CTOR' if w['func_in_initterm'] else ('ATEXIT_DTOR' if w['func_is_atexit_dtor'] else 'OTHER')
        out.append('=== write site %s (global %s) host %s cls=%s reg=%s ==='%(
            w['site'],w['global'],f,cls,w['atexit_reg_of_func']))
        out.append('  disasm lines recorded: %d (op_delete=%d atexit_calls=%d)'%(
            len(w['disasm']),w['calls_op_delete'],w['calls_atexit']))
        for ln in w['disasm']:
            out.append('  '+ln)
        out.append('')
    open(os.path.join(EVID,'%s.txt'%ea),'w',encoding='utf-8').write('\n'.join(out)+'\n')
print('per-entry evidence files:',len(s2))
