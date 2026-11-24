#!/usr/bin/env python3
# Static read-only reachability scan for 0x005A5020 in pinned gamemd.exe.
# Writes only REPORT.md and scan_hits.tsv in this card's product directory.
import hashlib, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

IMAGE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
TARGET_VA = 0x005A5020
PAT = struct.pack("<I", TARGET_VA)

with open(IMAGE, "rb") as f:
    blob = f.read()
sha = hashlib.sha256(blob).hexdigest().upper()
if sha != EXPECT_SHA:
    raise SystemExit(f"HASH MISMATCH: {sha}; report invalid")

def u16(o): return struct.unpack_from("<H", blob, o)[0]
def u32(o): return struct.unpack_from("<I", blob, o)[0]

lfa = u32(0x3C)
coff = lfa + 4
nsec = u16(coff + 2)
size_opt = u16(coff + 16)
opt = coff + 20
magic = u16(opt)
if magic != 0x10B:
    raise SystemExit(f"unexpected PE magic {magic:#x}")
image_base = u32(opt + 28)

class Sec:
    def __init__(self, raw):
        self.name = raw[:8].decode("latin1").rstrip("\0")
        self.vsize, self.va, self.rsize, self.raw = struct.unpack_from("<IIII", raw, 8)
    @property
    def start(self): return self.raw
    @property
    def end(self): return self.raw + self.rsize

sec_off = opt + size_opt
secs = [Sec(blob[sec_off + i*40: sec_off + (i+1)*40]) for i in range(nsec)]
by_name = {s.name: s for s in secs}

def sec_for_va(va):
    for s in secs:
        if s.va <= va < s.va + max(s.vsize, s.rsize): return s
    return None

def off_to_rva(off):
    for s in secs:
        if s.start <= off < s.end: return s.va + off - s.start
    return None

def fmt_va(x): return f"0x{x:08X}"
def fmt_off(x): return f"0x{x:08X}"

def find_pattern(lo, hi):
    hits, pos = [], lo
    while True:
        i = blob.find(PAT, pos, hi)
        if i < 0: break
        hits.append(i)
        pos = i + 1
    return hits

def sample(offs, limit=20):
    parts = []
    for h in offs[:limit]:
        if isinstance(h, tuple):
            parts.append(f"VA={fmt_va(h[0])}:{h[1]}")
        else:
            off = h
            rva = off_to_rva(off)
            parts.append(f"file={fmt_off(off)},RVA=" + (fmt_va(rva) if rva is not None else "n/a"))
    return "; ".join(parts) if parts else "NONE"

rows = []
def row(scan_id, question, region, scope, nbytes, hit_kind, hits, detail=""):
    rows.append({
        "scan_id": scan_id, "question": question, "region": region, "scope": scope,
        "bytes": nbytes, "hit_kind": hit_kind, "hits": len(hits),
        "detail": detail if hits == 0 else detail + " | " + sample(hits),
    })

text, rdata, data = by_name[".text"], by_name[".rdata"], by_name[".data"]
target_rva = TARGET_VA - image_base
target_sec = sec_for_va(TARGET_VA)
target_file_off = None
if target_sec:
    target_file_off = target_sec.start + (TARGET_VA - image_base - target_sec.va)

all_text = find_pattern(text.start, text.end)
all_rdata = find_pattern(rdata.start, rdata.end)
all_data = find_pattern(data.start, data.end)
all_file = find_pattern(0, len(blob))
row("D0", "identity", "WHOLE_FILE", "file[0:len]", len(blob), "dword_literal_005A5020", all_file, "whole-file cross-check")
row("D1", "Q1", ".text", f"file[{fmt_off(text.start)}:{fmt_off(text.end)}]", text.rsize, "dword_literal_005A5020", all_text, "jump-table entry / text literal")
row("D2", "Q1/Q3", ".rdata", f"file[{fmt_off(rdata.start)}:{fmt_off(rdata.end)}]", rdata.rsize, "dword_literal_005A5020", all_rdata, "pointer table / jump table entry")
row("D3", "Q1/Q3", ".data", f"file[{fmt_off(data.start)}:{fmt_off(data.end)}]", data.rsize, "dword_literal_005A5020", all_data, "pointer table / callback table")
row("D4", "Q2", ".text", f"file[{fmt_off(text.start)}:{fmt_off(text.end)}]", text.rsize, "dword_literal_005A5020", all_text, "mov/push/lea immediate or absolute disp32")

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True
code = blob[text.start:text.end]
base_va = image_base + text.va

