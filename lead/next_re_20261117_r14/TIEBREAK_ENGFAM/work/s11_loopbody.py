"""s11: annotated loop body for the 6 sampled rows.

Prints every instruction in the counting loop with a write classification, so
the claim "no non-stack write instruction in the loop body" can be checked by
eye against the printed bytes, not trusted from a counter.
"""
import capstone

import pe

SAMPLE = ["0067FDF0", "006800F0", "00680470", "006807F0", "00680B70", "00680EF0"]
N = 127


WRITE_MNEM = {"mov", "add", "adc", "sub", "sbb", "and", "or", "xor", "inc",
              "dec", "neg", "not", "shl", "shr", "sar", "rol", "ror",
              "xchg", "cmpxchg", "stosd", "stosb", "movsd", "movsb"}


def main():
    p = pe.open_pe()
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    for s in SAMPLE:
        va = int(s, 16)
        insns = list(m.disasm(p.raw(va, N), va))
        back = [i for i in insns if i.mnemonic in ("jl", "jne", "jb")
                and i.operands[0].type == capstone.x86.X86_OP_IMM
                and i.operands[0].imm < i.address]
        lp = max(back, key=lambda i: i.address - i.operands[0].imm)
        tgt = lp.operands[0].imm
        print(f"\n===== {s} (0x{va:08X})  loop 0x{tgt:08X}..0x{lp.address:08X} "
              f"back-edge {lp.mnemonic} -> 0x{tgt:08X}")
        for i in insns:
            if not (tgt <= i.address <= lp.address):
                continue
            note = ""
            if i.mnemonic == "push":
                note = "WRITE-STACK(push)"
            elif i.mnemonic in WRITE_MNEM:
                for k, op in enumerate(i.operands):
                    if op.type != capstone.x86.X86_OP_MEM:
                        continue
                    b = i.reg_name(op.mem.base) if op.mem.base else ""
                    stack = b in ("esp", "ebp")
                    if k == 0:
                        note = "WRITE-STACK" if stack else "**WRITE-NONSTACK**"
                    else:
                        note = "read(mem)"
                    break
            elif i.mnemonic in ("call", "jmp"):
                note = "mem read = fn ptr (no write)"
            else:
                for op in i.operands:
                    if op.type == capstone.x86.X86_OP_MEM:
                        note = "read(mem)"
                        break
            print(f"  +0x{i.address - va:02X}  {i.address:08X}  "
                  f"{' '.join(f'{b:02X}' for b in i.bytes):<20} "
                  f"{i.mnemonic:<7} {i.op_str:<28} {note}")


if __name__ == "__main__":
    main()
