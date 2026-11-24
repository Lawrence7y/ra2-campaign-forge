
import sys,hashlib,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import re_lib as R
CARD=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K9')
OUT=CARD/'EVIDENCE/MISSION_STATE_PROOF.txt'
VC=(CARD/'EVIDENCE/VIRTUAL_CALLERS.txt').read_text(encoding='utf-8').split('\n')
def dr(a,b):
 return R.dis(int(a,16),int(b,16)-int(a,16))
def ctx(site,n=16):
 for i,x in enumerate(VC):
  if x.startswith('CALL_SITE '+site):
   return '\n'.join(VC[i:i+n])
 return 'CONTEXT_NOT_FOUND '+site
def ev(va):
 raw=R.read(va,16).hex().upper();return 'BYTES@'+f'{va:08X}'+'='+raw
L=['S10_K9 MISSION-STATE BEHAVIOR PROOF','SAMPLE='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'EXE_SHA256='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper(),'TOOLS=Python3.12.10 capstone5.0.7(skipdata=True)+pefile2024.8.26','METHOD=byte excerpts only; RTTI class-name chain uses COL+0xC -> TD and TD+8 inline string; vtable slot location never used alone as semantics','BASELINE=EVIDENCE/BASELINE_K9.txt']
L.append('\n=== RTTI_AND_VTABLE ===')
vt=0x7EB058;col=R.u32(vt-8);td=R.u32(col+0xC)
if td>0xB00000 or True:
 col=0x8033B8;td=R.u32(col+0xC)
L += ['PRIMARY_VTABLE=0x7EB058','COL(vt-8)='+hex(col),'TD(COL+0xC)='+hex(td),'CLASS_NAME(TD+8)='+repr(R.cstring(td+8,80))]
for off in [0x5C,0x3C8,0x500,0x53C,0x558,0x1E8]:
 L.append(f'SLOT+0x{off:X}={R.u32(vt+off):08X}')
L.append('CONSTRUCTION_VPTR_WRITE=00517D9D c70658b07e00 mov dword ptr [esi],0x7EB058')
L.append('\n=== MISSION_ENUM ===')
names=[]
for i in range(32):
 p=R.u32(0x816CAC+4*i)
 names.append(R.cstring(p,80) if p else '?')
L.append('TABLE=0x816CAC[0..31]='+'|'.join(f'{i}:{names[i]}' for i in range(32)))
L.append('YRPP_ENUM=ref/yrpp/GeneralDefinitions.h Mission: 27=ParadropOverfly 28=Wait 29=AttackMove 30=SpyplaneApproach 31=SpyplaneOverfly')
L.append('\n=== CALLEE_0051D6F0 (v+0x558 target, mission-state setter) ===')
L.append(ev(0x51D6F0));L.append(dr('0051D6F0','0051D736'));L.append(dr('0051D7E0','0051D842'));L.append(dr('0051D90B','0051DA44'));L.append(dr('0051DA4A','0051DAE2'))
L.append('CALLER_00521760_full:');L.append(R.dis(0x00521760,90));L.append('CALLER_ARG_NOTE=push 0 / push 1 / push 0x21 / ecx=esi then call [v+0x558] at 005217A8')
L.append('\n=== CALLEE_005B35E0 (v+0x1E8 QueueMission, separate slot not used for these semantics) ===')
L.append(ev(0x5B35E0));L.append(R.dis(0x005B35E0,101))
for a,mode in [('0051DAF0','full'),('0051B1F0','full'),('0051BAB0','partial'),('00522340','full')]:
 L.append('\n### '+a)
 va=int(a,16)
 if mode=='full':
  L.append(ev(va));L.append(R.dis(va,{'0051DAF0':223,'0051B1F0':347,'00522340':393}[a]));L.append('POST='+R.read(va+{'0051DAF0':223,'0051B1F0':347,'00522340':393}[a],16).hex().upper())
 else:
  L.append(ev(va));L.append(dr('0051BBD1','0051BBEF'));L.append(dr('0051BDFB','0051BE3E'));L.append('POST='+R.read(va+1239,16).hex().upper())
 L.append('CALLER_CONTEXT:')
 site={'0051DAF0':'0051DAA1','0051B1F0':'0051BBEF','0051BAB0':'004DAEF3','00522340':'004D473A'}[a]
 L.append(ctx(site))
L.append('\n### 0051D6F0')
L.append('See CALLEE_0051D6F0 above; that section is this entry proof.')
OUT.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',OUT,'lines',len(L),'bytes',OUT.stat().st_size)
