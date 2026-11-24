import sys, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
instrs, by = b.sweep()
reads = [ins.address for ins in instrs if ins.mnemonic == "mov" and "0x887324" in ins.op_str
         and ins.op_str.rstrip().endswith("0x887324]")]
offs = {}
for r in reads:
    seq = b.dis(r, 25)
    if not seq:
        continue
    regs = set()
    m = re.match(r"(\w+),", seq[0].op_str)
    if m:
        regs.add(m.group(1))
    for ins in seq[1:]:
        if ins.mnemonic == "mov":
            dst, _, src = ins.op_str.partition(", ")
            if src.strip().startswith("[") and any(("[" + x + "]") in src or ("[" + x + " +") in src or ("[" + x + " -") in src for x in regs):
                regs.add(dst)
        if ins.mnemonic == "call" and ins.op_str.startswith("dword ptr ["):
            mm = re.search(r"\b(eax|ebx|ecx|edx|esi|edi) \+ (0x[0-9a-f]+)\]", ins.op_str)
            if mm and mm.group(1) in regs:
                offs.setdefault(mm.group(2), []).append(ins.address)
print("dispatch offsets via Tactical vtable:", {k: len(v) for k, v in sorted(offs.items(), key=lambda x: -len(x[1]))})
for k in list(offs)[:4]:
    a = offs[k][0]
    print(f"--- slot off {k} sample @{a:08X}")
    print(show(b.dis(a - 0x1c, 14), "    "))
