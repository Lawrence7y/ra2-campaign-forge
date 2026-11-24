import json, re, struct, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
raw=open('ra2bench/gamemd.exe','rb').read()
print('sha', hashlib.sha256(raw).hexdigest()[:16])
e=struct.unpack_from('<I',raw,0x3c)[0]; nsec,=struct.unpack_from('<H',raw,e+6); osz,=struct.unpack_from('<H',raw,e+20)
opt=e+24; IB=struct.unpack_from('<I',raw,opt+28)[0]
secs=[]
for i in range(nsec):
    o=opt+osz+i*40; nm=raw[o:o+8].rstrip(b'\0').decode()
    vs,rva,rs,ra=struct.unpack_from('<IIII',raw,o+8); secs.append((nm,IB+rva,vs,ra,rs))
def off(va):
    for nm,sv,vs,ra,rs in secs:
        if sv<=va<sv+max(vs,rs): return ra+(va-sv)
tn,TS,tvs,tra,trs=next(s for s in secs if s[0]=='.text'); TE=TS+tvs
sym=json.load(open('out/reverse/symbols.json'))['classes']
vt={}
for k,v in sym.items():
    if v.get('vtable_va'): vt[int(v['vtable_va'],16)]=v['name']
print('vtables', len(vt))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
pat=re.compile(r'^dword ptr \[(e[a-z]{2})\]?, (0x[0-9a-f]+)$')
pat2=re.compile(r'^dword ptr \[(e[a-z]{2}) \+ (0x[0-9a-f]+)\], (0x[0-9a-f]+)$')
hits=[]
pos=TS
while pos<TE:
    hi=min(pos+65536,TE); buf=raw[off(pos):off(hi)+16]; last=pos
    for a,sz,m,o in md.disasm_lite(buf,pos):
        if a>=hi: break
        last=a+sz
        if m=='mov' and o.endswith(tuple('0123456789abcdef')) and 'ptr [' in o and ', 0x' in o:
            mm=pat.match(o) or pat2.match(o)
            if mm:
                g=mm.groups()
                if len(g)==2: reg,imm=g; disp=0
                else: reg,disp,imm=g; disp=int(disp,16)
                iv=int(imm,16)
                if iv in vt: hits.append((hex(a),reg,disp,hex(iv),vt[iv]))
    if last<=pos: last=pos+1
    pos=last
print('hits', len(hits))
from collections import Counter
print(Counter(h[2] for h in hits).most_common(12))
for h in hits[:15]: print(h)
json.dump(hits,open('_r109/probe_vt0.json','w'))
