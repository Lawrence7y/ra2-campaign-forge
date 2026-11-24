"""找 S09 类的构造器：全 .text capstone skipdata 扫 mov [mem], imm32 写 vtable 常量的站点；
在站点附近找 push <size>; call operator new (0x7C8E17) 或 push <size>。"""
import struct
import re_lib as R

b = R.Bin()
m = R.md32(True)
text = b.sec(".text")
data = b.pe.__data__[text["raw"]:text["raw"] + text["rawsize"]]
base = text["va"]

VT = {
    0x7F3058: "SidebarClass",
    0x7E6114: "DisplayClass",
    0x7E1964: "MouseClass",
    0x7F7B2C: "WWMouseClass",
    0x7F2FCC: "SelectClass@Strip",
    0x7F2F44: "SBGadgetClass@Sidebar",
    0x7EBE3C: "CommandClass",
    0x7EDFB4: "TabClass",
    0x7F1094: "ScrollClass",
    0x7E92BC: "GadgetClass",
    0x7F4348: "Tactical",
    0x7F0344: "RadarClass",
    0x7EFF54: "PowerClass",
    0x7ED10C: "ListClass",
    0x7E4F84: "CheckListClass",
    0x7E81A4: "EditClass",
    0x7E7FCC: "DropListClass",
    0x7ED21C: "SliderClass",
}
vtset = set(VT.keys())

# capstone 扫所有 mov [mem], imm32（C7 / C6）写 vtable 常量
writes = []
for insn in m.disasm(data, base):
    if insn.id == 0:
        continue
    if insn.mnemonic not in ("mov",):
        continue
    ops = insn.operands
    if len(ops) != 2:
        continue
    dst, src = ops[0], ops[1]
    if dst.type != R.capstone.x86.X86_OP_MEM or src.type != R.capstone.x86.X86_OP_IMM:
        continue
    if src.imm in vtset:
        writes.append((insn.address, src.imm, insn.mnemonic + " " + insn.op_str))

print("vtable-write sites:", len(writes))
import collections
byvt = collections.defaultdict(list)
for va, vt, s in writes:
    byvt[vt].append((va, s))

# 对每个写点，往前后 0x120 字节找 push imm32 + call 0x7C8E17 (operator new)
NEW = 0x7C8E17
def find_ctor_near(site):
    lo = max(base, site - 0x180)
    hi = min(base + len(data), site + 0x80)
    seg = b.read(lo, hi - lo)
    out = []
    for ins in m.disasm(seg, lo):
        if ins.id == 0:
            continue
        # push imm32
        if ins.mnemonic == "push" and ins.operands and ins.operands[0].type == R.capstone.x86.X86_OP_IMM:
            im = ins.operands[0].imm & 0xFFFFFFFF
            if 0x8 <= im <= 0x10000:
                out.append(("push", ins.address, im))
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == R.capstone.x86.X86_OP_IMM:
            if ins.operands[0].imm == NEW:
                out.append(("new", ins.address, NEW))
    return out

for vt in sorted(VT):
    sites = byvt.get(vt, [])
    print("\n=== %s vt=%08X writes=%d ===" % (VT[vt], vt, len(sites)))
    for va, s in sites[:8]:
        near = find_ctor_near(va)
        print("  vtwrite@%08X %s" % (va, s))
        # 只列与 new 相关的 push（紧凑）
        pushes = [x for x in near if x[0] == "push"]
        news = [x for x in near if x[0] == "new"]
        print("     push-imm candidates:", [(hex(p[1]), hex(p[2])) for p in pushes[:12]])
        print("     new sites:", [hex(n[1]) for n in news])
