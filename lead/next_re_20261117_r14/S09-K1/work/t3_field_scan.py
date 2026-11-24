"""T3：字段布局双支撑扫描。对给定函数体区间，收集 [reg+disp] 访问，
区分写(mov [mem],x / inc/dec / add [mem]) 与读(mov reg,[mem] / cmp [mem])，
只在"该函数(本类方法)内同时有写点与≥3读点"的字段才给语义。"""
import collections
import re_lib as R

b = R.Bin()
m = R.md32(True)
capstone = R.capstone

# DisplayClass 已知方法体区间（来自 S09-F1 / R8）：LMBUp 0x4AB9B0 size~2400; 清拖拽 0x4AC310
REGIONS = {
    "DisplayClass::LMBUp": (0x4AB9B0, 0x4AC310),
    "DisplayClass::ClearDrag(v45)": (0x4AC310, 0x4AC380),
    "DisplayClass::LMBDown(v47)": (0x4AC380, 0x4AC900),
}

def scan_region(va_lo, va_hi):
    data = b.read(va_lo, va_hi - va_lo)
    reads = collections.defaultdict(list)
    writes = collections.defaultdict(list)
    for ins in m.disasm(data, va_lo):
        if ins.id == 0:
            continue
        for opi, op in enumerate(ins.operands):
            if op.type != capstone.x86.X86_OP_MEM:
                continue
            if op.mem.base == 0 and op.mem.index == 0:
                continue  # 绝对寻址跳过（本函数是 thiscall，字段走 [reg+off]）
            disp = op.mem.disp & 0xFFFFFFFF
            if disp < 0x10 or disp > 0x2000:
                continue
            # 判写：op0 是 mem 且是写类指令
            is_write_target = (opi == 0 and ins.mnemonic in (
                "mov", "inc", "dec", "add", "sub", "and", "or", "xor", "cmp"))
            # 更精确：mov [mem],x 一定是写；cmp [mem],x 是读
            if opi == 0 and ins.mnemonic == "mov":
                writes[disp].append((ins.address, ins.mnemonic + " " + ins.op_str))
            elif opi == 0 and ins.mnemonic in ("inc", "dec", "add", "sub", "and", "or", "xor"):
                writes[disp].append((ins.address, ins.mnemonic + " " + ins.op_str))
            else:
                reads[disp].append((ins.address, ins.mnemonic + " " + ins.op_str))
    return reads, writes

all_reads = collections.defaultdict(list)
all_writes = collections.defaultdict(list)
for name, (lo, hi) in REGIONS.items():
    reads, writes = scan_region(lo, hi)
    print("\n=== %s [%08X,%08X) ===" % (name, lo, hi))
    for d in sorted(set(list(reads) + list(writes))):
        print("  +0x%X: W=%d R=%d  W@%s R@%s" % (
            d, len(writes.get(d, [])), len(reads.get(d, [])),
            [hex(x[0]) for x in writes.get(d, [])[:4]],
            [hex(x[0]) for x in reads.get(d, [])[:4]]))
        for x in writes.get(d, []): all_writes[d].append((x[0], name))
        for x in reads.get(d, []): all_reads[d].append((x[0], name))

print("\n=== 合并：写点>=1 且读点>=3 的字段（DisplayClass 方法群）===")
for d in sorted(all_writes):
    nw = len(all_writes[d]); nr = len(all_reads.get(d, []))
    if nw >= 1 and nr >= 3:
        print("  +0x%X: W=%d R=%d  %s" % (d, nw, nr,
              "W:"+",".join(hex(x[0]) for x in all_writes[d][:6])+
              " R:"+",".join(hex(x[0]) for x in all_reads[d][:6])))
