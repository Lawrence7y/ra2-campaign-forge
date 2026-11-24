"""s3b: re-dump disassembly for ALL 33 candidates using correct function extents (FuncMap)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from core import Bin, build_rtti, sweep_calls, FuncMap, disasm_range

HERE = os.path.dirname(__file__)
R14 = os.path.dirname(os.path.dirname(HERE))
b = Bin()
rtti = build_rtti(b)
sw = sweep_calls(b)
fm = FuncMap(b, rtti, sw)

# all 33 candidates
rem = json.load(open(os.path.join(R14, 'S10_KPROVED3', 'work', 'a_rows_remaining.json'), encoding='utf-8'))
EXCLUDE = set("""004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690
004D82B0 004D5690 004DB260 00702D40 00706640 00708C30 004D94B0 004DDDE0""".split())
CAND = [r['entry'] for r in rem if r['entry'] not in EXCLUDE]
print('candidates', len(CAND))

outdir = os.path.join(HERE, '..', 'EVIDENCE', 'disasm')
os.makedirs(outdir, exist_ok=True)
extents = {}
for e in CAND:
    ea = int(e, 16)
    st, en = fm.extent(ea)
    insns = disasm_range(b, st, en)
    extents[e] = {'start': f'{st:08X}', 'end': f'{en:08X}', 'size': en-st, 'n_ins': len(insns)}
    lines = [f'{i.address:08X} +{i.address-ea:04X}  {i.bytes.hex():<20s} {i.mnemonic:<8s} {i.op_str}' for i in insns]
    open(os.path.join(outdir, f'{e}.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
    print(f'{e} ext [{st:08X},{en:08X}) size={en-st} ins={len(insns)}')

json.dump(extents, open(os.path.join(HERE,'..','EVIDENCE','function_extents.json'),'w',encoding='utf-8'),
          indent=1, ensure_ascii=False)
print('done')
