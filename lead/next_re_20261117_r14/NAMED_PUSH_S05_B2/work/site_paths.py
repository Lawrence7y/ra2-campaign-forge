# -*- coding: utf-8 -*-
"""对每个 chA 站点打印 call/test/jcc 与两条路径的实际指令（含非栈写标记），便于手判 ③b②。
对 chB 跳表打印每个 case 目标及目标处头几条指令，便于手判 ③b①。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_REG_EBP, X86_REG_ESP
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True
WORK=os.path.dirname(os.path.abspath(__file__))
data={r["entry"]:r for r in json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))}

def va(x): return int(x,16) if isinstance(x,str) else int(x)
def hx(x): return R.hx(va(x))

def is_nonstack_write(ins):
    try:
        _,wr=ins.regs_access()
    except Exception:
        return False
    if len(ins.operands) and ins.operands[0].type==X86_OP_MEM:
        m=ins.operands[0].mem
        # 非栈：base 不是 esp/ebp
        if m.base not in (X86_REG_ESP, X86_REG_EBP):
            return True
    return False

def insn_line(ins):
    tag=" <<W" if is_nonstack_write(ins) else ""
    return "    %08X: %-8s %-30s | %s%s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex(),tag)

def dis_range(start,n=14):
    code=R.read_va(start, n*8)
    out=[]
    for ins in MD.disasm(code,start):
        out.append(insn_line(ins))
        if len(out)>=n: break
    return out

def callee_ret(target):
    if not target or not R.in_text(target): return "?"
    size=R.ATLAS.get(R.hx(target),{}).get("size",120)
    consts=[]; nret=0
    for ins in MD.disasm(R.read_va(target,size),target):
        if ins.id==0: continue
        if ins.mnemonic=="mov" and ins.op_str.startswith("eax, 0x"):
            consts.append(ins.op_str[5:])
        elif ins.mnemonic in ("xor","sub") and ins.op_str=="eax, eax":
            consts.append("0")
        elif ins.mnemonic=="ret":
            nret+=1
    return "rets=%d consts=%s"%(nret,consts[:8])

for e in sys.argv[1:]:
    r=data[e]
    print("="*100)
    print("ENTRY %s %s"%(e,r["hint_name"]))
    for i,s in enumerate(r["chA_sites"]):
        print("  --- A%d call=%s callee=%s [%s] test=%s imm=%s jcc=%s->%s" % (
            i, hx(s["call_addr"]), hx(s["callee"]) if s.get("callee") else "None",
            callee_ret(s.get("callee")), s["test_kind"], s["test_imm"],
            s["jcc_mnemonic"], hx(s["jcc_target"]) if s.get("jcc_target") else "N/A"))
        # taken path
        st=hx(s["jcc_target"]) if s.get("jcc_target") else None
        if st:
            print("    TAKEN @%s:"%st)
            for l in dis_range(va(st),10): print(l)
        ft=va(s["jcc_addr"])+ (6 if False else 0)
        # fallthrough = jcc_addr + size; size unknown here, recompute by disasm at jcc
        jc=va(s["jcc_addr"])
        jins=next(MD.disasm(R.read_va(jc,8),jc),None)
        faddr=jc+(jins.size if jins else 2)
        print("    FALLTHROUGH @%08X:"%faddr)
        for l in dis_range(faddr,10): print(l)
    for b in r["chB"]:
        print("  --- B jmp=%s table=%s bound=%s ncase=%s targets=%d"%(b["jmp_addr"],b["table_va"],b["bound"],b["ncase"],len(b["targets"])))
        for t in b["targets"][:6]:
            print("    case %s -> %s :"%(t["case"],t["target"]))
            for l in dis_range(va(t["target"]),5): print(l)
