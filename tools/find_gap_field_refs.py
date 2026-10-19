import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\tools")
from re_gap_spysat_deep import read_bytes, md, base, names, secs, disasm_func

text = next(s for s in secs if s['name'] == '.text')
code = text['raw'][:text['vsize']]
tva = text['va']

pos = 0
found = []
while pos < len(code):
    for insn in md.disasm(code[pos:], tva + pos):
        for off in ('0xcd1', '0xcd2', '0xcd3'):
            if off in insn.op_str.lower() and 'esp' not in insn.op_str and 'ebp' not in insn.op_str:
                found.append((insn.address, insn.mnemonic, insn.op_str))
        pos = insn.address - tva + insn.size
    if pos < len(code):
        pos += 1

print(f"Total occurrences of CD1/CD2/CD3: {len(found)}")
for a, m, o in found:
    print(f"  0x{a:08X}: {m:<6} {o}")
