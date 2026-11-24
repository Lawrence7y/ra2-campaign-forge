import w152_core as C
# verify: does 0x5687F0 contain a reference to [type+0x1664]?  compare with 0x5683C0
for e,label in ((0x5683C0,"attach"),(0x5687F0,"detach")):
    inss=C.disas_fn(e)
    hits=[a for a in inss if "0x1664" in a.op_str or "0x1668" in a.op_str]
    hits2=[a for a in inss if "0x1624" in a.op_str or "0x1628" in a.op_str]
    hits3=[a for a in inss if "0x100" in a.op_str]
    print("%s %08X: refs to +0x1664/+0x1668 = %d ; refs to +0x1624/+0x1628 = %d ; refs to +0x100 = %d"%(
        label,e,len(hits),len(hits2),len(hits3)))
    for a in hits:  print("    1664/1668: "+C.fmt(a))
    for a in hits2: print("    1624/1628: "+C.fmt(a))
    print()