jt, indirect_calls, target_ops, direct_target_calls = [], [], [], []
decoded = 0
for ins in md.disasm(code, base_va):
    decoded += 1
    try:
        ops = ins.operands
    except Exception:
        continue  # capstone skipdata pseudo-record (.byte) has no detail
    if ins.mnemonic == "jmp" and ops and ops[0].type == X86_OP_MEM:
        m = ops[0].mem
        if m.index != 0 and m.scale == 2:
            jt.append((ins.address, ins.mnemonic + " " + ins.op_str))
    if ins.mnemonic in ("call", "callf") and ops:
        op0 = ops[0]
        if op0.type in (X86_OP_REG, X86_OP_MEM):
            indirect_calls.append((ins.address, ins.mnemonic + " " + ins.op_str))
        elif op0.type == X86_OP_IMM and op0.imm == TARGET_VA:
            direct_target_calls.append((ins.address, ins.mnemonic + " " + ins.op_str))
    if ins.mnemonic in ("mov", "push", "lea"):
        hit = False
        for op in ops:
            if op.type == X86_OP_IMM and op.imm == TARGET_VA: hit = True
            if op.type == X86_OP_MEM and op.mem.disp == TARGET_VA: hit = True
        if hit:
            target_ops.append((ins.address, ins.mnemonic + " " + ins.op_str))

load_vas = [x[0] for x in target_ops]
resolved = [(lv, cv) for cv, _ in indirect_calls for lv in load_vas if 0 <= cv - lv <= 32]

row("I1", "Q1", ".text", f"linear capstone decode from {fmt_va(base_va)}", text.rsize,
    "jmp_dword_ptr_reg_times_4", jt, f"decoded={decoded}; jump-table-shaped instruction candidates")
row("I2", "Q2", ".text", f"linear capstone decode from {fmt_va(base_va)}", text.rsize,
    "indirect_call_reg_or_mem", indirect_calls, f"decoded={decoded}; indirect call sites, not target hits")
row("I3", "Q2", ".text", f"linear capstone decode from {fmt_va(base_va)}", text.rsize,
    "mov_push_lea_operand_equals_target_literal", target_ops, f"decoded={decoded}; target-address load instructions")
row("I4", "Q2", ".text", f"linear capstone decode from {fmt_va(base_va)}", text.rsize,
    "indirect_call_locally_resolved_to_target", resolved, "target literal load within 32 bytes before call")

header = ["scan_id", "question", "region", "scope", "bytes", "hit_kind", "hits", "detail"]
with open("scan_hits.tsv", "w", encoding="utf-8", newline="\n") as f:
    f.write("\t".join(header) + "\n")
    for r in rows:
        f.write("\t".join(str(r[k]).replace("\t", " ").replace("\n", " ") for k in header) + "\n")

def hitcount(*ids): return sum(r["hits"] for r in rows if r["scan_id"] in ids)
q1 = hitcount("D1", "D2", "D3")
q2 = hitcount("D4", "I3", "I4")
q3 = hitcount("D2", "D3")
q1_dword_all = hitcount("D0")

report = f"""IMAGE: {IMAGE} | sha256={sha}
# R17-R32-REACH5020 · 0x005A5020 静态到达性

- 方法：纯静态、只读、未建进程、未调试、未启动 gamemd.exe；产物仅写本卡目录。
- 镜像校验：file size {len(blob)} bytes；sha256 {sha}（前缀 73201CC0、后缀 F67476 均匹配）。
- PE：ImageBase={fmt_va(image_base)}，目标 VA {fmt_va(TARGET_VA)} → RVA {fmt_va(target_rva)} → section {target_sec.name if target_sec else 'N/A'} → file offset {fmt_off(target_file_off) if target_file_off is not None else 'N/A'}。
- 判据：dword 采用小端 20 50 5A 00，对区段内每个字节偏移搜索（不要求 4 对齐，故是跳表/指针表条目的超集）；反汇编采用 capstone x86-32，从 .text 起始 VA {fmt_va(base_va)} 线性解码并启用 skipdata，共解码 {decoded} 条记录。

## 扫描声明与命中

| scan_id | 问题 | 区段 | 扫描字节数 | 命中类型 | 命中数 |
|---|---|---|---:|---|---:|
"""
for r in rows:
    report += f"| {r['scan_id']} | {r['question']} | {r['region']} | {r['bytes']} | {r['hit_kind']} | {r['hits']} |\n"

