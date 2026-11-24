import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import core as C

C.build_jt()
print('SHA', C.SHA, 'jtables', len(C.TGT_JT))

def dump(entry, name=''):
    lo, hi, addrs, blocks = C.extent(entry)
    print('='*90)
    print('%s entry=%s extent=%d..%d (%d insns, %d blocks)' % (
        name, hex(entry), lo, hi, len(addrs), len(blocks)))
    ins = C.decode_fn(blocks)
    for i in ins:
        print('%08X  %-20s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    return ins

for e, n in [(0x0069DEB0,'NEG-A 0069DEB0'), (0x00704350,'NEG-B 00704350'), (0x004DDDE0,'NEG-C 004DDDE0')]:
    dump(e, n)
