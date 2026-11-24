import capstone, w152_core as C
X=capstone.x86
reads=[]; writes=[]
for entry in C.ENTRIES:
    for ins in C.disas_fn(entry):
        if not ins.operands: continue
        o=ins.operands[0]
        # absolute memory operand [0x87F924]
        am=False
        for oo in ins.operands:
            if oo.type==X.X86_OP_MEM and oo.mem.base==0 and oo.mem.index==0 and (oo.mem.disp&0xffffffff)==0x87F924:
                am=True
        if not am: continue
        is_write = (o.type==X.X86_OP_MEM and o.mem.base==0 and o.mem.index==0
                    and (o.mem.disp&0xffffffff)==0x87F924 and ins.mnemonic.startswith(("mov","and","or","xor")))
        (writes if is_write else reads).append((ins.address, entry, C.fmt(ins)))
print("refs to 0x87F924: total=%d writes=%d reads=%d"%(len(reads)+len(writes),len(writes),len(reads)))
print("")
print("--- WRITES ---")
for a,e,t in sorted(writes): print("%s   fn=%s"%(t,C.fn_label(e)))
print("")
print("--- sample of last 5 reads ---")
for a,e,t in sorted(reads)[-5:]: print("%s   fn=%s"%(t,C.fn_label(e)))
