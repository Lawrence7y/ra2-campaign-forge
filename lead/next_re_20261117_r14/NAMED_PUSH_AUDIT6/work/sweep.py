"""Single-pass .text sweep: instruction boundaries, direct call sites, immediates."""
import core, pickle

X86_OP_REG, X86_OP_IMM, X86_OP_MEM = 1, 2, 3

o = core.va2off(core.TEXT_LO)
blob = core.DATA[o:core.va2off(core.TEXT_HI)]
md = core.md

insns = 0
call_targets = {}
push_imms = {}
imm32_refs = {}
for insn in md.disasm(blob, core.TEXT_LO):
    insns += 1
    if insn.id == 0:      # skipdata pseudo-insn
        continue
    mn = insn.mnemonic
    if mn == 'call' and insn.operands and insn.operands[0].type == X86_OP_IMM:
        t = insn.operands[0].imm & 0xFFFFFFFF
        call_targets.setdefault(t, []).append(insn.address)
    if mn == 'push' and insn.operands and insn.operands[0].type == X86_OP_IMM:
        push_imms.setdefault(insn.operands[0].imm & 0xFFFFFFFF, []).append(insn.address)
    if insn.operands:
        for op in insn.operands:
            if op.type == X86_OP_MEM:
                if op.mem.disp:
                    imm32_refs.setdefault(op.mem.disp & 0xFFFFFFFF, []).append(insn.address)
            elif op.type == X86_OP_IMM:
                imm32_refs.setdefault(op.imm & 0xFFFFFFFF, []).append(insn.address)

print('insns=%d call_targets=%d push_imms=%d imm32=%d' % (insns, len(call_targets), len(push_imms), len(imm32_refs)))
pickle.dump({'call_targets': call_targets, 'push_imms': push_imms, 'imm32_refs': imm32_refs,
             'insns': insns}, open('sweep.pkl', 'wb'))
