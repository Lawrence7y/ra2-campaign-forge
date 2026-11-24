#!/usr/bin/env python3
# W157 Q4: identify the real per-frame worker among 0x55D360 callees,
# and confirm 0x55dc92 (caller of save-chain 0x67CEF0) is a gated save branch.
import pefile, capstone
PE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(PE, fast_load=True); data = pe.__data__
def off(va): return pe.get_offset_from_rva(va-0x400000)
def rd(va,n):
    o=off(va); return data[o:o+n]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
def dis(start,size):
    return list(md.disasm(rd(start,size),start))

# 1) all direct call targets in 0x55D360 (size 2940)
print("=== 0x55D360 direct CALL targets ===")
ins=dis(0x55D360,2940)
calls=[]
for i in ins:
    if i.group(capstone.CS_GRP_CALL) and i.operands and i.operands[0].type==capstone.CS_OP_IMM:
        calls.append((i.address,i.mnemonic,i.operands[0].imm))
print(f"total direct calls={len(calls)} unique={len(set(c for _,_,c in calls))}")
for a,m,t in calls:
    print(f"  {a:#x}  call {t:#x}")

# 2) control flow INTO the save branch at 0x55dc40..0x55dc92: find jumps whose target lands there
print("\n=== jumps targeting [0x55DBF0,0x55DC92] from within 0x55D360 ===")
for i in ins:
    if i.group(capstone.CS_GRP_JUMP) and i.operands and i.operands[0].type==capstone.CS_OP_IMM:
        t=i.operands[0].imm
        if 0x55DBF0 <= t <= 0x55DC92:
            print(f"  {i.address:#x}  {i.mnemonic} -> {t:#x}")

# 3) dump the save branch region with bytes
print("\n=== 0x55DB90..0x55DC95 (save branch lead-in) ===")
for i in dis(0x55DB90,0x105):
    ref=''
    if i.group(capstone.CS_GRP_CALL) and i.operands and i.operands[0].type==capstone.CS_OP_IMM:
        ref=f'  ; CALL {i.operands[0].imm:#x}'
    if i.group(capstone.CS_GRP_JUMP) and i.operands and i.operands[0].type==capstone.CS_OP_IMM:
        ref=f'  ; JMP {i.operands[0].imm:#x}'
    print(f"  {i.address:#x}  {i.bytes.hex():<16s}  {i.mnemonic:<7s} {i.op_str}{ref}")

# 4) candidate per-frame workers: entry disasm + backedge count
print("\n=== candidate per-frame workers ===")
cands={0x55AFB0:'House x2 d1',0x64C380:'event-ring consumer d2',0x6D3D10:'Techno/House d2',
       0x55E420:'House d2',0x64DAB0:'Inf/Unit/Bldg/House d2',0x6C6F50:'H/U/I/A d3',
       0x650A90:'5 arrays x4 d3',0x6D8DB0:'Building x2 d3',0x647260:'event pump outer d1'}
# function sizes from W134 atlas if available; use byte scan until ret heuristic cap
for a,label in sorted(cands.items()):
    seq=dis(a,2000)
    nb=sum(1 for i in seq if i.group(capstone.CS_GRP_JUMP) and i.operands and i.operands[0].type==capstone.CS_OP_IMM and i.operands[0].imm<=i.address)
    head=' | '.join(f'{i.mnemonic} {i.op_str}' for i in seq[:6])
    print(f"  {a:#x}  [{label}]  head: {head}")
    print(f"       first 0x100 bytes scanned, jump-backedges(<=addr)={nb}")

# 5) confirm 0x64C380 is called unconditionally at end of 0x6474C7 event pump
print("\n=== calls to 0x64C380 near 0x6474C7..0x647600 ===")
for i in dis(0x6474C7,0x200):
    if i.group(capstone.CS_GRP_CALL) and i.operands and i.operands[0].type==capstone.CS_OP_IMM:
        if i.operands[0].imm==0x64C380:
            print(f"  {i.address:#x}  {i.mnemonic} {i.op_str}")
