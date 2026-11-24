
import sys,csv,struct,hashlib,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import re_lib as R
CARD=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K9')
ATL=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')
COV=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
OUT=CARD/'EVIDENCE/CANDIDATE_DISASM.txt'
atl=[r for r in csv.DictReader(ATL.open(encoding='utf-8',newline=''),delimiter='\t')]
by={r['entry'].strip().upper():r for r in atl}
iv=[(int(r['entry'],16),int(r['entry'],16)+int(r['size']),r['entry']) for r in atl]
iv.sort()
cov={r['entry'].strip().upper():r for r in csv.DictReader(COV.open(encoding='utf-8',newline=''),delimiter='\t')}
def containing(va):
 lo,hi=0,len(iv)-1
 # simple scan for small calls okay
 for a,b,e in iv:
  if a<=va<b:return a,b,e
 return None
def call_xrefs(target):
 sec=R.sections()[0]; data=R.PE.__data__[sec[4]:sec[4]+sec[3]]
 pat=b'\xe8'+struct.pack('<i',target-(sec[1]+5))
 hits=[];pos=0
 while True:
  i=data.find(pat,pos)
  if i<0:break
  va=sec[1]+i+5
  c=containing(va)
  if c:
   a,b,e=c
   lines=[];found=False
   for ins in R.MD.disasm(R.read(a,b-a),a):
    lines.append(f'{ins.address:08X}  {ins.bytes.hex():<16} {ins.mnemonic:<7} {ins.op_str}')
    if ins.address==va:found=True;break
   if found:hits.append((va,e,lines[-14:]))
  pos=i+1
 return hits
addrs=['0051DAF0','00709820','00740FD0','004DB3C0','006FCDB0','00746100','00522A60','00737430','0051DBD0','00700C40','004B4890','005F5E80','005B3060','005B2E40','0051CDB0','0051F2C0','0070AA60','00746B20']
L=['CANDIDATE_DISASM exact excerpts','SAMPLE='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'EXE_SHA256='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper(),'TOOLS=Python3.12 capstone5.0.7(skipdata=True)+pefile2024.8.26']
for a in addrs:
 va=int(a,16);r=by.get(a);size=int(r['size']) if r else 0x100
 q=cov.get(a);L.append('\n### '+a+' size='+str(size)+' cov_name='+(q['name'] if q else '-')+' cov_grade='+(q['grade'].strip() if q else '-'))
 L.append('RAW='+R.read(va,size).hex().upper())
 L.append(R.dis(va,size))
 L.append('POST='+R.read(va+size,16).hex().upper())
 xs=call_xrefs(va)
 L.append('DIRECT_CALL_XREFS='+str(len(xs)))
 for callva,fn,lines in xs:
  L.append('  CALL_SITE '+f'{callva:08X}'+' in '+fn)
  L.extend('    '+x for x in lines)
OUT.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',OUT,'lines',len(L))
for a in addrs:
 print(a,'callers',len(call_xrefs(int(a,16))))
