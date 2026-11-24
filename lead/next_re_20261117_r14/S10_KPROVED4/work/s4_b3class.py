"""s4: rigorous ③b classification for all 33 candidates, bounded by FuncMap extents."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from core import Bin, build_rtti, sweep_calls, FuncMap, disasm_range
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE = os.path.dirname(__file__)
R14 = os.path.dirname(os.path.dirname(HERE))
b = Bin(); rtti=build_rtti(b); sw=sweep_calls(b); fm=FuncMap(b,rtti,sw)
rem = json.load(open(os.path.join(R14,'S10_KPROVED3','work','a_rows_remaining.json'),encoding='utf-8'))
EXCLUDE = set("""004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690
004D82B0 004D5690 004DB260 00702D40 00706640 00708C30 004D94B0 004DDDE0""".split())
CAND = [r['entry'] for r in rem if r['entry'] not in EXCLUDE]

ERR_IMMS = {0x80004002, 0x80004005, 0x80070057, 0xffffffff, 0xfffffffe}

def mem_write(y):
    """explicit write to memory (dest operand is mem) - exclude stack-only pushes."""
    if y.mnemonic not in ('mov','inc','dec','add','sub','and','or','xor','stos','movs','rep'):
        return None
    if not y.operands:
        return None
    d = y.operands[0]
    if d.type == X86_OP_MEM:
        return y.op_str
    return None

def classify(ea):
    st,en = fm.extent(ea)
    insns = disasm_range(b, st, en)
    out = {'size':en-st,'n_ins':len(insns),'verdict':'③a','reasons':[]}
    # --- loops with explicit write ---
    loops=[]
    for i,x in enumerate(insns):
        if x.mnemonic.startswith('j') and x.operands and x.operands[0].type==X86_OP_IMM:
            tgt=x.operands[0].imm
            if st <= tgt < x.address:
                body=[y for y in insns if tgt<=y.address<=x.address]
                writes=[]
                for y in body:
                    w=mem_write(y)
                    if w:
                        # exclude pure stack writes [esp/ebp] unless it's the accumulator case
                        if '[esp' not in w and '[ebp' not in w:
                            writes.append((y.address-ea,y.mnemonic,w))
                loops.append({'head':tgt-ea,'back':x.address-ea,'jcc':x.mnemonic,
                              'n':len(body),'nw':len(writes),'writes':writes[:8]})
    out['loops']=loops
    good_loops=[l for l in loops if l['nw']>=1]
    if good_loops:
        out['verdict']='③b④'
        out['reasons'].append(f"loop with explicit non-stack write: {good_loops[0]['writes'][:3]}")
    # --- error codes ---
    eps=[]
    for i,x in enumerate(insns):
        if x.mnemonic in ('cmp','test'):
            for o in x.operands:
                if o.type==X86_OP_IMM:
                    v=o.imm & 0xffffffff
                    if v in ERR_IMMS:
                        # need preceding call within 8 insns and following jcc within 4
                        pre=[y.mnemonic for y in insns[max(0,i-8):i]]
                        post=[y.mnemonic for y in insns[i+1:i+5]]
                        eps.append({'off':x.address-ea,'ins':f'{x.mnemonic} {x.op_str}',
                                    'imm':f'{v:#x}','pre_calls':pre.count('call'),
                                    'post_jcc':sum(1 for m in post if m.startswith('j'))})
    out['eps']=eps
    if not good_loops:
        errgood=[e for e in eps if e['pre_calls']>=1 and e['post_jcc']>=1 and e['imm']!='0xffffffff']
        if errgood:
            out['verdict']='③b②'
            out['reasons'].append(f'error-code pattern: {errgood[0]}')
    # --- jump tables (already known none, but be thorough) ---
    jt=[]
    for x in insns:
        if x.mnemonic=='jmp' and x.operands and x.operands[0].type==X86_OP_MEM:
            op=x.operands[0]
            if op.mem.index:
                jt.append((x.address-ea,x.op_str))
    out['jt']=jt
    if jt and out['verdict']=='③a':
        out['verdict']='③b①'; out['reasons'].append(f'indirect jmp: {jt}')
    # --- memory shape: count vt writes (mov [reg], imm where imm in rdata vt range) ---
    vtw=[]
    for x in insns:
        if x.mnemonic=='mov' and len(x.operands)==2 and x.operands[0].type==X86_OP_MEM and x.operands[1].type==X86_OP_IMM:
            v=x.operands[1].imm
            if b.in_rdata(v) or (0x7e0000<=v<0x812000):
                vtw.append((x.address-ea,x.op_str,f'{v:#x}'))
    out['vt_writes']=vtw[:10]
    return out

results={}
for e in CAND:
    r=classify(int(e,16))
    results[e]=r
    loops=len(r.get('loops',[])); gl=sum(1 for l in r.get('loops',[]) if l['nw']>=1)
    print(f"{e} {r['verdict']:6s} size={r['size']:4d} ins={r['n_ins']:3d} "
          f"loops={loops} goodloops={gl} eps={len(r.get('eps',[]))} jt={len(r.get('jt',[]))} vtw={len(r.get('vt_writes',[]))}")
    if r['verdict']!='③a':
        for reason in r['reasons'][:2]:
            print('      ', reason[:200])

json.dump(results, open(os.path.join(HERE,'..','EVIDENCE','b3_classification.json'),'w',encoding='utf-8'),
          ensure_ascii=False, indent=1)
from collections import Counter
print('verdict counts', Counter(r['verdict'] for r in results.values()))
