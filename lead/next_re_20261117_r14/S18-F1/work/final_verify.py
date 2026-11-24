"""S18-F1: final verifications - GameRunner order, SYNC class categories, executed flag."""
import sys, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import disasm_insns, read, sections, scan_rel32_calls

# 1. GameRunner: find call sites 0x48CE8A (MainLogicFrame) and UI pump
print("===== GameRunner region: calls around 0x48CE00-0x48CF00 =====")
for ins in disasm_insns(0x48CE00, 300):
    if ins.address >= 0x48CF00: break
    if ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
        print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

# 2. Count '* CRCs *' SYNC report category strings
print("\n===== SYNC report class categories ('*** XXX CRCs ***') =====")
cats=set()
for name,va_base,vsize,praw,rawsize,ch in sections():
    if rawsize<=0: continue
    d=read(va_base,rawsize)
    if not d: continue
    for m in re.finditer(rb'\*\*\* ([A-Za-z ][A-Za-z ]{1,30}) CRCs \*\*\*', d):
        cats.add((va_base+m.start(), m.group(1).decode('latin1').strip()))
for va,s in sorted(cats):
    print(f"  0x{va:08X}: {s}")
print(f"  TOTAL distinct category strings = {len(cats)}")

# 3. executed flag [event+1]&1 - search all writes of form 'or byte ptr [reg*3+0x8b4205],1' etc in 0x64C380
print("\n===== candidate executed-flag writes in 0x64C380..0x64CD00 =====")
for ins in disasm_insns(0x64C380, 2400):
    if ins.address>=0x64CD00: break
    o=ins.op_str
    if '0x8b4205' in o or ('[esi + 1]' in o) or ('[eax + 1]' in o):
        print(f"  {ins.address:08X}: {ins.mnemonic} {o}")

# 4. Verify NetFrameSync internal order: calls to CRC / RNG / receive / execute / send
print("\n===== NetFrameSync 0x647260 internal call order (first 0x1000 bytes) =====")
for ins in disasm_insns(0x647260, 1200):
    if ins.address>=0x648260: break
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        t=int(ins.op_str,16)
        if t in (0x64DAB0,0x650A90,0x64A0C0,0x64C380,0x64BDD0,0x649CA0,0x64DEA0,0x6516F0,0x4068E0):
            print(f"  {ins.address:08X}: call {ins.op_str}")
