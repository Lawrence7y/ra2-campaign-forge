import sys, os, re, struct
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work')
import pe_util as pu
CARD=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE=pu.EXE
PATTERNS=[b'COPYPROTECTION',b'WChat\\SysID',b'WChat',b'SysID',b'COPY PROTECTION',b'COPY_PROTECTION']
def allbytes():
    with open(EXE,'rb') as f: return f.read()
data=allbytes()
lines=[]
lines.append('S17-K5 full-image string scan (read-only)')
lines.append('patterns='+repr([p.decode() for p in PATTERNS]))
found=[]
for pat in PATTERNS:
    for enc,label in [(pat,'ascii'),(pat.decode().encode('utf-16le'),'utf16le')]:
        low=pat.lower() if label=='ascii' else pat.decode().lower().encode('utf-16le')
        blob=data.lower()
        pos=0
        while True:
            j=blob.find(low,pos)
            if j<0: break
            found.append((j,label,pat.decode(),data[j:j+160]))
            pos=j+1
# also print all printable strings in a window around each hit
seen=set()
for off,label,pat,raw in sorted(found):
    key=(off,label)
    if key in seen: continue
    seen.add(key)
    # VA for file offset
    va=None
    for name,vbase,vsize,praw,rawsize,ch in pu.sections():
        if praw <= off < praw+rawsize:
            va=vbase+off-praw; sec=name; break
    else: sec='?'
    ctx=data[max(0,off-64):off+192]
    strs=re.findall(rb'[ -~]{4,}',ctx)
    lines.append(f'\nOFF=0x{off:X} VA={va and hex(va)} SECTION={sec} ENC={label} PAT={pat}')
    lines.append('  raw='+repr(raw[:100]))
    lines.append('  ascii_context='+' | '.join(s.decode('latin1') for s in strs))
open(CARD+r'\EVIDENCE\string_scan_raw.txt','w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('\n'.join(lines))
