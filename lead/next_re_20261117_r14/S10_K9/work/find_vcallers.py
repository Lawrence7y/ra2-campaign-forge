
import sys,csv,hashlib,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import re_lib as R
from capstone.x86 import X86_OP_MEM
ROOT=Path(r'D:\Project\ra2-campaign-forge')
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
OUT=ROOT/'lead/next_re_20261117_r14/S10_K9/EVIDENCE/VIRTUAL_CALLERS.txt'
targets={0x3c8:'0051B1F0 slot242',0x500:'0051DAF0 slot320',0x174:'0051D0D0 slot93',0x480:'0051AA40 slot288',0x5c:'0051BAB0 slot23',0x53c:'00522340 slot335'}
cov={r['entry'].strip().upper():r for r in csv.DictReader(COV.open(encoding='utf-8',newline=''),delimiter='\t')}
L=['VIRTUAL_CALLERS','SAMPLE='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'EXE_SHA256='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper()]
hits={k:[] for k in targets}
for ar in csv.DictReader(ATL.open(encoding='utf-8',newline=''),delimiter='\t'):
 a=int(ar['entry'],16);sz=int(ar['size'])
 ring=[]
 for ins in R.MD.disasm(R.read(a,sz),a):
  txt=f'{ins.address:08X}  {ins.bytes.hex():<16} {ins.mnemonic:<7} {ins.op_str}'
  ring.append(txt)
  if len(ring)>24:ring.pop(0)
  try:ops=ins.operands
  except:continue
  if ins.mnemonic.startswith('call'):
   for op in ops:
    if op.type==X86_OP_MEM and op.mem.disp in targets:
     nm=cov.get(f'{a:08X}',{}).get('name','-')
     hits[op.mem.disp].append((ins.address,a,nm,list(ring)))
for off,label in targets.items():
 L.append('\n=== '+label+' vt_offset='+hex(off)+' hits='+str(len(hits[off]))+' ===')
 for callva,fa,nm,ring in hits[off]:
  L.append('CALL_SITE '+f'{callva:08X}'+' in '+f'{fa:08X}'+' '+nm)
  L.extend('  '+x for x in ring[-16:])
OUT.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',OUT)
for off,label in targets.items():print(label,len(hits[off]))
