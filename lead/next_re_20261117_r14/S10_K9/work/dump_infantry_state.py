
import sys,csv,hashlib,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
ATL={r['entry'].strip().lower():r for r in csv.DictReader((ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv').open(encoding='utf-8',newline=''),delimiter='\t')}
OUT=ROOT/'lead/next_re_20261117_r14/S10_K9/EVIDENCE/INFANTRY_STATE_CANDIDATES.txt'
addrs=['0051AA40','0051B1F0','0051BAB0','0051D0D0','0051DAF0','00522340','00522510','00522CB0','0051BAB0']
L=['INFANTRY_STATE_CANDIDATES','SAMPLE='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'EXE_SHA256='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper()]
for a in dict.fromkeys(addrs):
 ar=ATL.get(a.lower());sz=int(ar['size']) if ar else 0x100
 L.append('\n### '+a+' size='+str(sz))
 L.append('RAW='+R.read(int(a,16),sz).hex().upper())
 L.append(R.dis(int(a,16),sz))
 L.append('POST='+R.read(int(a,16)+sz,16).hex().upper())
OUT.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',OUT,'lines',len(L))
