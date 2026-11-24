import capstone, w152_core as C
X=capstone.x86
hits=[]
for entry in C.ENTRIES:
    for ins in C.disas_fn(entry):
        if not ins.mnemonic.startswith("mov") or not ins.operands: continue
        o=ins.operands[0]
        if o.type==X.X86_OP_MEM and o.mem.index==0 and o.mem.disp in (0x13C,0x140) and o.size==4:
            hits.append((ins.address,entry,o.mem.disp,C.fmt(ins)))
print("4-byte stores to [reg+0x13C] or [reg+0x140]: %d"%len(hits))
for a,e,d,t in sorted(hits):
    print("%s   fn=%s  disp=0x%X"%(t,C.fn_label(e),d))
