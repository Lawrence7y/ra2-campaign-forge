import sys, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
instrs, _ = b.sweep()

reads = [ins.address for ins in instrs if ins.mnemonic == "mov" and "0x887324" in ins.op_str
         and ins.op_str.rstrip().endswith("0x887324]")]
print("reads of [0x887324] as source:", len(reads))

# For each read, walk forward and look for call dword ptr [reg + 0x18] where reg held a vptr loaded from a Tactical-ish reg
out = []
for r in reads:
    seq = b.dis(r, 40)
    regs_from_tac = set()
    m = re.match(r"(\w+),", seq[0].op_str) if seq else None
    if m:
        regs_from_tac.add(m.group(1))
    for ins in seq[1:]:
        if ins.mnemonic == "mov":
            dst, _, src = ins.op_str.partition(", ")
            src = src.strip()
            if src.startswith("[") and any(("[" + x) in src for x in regs_from_tac) and dst in ("eax","ebx","ecx","edx","esi","edi","ebp"):
                regs_from_tac.add(dst)
                if "0x18]" in ins.op_str or True:
                    pass
        if ins.mnemonic == "call" and ins.op_str.startswith("dword ptr [") and re.search(r"\b(eax|ebx|ecx|edx|esi|edi) \+ 0x18\]", ins.op_str):
            reg = re.search(r"\b(eax|ebx|ecx|edx|esi|edi) \+ 0x18\]", ins.op_str).group(1)
            if reg in regs_from_tac:
                out.append((r, ins.address, f(ins)))
                break
print("candidate slot6 dispatches:", len(out))
seen = set()
for r, a, t in out:
    if a in seen:
        continue
    seen.add(a)
    print(f"--- tactical-read@{r:08X}  dispatch@{a:08X}  {t}")
    print(show(b.dis(r, 16), "    "))
    if len(seen) >= 6:
        break
