import w152_core as C
inss=C.disas_fn(0x565C10)
idx={a.address:i for i,a in enumerate(inss)}
print("fn 0x565C10 instructions=%d size=%s" % (len(inss), C.fn_size(0x565C10)))
for st in (0x565E61,0x565E6D,0x566673,0x56667F):
    i=idx.get(st)
    if i is None:
        print("store %08X not on boundary"%st); continue
    print("")
    print("---- store %08X (insn #%d) ----"%(st,i))
    for j in range(max(0,i-16), min(len(inss), i+8)):
        print("   "+C.fmt(inss[j])+("   <<== STORE" if inss[j].address==st else ""))
