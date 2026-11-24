import w152_core as C
for e in (0x47D210, 0x43B740):
    inss=C.disas_fn(e)
    print("="*70); print("fn %s  n=%d"%(C.fn_label(e),len(inss)))
    show=inss if len(inss)<200 else inss[:60]
    for ins in show: print("   "+C.fmt(ins))
    if len(inss)>=200: print("   ... (truncated)")
