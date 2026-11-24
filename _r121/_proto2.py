import sys, json, collections, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r119')
from _pe119 import PE_, BUF
import capstone
T = PE_.sec_by_name('.text')
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); MD.detail=False; MD.skipdata=True
IAT = json.load(open('/home/t628/projects/ra2-campaign-forge/_r119/iat_names.json'))
IATV = {int(k,16): v[1] for k,v in IAT.items()}
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
WRITE_MN={'mov','lea','xor','pop','add','sub','and','or','shl','shr','imul','movzx','movsx','inc','dec','xchg'}
def trace(va_site, reg, back=0x600):
    lo=max(T['va'],va_site-back); o=PE_.va2off(lo); e=PE_.va2off(va_site)
    last=None
    for (a,sz,mn,ops) in MD.disasm_lite(BUF[o:e],lo):
        m=re.match(r'^%s,'%reg, ops)
        if m and mn in WRITE_MN:
            last=(hex(a),mn,ops)
    return last
for target in (0x7f7c80,0x7f7c90,0x817bc0,0x818858,0x820270,0x87da00):
    S=sites(target); cnt=collections.Counter(); ex={}
    for s in S:
        o=PE_.va2off(s); seq=list(MD.disasm_lite(BUF[o:o+64],s))
        callee=None
        for (a,sz,mn,ops) in seq[1:9]:
            if mn=='call':
                if ops.startswith('dword ptr [0x'): callee=('IAT',hex(a),int(ops[len('dword ptr ['):-1],16))
                elif ops.startswith('dword ptr ['): callee=('IND',hex(a),ops[len('dword ptr ['):-1].split('+')[0].strip())
                else: callee=('REL',hex(a),ops)
                break
        if callee is None: cnt['no-call']+=1; continue
        if callee[0]=='IAT': cnt['IAT:'+IATV.get(callee[2],'?')]+=1
        elif callee[0]=='REL': cnt['REL:'+callee[2]]+=1
        else:
            tr=trace(s,callee[2])
            if tr is None: cnt['IND[%s]<-UNRESOLVED'%callee[2]]+=1
            else:
                m=re.fullmatch(r'%s, dword ptr \[(0x[0-9a-f]+)\]'%callee[2], tr[2])
                if m: cnt['IND[%s]<IAT:%s'%(callee[2],IATV.get(int(m.group(1),16),'?'))]+=1
                else:
                    cnt['IND[%s]<%s'%(callee[2],tr[1])]+=1
                    ex.setdefault('IND[%s]<%s'%(callee[2],tr[1]),[]).append((hex(s),tr))
    print('===',hex(target),'sites',len(S))
    for k,v in cnt.most_common(): print('   %-34s %d'%(k,v))
    for k,v in list(ex.items())[:3]: print('     ex',k,v[:2])
