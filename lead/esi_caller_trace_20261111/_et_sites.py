#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_et_sites.py — 全 .text 搜索「经虚表 slot2 调用 0x54A4F0 / 0x54A630」的所有调用点(只读)。

对象: ra2bench/gamemd.exe (sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476)
方法: pefile + capstone 纯静态; 不启动进程、不 attach、不读活内存、不打补丁。
输出: _et_sites_out.txt / _et_sites_out.json (与本脚本同目录)

任务口径 (与 ask 一一对应):
  1. 复核「直接 call 0x54A4F0 的指令数 = 0」(自行扫描, 两种独立方法)。
  2. 找出全 .text 所有形如 call dword ptr [reg + 8] 的指令; 逐点回溯 ≤20 条,
     判定 reg 的来源对象与其虚表是否可能为 0x7ECBFC / 0x7ECBDC。
  3. 对候选点追 this 的来源 (ecx / 第一栈参数 / 全局 imm)。
  4. 按 form 分类, this_source 写清。

已知陷阱: capstone 单次 disasm 在 RVA 0x6F59D (VA 0x46F59D) 截断 (155,215 条)。
        → 本脚本用「分块 + 停点步进」扫描覆盖全 .text, 并先复现该陷阱作为对照。

排除逻辑(全局值闸门, 六条腿全部由本脚本当场验证, 任一失败记 MISMATCH):
  G1 镜像内值==0x54A4F0/0x54A630 的 dword 只有各自虚表 slot2 项 → call [reg+8] 命中二者
     当且仅当 reg ∈ {0x7ECBFC, 0x7ECBDC}。
  G2 镜像内值==0x7ECBFC/0x7ECBDC 的 dword 只有 4 处且全是 c7 存储立即数(无 mov reg,imm 装载,
     无 .rdata/.data 值单元) → 寄存器不可能直接装入这两个值。
  G3 这两个 vtable 的 vptr 写入点共 5 处: 3 处写固定地址 [0xAA1078], 2 处写 [esi](析构器体内,
     esi=ecx=this, 且两析构器无直接 call/jmp 进入) → 归纳法: 能持有这两个 vptr 值的对象只有
     全局 0xAA1078。
  G4 对 0xAA1078 的 imm32 引用全镜像恰 4 处: 2 处 disp32 存储 + 1 处 disp32 装载(0x54605F,
     vptr→eax) + 1 处 imm 装载(0x546064, this→ecx); 无别名合成(基址立即数审计)。
  G5 .data/.rdata 无 dword==0xAA1078(不存在指向该对象的指针变量)。
  G6 装载点(0x54605F/0x546064)与其唯一消费者 0x546069 之间无 store/push/call 逃逸, 之后立即被
     覆写 → 指针/vptr 值不逃逸出该函数。
  ⇒ 结论: 全模块唯一的 slot2 虚派发点(就这两个 vtable 而言) = 0x546069。
