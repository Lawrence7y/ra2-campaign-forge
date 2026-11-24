"""S03-K1 step1: RTTI discovery for CCFileClass / MixFileClass.
Channel A = RTTI TypeDescriptor -> COL -> vftable (independent of function_atlas).
Also dump vtable slots and test the B8 <imm32> C3 (GetSize) hypothesis at slot 12.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b = Bin()
out = []
out.append("IMAGEBASE %08X" % b.base)
for s in b.secs:
    out.append("  %-8s va=%08X raw=%08X rawsize=%08X" % (s['name'], s['va'], s['raw'], s['rawsize']))

for needle in ('CCFileClass', 'MixFileClass', 'RawFileClass', 'BufferIOFileClass', 'CDFileClass', 'FileClass'):
    tds = rtti_type_descriptors(b, needle)
    out.append(f"\n=== TD name contains '{needle}': {len(tds)} ===")
    for td in tds:
        out.append("  TD %08X name=%r pVF=%08X sec=%s" % (td['va'], td['name'], td['pvf'], td['sec']))
        vfts = rtti_vftables(b, td['va'])
        out.append("    VFTables via COL: %d" % len(vfts))
        for v in vfts:
            out.append("      COL %08X vft=%08X off=%d cd=%d nslots=%d classTD=%08X"
                       % (v['col_va'], v['vftable_va'], v['offset'], v['cd'], len(v['slots']), v['class_td']))
            out.append("      slots[0..15]: " + " ".join("%08X" % x for x in v['slots'][:16]))

# Now specifically test slot 12 GetSize at the two main vtables from the lead.
for vft_name, vft in (('CCFileClass', 0x7E16B0), ('MixFileClass', 0x7EDF50)):
    out.append(f"\n=== vtable {vft_name} @{vft:08X} slots 0..15 ===")
    for k in range(16):
        val = b.u32(vft + 4*k)
        note = ""
        # test for B8 imm32 C3
        try:
            raw = b.read(val, 8)
            if len(raw) == 8 and raw[0] == 0xB8 and raw[5] == 0xC3:
                imm = int.from_bytes(raw[1:5], 'little')
                note = "  <== B8 imm32 C3  imm=%08X" % imm
        except Exception:
            pass
        out.append("  v[%2d] @%08X = %08X%s" % (k, vft+4*k, val, note))

text = "\n".join(out)
open(os.path.join(os.path.dirname(__file__), '..', 'EVIDENCE', 'E01_rtti.txt'), 'w', encoding='utf-8').write(text)
print(text)
