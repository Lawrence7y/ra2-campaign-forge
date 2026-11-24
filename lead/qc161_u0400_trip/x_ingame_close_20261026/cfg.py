"""CFG closure disassembler for gamemd.exe (branch-graph closure; never truncate at first ret)."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\x_ingame_close_20261026')
from common import IMG
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
TEXT_START = 0x401000
TEXT_END = 0x401000 + 0x3DF38D

def ins_at(va):
    b = IMG.read(va, 16)
    if b is None:
        return None
    for i in md.disasm(b, va):
        return i
    return None

def in_text(va):
    return TEXT_START <= va < TEXT_END

def succ(ins, nxt):
    """Return (terminates_block, [(kind,target_or_None), ...])."""
    m = ins.mnemonic
    if m in ('ret', 'retn', 'retf', 'iret', 'iretd'):
        return True, [('ret', None)]
    if m == 'jmp':
        if ins.operands and ins.operands[0].type == 4:
            return True, [('jmp', int(ins.operands[0].imm))]
        return True, [('ijmp', None)]
    if m.startswith('j'):  # conditional branch (jmp already handled)
        outs = [('fall', nxt)]
        if ins.operands and ins.operands[0].type == 4:
            outs.append(('taken', int(ins.operands[0].imm)))
        return True, outs
    if m == 'call':
        return False, []  # linear continues after call
    if m == 'leave':
        return False, []
    return False, []

def closure(entry, max_blocks=20000):
    blocks = {}
    calls = set()
    ijmps = set()
    rets = set()
    stack = [entry]
    while stack:
        a = stack.pop()
        if a in blocks or not in_text(a):
            continue
        ins_list = []
        va = a
        linear_next = None
        while True:
            ins = ins_at(va)
            if ins is None:
                break
            ins_list.append(ins)
            nxt = va + ins.size
            # capture call targets
            if ins.mnemonic == 'call':
                if ins.operands and ins.operands[0].type == 4:
                    calls.add((va, int(ins.operands[0].imm)))
                else:
                    calls.add((va, None))
            term, outs = succ(ins, nxt)
            if not term:
                va = nxt
                if len(ins_list) > 5000:
                    break
                continue
            if 'ret' in [k for k, _ in outs]:
                rets.add(va)
            for kind, t in outs:
                if kind == 'ijmp':
                    ijmps.add((va, ins.op_str))
                elif kind in ('jmp', 'taken', 'fall') and t is not None:
                    if in_text(t) and t not in blocks:
                        stack.append(t)
            break
        blocks[a] = ins_list
        if len(blocks) >= max_blocks:
            break
    return blocks, calls, ijmps, rets

def fmt(ins):
    return f"0x{ins.address:08X}: {ins.bytes.hex().upper():<18} {ins.mnemonic} {ins.op_str}".rstrip()

def dump(blocks, calls, ijmps, rets, f):
    for s in sorted(k for k in blocks if blocks[k]):
        f.write(f"--- block @ 0x{s:08X} ---\n")
        for ins in blocks[s]:
            f.write(fmt(ins) + "\n")
    f.write("\n== calls (site -> target) ==\n")
    for site, t in sorted(calls):
        f.write(f"0x{site:08X} -> {'0x%08X'%t if t is not None else 'IND'}\n")
    f.write("\n== indirect jumps ==\n")
    for site, ops in sorted(ijmps):
        f.write(f"0x{site:08X} {ops}\n")
    f.write("\n== ret sites ==\n")
    for r in sorted(rets):
        f.write(f"0x{r:08X}\n")

if __name__ == '__main__':
    entry = int(sys.argv[1], 16)
    out = sys.argv[2]
    blocks, calls, ijmps, rets = closure(entry)
    with open(out, 'w') as f:
        dump(blocks, calls, ijmps, rets, f)
    print(f"entry 0x{entry:08X}: {sum(1 for v in blocks.values() if v)} blocks, "
          f"{sum(len(v) for v in blocks.values() if v)} insns, {len(calls)} calls")
