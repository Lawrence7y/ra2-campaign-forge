import sys,re,collections,json
ROOT='/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0,ROOT+'/_r119')
from _pe119 import PE_, BUF
import capstone
T=PE_.sec_by_name('.text')
MD=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); MD.detail=False; MD.skipdata=True
IAT=json.load(open(ROOT+'/_r119/iat_names.json')); IATV={int(k,16):v[1] for k,v in IAT.items()}
WRITE_MN={'mov','lea','xor','pop','add','sub','and','or','imul','movzx','movsx','inc','dec','shl','shr','xchg','adc','sbb','neg','not'}
REGS='eax ebx ecx edx esi edi ebp esp'.split()
def fstart(va, back=0x4000):
    lo=max(T['va'],va-back); o=PE_.va2off(lo); e=PE_.va2off(va)
    blob=BUF[o:e]
    i=blob.rfind(b'\xcc\xcc\xcc')
    if i>=0: return lo+i+3
    i=blob.rfind(b'\xcc')
    return lo+i+1 if i>=0 else lo
def stream(st,to):
    o=PE_.va2off(st); n=PE_.va2off(to)-o
    return list(MD.disasm_lite(BUF[o:o+n],st))
def sites(t):
    out=[]
    for off in range(0,T['vsize'],65536):
        blob=BUF[T['raw']+off:T['raw']+min(off+65536,T['vsize'])]
        for (a,sz,mn,ops) in MD.disasm_lite(blob,T['va']+off):
            if mn=='push' and ops.startswith('0x'):
                try:
                    if int(ops,16)==t: out.append(a)
                except ValueError: pass
    return out
def reg_at(seq, upto, reg):
    """last write to reg before index upto within seq"""
    last=None
    for k in range(0,upto):
        a,sz,mn,ops=seq[k]
        if not re.match(r'^%s(,|$)'%reg, ops) and not re.match(r'^%s,'%reg,ops): 
            # also handle 'push'/'call' clobber later
            continue
        if mn in WRITE_MN: last=(hex(a),mn,ops)
    return last
def resolve(val, idx, seq, reg):
    m=re.fullmatch(r'%s, dword ptr \[(0x[0-9a-f]+)\]'%reg, val[2] if isinstance(val,tuple) else '')
    return None
def analyze(s):
    st=fstart(s)
    seq=stream(st, s+0x90)
    idx=[i for i,x in enumerate(seq) if x[0]==s]
    if not idx: return {'site':hex(s),'err':'nolocate'}
    idx=idx[0]
    out={'site':hex(s),'func':hex(st)}
    # ppv slot
    slot=None
    for i in range(idx-1,max(-1,idx-10),-1):
        if seq[i][2]=='push' and re.fullmatch(r'[a-z]{2,3}',seq[i][3]):
            R=seq[i][3]
            for j in range(i-1,max(-1,i-10),-1):
                m=re.fullmatch(r'([a-z]{2,3}), \[esp \+ (0x[0-9a-f]+)\]',seq[j][3])
                if seq[j][2]=='lea' and m and m.group(1)==R:
                    slot=(R,m.group(2),j); break
                if re.match(r'^%s,'%R,seq[j][3]) and seq[j][2] in WRITE_MN: break
            break
    qi=None
    for i in range(idx,len(seq)):
        if seq[i][2]=='call' and seq[i][3]=='dword ptr [ecx]': qi=i;break
    out['ppv']= (slot[0],slot[1]) if slot else None
    if not slot: out['consume']='NO-PPV'; return out
    if qi is None: out['consume']='NO-QI'; return out
    K=slot[1]; P=None; pushes=[]
    for i in range(qi+1,len(seq)):
        a,sz,mn,ops=seq[i]
        m=re.fullmatch(r'([a-z]{2,3}), dword ptr \[esp \+ %s\]'%re.escape(K),ops)
        if mn=='mov' and m: P=m.group(1); out['P']=P; continue
        if mn=='push':
            mm=re.fullmatch(r'([a-z]{2,3})',ops)
            pushes.append(mm.group(1) if mm else 'imm:'+ops); pushes=pushes[-4:]
            continue
        if mn=='call':
            if ops.startswith('dword ptr [0x'):
                v=int(ops[len('dword ptr ['):-1],16)
                out['consume']='IAT:'+IATV.get(v,'NOT-IAT:%x'%v); out['consume_at']=hex(a)
            elif re.fullmatch(r'[a-z]{2,3}',ops):
                w=reg_at(seq,i,ops)
                nm='REG:'+ops
                if w:
                    mm=re.fullmatch(r'%s, dword ptr \[(0x[0-9a-f]+)\]'%ops,w[2])
                    if mm: nm='REG:'+ops+'<-IAT:'+IATV.get(int(mm.group(1),16),'NOT-IAT')
                    else: nm='REG:'+ops+'<-'+w[1]
                out['consume']=nm; out['consume_at']=hex(a); out['regwrite']=w
            elif ops.startswith('dword ptr ['):
                out['consume']='IND:'+ops[len('dword ptr ['):-1]; out['consume_at']=hex(a)
            else:
                out['consume']='REL:'+ops; out['consume_at']=hex(a)
            out['argpos']=(len(pushes)-1-pushes[::-1].index(P)) if (P and P in pushes) else None
            out['pushes']=list(pushes)
            return out
        if mn=='ret': out['consume']='RET'; return out
    out['consume']='SCAN-END'; return out
for target in (0x7f7c80,):
    S=sites(target); R=[analyze(s) for s in S]
    print('===',hex(target),'sites',len(S))
    print(' ppv resolved',sum(1 for r in R if r.get('ppv')))
    c=collections.Counter(r.get('consume') for r in R)
    for k,v in c.most_common(): print('   %-34s %d'%(k,v))
    print(' argpos',dict(collections.Counter((r.get('consume'),r.get('argpos')) for r in R)))
    json.dump(R,open(ROOT+'/_r121/_proto3_%x.json'%target,'w'),ensure_ascii=False,indent=1)