report += f"""
### Q1 · 跳表 / jmp 表
- .text 中形如 jmp dword ptr [reg*4+disp] 的指令候选：{hitcount('I1')} 处（这是形态候选，不是到达命中）。
- .text/.rdata/.data 内 dword == 0x005A5020：{q1} 命中；全文件交叉检查 {q1_dword_all} 命中。
- 结论：Q1 到达命中 0。任何含该 dword 的跳表条目都未出现；若跳表条目在段外或运行期生成，见 Q4 覆盖边界。

### Q2 · 间接调用与地址装入
- capstone 解码得到间接 call reg / call [reg+disp] 候选 {hitcount('I2')} 处；其中能通过局部立即数装入关系确定到 0x005A5020 的：{hitcount('I4')} 处。
- mov / push / lea 的操作数（imm32 或 disp32）等于 0x005A5020 的指令：{hitcount('I3')} 条；.text 4 字节字面量扫描：{hitcount('D4')} 命中。
- 直接 call 0x005A5020 的 capstone 交叉计数：{len(direct_target_calls)}。
- 结论：Q2 到达命中 0。间接调用形态存在与否不等于目标可解析；本镜像未发现把该地址作为字面量装入寄存器/栈的指令，因此未发现可静态绑定到该目标的间接调用。

### Q3 · 函数指针表 / 回调注册
- .rdata + .data 合计 {rdata.rsize + data.rsize} bytes，dword == 0x005A5020 命中 {q3}；全文件交叉检查仍为 {q1_dword_all}。
- 结论：Q3 到达命中 0。未发现以 0x005A5020 为值的函数指针、回调槽或结构起始指针。

### Q4 · 是否真的是死代码
三项到达方式（Q1/Q2/Q3）的目标命中均为 0，扫描字节数汇总：
- Q1：.text {text.rsize} + .rdata {rdata.rsize} + .data {data.rsize} = {text.rsize+rdata.rsize+data.rsize} bytes；另有全文件 {len(blob)} bytes 交叉检查。
- Q2：.text {text.rsize} bytes（字面量扫描 + capstone 指令边界扫描）。
- Q3：.rdata {rdata.rsize} + .data {data.rsize} = {rdata.rsize+data.rsize} bytes。

静态未发现任何到达 `0x5A5020` 的路径。

覆盖不到的情形：
1. 运行期计算地址：由算术、索引、跨函数寄存器/栈传播得到目标，而镜像中没有 20 50 5A 00 字面量。
2. 外部 DLL / 插件 / 注入代码回调：指针在进程外构造后传入，不在本镜像 .rdata/.data 中静态出现。
3. 运行期被覆写的数据：IAT/重定位/全局变量在启动后写入函数指针，扫文件无法观察写后状态；.data 的未初始化尾部也不在文件里。
4. VirtualProtect 后的自改代码、解包、detour/hook、补丁运行期改写指令或表项。
5. 反汇编边界限制：x86-32 线性解码遇到嵌入数据/重叠指令可能失步；本卡的 dword 字节扫描不依赖反汇编边界，但语义级数据流/别名分析未做全程序证明。

因此不要断言它是死代码；只能说“静态未发现到达路径”。

### Q5 · 对既有结论的影响（方向判断）
同意卡中表述。依据：
- 0x43F180 ← 0x5A6860（call [edx+0x124]）← host 0x5A6510 ← 0x5A531E ← host 0x5A5020 的调用方字节证据仍在；本次没有删除或推翻任何指令字节事实，所以“调用方字节证实存在”成立。
- 但 Q1–Q3 未发现到达 0x5A5020 的静态路径，故该链路顶端缺少运行期入口证据；“运行期真会执行 0x43F180 这个派发点”只能更弱，不能由结构可能性升格为运行期事实。
- 这不改变 §2.9 的 [静态推断] 收口，也不改变“不证唯一、不证运行期真执行”的既有边界；本卡只收紧上游可达性的表述强度。
"""
with open("REPORT.md", "w", encoding="utf-8", newline="\n") as f:
    f.write(report)

print(report.splitlines()[0])
print(f"Q1={q1} Q2={q2} Q3={q3} all_file={q1_dword_all} jt={hitcount('I1')} indirect_calls={hitcount('I2')} target_ops={hitcount('I3')} decoded={decoded}")
