"""S18-F1 discipline audit helpers: rule5 (no-op full body), rule6 (stack params), rule15 (all writes)."""
import sys, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import disasm_insns

print("===== RULE 5: full body of no-op target 0x4C8109 until ret =====")
for ins in disasm_insns(0x4C8109, 30):
    print(f"  {ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")
    if ins.mnemonic=='ret': break

print("\n===== RULE 6: Build_FrameInfo 0x649CA0 [esp+N] set & max (first 0x100 bytes) =====")
offs=set(); mx=0
for ins in disasm_insns(0x649CA0, 120):
    for m in re.finditer(r'\[esp\s*\+\s*(0x[0-9a-fA-F]+|\d+)\]', ins.op_str):
        v=int(m.group(1),0); offs.add(v); mx=max(mx,v)
    if ins.address>=0x649D40: break
# note: pushes before reads shift esp; report raw set + max, and the prologue push count
print(f"  raw [esp+N] offsets = {sorted(hex(x) for x in offs)}; max = {hex(mx)}")
print("  prologue: sub esp,0x1C + push ebx/ebp/esi/edi (4 pushes) => before reads esp shifted by 0x1C+0x10=0x2C")
print("  => [esp+0x34] corresponds to original arg area; [esp+0x38] = CommandCount arg (max offset 0x38)")

print("\n===== RULE 6b: FillEvent_Place 0x4C6AE0 [esp+N] set & max =====")
offs=set(); mx=0
for ins in disasm_insns(0x4C6AE0, 90):
    for m in re.finditer(r'\[esp\s*\+\s*(0x[0-9a-fA-F]+|\d+)\]', ins.op_str):
        v=int(m.group(1),0); offs.add(v); mx=max(mx,v)
    if ins.address>=0x4C6B60: break
print(f"  raw [esp+N] offsets = {sorted(hex(x) for x in offs)}; max = {hex(mx)}")

print("\n===== RULE 15: ALL memory writes in FillEvent_Place/SellCell (any base reg, op0 or op1) =====")
for fn,end in [(0x4C6AE0,0x4C6B60),(0x4C6650,0x4C66C0)]:
    print(f"  -- fn 0x{fn:08X} --")
    for ins in disasm_insns(fn, 120):
        if ins.address>=end: break
        # capstone: for `mov [mem], reg` mem is op0; detect any op being MEM and written
        ops=ins.op_str
        if ins.mnemonic in ('mov','movsx','movzx','or','and','add','sub') and '[' in ops:
            # print all mov instructions with memory operands (both op0 and op1)
            print(f"    {ins.address:08X}: {ins.mnemonic} {ops}")
