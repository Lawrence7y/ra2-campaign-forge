"""s5: check D-42 rule#1 guard chains + memory shape + extent sanity for all 33."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from core import Bin, build_rtti, sweep_calls, FuncMap, disasm_range
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE=os.path.dirname(__file__); R14=os.path.dirname(os.path.dirname(HERE))
b=Bin(); rtti=build_rtti(b); sw=sweep_calls(b); fm=FuncMap(b,rtti,sw)
rem=json.load(open(os.path.join(R14,'S10_KPROVED3','work','a_rows_remaining.json'),encoding='utf-8'))
EXCLUDE=set("""004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690
004D82B0 004D5690 004DB260 00702D40 00706640 00708C30 004D94B0 004DDDE0""".split())
CAND=[r['entry'] for r in rem if r['entry'] not in EXCLUDE]

def action_sig(insns, start_idx, window=10):
    """Distinct action signature of a branch target: the calls/returns in next N insns."""
    sig=[]
    for y in insns[start_idx:start_idx+window]:
        if y.mnemonic=='call':
            sig.append('call:'+(y.op_str[:24]))
        elif y.mnemonic=='ret':
            sig.append('ret')
    return tuple(sig) if sig else ('none',)

out={}
for e in CAND:
    ea=int(e,16); st,en=fm.extent(ea); insns=disasm_range(b,st,en)
    idx={x.address:i for i,x in enumerate(insns)}
    # field immediate writes (memory shape)
    fw=[]
    for x in insns:
        if x.mnemonic=='mov' and len(x.operands)==2 and x.operands[0].type==X86_OP_MEM and x.operands[1].type==X86_OP_IMM:
            fw.append((x.address-ea,x.op_str))
    # guard chain: count jcc, each with distinct action sig + guard predicate
    jccs=[]
    for i,x in enumerate(insns):
        if x.mnemonic.startswith('j') and x.mnemonic not in ('jmp',) and x.operands and x.operands[0].type==X86_OP_IMM:
            tgt=x.operands[0].imm
            if tgt in idx:
                sig=action_sig(insns,idx[tgt])
                jccs.append((x.address-ea,x.mnemonic,tgt-ea,sig))
            else:
                jccs.append((x.address-ea,x.mnemonic,tgt-ea,('OUT',)))
    # distinct non-none action sigs
    acts=set(s for (_,_,_,s) in jccs if s!=('none',))
    out[e]={'size':en-st,'n_ins':len(insns),'n_field_writes':len(fw),'field_writes':fw[:12],
            'n_jcc':len(jccs),'n_distinct_actions':len(acts),'actions':[list(a) for a in list(acts)[:12]]}
    print(f"{e} size={en-st:4d} fw={len(fw):3d} jcc={len(jccs):3d} distinct_acts={len(acts):2d}")
    if len(fw)>=10 or len(acts)>=3:
        print('   fw sample', fw[:4])
        print('   acts sample', [list(a) for a in list(acts)[:4]])

json.dump(out,open(os.path.join(HERE,'..','EVIDENCE','guard_shape_check.json'),'w',encoding='utf-8'),
          ensure_ascii=False,indent=1)
