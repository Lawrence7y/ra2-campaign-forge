"""S09-KPROVED7 step 3 FINAL: 8 chosen rows + full rigorous evidence.
Baseline computed over ALL 103 A-set rows (features generated on the fly)."""
import sys, io, json, struct, random, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED7\work')
import s09lib as L
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_GRP_JUMP
import capstone.x86 as cx

BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
EV = BASE + r'\S09_KPROVED7\EVIDENCE'

# final chosen 8: (entry, final_name, ③b tier, base class)
CHOSEN = [
 ('004E2580','GaugeClass::slot34','③b②','GaugeClass'),
 ('004E1530','GadgetClass::slot31','③b②','GadgetClass'),
 ('004E1550','GadgetClass::slot27','③b②','GadgetClass'),
 ('0048E5A0','ControlClass::slot31','③b①','ControlClass'),
 ('004F4450','GScreenClass::slot13','③b②','GScreenClass'),
 ('00557AC0','ListClass::slot40','③b②','ListClass'),
 ('004E19F0','GadgetClass::slot22','③b②','GadgetClass'),
 ('00557AE0','ListClass::slot39','③b②','ListClass'),
]

tables = L.rtti_tables(1024)
insns, calls = L.full_e8_sweep()

VT_ALL=[]; DIRECT_ALL=[]; SUMMARY=[]
for entry,fname,tier,base in CHOSEN:
    e=int(entry,16)
    holds=sorted(L.tables_holding(tables,e), key=lambda th:th[0]['vt'])
    hold_rows=[]
    for t,slot in holds:
        col=t['col']; td=L.u32(col+0xC); nm=L.cstr(td+8) if td else None
        hold_rows.append(dict(vt=hex(t['vt']),slot=slot,col=hex(col),td=hex(td) if td else None,
                              td8=nm,nslots=len(t['slots']),col_minus4=hex(L.u32(t['vt']-4))))
        VT_ALL.append(dict(entry=entry,final_name=fname,vt=hex(t['vt']),slot=slot,col=hex(col),
                           td=hex(td) if td else None,td8=nm,col_minus4=hex(L.u32(t['vt']-4))))
    lo,hi,ordered,byaddr=L.cfg_extent(e,cap=8000)
    lo2,hi2,sites=L.direct_sites_for(e,calls)
    good=[s for s in sites if s['ok']]
    for s in good:
        DIRECT_ALL.append(dict(entry=entry,site=hex(s['site']),rel=s['rel'],target=hex(e),
                               body_lo=hex(lo),body_hi=hex(hi),in_body=s['in_body'],
                               selfloop=s['selfloop'],ok=s['ok'],boundary=True,
                               formula='site+5+rel32==entry'))
    lines=[]
    for ins in sorted(ordered,key=lambda i:i.address):
        lines.append('+0x%04X  %-10s %s %s'%(ins.address-e,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    open(EV+r'\DISASM_%s.txt'%entry,'w',encoding='utf-8').write(
        'entry=%s final_name=%s tier=%s base=%s\n'%(entry,fname,tier,base)+
        'CFG extent(self-written,no atlas):[0x%X,0x%X) size=%d nins=%d\n'%(lo,hi,hi-lo,len(ordered))+
        'holding tables=%d\n'%len(holds)+'\n'.join(
          '  %s slot%d COL=%s TD=%s TD+8=%s nslots=%d'%(h['vt'],h['slot'],h['col'],h['td'],h['td8'],h['nslots']) for h in hold_rows)+
        '\n\ndirect sites(E8@boundary,site+5+rel32==entry,outside body,non-self):%d\n'%len(good)+
        '\n'.join('  site=%s rel=%d'%(hex(s['site']),s['rel']) for s in good)+
        '\n\n--- disassembly(entry-relative) ---\n'+'\n'.join(lines))
    SUMMARY.append(dict(entry=entry,final_name=fname,tier=tier,base=base,n_holds=len(holds),
                        n_direct=len(good),extent=[hex(lo),hex(hi)],nins=len(ordered),
                        holds=hold_rows,direct=[hex(s['site']) for s in good]))

def wtsv(path,rows,cols):
    with open(path,'w',encoding='utf-8') as f:
        f.write('\t'.join(cols)+'\n')
        for r in rows: f.write('\t'.join(str(r.get(c,'')) for c in cols)+'\n')
wtsv(EV+r'\VTABLES_ALL8.tsv',VT_ALL,['entry','final_name','vt','slot','col','td','td8','col_minus4'])
wtsv(EV+r'\DIRECT_SITES_8.tsv',DIRECT_ALL,['entry','site','rel','target','body_lo','body_hi','in_body','selfloop','ok','boundary','formula'])
json.dump(SUMMARY,open(OUT+r'\rings8.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

# ---------- ③b base rate over ALL 103 A-set rows ----------
JCCS={'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno'}
def feat_for(entry):
    e=int(entry,16)
    lo,hi,ordered,byaddr=L.cfg_extent(e,cap=6000)
    rset=set(byaddr)
    jt=[];loops=[];sent=[];jccT=set();calls2=set();writes=0
    for ins in ordered:
        a=ins.address;mn=ins.mnemonic;ops=ins.operands
        if mn=='jmp' and ops and ops[0].type==X86_OP_MEM:
            m=ops[0].mem
            if m.index!=0 and m.scale in (2,4,8): jt.append(1)
        if mn in ('cmp','test'):
            for op in ops:
                if op.type==X86_OP_IMM and (int(op.imm)&0xffffffff)==0xffffffff: sent.append(1)
        if mn in JCCS and ops and ops[0].type==X86_OP_IMM:
            t=int(ops[0].imm)&0xffffffff
            if t in rset: jccT.add(t)
        if mn=='call' and ops and ops[0].type==X86_OP_IMM: calls2.add(int(ops[0].imm)&0xffffffff)
        if ops and ops[0].type==X86_OP_MEM and mn in ('mov','add','sub','inc','dec','and','or','xor','movzx','movsx'):
            m=ops[0].mem
            if not (m.base in (cx.X86_REG_ESP,cx.X86_REG_EBP) and m.index==0): writes+=1
        if mn in ('jmp',) or mn in JCCS:
            if ops and ops[0].type==X86_OP_IMM:
                t=int(ops[0].imm)&0xffffffff
                if lo<=t<=a: loops.append(1)
    return dict(jt=len(jt),loops=len(loops),sent=len(sent),gates=len(jccT),calls=len(calls2),writes=writes,
                txt=' '.join('%s %s'%(i.mnemonic,i.op_str) for i in ordered))

rows=list(csv.DictReader(open(BASE+r'\SURVEY_RING24\EVIDENCE\classification.tsv',encoding='utf-8'),delimiter='\t'))
Apop=[r for r in rows if r['subsystem']=='S09' and r['has2_rtti']=='1' and r['has4_strict']=='1']
assert len(Apop)==103
featmap={r['entry']:feat_for(r['entry']) for r in Apop}
def strict(f):
    return (f['jt']>0 or (f['loops']>0 and f['writes']>0) or
            (f['sent']>0 and 'ret' in f['txt']) or f['writes']>=10 or f['gates']>=3)
def loose(f):
    if strict(f): return True
    return ('xor eax, eax' in f['txt'] and ('mov eax, 1' in f['txt'] or 'mov al, 1' in f['txt'])) or \
           ('sete al' in f['txt'] or 'setne al' in f['txt']) or f['gates']>=1

rng=random.Random(20261119); N=8; T=2000
entries=[r['entry'] for r in Apop]
sh=sl=0
for _ in range(T):
    s=rng.sample(entries,N)
    sh+=sum(1 for e in s if strict(featmap[e]))
    sl+=sum(1 for e in s if loose(featmap[e]))
base=dict(seed=20261119,draws=T,N=N,population='S09 A set (has2_rtti & has4_strict) = 103 rows',
          strict_mean=sh/(T*N),loose_mean=sl/(T*N),strict_hits=sh,loose_hits=sl,total=T*N,
          strict_operationalization='jump-table OR loop-with-nonstack-write OR falsifiable error code(cmp -1 & ret) OR memory-shape(>=10 nonstack writes) OR >=3 distinct jcc gate targets',
          loose_operationalization='strict OR falsifiable boolean return(0/1 pair) OR setcc return OR >=1 gate')
json.dump(base,open(OUT+r'\baseline_3b.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('=== FINAL 8 ===')
for s2 in SUMMARY: print(s2['entry'],s2['final_name'],s2['tier'],'holds=%d direct=%d ins=%d'%(s2['n_holds'],s2['n_direct'],s2['nins']))
print('\n=== ③b BASE RATE (over all 103 A rows) ===')
print('strict mean=%.4f (%d/%d)'%(base['strict_mean'],sh,T*N))
print('loose  mean=%.4f (%d/%d)'%(base['loose_mean'],sl,T*N))
