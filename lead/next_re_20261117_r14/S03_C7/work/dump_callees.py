import common as C
# Dump a handful of callee function bodies to identify contracts
targets = [0x431f10, 0x4325a0, 0x43ad00, 0x5b4430]
for t in targets:
    print(f"\n===== callee 0x{t:08X} =====")
    insns = list(C.disasm_n(t, 180))
    for ins in insns[:45]:
        print(f"  +0x{ins.address-t:03X} {ins.bytes.hex():<18} {ins.mnemonic} {ins.op_str}")
