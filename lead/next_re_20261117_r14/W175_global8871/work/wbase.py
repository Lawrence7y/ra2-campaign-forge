"""W175 基础工具：加载 PE + capstone(skipdata=True) + 常用反汇编/引用扫描。
只读目标文件；输出写到本卡 EVIDENCE/work。"""
import sys, os, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A

BIN = A.Bin()
IMAGE_BASE = BIN.image_base

def md():
    return A.md32(skipdata=True)

def disasm(va, nbytes, stop_at=None):
    m = md()
    data = BIN.read(va, nbytes)
    out = []
    for insn in m.disasm(data, va):
        if insn.id == 0:
            continue
        out.append(insn)
        if stop_at is not None and insn.address >= stop_at:
            break
    return out

def fmt(insns):
    return "\n".join("%08X  %-8s %s" % (i.address, i.mnemonic, i.op_str) for i in insns)

def dump(va, nbytes, path, stop_at=None, header=None):
    insns = disasm(va, nbytes, stop_at)
    with open(path, "w", encoding="utf-8") as f:
        if header:
            f.write(header + "\n")
        f.write(fmt(insns) + "\n")
    return insns

def u32(va): return BIN.u32(va)
def u16(va): return BIN.u16(va)
def u8(va):  return BIN.u8(va)

def sections():
    return BIN.sections

def find_abs_refs(target_va):
    """全 .text 找以绝对寻址引用 target_va 的指令（op0/op1 都查）。"""
    m = md()
    t = BIN.text
    data = BIN.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    found = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                mem = op.mem
                if mem.base == 0 and mem.index == 0 and (mem.disp & 0xFFFFFFFF) == target_va:
                    found.append((insn.address, "%s %s" % (insn.mnemonic, insn.op_str)))
                    break
    return found

import capstone  # noqa: E402

if __name__ == "__main__":
    print("ImageBase", hex(IMAGE_BASE))
    for s in sections():
        print("  %-8s va=%08X vsize=%08X raw=%08X rawsize=%08X"
              % (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"]))
