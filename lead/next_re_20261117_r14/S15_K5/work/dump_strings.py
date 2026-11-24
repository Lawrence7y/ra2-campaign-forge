from pathlib import Path
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
from pe_common import PE, IMAGE_BASE
OUT = Path(__file__).resolve().parents[1] / 'EVIDENCE' / 'strings_trigger_candidates.txt'
patterns = re.compile(r'(?i)(taaction|tevent|ttrigger|trigger|action|event|eva_|\.cpp|\.h|%s|\[triggers\]|\[events\]|\[actions\]|\[tags\]|voc|vox|theme|movie|talkbubble|waypoint|<none>|invalid|sound\.ini|eva\.ini)')
rows=[]
for sec in PE.sections:
    name=sec.Name.rstrip(b'\x00').decode('ascii','replace')
    if sec.SizeOfRawData == 0: continue
    data=PE.__data__[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
    for m in re.finditer(rb'[\x20-\x7e]{4,}', data):
        s=m.group().decode('ascii','replace')
        if patterns.search(s):
            va=IMAGE_BASE+sec.VirtualAddress+m.start()
            rows.append((va,name,s))
rows.sort()
OUT.write_text('\n'.join(f'{va:08X}\t{sec}\t{s}' for va,sec,s in rows)+'\n', encoding='utf-8')
print('strings',len(rows),'->',OUT)
for r in rows[:200]: print(f'{r[0]:08X}\t{r[1]}\t{r[2]}')
