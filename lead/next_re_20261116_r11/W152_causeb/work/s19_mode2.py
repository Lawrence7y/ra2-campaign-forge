import w152_core as C
inss=C.disas_fn(0x43F180); idx={a.address:i for i,a in enumerate(inss)}
print("=== mode2 branch from 0x43F9A6: does it call 0x5683C0 / 0x5687F0 ? ===")
i=idx.get(0x43F9A6)
print("insn index=%s of %d"%(i,len(inss)))
if i is not None:
    seg=inss[i:i+40]
    for ins in seg: print("   "+C.fmt(ins))
    # scan whole fn for wrapper calls
print("")
calls=[(a.address,a.mnemonic,a.op_str) for a in inss if a.mnemonic=='call' and '0x56' in a.op_str]
print("all calls in 0x43F180 targeting 0x56xxxx: %s"%calls)
