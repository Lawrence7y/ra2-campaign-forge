"""Diagnose atlas-gap candidates: context around each target, prologue check, callers."""
import os, json, bisect, struct
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..'))
PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EVID=os.path.join(BASE,'EVIDENCE')
EXE=os.path.join(PROJECT,'ra2youli','gamemd.exe')
ATLAS=os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB=chr(9)
import pefile, capstone
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.decode(errors='replace').rstrip('\x00'); va=IB+s.VirtualAddress
    secs.append(dict(name=nm,va=va,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
text=next(s for s in secs if s['name']=='.text'); DATA=pe.__data__
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
with open(ATLAS,encoding='utf-8',errors='replace') as f: lines=f.read().splitlines()
rows=[]
for ln in lines[1:]:
    p=ln.split(TAB)
    if len(p)<9: continue
    try: e=int(p[0],16)
    except: continue
    rows.append((e,e+int(p[1]),p[0],int(p[1])))
rows.sort(); starts=[r[0] for r in rows]; ends=[r[1] for r in rows]
def readva(va,n):
    off=text['raw']+(va-text['va'])
    return DATA[off:off+n]
def disasm_from(va,n=48):
    out=[]
    for insn in md.disasm(readva(va,n),va):
        if insn.id==0: continue
        out.append('%s %s'%(insn.mnemonic,insn.op_str))
        if len(out)>=8: break
    return ' ; '.join(out)
d=json.load(open(os.path.join(EVID,'atlas_gaps_full.json'),encoding='utf-8'))
notcov=[x for x in d['gaps'] if not x['inside_atlas']]
calls=json.load(open(os.path.join(EVID,'callgraph.json'),encoding='utf-8'))
print('total not-covered:',len(notcov))
for x in notcov:
    t=x['target']
    i=bisect.bisect_right(starts,t)-1
    prev = '%08X+%d(end %08X)'%(rows[i][0],rows[i][3],rows[i][1]) if i>=0 else '-'
    nxt = '%08X'%rows[i+1][0] if i+1<len(rows) else '-'
    callers = calls.get(str(t),[])
    print('%08X c%d j%d prev=%s nxt=%s'%(t,x['ncall'],x['njmp'],prev,nxt))
    print('    body:',disasm_from(t)[:100])
    if callers: print('    callers:',[('%08X'%c['src']) for c in callers[:6]])
