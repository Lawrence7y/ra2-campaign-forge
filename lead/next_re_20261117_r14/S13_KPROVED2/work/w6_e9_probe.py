"""Investigate E9 tail-jmp sites hitting 0046AFD0 / 0046AFF0 and the target bodies."""
from s13lib import MD, DATA, va2off, TEXT_VA, TEXT_VS, disasm_range

# find E9 sites
raw = DATA(va2off(TEXT_VA), TEXT_VS)
targets = {0x46AFD0, 0x46AFF0}
for ins in MD.disasm(raw, TEXT_VA):
    if ins.mnemonic == 'jmp' and ins.op_str.startswith('0x'):
        t = int(ins.op_str, 16)
        if t in targets:
            o = va2off(ins.address)
            b0 = DATA(o,1)[0]
            if b0 == 0xE9:
                print('E9 site', hex(ins.address), '->', hex(t))
                # show +/- 8 insns context
                ctx = disasm_range(ins.address-24, ins.address+8)
                for z in ctx:
                    print('   ', hex(z.address), z.mnemonic, z.op_str)

# bodies of targets
for e in sorted(targets):
    print('=== body', hex(e), '===')
    body = disasm_range(e, e+0x60)
    for z in body[:24]:
        print('  ', hex(z.address), z.bytes.hex(), z.mnemonic, z.op_str)
