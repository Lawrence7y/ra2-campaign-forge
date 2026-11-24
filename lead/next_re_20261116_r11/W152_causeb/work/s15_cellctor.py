import w152_core as C
for e,stores in ((0x48E740,[0x48E846,0x48E84C,0x48E8D5]),(0x490490,[0x4908AC,0x4908C2,0x490A96]),(0x48EBF0,[0x48EE2A,0x48EE51]),(0x48E740,None)):
    if stores is None: continue
    inss=C.disas_fn(e); idx={a.address:i for i,a in enumerate(inss)}
    print("="*70); print("fn %s  n=%d"%(C.fn_label(e),len(inss)))
    print("--- first 24 instructions ---")
    for j in range(min(24,len(inss))): print("   "+C.fmt(inss[j]))
    for st in stores:
        i=idx.get(st)
        if i is None: print("  %08X not on boundary"%st); continue
        print("--- around store %08X ---"%st)
        for j in range(max(0,i-8),min(len(inss),i+5)):
            print("   "+C.fmt(inss[j])+("  <<== STORE" if inss[j].address==st else ""))
