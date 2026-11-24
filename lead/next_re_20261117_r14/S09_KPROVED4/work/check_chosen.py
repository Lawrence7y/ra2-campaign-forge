import json,sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4\work')
from s4_baseline import detect_3b
CHOSEN=['004E2830','00557830','00565B00','00577920','006568A0','006A7D70','00723EC0','006D02B0']
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4\work')
from s09lib import u32
import json
sz={r['entry']:r['size'] for r in json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4\work\s09_A_remaining.json'))}
for eh in CHOSEN:
    st,lo,fl=detect_3b(int(eh,16),sz.get(eh,0))
    print(eh,'strict=',st,'loose=',lo,'flags=',{k:v for k,v in fl.items() if k in ('S1','S2','S3','S4','S5','S6','jcc','dcall','jtgt')})
