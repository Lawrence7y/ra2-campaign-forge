#!/usr/bin/env python3
"""S09 static-pool ③b detector + random baseline.
③b operational patterns (mirror the 8-row manual analysis):
  P1 jump table : any `jmp dword ptr [reg*4 + disp]`
  P2 error code : `cmp X,-1` followed within 4 insns by a jcc (falsifiable sentinel)
  P4 loop       : a backward branch whose body has >=1 cmp/test (judge) + >=1 memory write
                  + >=1 pointer/index advance (add/sub/inc/dec) => read/judge/write/advance/bound
④ = has4_strict==1.
Then: S09 static pool rows; K = #{④ AND ③b}; random baseline = mean over 2000 trials
of sampling 8 rows (seed 20261119, without replacement) and counting ④∧③b hits.
Read-only on target; writes EVIDENCE/baseline_*.json
"""
import csv, struct, json, random, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
CLASS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED'
EV=os.path.join(BASE,'EVIDENCE')
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase; D=pe.__data__
SEC=[(s.VirtualAddress,max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData) for s in pe.sections]
def va2off(va):
    r=va-IB
    for v,sz,p in SEC:
        if v<=r<v+sz: return p+(r-v)
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

rows=[r for r in csv.DictReader(open(CLASS,encoding='utf-8'),delimiter='\t') if r['subsystem']=='S09']
print('S09 static pool rows:',len(rows))

def analyze(r):
    lo=int(r['ext_lo'],16); hi=int(r['ext_hi'],16)
    if hi<=lo or hi-lo>20000: hi=lo+ (int(r['atlas_size']) or 64)
    o=va2off(lo)
    if o is None: return (False,False,False,False)
    ins=list(md.disasm(D[o:o+(hi-lo)],lo))
    addrs=[i.address for i in ins]; aset=set(addrs); idx={a:i for i,a in enumerate(addrs)}
    p1=False;p2=False;p4=False
    for k,i in enumerate(ins):
        # P1 jump table
        if i.mnemonic=='jmp':
            for op in i.operands:
                if op.type==X86_OP_MEM and op.mem.scale==4:
                    p1=True
        # P2 error/sentinel code: cmp ...,-1 then jcc within 4
        if i.mnemonic=='cmp' and any(op.type==X86_OP_IMM and op.imm==-1 for op in i.operands):
            for j in range(k+1,min(k+5,len(ins))):
                if ins[j].mnemonic.startswith('j'):
                    p2=True;break
        # P4 loop: backward branch with judge+write+advance in body
        if i.mnemonic.startswith('j') and i.operands and i.operands[0].type==X86_OP_IMM:
            t=i.operands[0].imm
            if t in idx and t<i.address:
                body=ins[idx[t]:k+1]
                judge=any(x.mnemonic.startswith(('cmp','test')) for x in body)
                write=any(x.mnemonic in ('mov','call','stosd','rep') and x.operands and
                          x.operands[0].type==X86_OP_MEM for x in body)
                advance=any(x.mnemonic in ('add','sub','inc','dec','lea') for x in body)
                if judge and write and advance:
                    p4=True
    return (p1,p2,p4, p1 or p2 or p4)

flags={}
k4_3b=0
for r in rows:
    f=analyze(r)
    has4=(r['has4_strict']=='1')
    flags[r['entry']]={'p1':f[0],'p2':f[1],'p4':f[2],'b3':f[3],'b4':has4,'hit':has4 and f[3]}
    if flags[r['entry']]['hit']: k4_3b+=1

N=len(rows)
p=k4_3b/N
analytic=8*p
# Monte Carlo: seed 20261119, 2000 trials, sample 8 without replacement
rng=random.Random(20261119)
hits=[]
entries=[r['entry'] for r in rows]
for _ in range(2000):
    smp=rng.sample(entries,8)
    hits.append(sum(1 for e in smp if flags[e]['hit']))
emp=sum(hits)/len(hits)
dist={h:hits.count(h) for h in sorted(set(hits))}

out={
 'pool':'classification.tsv subsystem=S09 (grade=[静态推断] ∩ atlas)',
 'N':N,
 'has4_count':sum(1 for r in rows if r['has4_strict']=='1'),
 'b3_count':sum(1 for v in flags.values() if v['b3']),
 'K_4and3b':k4_3b,
 'p_4and3b':p,
 'analytic_expected_hits_in_8':analytic,
 'seed':20261119,'trials':2000,'sample_n':8,
 'empirical_mean_hits':emp,
 'distribution':dist,
 'detector':{'P1':'jmp dword ptr [reg*4+disp]','P2':'cmp X,-1 then jcc within 4','P4':'backward branch w/ judge(cmp/test)+write(mem)+advance(add/sub/inc/dec/lea) in body'},
 'CAVEAT':'③b detector is an operational byte-pattern proxy; per-row ③b for the 8 chosen rows was confirmed by manual full-disasm reading, not by this proxy.',
}
json.dump(out,open(os.path.join(EV,'baseline_4and3b.json'),'w'),indent=2)
# per-row flag dump
with open(os.path.join(EV,'pool_3b_flags.tsv'),'w',encoding='utf-8') as fp:
    fp.write('entry\thas4\tp1_jt\tp2_err\tp4_loop\tb3\thit\n')
    for r in rows:
        v=flags[r['entry']]
        fp.write('%s\t%d\t%d\t%d\t%d\t%d\t%d\n'%(r['entry'],v['b4'],v['p1'],v['p2'],v['p4'],v['b3'],v['hit']))
print('has4=',out['has4_count'],'b3=',out['b3_count'],'K(4&3b)=',k4_3b,'p=',round(p,4))
print('analytic 8p=',round(analytic,4),'empirical mean=',round(emp,4))
print('dist',dist)
