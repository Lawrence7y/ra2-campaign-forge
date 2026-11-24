import sys,struct,json,collections,array
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
TL,TH=0x401000,0x7e1000
SPAN=TH-TL
md=Cs(CS_ARCH_X86,CS_MODE_32)

raw=open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','rb').read()
n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n])
SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
ISSTART=bytearray(SPAN); SIZE=bytearray(SPAN)
for a,s in zip(STARTS,SIZES):
    ISSTART[a-TL]=1; SIZE[a-TL]=s
print('starts',len(STARTS))

# rel targets: call(0xE8) / jmp(0xE9) / jcc(0F 8x)
tlo=foff(TL); seg=_img[tlo:tlo+SPAN]
calls=[]; jmps=[]; jccs=[]
for k in range(SPAN-6):
    if not ISSTART[k]: continue
    b=seg[k]; a=TL+k
    if b==0xE8 and SIZE[k]==5:
        t=(a+5+struct.unpack('<i',seg[k+1:k+5])[0])&0xffffffff
        if TL<=t<TH: calls.append(t)
    elif b==0xE9 and SIZE[k]==5:
        t=(a+5+struct.unpack('<i',seg[k+1:k+5])[0])&0xffffffff
        if TL<=t<TH: jmps.append(t)
    elif b==0x0f and SIZE[k]==6 and 0x80<=seg[k+1]<=0x8f:
        t=(a+6+struct.unpack('<i',seg[k+2:k+6])[0])&0xffffffff
        if TL<=t<TH: jccs.append(t)
print('call targets',len(set(calls)),'jmp targets',len(set(jmps)),'jcc targets',len(set(jccs)))

# --- function entries: call targets that are instruction starts; plus non-referenced prologues ---
cand_entries=sorted({t for t in calls if ISSTART[t-TL]})
print('entry candidates (start-aligned call targets)',len(cand_entries))

FUNC=array.array('i',[-1])*1  # placeholder
FUNC=array.array('i',bytes(4*SPAN))  # zeros
for i in range(SPAN): pass
# use 0 = unvisited, k = func id
def decode(a):
    o=foff(a)
    if o is None: return None
    for ins in md.disasm_lite(_img[o:o+16],a):
        return ins
    return None

funcentries=[]; fid=0
resolved={}
stack=[]
for e in cand_entries:
    if not ISSTART[e-TL]: continue
    fid+=1
    funcentries.append(e)
    stack=[e]
    while stack:
        a=stack.pop()
        while True:
            if not (TL<=a<TH): break
            if FUNC[a-TL]!=0: break
            if not ISSTART[a-TL]: break
            FUNC[a-TL]=fid
            ins=decode(a)
            if ins is None: break
            _,sz,mn,op=ins
            nxt=a+sz
            if mn=='ret' or mn=='retf' or mn.startswith('iret'): break
            if mn in ('jmp',):
                if op.startswith('0x'):
                    stack.append(int(op,16)); break
                break   # indirect jmp ends this path
            if mn.startswith('j') or mn=='loop' or mn.startswith('loop'):
                if op.startswith('0x'): stack.append(int(op,16))
                a=nxt; continue
            if mn=='call':
                a=nxt; continue
            a=nxt
print('functions discovered',fid)
cov=sum(1 for i in range(SPAN) if FUNC[i]!=0)
print('instructions attributed',cov,'of',len(STARTS))
json.dump(dict(n_func=fid,entries=funcentries,covered=cov),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_funcstat.json','w'))
with open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_funcmap.bin','wb') as f:
    f.write(FUNC.tobytes())
with open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_entries.bin','wb') as f:
    f.write(array.array('I',funcentries).tobytes())
