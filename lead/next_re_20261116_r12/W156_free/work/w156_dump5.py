"""Quick capstone dump of the 5 priority functions + constructors/dispatchers."""
import w156_core as C

targets = [0x44FE60, 0x452D40, 0x44FEC0, 0x452DC0, 0x4533A0,
           0x43B740, 0x43F180, 0x4D3780, 0x71BFB0]
for e in targets:
    inss = C.disas_fn(e, cap=8000)
    print("="*72)
    print("FN %s  n_insn=%d" % (C.fn_label(e), len(inss)))
    print("="*72)
    for ins in inss:
        print("  " + C.fmt(ins))
    print("")
