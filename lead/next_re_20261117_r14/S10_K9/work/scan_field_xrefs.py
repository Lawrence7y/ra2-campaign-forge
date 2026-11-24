
import sys,csv,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import re_lib as R
from capstone.x86 import X86_OP_MEM
ROOT=Path(r'D:\Project\ra2-campaign-forge')
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
OUT=ROOT/'lead/next_re_20261117_r14/S10_K9/EVIDENCE/FIELD_XREFS.txt'
targets={0x6c4,0x6db,0x6dc,0x2dc,0x2d0}
cov={r['entry'].strip().upper():r for r in csv.DictReader(COV.open(encoding='utf-8',newline=''),delimiter='\t')}
L=['FIELD_XREFS','TARGET_DISPS='+','.join(hex(x) for x in sorted(targets))]
for ar in csv.DictReader(ATL.open(encoding='utf-8',newline=''),delimiter='\t'):
 a=int(ar['entry'],16);sz=int(ar['size'])
 for ins in R.MD.disasm(R.read(a,sz),a):
  try:ops=ins.operands
  except:continue
  for k,op in enumerate(ops):
   if op.type==X86_OP_MEM and op.mem.disp in targets:
    nm=cov.get(f'{a:08X}',{}).get('name','-')
    rw='W' if k==0 and ins.mnemonic in ('mov','movzx','movsx','add','sub','inc','dec','and','or','xor','setne','sete') else 'R'
    L.append(f'{rw} {ins.address:08X} {ins.mnemonic} {ins.op_str} | fn={a:08X} {nm}')
OUT.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',OUT,'hits',len(L)-2)
