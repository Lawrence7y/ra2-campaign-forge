from re_core import PE
from func_analyze import disasm_range, load_a_rows
pe=PE()
rows={int(r['entry'],16):r for r in load_a_rows()}
LOOPS={
 0x004D7170:[(0xeb,0x13c)],
 0x004D9960:[(0x1ef,0x235),(0x213,0x229),(0x243,0x289),(0x267,0x27d)],
 0x004DB690:[(0x4c,0x6f),(0x9c,0xbf)],
 0x004DF040:[(0x1e,0x75)],
 0x004D7D50:[(0x2a4,0x2ba)],
}
for e,ranges in LOOPS.items():
    hi=int(rows[e]['ext_hi'],16)
    insns=disasm_range(pe,e,hi)
    print(f'===== {e:08X} {rows[e]["name"]}')
    for (a,b) in ranges:
        print(f'  --- loop body +{a:#x}..+{b:#x} ---')
        for ins in insns:
            off=ins.address-e
            if a<=off<=b:
                print(f'    {ins.address:08X} +{off:04x}: {ins.mnemonic} {ins.op_str}')
    print()
