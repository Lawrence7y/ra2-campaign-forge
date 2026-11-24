
import sys,csv,hashlib,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import re_lib as R
ATL=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')
OUT=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K9\EVIDENCE\MISSION_SKELETON_DISASM.txt')
atl={r['entry'].strip().lower():r for r in csv.DictReader(ATL.open(encoding='utf-8',newline=''),delimiter='\t')}
addrs=['005B3060','005B3650','005B36B0','005B3700','005B3760','005B3910','005B3970','005B35E0','005B3570','0041BA90','0041B870','005F5E80','005F6250','00410410']
L=['MISSIONSKELETON DISASSEMBLY','SAMPLE='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'EXE_SHA256='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper(),'TOOLS=Python3.12 capstone5.0.7(skipdata=True) pefile2024.8.26','NOTE=range from atlas size; boundary independently checked by last ret and post-ret bytes']
for a in addrs:
 r=atl.get(a.lower()); va=int(a,16); size=int(r['size']) if r else 0x100
 raw=R.read(va,size)
 L.append('\n### '+a+' size='+str(size)+' bytes='+raw.hex().upper())
 L.append(R.dis(va,size))
 post=R.read(va+size,16)
 L.append('POST_'+a+'='+post.hex().upper())
OUT.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',OUT,'lines',len(L))