"""
import sys
sys.dont_write_bytecode = True
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import hashlib
import json
import os
import re
import struct

import pefile
import capstone

# ----------------------------------------------------------------------------
# 0. 常量
# ----------------------------------------------------------------------------
EXPECTED_SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
EXPECTED_SIZE = 4825360

TARGET_FN = 0x0054A4F0          # VectorClass<PAUTileInsertType*> slot2 (vtable 0x7ECBFC)
TWIN_FN = 0x0054A630            # DynamicVectorClass<PAUTileInsertType> slot2 (vtable 0x7ECBDC)
VT_BASE = 0x7ECBFC              # 基类 vtable
VT_DER = 0x7ECBDC               # 派生 vtable
GLOBAL_OBJ = 0xAA1078           # 全局唯一实例
SLOT2 = 8                       # slot2 偏移

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXE_PATH = os.path.join(REPO_ROOT, "ra2bench", "gamemd.exe")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

notes = []
def note(kind, text):
    notes.append({"kind": kind, "text": text})
    print("[%s] %s" % (kind, text))

def check(cond, ok_text, bad_text):
    note("FACT" if cond else "MISMATCH", ok_text if cond else bad_text)
    return cond

# ----------------------------------------------------------------------------
# 1. 文件身份
# ----------------------------------------------------------------------------
raw = open(EXE_PATH, "rb").read()
sha = hashlib.sha256(raw).hexdigest()
check(sha == EXPECTED_SHA256, "sha256 = %s (与台账一致)" % sha,
      "sha256 = %s 与台账不一致" % sha)
check(len(raw) == EXPECTED_SIZE, "size = %d B" % len(raw), "size 异常: %d" % len(raw))

pe = pefile.PE(EXE_PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
image = pe.get_memory_mapped_image(ImageBase=IB)

def u32(va):
    return struct.unpack_from("<I", image, va - IB)[0]

def cstr(va, maxn=160):
    out = []
    o = va - IB
    while o < len(image) and image[o] != 0 and len(out) < maxn:
        out.append(chr(image[o]))
        o += 1
    return "".join(out)

sections = {}
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode()
    sections[name] = {"va": IB + s.VirtualAddress, "vsize": s.Misc_VirtualSize,
                      "characteristics": s.Characteristics}
TSTART = sections[".text"]["va"]
TEND = TSTART + sections[".text"]["vsize"]
print(".text [0x%X..0x%X]  .rdata [0x%X..0x%X]  .data [0x%X..0x%X]" % (
    TSTART, TEND, sections[".rdata"]["va"], sections[".rdata"]["va"] + sections[".rdata"]["vsize"],
    sections[".data"]["va"], sections[".data"]["va"] + sections[".data"]["vsize"]))

# ----------------------------------------------------------------------------
# 2. 前提复核: vtable / RTTI / 全局对象文件字节
# ----------------------------------------------------------------------------
check(u32(VT_BASE + SLOT2) == TARGET_FN,
      "vtable 0x7ECBFC slot2 = 0x54A4F0", "vtable 0x7ECBFC slot2 != 0x54A4F0")
check(u32(VT_DER + SLOT2) == TWIN_FN,
      "vtable 0x7ECBDC slot2 = 0x54A630", "vtable 0x7ECBDC slot2 != 0x54A630")
for vt, expect in ((VT_BASE, "VectorClass"), (VT_DER, "DynamicVectorClass")):
    col = u32(vt - 4)
    td = u32(col + 0x0C)
    nm = cstr(td + 8)
    check(expect in nm,
          "RTTI @vtable 0x%X: %r" % (vt, nm), "RTTI @0x%X 异常: %r" % (vt, nm))
check(u32(GLOBAL_OBJ) == 0 and u32(GLOBAL_OBJ + 4) == 0 and u32(GLOBAL_OBJ + 8) == 0,
      "文件镜像 .data @0xAA1078 vptr/Vector/VectorMax 均为 0 (运行期动态初始化, 与台账一致)",
      "文件镜像 .data @0xAA1078 非零(与台账不符)")

# ----------------------------------------------------------------------------
# 3. 反汇编: 先复现截断陷阱, 再分块全覆盖
# ----------------------------------------------------------------------------
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False

single = list(md.disasm(bytes(image[TSTART - IB:TEND - IB]), TSTART))
single_last = single[-1].address
check(len(single) == 155215 and single_last == 0x46F59D,
      "复现陷阱: 单次 disasm = %d 条, 末条 VA 0x%X (即台账所谓『155215 条 / RVA 0x6F59D 截断』)" % (
          len(single), single_last),
      "单次 disasm 复现值与 ask 不符: %d 条 @ 0x%X" % (len(single), single_last))

full = []
restarts = []
pos = TSTART
while pos < TEND:
    chunk = list(md.disasm(bytes(image[pos - IB:TEND - IB]), pos))
    if chunk:
        full.extend(chunk)
        pos = chunk[-1].address + chunk[-1].size
    if pos >= TEND:
        break
    restarts.append(pos)
    pos += 1
restart_set = set(restarts)
cov_end = full[-1].address + full[-1].size
check(cov_end == TEND,
      "分块扫描覆盖全 .text: %d 条指令, %d 个停点, 末条 0x%X (覆盖至 0x%X)" % (
          len(full), len(restarts), full[-1].address, cov_end),
      "分块扫描未覆盖到段尾: 末条 0x%X, TEND 0x%X" % (full[-1].address, TEND))

addr2idx = {}
for k, ins in enumerate(full):
    addr2idx.setdefault(ins.address, k)   # 停点漂移可能产生重解码; 保留首次解码

# 全 .text call/jmp rel32 目标集合(字节级) — 外层函数归属的近似定位用
all_targets = []
for va in range(TSTART, TEND - 5):
    if image[va - IB] in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", image, va - IB + 1)[0]
        t = va + 5 + rel
        if TSTART <= t < TEND:
            all_targets.append(t)
all_targets = sorted(set(all_targets))
import bisect
def enclosing_fn_approx(va):
    i = bisect.bisect_right(all_targets, va) - 1
    return hex(all_targets[i]) if i >= 0 else None

# ----------------------------------------------------------------------------
# 4. 任务1: 直接调用者复核 (指令级 + 字节级两种独立方法)
# ----------------------------------------------------------------------------
def byte_e8e9_targets(target):
    """字节级暴力扫 E8/E9 rel32, 与反汇编无关(不受漂移影响)。"""
    hits = []
    for va in range(TSTART, TEND - 5):
        if image[va - IB] in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", image, va - IB + 1)[0]
            if va + 5 + rel == target:
                hits.append((va, "call" if image[va - IB] == 0xE8 else "jmp"))
    return hits

direct = {}
for tgt in (TARGET_FN, TWIN_FN):
    insn_hits = [i.address for i in full
                 if i.mnemonic in ("call", "jmp") and i.op_str.startswith("0x")
                 and int(i.op_str.split()[0], 16) == tgt]
    byte_hits = byte_e8e9_targets(tgt)
    direct[tgt] = {"insn_level": [hex(x) for x in insn_hits],
                   "byte_level": [(hex(a), k) for a, k in byte_hits]}
    check(len(insn_hits) == 0 and len(byte_hits) == 0,
          "直接调用复核: call/jmp → 0x%08X = 0 (指令级 %d 处 + 字节级 E8/E9 %d 处, 两法一致)" % (
              tgt, len(insn_hits), len(byte_hits)),
          "0x%08X 存在直接调用: insn=%s byte=%s" % (tgt, insn_hits, byte_hits))

# 析构器直接进入检查(归纳腿 G3 需要)
dtor_xrefs = {f: byte_e8e9_targets(f) for f in (0x54A7B0, 0x54A800)}
check(all(len(v) == 0 for v in dtor_xrefs.values()),
      "两个 deleting dtor (0x54A7B0/0x54A800) 无直接 call/jmp 进入 → [esi]←vtable 写只能作用于经"
      " slot0 虚派发到达的 this (归纳腿闭合)", "析构器存在直接进入点: %s" % dtor_xrefs)

# ----------------------------------------------------------------------------
# 5. 全局值闸门 (G1/G2/G4/G5) — 逐腿验证
# ----------------------------------------------------------------------------
def image_dwords_equal(value):
    pat = struct.pack("<I", value)
    hits = []
    pos = 0
    while True:
        i = image.find(pat, pos)
        if i < 0:
            break
        hits.append(i + IB)
        pos = i + 1
    return hits

# G1: 只有虚表项含有这两个函数指针
r_fn = {TARGET_FN: image_dwords_equal(TARGET_FN), TWIN_FN: image_dwords_equal(TWIN_FN)}
check(r_fn[TARGET_FN] == [VT_BASE + SLOT2],
      "G1: 全镜像值==0x54A4F0 的 dword 仅 1 处: 0x%X (=vtable 0x7ECBFC slot2) → 无回调/无第二虚表" % (
          VT_BASE + SLOT2),
      "G1 失败: 0x54A4F0 出现于 %s" % [hex(x) for x in r_fn[TARGET_FN]])
check(r_fn[TWIN_FN] == [VT_DER + SLOT2],
      "G1: 全镜像值==0x54A630 的 dword 仅 1 处: 0x%X (=vtable 0x7ECBDC slot2)" % (VT_DER + SLOT2),
      "G1 失败: 0x54A630 出现于 %s" % [hex(x) for x in r_fn[TWIN_FN]])
check(u32(VT_BASE + SLOT2) == TARGET_FN and u32(VT_DER + SLOT2) == TWIN_FN,
      "G1 推论: call [reg+8] 命中二者 ⇔ reg 值 ∈ {0x7ECBFC, 0x7ECBDC} (运行期被改写的堆/栈单元"
      "不可能持该值, 见 G2)", "G1 推论链断裂")

# G2: 这两个 vtable 值只存在于 4 条 c7 存储立即数中
# 判定方法: G3 的 vptr-store 扫描(modrm 精确)给出 4 条存储指令; 要求每个值引用都完整落在
# 其中一条指令的字节范围内 → 排除『mov reg, imm』装载与 .rdata/.data 值单元。
r_vt = {VT_BASE: image_dwords_equal(VT_BASE), VT_DER: image_dwords_equal(VT_DER)}
STORE_INSNS = [(0x543E8D, "mov dword ptr [0xaa1078], 0x7ecbdc"),
               (0x543EBE, "mov dword ptr [0xaa1078], 0x7ecbfc"),
               (0x54A7B6, "mov dword ptr [esi], 0x7ecbfc"),
               (0x54A806, "mov dword ptr [esi], 0x7ecbfc")]
store_spans = []
for va, txt in STORE_INSNS:
    ins = next(md.disasm(bytes(image[va - IB: va - IB + 12]), va))
    store_spans.append((ins.address, ins.address + ins.size, "%s %s" % (ins.mnemonic, ins.op_str)))
check([s[2] for s in store_spans] == [t for _, t in STORE_INSNS],
      "G3 存储指令字节形态确认: %s" % " | ".join(s[2] for s in store_spans),
      "G3 存储指令形态异常: %s" % store_spans)
g2_ok = True
g2_desc = []
for v, hits in r_vt.items():
    for h in hits:
        owner = [s for s in store_spans if s[0] <= h and h + 4 <= s[1]]
        if owner:
            g2_desc.append("0x%X ← imm of %s" % (h, owner[0][2]))
        else:
            g2_ok = False
            g2_desc.append("0x%X ← 未归属任何 c7 存储(疑似 mov reg,imm 装载或数据单元!)" % h)
check(g2_ok and len(r_vt[VT_BASE]) == 3 and len(r_vt[VT_DER]) == 1,
      "G2: 值 0x7ECBFC×3 + 0x7ECBDC×1 共 4 处, 全部落在 c7 存储立即数内: %s → 无『mov reg, vtable值』"
      "装载, 无 .rdata/.data 值单元; 寄存器只能经装载 [0xAA1078] 获得这两个值" % "; ".join(g2_desc),
      "G2 失败: %s" % g2_desc)

# G3: vptr 写入点 (c7 /0 形式) — 与上轮同法独立重扫
def find_vptr_stores(vtable_va):
    pat = struct.pack("<I", vtable_va)
    hits = []
    va = TSTART
    while va < TEND - 10:
        if image[va - IB] == 0xC7:
            m = image[va - IB + 1]
            mod, reg, rm = m >> 6, (m >> 3) & 7, m & 7
            if reg == 0 and mod != 3:
                imm_off = None
                if mod == 0 and rm == 5:
                    imm_off = 6
                elif mod == 0 and rm == 4 and image[va - IB + 3] == 0x25:
                    imm_off = 7
                elif mod == 0:
                    imm_off = 2
                elif mod == 1:
                    imm_off = 3 + (1 if rm == 4 else 0)
                elif mod == 2:
                    imm_off = 6 + (1 if rm == 4 else 0)
                if imm_off and image[va - IB + imm_off: va - IB + imm_off + 4] == pat:
                    hits.append(va)
        va += 1
    return hits

stores_base = find_vptr_stores(VT_BASE)
stores_der = find_vptr_stores(VT_DER)
check(stores_der == [0x543E8D] and stores_base == [0x543EBE, 0x54A7B6, 0x54A806],
      "G3: vptr 写入点重扫一致 — 0x7ECBDC: [0x543E8D](→[0xAA1078] 动态初始化器); "
      "0x7ECBFC: [0x543EBE](→[0xAA1078] atexit 析构器), [0x54A7B6]/[0x54A806](析构器体内 →[esi])",
      "G3 失败: der=%s base=%s" % (stores_der, stores_base))
def ins_at(va, span=12):
    return ["%08X %s %s" % (i.address, i.mnemonic, i.op_str)
            for i in md.disasm(bytes(image[va - IB: va - IB + span]), va)]
e1 = ins_at(0x54A7B0, 8)
e2 = ins_at(0x54A800, 8)
check(any("mov esi, ecx" in x for x in e1) and any("mov esi, ecx" in x for x in e2),
      "G3 支撑: 两析构器入口 esi=ecx=this (0x54A7B1 / 0x54A801) → [esi] 写的目标对象 = 被派发对象; "
      "结合『无直接进入』与『slot0 派发要求 reg 已是这两个 vptr 值』→ 归纳: 唯一实例 = 全局 0xAA1078",
      "G3 支撑失败: %s | %s" % (e1, e2))

# G4: 对 0xAA1078 的全部引用(imm32 字节模式, 与上一轮口径一致 — 报告的是立即数字节地址)
refs_g = image_dwords_equal(GLOBAL_OBJ)
check(refs_g == [0x543E8F, 0x543EC0, 0x546060, 0x546065],
      "G4: 全镜像 imm32 引用 0xAA1078 恰 4 处(立即数字节地址): 0x543E8F(init 存储)/0x543EC0"
      "(atexit 存储)/0x546060(vptr 装载 @0x54605F)/0x546065(this 装载 @0x546064)",
      "G4 失败: %s" % [hex(x) for x in refs_g])
def insn_containing(ref, end_fixed=False):
    """回找完整覆盖 [ref, ref+4) 的指令; end_fixed=True 时额外要求指令恰在 ref+4 结束(imm32 尾操作数)。"""
    best = None
    for back in range(1, 16):
        seg = list(md.disasm(bytes(image[ref - IB - back: ref - IB - back + 24]), ref - back))
        for ins in seg:
            if ins.address <= ref and ref + 4 <= ins.address + ins.size:
                if end_fixed and ins.address + ins.size != ref + 4:
                    continue
                if best is None or ins.address > best.address:
                    best = ins
    return best
# 用与 G3 一致的『已知指令锚点』核对 4 处引用的归属(避免回找误解码)
g4_owner = {
    0x543E8F: (0x543E8D, "mov dword ptr [0xaa1078], 0x7ecbdc (disp32=0xAA1078)"),
    0x543EC0: (0x543EBE, "mov dword ptr [0xaa1078], 0x7ecbfc (disp32=0xAA1078)"),
    0x546060: (0x54605F, "mov eax, dword ptr [0xaa1078] (disp32=0xAA1078, vptr 装载)"),
    0x546065: (0x546064, "mov ecx, 0xaa1078 (imm32=0xAA1078, this 装载)"),
}
g4_ok = True
g4_ctx = []
for r in refs_g:
    exp_start, desc = g4_owner[r]
    ins = next(md.disasm(bytes(image[exp_start - IB: exp_start - IB + 12]), exp_start))
    covers = ins.address <= r and r + 4 <= ins.address + ins.size
    g4_ok = g4_ok and covers
    g4_ctx.append("%08X %s %s ← ref 0x%X" % (ins.address, ins.mnemonic, ins.op_str, r))
check(g4_ok,
      "G4: 4 处引用逐一归属: %s" % " | ".join(g4_ctx),
      "G4 归属失败: %s" % g4_ctx)
g4_load_ok = refs_g == [0x543E8F, 0x543EC0, 0x546060, 0x546065]
check(g4_load_ok,
      "G4: 唯一的 vptr 装载 = 0x54605F mov eax,[0xAA1078]; 唯一的 this 装载 = 0x546064 "
      "mov ecx,0xAA1078",
      "G4 装载点集合异常: %s" % [hex(x) for x in refs_g])

# G5: .data/.rdata 无指向 0xAA1078 的指针
ptr_hits = {}
for name in (".rdata", ".data"):
    sec = sections[name]
    hits = []
    pos = sec["va"] - IB
    end = pos + sec["vsize"]
    while True:
        i = image.find(struct.pack("<I", GLOBAL_OBJ), pos, end)
        if i < 0:
            break
        hits.append(i + IB)
        pos = i + 1
    ptr_hits[name] = hits
check(all(len(v) == 0 for v in ptr_hits.values()),
      "G5: .rdata/.data 无 dword==0xAA1078 → 不存在指向该全局对象的指针变量(指针值不逃逸的前提)",
      "G5 失败: %s" % ptr_hits)

# G4b: 别名合成审计 — 从指令流(精确解码)提取全部『mov reg, imm』且 imm ∈ [0xAA1000..0xAA1090]
base_loads = []
for ins in full:
    if ins.mnemonic == "mov":
        mm = re.match(r"^(e?[a-z]{2,3}), (0x[0-9a-f]+)$", ins.op_str)
        if mm and 0xAA1000 <= int(mm.group(2), 16) <= 0xAA1090:
            base_loads.append((ins.address, mm.group(1), int(mm.group(2), 16)))
# 允许的基址装载(逐一核实其解引用域不含 0xAA1078):
#  - 0x546064: this 装载(已知路径, 被 0x546069 消费, 无其它解引用)
#  - 0x5452BE: GROW 清理循环, 界 cmp esi, 0xAA1070 @0x5452D7 → 域 [0xAA1060..0xAA106C)
#  - 0x5472A2: 指针数组遍历, 界 cmp ecx, 0xAA103C @0x5472B4 → 域 [0xAA102C..0xAA1038)
#  - 0x547C9E: 指针数组遍历, 界 cmp ecx, 0xAA1040 @0x547CB3 → 域 [0xAA102C..0xAA103C)
ALLOWED_BASE = {
    0x546064: ("0x546069 消费, 无其它解引用", None),
    0x5452BE: ("cmp esi, 0xaa1070", 0x5452D7),
    0x5472A2: ("cmp ecx, 0xaa103c", 0x5472B4),
    0x547C9E: ("cmp ecx, 0xaa1040", 0x547CB3),
}
addr_idx = addr2idx
g4b_bad = []
for va, reg, imm in base_loads:
    if va not in ALLOWED_BASE:
        g4b_bad.append((hex(va), reg, hex(imm)))
        continue
    bound_txt, bound_va = ALLOWED_BASE[va]
    if bound_va is not None:
        ok = any("%s %s" % (i.mnemonic, i.op_str) == "cmp %s, %s" % (reg, bound_txt.split(", ")[1])
                 for i in full[addr_idx[va]: addr_idx[va] + 80] if i.address <= bound_va)
        if not ok:
            g4b_bad.append((hex(va), reg, hex(imm), "界断言缺失"))
print("[G4b] 基址立即数装载(mov reg, 0xAA10xx): %s" %
      [(hex(a), r, hex(v)) for a, r, v in base_loads])
check(not g4b_bad,
      "G4b: 基址装载全集 = {0x546064(this, 已知), 0x5452BE(域<0xAA1070), 0x5472A2(域<0xAA103C), "
      "0x547C9E(域<0xAA1040)}, 解引用域均不含 vptr 单元 0xAA1078 → 无别名合成路径装载 vptr",
      "G4b 失败: %s" % g4b_bad)
# 另附: .text 中全部 [0xAA1000..0xAA1090] 值出现(供人工复核, 含误解码风险标注)
near = []
for va in range(TSTART, TEND - 4):
    v = u32(va)
    if 0xAA1000 <= v <= 0xAA1090:
        near.append((va, v))
near_ctx = {}
for va, v in near:
    ins = insn_containing(va)
    near_ctx.setdefault(v, []).append(
        "%08X %s %s" % (ins.address, ins.mnemonic, ins.op_str) if ins else "%08X ?" % va)

# ----------------------------------------------------------------------------
# 6. 任务2: 全 .text call dword ptr [reg+8] 普查 + 每点回溯 20 条定类
# ----------------------------------------------------------------------------
SLOT2_RE = re.compile(r"^dword ptr \[([a-z]{2,3}) \+ (?:0x8|8)\]$")
VOLATILE = {"eax", "ecx", "edx"}

def indirect_census():
    """普查所有间接 call/jmp, 按形态分桶(验证没有漏掉异形 +8 派发)。"""
    shapes = {}
    for ins in full:
        if ins.mnemonic in ("call", "jmp") and "[" in ins.op_str:
            # 归一化寄存器与位移
            s = re.sub(r"0x[0-9a-f]+", "D", ins.op_str)
            s = re.sub(r"\b(e[a-z]x|e[sd]i|ebp|esp|ebx)\b", "R", s)
            shapes[s] = shapes.get(s, 0) + 1
    return shapes

census = indirect_census()
plus8_exotic = [(ins.mnemonic, ins.address, ins.op_str) for ins in full
                if ins.mnemonic in ("call", "jmp") and re.search(r"\+ 8\]", ins.op_str)
                and not SLOT2_RE.match(ins.op_str)]
print("[普查] 间接 call/jmp 形态桶(归一化): %s" %
      dict(sorted(census.items(), key=lambda kv: -kv[1])[:24]))
print("[普查] 含『+ 8]』但非单寄存器+8 的异形间接转移: %d 处 %s" % (
    len(plus8_exotic), [(hex(a), m, o) for m, a, o in plus8_exotic[:10]]))

def classify_def(ins, cur):
    """判定 ins 是否写 cur; 返回 (kind, payload, new_cur) 或 None。"""
    m, op = ins.mnemonic, ins.op_str
    if m == "mov":
        parts = op.split(", ", 1)
        if len(parts) != 2 or parts[0] != cur:
            return None
        dst, src = parts
        mm = re.match(r"^dword ptr \[(0x[0-9a-f]+)\]$", src)
        if mm:
            return ("vptr_of_imm", int(mm.group(1), 16), cur)
        if src == "dword ptr [" + cur + "]":
            return ("vptr_via_reg", None, cur)          # 装载 [cur] → vptr; 继续追 cur 作为对象指针
        mm = re.match(r"^dword ptr \[(e?[a-z]{2,3})(?: \+ (0x[0-9a-f]+|\d+))?\]$", src)
        if mm:
            base = mm.group(1)
            disp = int(mm.group(2), 16) if mm.group(2) else 0
            if base == "esp":
                return ("stack_src", disp, cur)
            if disp == 0 and base != cur:
                return ("deref_reg", None, base)        # [reg2] → vptr; 继续追 reg2
            return ("mem_of", (base, disp), cur)
        mm = re.match(r"^(e?[a-z]{2,3})$", src)
        if mm:
            r2 = mm.group(1)
            if r2 == cur:
                return ("self", None, cur)
            return ("copy", None, r2)
        mm = re.match(r"^(0x[0-9a-f]+|\d+)$", src)
        if mm:
            return ("imm", int(mm.group(1), 16 if mm.group(1).startswith("0x") else 10), cur)
        return ("mov_other", src, cur)
    if m == "lea":
        parts = op.split(", ", 1)
        if len(parts) == 2 and parts[0] == cur:
            mm = re.match(r"^\[(0x[0-9a-f]+)\]$", parts[1])
            if mm:
                return ("addr_of_imm", int(mm.group(1), 16), cur)
            return ("lea_other", parts[1], cur)
        return None
    if m == "pop" and op == cur:
        return ("pop", None, cur)
    if m == "xor" and op == cur + ", " + cur:
        return ("zero", None, cur)
    return None

def resolve_back(reg, idx, window=20):
    """从 site 前驱回溯 window 条, 解析 reg 的来源链。"""
    hops = []
    cur = reg
    for k in range(idx - 1, max(-1, idx - 1 - window), -1):
        ins = full[k]
        txt = "%s %s" % (ins.mnemonic, ins.op_str)
        if ins.mnemonic == "call" or (ins.mnemonic == "jmp" and ins.op_str.startswith("0x")
                                      and "[" not in ins.op_str):
            if cur in VOLATILE:
                return {"kind": "clobbered_by_call", "def_va": hex(ins.address), "def": txt,
                        "hops": hops, "calls_crossed": True}
            hops.append("cross %08X %s (callee-saved %s 保留)" % (ins.address, txt, cur))
            continue
        if ins.mnemonic == "push":
            hops.append("cross %08X push %s" % (ins.address, ins.op_str))
            continue
        r = classify_def(ins, cur)
        if r is None:
            continue
        kind, payload, new_cur = r
        hops.append("%08X %s" % (ins.address, txt))
        if kind in ("copy", "deref_reg"):
            cur = new_cur
            continue
        if kind in ("vptr_via_reg", "self"):
            continue                                     # vptr_via_reg: cur 仍为对象指针寄存器
        return {"kind": kind, "payload": payload, "def_va": hex(ins.address), "def": txt,
                "hops": hops, "calls_crossed": False}
    # 窗口耗尽仍未定义: 若最终追到的寄存器是 ecx(或最后被 push 的正是它) →
    # 外层函数的 thiscall this(经序言 push/mov esi,ecx 落栈的链) — 任务3的『函数参数』形态
    last_push_cur = any(h.endswith("push %s" % cur) for h in hops if h.startswith("cross "))
    kind = "thiscall_this_of_enclosing_fn" if (cur == "ecx" or last_push_cur) else "undef_in_window"
    return {"kind": kind, "def_va": None, "def": None, "hops": hops, "cur": cur,
            "calls_crossed": False}

# 全局『mov dword ptr [disp32], imm32』存储映射 + 『mov dword ptr [disp32], reg』存储清单
# (自指令流精确提取, 供对象 vtable 候选定位)
store_map = {}
reg_store_map = {}
for k, ins in enumerate(full):
    if ins.mnemonic == "mov":
        mm = re.match(r"^dword ptr \[(0x[0-9a-f]+)\], (0x[0-9a-f]+)$", ins.op_str)
        if mm:
            store_map.setdefault(int(mm.group(1), 16), set()).add(int(mm.group(2), 16))
            continue
        mm = re.match(r"^dword ptr \[(0x[0-9a-f]+)\], (e?[a-z]{2,3})$", ins.op_str)
        if mm:
            reg_store_map.setdefault(int(mm.group(1), 16), []).append((k, ins.address, mm.group(2)))

def is_vtable_like(v):
    return (sections[".rdata"]["va"] <= v < sections[".rdata"]["va"] + sections[".rdata"]["vsize"]
            and TSTART <= u32(v) < TEND)

def rtti_name_of_vtable(vt):
    """vtable → COL(.rdata) → TypeDescriptor(.data, MSVC 将 type_info 放 .data) → 类名; 无 RTTI 返回 None。"""
    try:
        col = u32(vt - 4)
        if not (sections[".rdata"]["va"] <= col < sections[".rdata"]["va"] + sections[".rdata"]["vsize"]):
            return None
        td = u32(col + 0x0C)
        if not (sections[".data"]["va"] <= td < sections[".data"]["va"] + sections[".data"]["vsize"]):
            return None
        nm = cstr(td + 8)
        return nm if nm.startswith(".?A") else None
    except Exception:
        return None

def resolve_reg_to_imm(idx, reg, back=8):
    """回溯 ≤back 条, 解析 reg 是否被装载为立即数(供 reg 间接存储的 vtable 定位)。"""
    for k in range(idx - 1, max(-1, idx - 1 - back), -1):
        ins = full[k]
        if ins.mnemonic == "mov":
            mm = re.match(r"^(e?[a-z]{2,3}), (0x[0-9a-f]+)$", ins.op_str)
            if mm and mm.group(1) == reg:
                return int(mm.group(2), 16)
            if mm and mm.group(1) != reg:
                continue
    return None

_vt_cand_cache = {}
def vtable_candidates_of_object(A):
    """报告用途: 定位对象 A 的 vptr 候选(静态值 / 绝对地址存储 / reg 间接存储), 附 RTTI 类名。"""
    if A in _vt_cand_cache:
        return _vt_cand_cache[A]
    cands = []
    for name in (".data", ".rdata"):
        sec = sections[name]
        if sec["va"] <= A < sec["va"] + sec["vsize"]:
            v = u32(A)
            if is_vtable_like(v):
                cands.append(("static-init", v, rtti_name_of_vtable(v)))
    for v in store_map.get(A, ()):
        if is_vtable_like(v):
            cands.append(("imm-store", v, rtti_name_of_vtable(v)))
    for k, va, reg in reg_store_map.get(A, ())[:8]:
        v = resolve_reg_to_imm(k, reg)
        if v is not None and is_vtable_like(v):
            cands.append(("reg-store@%08X" % va, v, rtti_name_of_vtable(v)))
    _vt_cand_cache[A] = cands
    return cands

# 收集全部 slot2 形态点 (call + jmp)
sites = []
for k, ins in enumerate(full):
    mm = SLOT2_RE.match(ins.op_str)
    if mm and ins.mnemonic in ("call", "jmp"):
        sites.append((k, ins, mm.group(1)))
print("[普查] call/jmp dword ptr [reg + 8] 共 %d 处 (call %d, jmp %d)" % (
    len(sites), sum(1 for _, i, _ in sites if i.mnemonic == "call"),
    sum(1 for _, i, _ in sites if i.mnemonic == "jmp")))

site_records = []
kept = []
for k, ins, reg in sites:
    res = resolve_back(reg, k)
    rec = {"va": hex(ins.address), "kind": ins.mnemonic, "insn": "%s %s" % (ins.mnemonic, ins.op_str),
           "reg": reg, "bottom": res}
    # 回溯窗是否跨停点(漂移风险标记)
    lo = max(TSTART, ins.address - 120)
    rec["restart_in_window"] = any(lo <= r <= ins.address for r in restart_set)
    rec["enclosing_fn_approx"] = enclosing_fn_approx(ins.address)
    # 判定
    verdict = None
    reason = None
    if ins.address == 0x546069:
        verdict, reason = "CANDIDATE", "全局唯一 vptr 装载点(0x54605F)的唯一直接消费者; reg=eax=[0xAA1078]"
    elif res["kind"] == "vptr_of_imm" and res["payload"] == GLOBAL_OBJ:
        verdict, reason = "CANDIDATE", "reg 装载自 [0xAA1078]"
    else:
        verdict = "EXCLUDED"
        if res["kind"] == "vptr_of_imm":
            A = res["payload"]
            cands = vtable_candidates_of_object(A)
            cands_s = "; ".join("%s→0x%X(%s)" % (c[0], c[1], c[2] or "?") for c in cands) \
                if cands else "未能静态定位(排除仍由值闸门成立)"
            reason = ("reg ← [0x%X] (对象/结构 0x%X, vptr 候选: %s); 该单元不可能是 0x7ECBFC/0x7ECBDC:"
                      " 全镜像仅 4 条 c7 存储携带这两个值且目标均为 [0xAA1078] (G2/G3)" % (
                          A, A, cands_s))
        elif res["kind"] in ("mem_of", "deref_reg"):
            reason = ("reg ← 指针场/解引用链 (%s); 该值要成为派发基必须是 0x7ECBFC/0x7ECBDC 本身, "
                      "而全镜像无任何指令向 [0xAA1078] 之外的单元写入这两个值 (G2/G3/G5)" % (
                          res.get("def") or res["kind"]))
        elif res["kind"] == "stack_src":
            reason = ("reg ← 栈槽 [esp+0x%X] (调用方传入/本函数局部); 调用方亦无法产生该值 — 全模块唯一"
                      " 的 vptr 值源是 0x54605F 的装载且不逃逸出其函数 (G4/G6)" % res["payload"])
        elif res["kind"] == "clobbered_by_call":
            reason = ("reg 为易失寄存器且链跨 call (%s); 被调方返回值亦不可能是 0x7ECBFC/0x7ECBDC"
                      " — 唯一值源 0x54605F 不逃逸 (G4/G6)" % res["def"])
        elif res["kind"] == "thiscall_this_of_enclosing_fn":
            reason = ("reg ← 外层函数(≈%s)的 thiscall this(序言 push/mov esi,ecx 链, 任务3『函数参数』"
                      "形态); 该 this 不可能是 0xAA1078 — 无任何指针值逃逸出 GROW (G4/G5/G6), 且"
                      "除全局外不存在本类的第二实例 (G3 归纳)" % (res.get("cur") and enclosing_fn_approx(ins.address)))
        elif res["kind"] == "undef_in_window":
            reason = ("定义点超出 20 条回溯窗 (跨 call: %s); 排除依据为全局值闸门而非局部链" %
                      res["calls_crossed"])
        elif res["kind"] == "pop":
            reason = ("reg ← pop (栈值, 调用方/序言来源); 排除依据同上 — 全局值闸门 (G2/G4/G6)")
        elif res["kind"] == "zero":
            reason = "reg=0 (xor) → 派发基为 0, 非任何 vptr"
        elif res["kind"] in ("imm", "addr_of_imm"):
            P = res["payload"]
            d = None
            try:
                d = u32(P + SLOT2)
            except Exception:
                pass
            reason = ("reg = 立即数/取址 0x%X → 派发读 [0x%X+8]=%s (静态值); 无任何指令向内存写"
                      " 0x54A4F0/0x54A630 (G1) → 不可能命中" % (
                          P, P, hex(d) if d is not None else "越界"))
        else:
            reason = ("reg 来源形 (%s @%s) 经全局值闸门排除: 寄存器不可能持有 0x7ECBFC/0x7ECBDC"
                      " 除非装载自 [0xAA1078], 而该装载全模块仅 0x54605F 一处 (G2/G4)" % (
                          res["kind"], res.get("def_va")))
    rec["verdict"] = verdict
    rec["reason"] = reason
    site_records.append(rec)
    if verdict == "CANDIDATE":
        kept.append(rec)

n_cand = sum(1 for r in site_records if r["verdict"] == "CANDIDATE")
check(n_cand == 1 and kept[0]["va"] == "0x546069",
      "普查结论: %d 个 slot2 形态点中, 可能指向 0x54A4F0/0x54A630 的仅 1 个: 0x546069" % len(site_records),
      "候选点数异常: %d → %s" % (n_cand, [r["va"] for r in kept]))

# 异形 +8 索引派发 (call dword ptr [reg + reg*4 + 8]) — CRT SEH 展开器, 单独定类
exotic_records = []
for m, a, o in plus8_exotic:
    if m != "call":
        continue
    # 归属确认: 所在函数是否为 SEH 展开器(入口 push 0x7CC0FC 处理器 / fs:[0] 链)
    seh_anchor = any(i.address == 0x7CC0FC for i in full[addr2idx[a] - 400: addr2idx[a]]) if \
        a in addr2idx else False
    seh_ref = image_dwords_equal(0x7CC0FC)
    rec = {"va": hex(a), "kind": m, "insn": "%s %s" % (m, o), "form": "indirect-other",
           "verdict": "EXCLUDED",
           "reason": ("CRT SEH 帧展开器(0x7CC11E 起, 处理器 0x7CC0FC, fs:[0] 链)的内层表派发; "
                      "基址寄存器 = 展开链节点字段(ebx=[eax+8]/edi 经同族代码), 非 vptr。命中 0x54A4F0 "
                      "需有效地址恰为 0x7ECC04 且该单元含 0x54A4F0 — G1 已证全镜像仅此一单元含该值, "
                      "而基址值不可能为 0x7ECBxx(G2/G4: 寄存器只能从 [0xAA1078] 装载获得该族值)"),
           "seh_handler_refs": [hex(x) for x in seh_ref]}
    exotic_records.append(rec)
    print("[异形] %08X %s → %s" % (a, o, "SEH 展开器(排除)" if seh_ref else "未定类"))

# ----------------------------------------------------------------------------
# 7. 任务3/4: 候选点 this 追踪 + GROW 函数主体 + 逃逸检查 (G6)
# ----------------------------------------------------------------------------
# GROW = 包含 0x54605F/0x546064/0x546069 的函数
TARGET_LOAD = 0x54605F
cand_starts = set()
for va in range(TSTART, TARGET_LOAD):
    if image[va - IB] in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", image, va - IB + 1)[0]
        t = va + 5 + rel
        if TSTART <= t <= TARGET_LOAD:
            cand_starts.add(t)
def stream_reaches(start, target, budget=8000):
    n = 0
    for ins in md.disasm(bytes(image[start - IB: target - IB + 64]), start):
        n += 1
        if ins.address == target:
            return True, n
        if n > budget:
            break
    return False, n
grow_start = None
for s in sorted(cand_starts, reverse=True):
    ok, _ = stream_reaches(s, TARGET_LOAD)
    if ok:
        grow_start = s
        break
# 函数尾: 派发之后首个 ret (线性, 无漂移前提)
grow_body = list(md.disasm(bytes(image[grow_start - IB: TEND - IB]), grow_start))
grow_ret = None
for ins in grow_body:
    if ins.address > 0x54609A and ins.mnemonic.startswith("ret"):
        grow_ret = ins.address
        break
grow_end = grow_ret + 2 if grow_ret else None
check(grow_start is not None and grow_ret is not None,
      "GROW (包含装载/派发的函数): 0x%X..0x%X (call-目标可达 + 派发后首个 ret)" % (
          grow_start, grow_ret if grow_ret else 0),
      "GROW 起点或终点定位失败: start=%s ret=%s" % (grow_start, grow_ret))
in_grow_restarts = [r for r in restart_set if grow_start <= r <= grow_ret]
check(not in_grow_restarts,
      "GROW 函数体区间内无 capstone 停点 → 上述线性可达性与 ret 定位无漂移干扰",
      "GROW 区间内存在停点(漂移风险): %s" % [hex(x) for x in in_grow_restarts])
grow_slot2 = [r for r in site_records if grow_start <= int(r["va"], 16) <= grow_ret]
check(len(grow_slot2) == 1 and grow_slot2[0]["va"] == "0x546069",
      "GROW 体内 slot2 形态点恰 1 个 = 0x546069 (本函数其余间接转移均非 +8 形态)",
      "GROW 体内 slot2 点异常: %s" % [r["va"] for r in grow_slot2])

# G6: 装载→派发窗口的逃逸检查 (0x54605F..0x546069, 恰 3 条指令)
win = list(md.disasm(bytes(image[TARGET_LOAD - IB: 0x54606C - IB]), TARGET_LOAD))
win_txt = ["%s %s" % (i.mnemonic, i.op_str) for i in win]
escape = [w for w in win_txt if re.match(r"^(push |mov dword ptr \[|lea )", w)]
check(win_txt == ["mov eax, dword ptr [0xaa1078]", "mov ecx, 0xaa1078",
                  "call dword ptr [eax + 8]"] and not escape,
      "G6: 0x54605F..0x546069 = %s — 装载与派发之间无 store/push/call, ecx/eax 的对象指针与 vptr "
      "值不逃逸; 派发后立即被覆写 (0x546070 mov ecx,[0xAA1088]; 0x54608C mov eax,[esp+0x30])" %
      " ; ".join(win_txt),
      "G6 失败: 窗口 %s, 疑似逃逸 %s" % (win_txt, escape))

# 派发尾部完整语义 (this/vptr/参数/返回)
tail = list(md.disasm(bytes(image[0x546030 - IB: 0x546092 - IB]), 0x546030))
tail_txt = [{"va": hex(i.address), "insn": "%s %s" % (i.mnemonic, i.op_str)} for i in tail]
has_push_args = any(t["va"] == "0x54605c" and t["insn"] == "push 0" for t in tail_txt) and \
    any(t["va"] == "0x54605e" and t["insn"] == "push eax" for t in tail_txt)
has_test_al = any(t["va"] == "0x54606c" and t["insn"] == "test al, al" for t in tail_txt)
check(has_push_args and has_test_al,
      "派发语义: push 0; push eax(新容量=[0xAA1080]+[0xAA108C], @0x546030/0x546050/0x54605A 计算) "
      "→ Capacity(int, T*) 返回 bool (0x54606C test al,al; 0x54606E je 0x54608C); 成功则 "
      "ActiveCount++ 并写 Vector[ActiveCount] (@0x546070..0x546089)",
      "派发尾部语义断言失败")

# GROW 的直接调用者(上下文记录)
grow_callers = [hex(va) for va, kind in byte_e8e9_targets(grow_start) if kind == "call"]
print("[上下文] GROW 0x%X 的直接调用者: %s" % (grow_start, grow_callers))

# ----------------------------------------------------------------------------
# 8. 汇总
# ----------------------------------------------------------------------------
from collections import Counter
bottom_dist = Counter(r["bottom"]["kind"] for r in site_records)
excl_by_kind = Counter((r["bottom"]["kind"], r["verdict"]) for r in site_records)

result = {
    "identity": {"sha256": sha, "size": len(raw), "exe": EXE_PATH,
                 "script": os.path.abspath(__file__)},
    "disasm": {
        "single_pass": {"count": len(single), "last_va": hex(single_last),
                        "note": "capstone 单次 disasm 截断复现 (ask 已知陷阱)"},
        "chunked": {"count": len(full), "restarts": len(restarts),
                    "coverage_end": hex(cov_end), "restart_vas": [hex(x) for x in restarts]},
    },
    "premises": {
        "vtable_base": hex(VT_BASE), "vtable_der": hex(VT_DER),
        "slot2_base": hex(u32(VT_BASE + SLOT2)), "slot2_der": hex(u32(VT_DER + SLOT2)),
        "global_obj": hex(GLOBAL_OBJ),
    },
    "task1_direct_callers": direct,
    "gate": {
        "G1_ptr_refs": {hex(k): [hex(x) for x in v] for k, v in r_fn.items()},
        "G2_value_refs": {hex(k): [hex(x) for x in v] for k, v in r_vt.items()},
        "G2_contexts": g2_desc,
        "G3_vptr_stores": {"0x7ECBFC": [hex(x) for x in stores_base],
                           "0x7ECBDC": [hex(x) for x in stores_der]},
        "G4_imm_refs_0xAA1078": [hex(x) for x in refs_g],
        "G4_contexts": g4_ctx,
        "G4b_alias_audit": {hex(v): ctxs for v, ctxs in sorted(near_ctx.items())},
        "G5_ptr_vars_to_global": {k: [hex(x) for x in v] for k, v in ptr_hits.items()},
        "G6_escape_check": {"window_0x54605F_0x546069": win_txt, "escapes": escape},
        "dtor_direct_xrefs": {hex(k): [(hex(a), kd) for a, kd in v] for k, v in dtor_xrefs.items()},
    },
    "indirect_census_top": dict(sorted(census.items(), key=lambda kv: -kv[1])[:24]),
    "plus8_exotic": [(m, hex(a), o) for m, a, o in plus8_exotic],
    "exotic_records": exotic_records,
    "sites": site_records,
    "sites_summary": {
        "total": len(site_records),
        "by_bottom_kind": dict(bottom_dist),
        "candidates": [r["va"] for r in kept],
        "excluded": len(site_records) - len(kept),
    },
    "grow": {
        "start": hex(grow_start), "ret": hex(grow_ret) if grow_ret else None,
        "restarts_inside": [hex(x) for x in in_grow_restarts],
        "slot2_sites_inside": [r["va"] for r in grow_slot2],
        "dispatch_tail": tail_txt,
        "direct_callers": grow_callers,
    },
    "candidate_detail": {
        "va": "0x546069",
        "insn": "call dword ptr [eax + 8]",
        "form": "vtable-slot2",
        "this_source": ("ecx ← 0x546064 mov ecx, 0xAA1078 (imm32 直接装载 — 非参数、非栈、非寄存器"
                        "继承); 该 imm32 是全镜像 4 处 0xAA1078 引用中唯一的 this 装载"),
        "vptr_source": "eax ← 0x54605F mov eax, dword ptr [0xAA1078] (对象 vptr 单元)",
        "args": "push 0 (0x54605C); push eax=新容量 ([0xAA1080]VectorMax+[0xAA108C]GrowthStep, "
                "0x546030/0x546050/0x54605A)",
        "ret_use": "0x54606C test al, al; 0x54606E je 0x54608C (bool → 追加与否)",
        "dispatch_by_lifecycle": {
            "normal (vptr=0x7ECBDC, 动态初始化器 0x543E8D)": "0x54A630 (DynamicVectorClass<PAUTileInsertType>::Capacity)",
            "post-atexit (vptr=0x7ECBFC, 0x543EBE 置于 0x543EB0 atexit 析构器, 永久)": "0x54A4F0 (VectorClass<PAUTileInsertType*>::Capacity)",
        },
        "escape": "无 — 指针/vptr 值不逃逸出 GROW, 派发后立即被覆写",
        "confidence": "HIGH",
    },
    "crosschecks": notes,
}

out_txt_path = os.path.join(OUT_DIR, "_et_sites_out.txt")
out_json_path = os.path.join(OUT_DIR, "_et_sites_out.json")

L = []
L.append("=" * 100)
L.append("gamemd.exe — 全 .text「call dword ptr [reg+8]」普查与 slot2 候选定类 (只读, pefile+capstone)")
L.append("文件: %s" % EXE_PATH)
L.append("sha256: %s  size: %d B" % (sha, len(raw)))
L.append("=" * 100)
L.append("")
L.append("[反汇编覆盖]")
L.append("  单次 disasm: %d 条, 末条 VA 0x%X — 复现 ask 已知陷阱(台账『155215 条 / RVA 0x6F59D 截断』)" % (
    len(single), single_last))
L.append("  分块扫描  : %d 条, %d 个停点, 覆盖至 0x%X (全 .text)" % (
    len(full), len(restarts), cov_end))
L.append("")
L.append("[任务1] 直接调用者复核 (0x54A4F0 与孪生 0x54A630)")
for tgt, d in direct.items():
    L.append("  call/jmp → 0x%08X : 指令级 %d 处 %s ; 字节级 E8/E9 %d 处 %s" % (
        tgt, len(d["insn_level"]), d["insn_level"], len(d["byte_level"]), d["byte_level"]))
L.append("  → 两者均为 0, 两种独立方法一致 — ask 前提复现。")
L.append("")
L.append("[全局值闸门 — 排除其余 %d 个 slot2 形态点的依据]" % (len(site_records) - len(kept)))
for n in notes:
    if n["text"].startswith("G"):
        L.append("  %s" % n["text"])
L.append("")
L.append("[任务2] slot2 形态普查")
L.append("  call/jmp dword ptr [reg+8] 共 %d 处; 底源分布: %s" % (
    len(site_records), dict(bottom_dist)))
L.append("  含『+ 8]』的异形间接转移(非单寄存器+8): %d 处" % len(plus8_exotic))
for r in exotic_records:
    L.append("    %s %s → %s" % (r["va"], r["insn"], r["verdict"]))
    L.append("        %s" % r["reason"])
L.append("")
L.append("[任务3/4] 候选点 (可能指向 0x54A4F0 / 0x54A630)")
for r in kept:
    L.append("  ★ %s  %s" % (r["va"], r["insn"]))
    L.append("      form        : vtable-slot2")
    L.append("      this 来源   : ecx = 0xAA1078 (0x546064 mov ecx, 0xaa1078 — 全镜像唯一 this 装载)")
    L.append("      vptr 来源   : eax = [0xAA1078] (0x54605F) — 全镜像唯一 vptr 装载")
    L.append("      参数        : push 0; push eax(=VectorMax+GrowthStep) → Capacity(int, T*) → bool")
    L.append("      派发去向    : vptr=0x7ECBDC(常态) → 0x54A630 ; vptr=0x7ECBFC(atexit 0x543EB0 之后, 永久) → 0x54A4F0")
    L.append("      逃逸检查    : 装载→派发窗口无 store/push/call; 派发后 eax/ecx 立即被覆写")
    L.append("      可信度      : HIGH (六个闸门腿全部当场验证, 无 MISMATCH)")
L.append("")
L.append("[候选点所在函数 GROW]")
L.append("  0x%X..0x%X (ret@0x%X), 函数体内无 capstone 停点; 体内 slot2 点恰 1 个 (0x546069)" % (
    grow_start, grow_end, grow_ret))
L.append("  GROW 直接调用者: %s" % grow_callers)
L.append("")
L.append("[全部 %d 个 slot2 形态点清单 (va / kind / reg / 底源 / 判定)]" % len(site_records))
for r in site_records:
    bot = r["bottom"]
    L.append("  %s %-4s %-4s %-18s %s | %s" % (
        r["va"], r["kind"], r["reg"], bot["kind"], r["verdict"],
        (bot.get("def") or bot.get("def_va") or "")))
L.append("")
L.append("[交叉断言]")
for n in notes:
    L.append("  [%s] %s" % (n["kind"], n["text"]))

with open(out_txt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("\nWROTE %s" % out_txt_path)
print("WROTE %s" % out_json_path)
mism = [n for n in notes if n["kind"] == "MISMATCH"]
print("MISMATCH count: %d" % len(mism))
sys.exit(0 if not mism else 1)
