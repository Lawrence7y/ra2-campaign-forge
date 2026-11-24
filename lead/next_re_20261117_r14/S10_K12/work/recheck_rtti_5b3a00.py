
import sys, hashlib
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K12\work')
from re_lib import PE, BASE, read, u32, dis, cstring, sections, off

L=[]
def log(s=''):
    L.append(str(s))

log('S10-K12 RECHECK 1: EXE SHA / RTTI / 005B3A00')
exe=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
log('EXE_SHA256='+hashlib.sha256(open(exe,'rb').read()).hexdigest().upper())
log('BASE='+hex(BASE))
log('SECTIONS:')
for name,va,vsz,rsz,ptr in sections():
    log(f'  {name:8s} va={va:08X} vsz={vsz:08X} rsz={rsz:08X} ptr={ptr:08X}')

log('')
log('--- RTTI chain check ---')
vt=0x7EB058
for label,addr in [('vt-12',vt-12),('vt-8',vt-8),('vt-4',vt-4),('vt',vt),('vt+4',vt+4)]:
    try:
        v=u32(addr)
        log(f'{label} @ {addr:08X} = {v:08X}')
    except Exception as e:
        log(f'{label} @ {addr:08X} ERR {e}')
# COL from vt-4
col=u32(vt-4)
log(f'COL candidate @vt-4 = {col:08X}')
try:
    sig=u32(col); off1=u32(col+4); cd=u32(col+8); pTD=u32(col+0xC); pCD=u32(col+0x10)
    log(f'  COL sig={sig:08X} off={off1:08X} cd={cd:08X} pTD={pTD:08X} pCD={pCD:08X}')
    td=pTD
    log(f'  TD+0={u32(td):08X} TD+4={u32(td+4):08X} TD+8 bytes={read(td+8,16).hex()}')
    log(f'  cstring(TD+8)={cstring(td+8,64)!r}')
    # RTTI name from CD
    try: log(f'  CD name: {cstring(pCD,64)!r}')
    except Exception as e: log(f'  CD name ERR {e}')
except Exception as e:
    log('  parse ERR '+repr(e))

log('')
log('--- 005B3A00 disassembly ---')
log(dis(0x5B3A00,64))

out=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K12\EVIDENCE\RECHECK_RTTI_5B3A00.txt'
open(out,'w',encoding='utf-8',newline='\n').write('\n'.join(L)+'\n')
print('\n'.join(L))
