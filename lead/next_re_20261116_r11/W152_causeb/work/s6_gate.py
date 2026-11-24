import w152_core as C
print("=== jump table at 0x43FB0C (4 dwords) ===")
for i in range(4):
    v=C.u32(0x43FB0C+4*i)
    print("  mode %d -> %08X  size=%s" % (i, v, C.fn_size(v) if v in C.FUNC else "NOT-ENTRY"))
print("")
for a,label in ((0x006F4A70,"gate checked by BOTH Building(0x43F180) and mobile(0x4D3780) dispatchers"),):
    print("=== %s  entry=%08X size=%s ===" % (label,a,C.fn_size(a)))
    for ins in C.disas_fn(a):
        print(C.fmt(ins))
