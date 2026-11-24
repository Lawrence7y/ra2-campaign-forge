"""S3: two censuses that bound "what can take a building off a cell chain".

  A) every `call dword ptr [reg + 0x124]`  (vtable slot 73 = occupancy-state
     switch).  Mode argument decoded by FORWARD-decoding the whole function from
     its Ghidra entry (the method §665-3 says must be used instead of the naive
     backwards heuristic).
  B) every 4-byte store to `[reg + 0xE4]` / `[reg + 0xE8]`  (the two chain-head
     fields of CellClass §651-1).

Run: python s3_slot73.py > ..\\EVIDENCE\\s3_slot73.log 2>&1
"""
import capstone
import w152_core as C

BRANCH_MN = {"jmp", "je", "jne", "jz", "jnz", "ja", "jb", "jae", "jbe", "jg",
             "jge", "jl", "jle", "js", "jns", "jo", "jno", "jp", "jnp", "jc",
             "jnc", "jecxz", "loop", "call"}


def is_call_slot124(insn):
    if insn.mnemonic != "call" or not insn.operands:
        return False
    o = insn.operands[0]
    return (o.type == capstone.x86.X86_OP_MEM and o.mem.disp == 0x124
            and o.mem.index == 0)


def is_chainhead_store(insn):
    if not insn.mnemonic.startswith("mov") or not insn.operands:
        return None
    o = insn.operands[0]
    if o.type != capstone.x86.X86_OP_MEM or o.mem.index != 0:
        return None
    if o.size != 4:
        return None
    if o.mem.disp in (0xE4, 0xE8):
        return o.mem.disp
    return None


def find_mode(inss, idx):
    """Nearest preceding `push imm` / `mov reg,imm ; push reg` in the same
    straight-line window, stopping at any branch/call/ret."""
    j = idx - 1
    steps = 0
    while j >= 0 and steps < 14:
        ins = inss[j]
        if ins.mnemonic in BRANCH_MN or ins.mnemonic == "ret":
            return None, "barrier@%08X" % ins.address
        if ins.mnemonic == "push" and ins.operands and \
                ins.operands[0].type == capstone.x86.X86_OP_IMM:
            return ins.operands[0].imm, "push@%08X" % ins.address
        j -= 1
        steps += 1
    return None, "no-push"


def main():
    slot73 = []
    chain_w = []
    decoded = 0
    for entry in C.ENTRIES:
        inss = C.disas_fn(entry)
        if not inss:
            continue
        decoded += 1
        for i, ins in enumerate(inss):
            if is_call_slot124(ins):
                mode, how = find_mode(inss, i)
                slot73.append((ins.address, entry, mode, how, ins.op_str))
            d = is_chainhead_store(ins)
            if d is not None:
                chain_w.append((ins.address, entry, d, ins.mnemonic, ins.op_str))

    print("functions decoded = %d" % decoded)
    print("")
    print("=== A) slot 73 call sites: %d ===" % len(slot73))
    from collections import Counter, defaultdict
    bymode = Counter()
    for a, e, m, how, ops in slot73:
        bymode[m] += 1
    print("mode histogram:", dict(bymode))
    print("")
    print("addr        function   mode  decode     target-operand")
    for a, e, m, how, ops in sorted(slot73):
        print("%08X  %08X  %-5s %-12s %s" % (a, e, m, how, ops))
    print("")
    print("=== mode -> containing functions ===")
    per = defaultdict(set)
    for a, e, m, how, ops in slot73:
        per[m].add(e)
    for m in sorted(per, key=lambda x: (x is None, x)):
        fs = sorted(per[m])
        print("mode %-5s : %d functions" % (m, len(fs)))
        for f in fs:
            print("             %s" % C.fn_label(f))
    print("")
    print("=== B) 4-byte stores to [reg+0xE4] / [reg+0xE8]: %d ===" % len(chain_w))
    for a, e, d, mn, ops in sorted(chain_w):
        print("%08X  fn=%08X disp=0x%02X  %-8s %s" % (a, e, d, mn, ops))


main()
