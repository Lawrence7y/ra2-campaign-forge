import w152_core as C
a=0x5F5850
print("=== 0x5F5850  entry size=%s ===" % C.fn_size(a))
for ins in C.disas_fn(a):
    print(C.fmt(ins))
print("")
print("=== callers of 0x5F5850 ===")
for entry in C.ENTRIES:
    for ins in C.disas_fn(entry):
        if ins.mnemonic=="call" and ins.operands and ins.operands[0].type==1 and (ins.operands[0].imm&0xffffffff) in (0x5F5850,):
            print("  site %08X in fn %s" % (ins.address, C.fn_label(entry)))
