"""AUDIT7: find runtime vtable installs into a global (.bss) object, via MEM-operand map."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *
import fast

TARGETS = {
    0x00A83DC8: 'ParticleClass registry',
    0x00A83D68: 'ParticleSystemTypeClass registry',
    0x00B0F670: 'shared type registry',
    0x00A83D98: 'ParticleTypeClass 2nd registry',
    0x00A8EB28: 'VoxelAnimTypeClass 2nd registry',
    0x00B0F680: 'shared registry count',
    0x00B0F674: 'shared registry array',
}

for addr, tag in TARGETS.items():
    print(f"\n=== {addr:08X} {tag} ===")
    for a in sorted(fast.db()['memmap'].get(addr, [])):
        mn, opstr, bh, imms = fast.db()['recs'][a]
        fn = fast.func_start(a)
        print(f"  {a:08X} fn={fn:08X}  {bh:<24} {mn} {opstr}")
