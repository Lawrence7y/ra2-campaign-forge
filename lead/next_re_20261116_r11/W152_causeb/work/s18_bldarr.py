import w152_core as C
for e in (0x44FE60, 0x452D40, 0x6D9B50, 0x6D9CE0):
    inss=C.disas_fn(e)
    print("="*70); print("fn %s  n=%d"%(C.fn_label(e),len(inss)))
    for ins in inss: print("   "+C.fmt(ins))
    print("")
