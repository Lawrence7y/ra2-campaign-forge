# -*- coding: utf-8 -*-
"""④ liveness: for each install site, decide ctor vs dtor (operator delete/refcount release),
trace callers one level, resolve global-write context. ③b due-diligence: enumerate every
call->test/cmp->jcc site + callee return profile across all 9 bodies."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE,"b5_rows.json"),encoding="utf-8") as f: rows=json.load(f)
with open(os.path.join(HERE,"ring_analysis.json"),encoding="utf-8") as f: RA=json.load(f)
with open(os.path.join(HERE,"dump.json"),encoding="utf-8") as f: DUMP=json.load(f)

DEL = {0x7C8B3D, 0x7C93E8}   # operator delete variants

def calls_of(ea, cap):
    out=[]
    for i in R.disasm_body(ea,cap):
        if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM:
            out.append(i.operands[0].imm & 0xFFFFFFFF)
    return out

for r in rows:
    entry=r["entry"]; d=RA[entry]
    print("="*110)
    print(entry, d["name"])
    # ---- ③b due diligence: every call site followed by test/cmp + jcc ----
    ea=int(entry,16); sz=DUMP[entry]["size"]; insns=R.disasm_body(ea,sz)
    idx={i.address:j for j,i in enumerate(insns)}
    findings=[]
    for j,i in enumerate(insns):
        if i.id!=X86_INS_CALL: continue
        cal=None
        if i.operands and i.operands[0].type==X86_OP_IMM:
            cal=i.operands[0].imm & 0xFFFFFFFF
        for k in range(j+1,min(j+6,len(insns))):
            p=insns[k]
            if p.id in (X86_INS_TEST,X86_INS_OR,X86_INS_CMP):
                tk=R.test_kind(p)
                for m in range(k+1,min(k+4,len(insns))):
                    if insns[m].id in R.JCC_IDS:
                        prof=R.callee_return_profile(cal) if cal else None
                        findings.append((("call@%08X"%i.address),
                            ("cal=%08X"%cal) if cal else i.op_str,
                            ("%s"%p.mnemonic), ("%s"%insns[m].mnemonic),
                            ("consts=%s"%([hex(x) for x in sorted(prof["consts"])] if prof else "NA")),
                            ("nret=%s"%(prof["n_rets"] if prof else "NA"))))
                        break
                break
    print("  ③b call->flag->jcc sites (%d):"%len(findings))
    for f in findings: print("    "," | ".join(f))
    # ---- ④ install sites ----
    print("  ④ install sites:")
    if not d["writes"]:
        print("    (none)")
        continue
    for ins in d["writes"]["installs"]:
        f=ins["in_func"]
        if not f:
            # global write: dump surrounding bytes to identify function
            wa=int(ins["write_va"],16)
            print("    write@%s GLOBAL %s : bytes around:"%(ins["write_va"],ins["global"]))
            for i in R.disasm_body(wa-24,48):
                print("       %08X %s %s"%(i.address,i.bytes.hex(),("%s %s"%(i.mnemonic,i.op_str))))
            continue
        ea2,_,sz2=f; ea2=int(ea2,16)
        cs=calls_of(ea2,sz2)
        dels=[hex(c) for c in cs if c in DEL]
        callers=C.find_direct_calls(ea2)
        print("    write@%s func=%08X(sz=%d) del=%s callers=%s"%(
            ins["write_va"],ea2,sz2,dels,["%08X"%x for x in callers[:8]]))
