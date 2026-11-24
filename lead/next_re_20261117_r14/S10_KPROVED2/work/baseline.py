"""③b base rate: strict/loose two tiers, seed 20261119, 2000 trials,
random 8 rows within S10 subsystem (pool = 398 S10 rows in classification.tsv).
Per D-42 条4: baseline = same-subsystem random same number of rows.
"""
import random, re
from re_core import PE
from func_analyze import disasm_range

pe=PE()

def load_s10_all():
    rows=[]
    with open(r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv', encoding='utf-8') as f:
        hdr=f.readline().rstrip('\n').split('\t'); ii={h:i for i,h in enumerate(hdr)}
        for line in f:
            c=line.rstrip('\n').split('\t')
            if c[ii['subsystem']]=='S10':
                rows.append({h:c[ii[h]] for h in hdr})
    return rows

s10=load_s10_all()
print('S10 pool rows:',len(s10))

# mem operand patterns (any size) -- capstone op_str excludes the mnemonic
RE_MREAD=re.compile(r'^\w+,\s*(?:byte|word|dword|qword) ptr \[')
RE_MWRITE=re.compile(r'^(?:byte|word|dword|qword) ptr \[')
RE_JTINDEX=re.compile(r'\[\s*\w+\*4\s*\+')

def detect_3b(entry, ext_hi):
    insns=disasm_range(pe,entry,ext_hi)
    ev=[]
    n_jcc=0; backward=[]; jt=[]; errcode=[]; vtwrites=[]; fieldimm=0
    for ins in insns:
        off=ins.address-entry; m=ins.mnemonic; ops=ins.op_str
        if m.startswith('j') and m!='jmp':
            n_jcc+=1
            mm=re.search(r'0x([0-9a-fA-F]+)',ops)
            if mm:
                t=int(mm.group(1),16)
                if entry<=t<=ins.address:
                    backward.append((off,m,ops,ins.address))
        if m=='jmp' and RE_JTINDEX.search(ops):
            mm=re.search(r'0x([0-9a-fA-F]+)',ops)
            if mm:
                tbl=int(mm.group(1),16)
                targets=[]
                for i in range(16):
                    v=pe.u32va(tbl+4*i)
                    if v is None or pe.sec_of_va(v)!='.text':
                        break
                    targets.append(v)
                nuniq=len(set(targets))
                if nuniq>=2:
                    jt.append((off,ops,nuniq))
                    ev.append(f'jumptable @{off:#x} targets={nuniq}')
        if re.search(r'0x8000[0-9a-fA-F]{4}',ops) or (m in ('mov','or','push','cmp') and re.search(r'\b-1\b',ops)):
            errcode.append((off,m,ops))
        mm=re.match(r'dword ptr \[\w+[^\]]*\],\s*(0x[0-9a-fA-F]+)',ops)
        if mm and m=='mov':
            imm=int(mm.group(1),16)
            if 0x7e0000<=imm<=0x810000:
                vtwrites.append((off,ops))
            else:
                fieldimm+=1
    # complete loop detection: backward jump whose preceding 45 insns contain
    # mem read + mem write + index advance (any size)
    strict=False
    for off,m,ops,va in backward:
        for i,ins in enumerate(insns):
            if ins.address==va:
                body=insns[max(0,i-45):i]
                has_read=any(x.mnemonic=='mov' and RE_MREAD.search(x.op_str) for x in body)
                has_write=any(x.mnemonic=='mov' and RE_MWRITE.search(x.op_str) for x in body)
                has_adv=any(x.mnemonic in ('inc','dec','add','sub') for x in body)
                if has_read and has_write and has_adv:
                    strict=True
                    ev.append(f'completeloop @{off:#x}')
                break
    if any(c>=3 for _,_,c in jt):
        strict=True
    if len(vtwrites)>=2 or fieldimm>=10:
        strict=True
    if errcode:
        strict=True
    loose = bool(jt) or bool(backward) or n_jcc>=3 or bool(errcode)
    return strict,loose,ev

cache={}
for r in s10:
    e=int(r['entry'],16); hi=int(r['ext_hi'],16)
    if hi-e>20000: hi=e+4000  # guard bogus ext_hi (tiny stubs)
    cache[(e,hi)]=detect_3b(e,hi)

strict_pool=[k for k,v in cache.items() if v[0]]
loose_pool=[k for k,v in cache.items() if v[1]]
print(f'strict③b+ rows: {len(strict_pool)}/{len(cache)} = {len(strict_pool)/len(cache)*100:.2f}%')
print(f'loose③b+ rows: {len(loose_pool)}/{len(cache)} = {len(loose_pool)/len(cache)*100:.2f}%')

random.seed(20261119)
pool=list(cache.keys())
N=8; T=2000
sc_all=[]; lc_all=[]
for _ in range(T):
    sample=random.sample(pool,N)
    sc_all.append(sum(1 for k in sample if cache[k][0]))
    lc_all.append(sum(1 for k in sample if cache[k][1]))
ms=sum(sc_all)/T; ml=sum(lc_all)/T
print(f'BASE strict: mean={ms:.4f} rows/8 ({ms/N*100:.2f}%), E-rate={len(strict_pool)/len(cache)*100:.2f}%')
print(f'BASE loose : mean={ml:.4f} rows/8 ({ml/N*100:.2f}%), E-rate={len(loose_pool)/len(cache)*100:.2f}%')
rate_s=len(strict_pool)/len(cache); rate_l=len(loose_pool)/len(cache)
print(f'K identity (NOT validation): strict {N}x{rate_s:.4f}={N*rate_s:.4f}; measured mean over T trials={ms:.4f}')
print(f'K identity (NOT validation): loose  {N}x{rate_l:.4f}={N*rate_l:.4f}; measured mean over T trials={ml:.4f}')
# note: without-replacement sampling mean differs slightly from N x pool rate; both reported

my8=[0x004D74E0,0x004D7D50,0x00702D40,0x00706640,0x00708C30,0x004D85D0,0x004DB3C0,0x004D5690]
print('--- my 8 ---')
for e in my8:
    keys=[k for k in cache if k[0]==e]
    if keys:
        s,l,ev=cache[keys[0]]
        print(f'{e:08X} strict={s} loose={l} ev={ev[:4]}')
