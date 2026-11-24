import sys, json
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import core as C

C.build_jt()
print('SHA', C.SHA)
print('text', hex(C.TVA), hex(C.TLEN), 'insns', C.NINSN, 'jtables', len(C.TGT_JT))

def dump(entry, name=''):
    lo, hi, addrs, blocks = C.extent(entry)
    print('='*90)
    print('%s entry=%s extent=%d..%d (%d insns, %d blocks, %d bytes)' % (
        name, hex(entry), lo, hi, len(addrs), len(blocks), hi-lo))
    ins = C.decode_fn(blocks)
    for i in ins:
        s = '%08X  %-22s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)
        print(s)
    return lo, hi, addrs, blocks, ins

for e, n in [(0x0053AF40,'POS 0053AF40'), ]:
    dump(e, n)
