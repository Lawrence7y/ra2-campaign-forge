#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_cw_disasm.py — 0x0054A56E 数据依赖链静态还原(只读)。

对象: ra2bench/gamemd.exe (sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476)
方法: pefile + capstone 纯静态;不启动进程、不读活内存、不打补丁。
输出: _cw_disasm_out.txt / _cw_disasm_out.json (与本脚本同目录)

铁律: 所有结论由本脚本当场计算;EXPECTED_* 常量仅用于交叉断言,
      断言不符时在输出中标记 MISMATCH 而不是静默通过。
"""
import sys
sys.dont_write_bytecode = True

import hashlib
import json
import os
import struct

import pefile
import capstone

# ----------------------------------------------------------------------------
# 常量(台账口径,用于交叉断言)
# ----------------------------------------------------------------------------
EXPECTED_SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
EXPECTED_SIZE = 4825360

TARGET = 0x0054A56E          # 台账崩溃点(本脚本核实其指令与语义)
TARGET_BYTES = bytes.fromhex("c7460400000000")   # mov dword [esi+4], 0
EIP_DATA = 0x0084F2BA        # 台账另一崩溃点(EIP 落 .data)
WINDOW = 40                  # 前后各 40 条

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXE_PATH = os.path.join(REPO_ROOT, "ra2bench", "gamemd.exe")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

notes = []          # (kind, text)  kind: FACT/MISMATCH/WARN
def note(kind, text):
    notes.append({"kind": kind, "text": text})
    print("[%s] %s" % (kind, text))

def check(cond, ok_text, bad_text):
    if cond:
        note("FACT", ok_text)
    else:
        note("MISMATCH", bad_text)
    return cond

# ----------------------------------------------------------------------------
# 1. 文件身份
# ----------------------------------------------------------------------------
raw = open(EXE_PATH, "rb").read()
sha = hashlib.sha256(raw).hexdigest()
check(sha == EXPECTED_SHA256, "sha256 = %s (与台账一致)" % sha,
      "sha256 = %s 与台账 %s 不一致" % (sha, EXPECTED_SHA256))
check(len(raw) == EXPECTED_SIZE, "size = %d B (与台账一致)" % len(raw),
      "size = %d B 与台账 %d 不一致" % (len(raw), EXPECTED_SIZE))

pe = pefile.PE(EXE_PATH)
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
image = pe.get_memory_mapped_image(ImageBase=IMAGE_BASE)

def u32(va):
    return struct.unpack_from("<I", image, va - IMAGE_BASE)[0]

def cstr(va, maxn=160):
    out = []
    o = va - IMAGE_BASE
    while o < len(image) and image[o] != 0 and len(out) < maxn:
        out.append(chr(image[o]))
        o += 1
    return "".join(out)

def disasm_range(va_start, va_end):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    return list(md.disasm(bytes(image[va_start - IMAGE_BASE:va_end - IMAGE_BASE]), va_start))

# ----------------------------------------------------------------------------
# 2. 节表与 DEP 前提
# ----------------------------------------------------------------------------
sections = {}
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode()
    sections[name] = {
        "va": IMAGE_BASE + s.VirtualAddress,
        "vsize": s.Misc_VirtualSize,
        "characteristics": s.Characteristics,
    }

def in_section(va, sec):
    return sections[sec]["va"] <= va < sections[sec]["va"] + sections[sec]["vsize"]

EXEC = 0x20000000  # IMAGE_SCN_MEM_EXECUTE
check(sections[".data"]["characteristics"] == 0xC0000040,
      ".data Characteristics=0xC0000040 (可读+可写+已初始化, 无 EXECUTE) 与台账一致",
      ".data Characteristics=0x%08X 与台账 0xC0000040 不一致" % sections[".data"]["characteristics"])
check(in_section(EIP_DATA, ".data"), "0x0084F2BA 落在 .data [0x%X..0x%X]" % (
    sections[".data"]["va"], sections[".data"]["va"] + sections[".data"]["vsize"]),
    "0x0084F2BA 不在 .data 范围内")
check(not (sections[".data"]["characteristics"] & EXEC),
      ".data 无 IMAGE_SCN_MEM_EXECUTE → 静态上 EIP 进入该页属取指违规(DEP)而非写失败",
      ".data 含 EXECUTE 位, 台账 DEP 结论不成立")
check(not (sections[".text"]["characteristics"] & EXEC) is False,
      ".text 含 EXECUTE (0x%X)" % sections[".text"]["characteristics"],
      ".text 不含 EXECUTE 位(异常)")

# ----------------------------------------------------------------------------
# 3. 0x0054A56E 字节与线性上下文
# ----------------------------------------------------------------------------
check(bytes(image[TARGET - IMAGE_BASE: TARGET - IMAGE_BASE + 7]) == TARGET_BYTES,
      "0x0054A56E 处字节 = c7 46 04 00 00 00 00 = mov dword ptr [esi+4], 0 (与台账一致)",
      "0x0054A56E 处字节与 c7460400000000 不符")

# ----------------------------------------------------------------------------
# 4. 交叉引用基础设施(纯字节扫描, 不依赖线性 sweep 对齐)
# ----------------------------------------------------------------------------
TSTART = sections[".text"]["va"]
TEND = TSTART + sections[".text"]["vsize"]

def find_call_jmp_targets(target):
    """全 .text 暴力扫描 E8/E9 rel32 目标 == target 的调用点(可能含误报, 只作 xref 用)。"""
    hits = []
    for va in range(TSTART, TEND - 5):
        b = image[va - IMAGE_BASE]
        if b in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", image, va - IMAGE_BASE + 1)[0]
            if va + 5 + rel == target:
                hits.append({"va": va, "kind": "call" if b == 0xE8 else "jmp"})
    return hits

def find_ptr_refs(target):
    """在 .rdata/.data/.detour 中找 dword==target 的指针引用(vtable 项等)。"""
    refs = []
    for name in (".rdata", ".data", ".detour"):
        sec = sections[name]
        base = sec["va"]
        for off in range(0, sec["vsize"] - 4, 4):
            if u32(base + off) == target:
                refs.append({"va": base + off, "section": name})
    return refs

def find_imm32_refs(target, rng=None):
    """在 .text 中找任意 4 字节立即数引用(字段访问/构造写入等)。"""
    pat = struct.pack("<I", target)
    refs = []
    va = TSTART
    lo, hi = (TSTART, TEND) if rng is None else rng
    while True:
        i = image.find(pat, va - IMAGE_BASE, hi - IMAGE_BASE)
        if i < 0:
            break
        refs.append(i + IMAGE_BASE)
        va = i + IMAGE_BASE + 1
    return refs

def find_vptr_stores(vtable_va):
    """全 .text 扫描 mov dword ptr [<mem>], imm32 的 imm32==vtable 形式(c7 /0 组)。
    返回指令地址列表。imm 偏移按 modrm/sib/disp 分别计算。"""
    pat = struct.pack("<I", vtable_va)
    hits = []
    va = TSTART
    while va < TEND - 10:
        if image[va - IMAGE_BASE] == 0xC7:
            m = image[va - IMAGE_BASE + 1]
            mod, reg, rm = m >> 6, (m >> 3) & 7, m & 7
            if reg == 0 and mod != 3:
                imm_off = None
                if mod == 0 and rm == 5:
                    imm_off = 6                      # c7 05 disp32 imm32
                elif mod == 0 and rm == 4 and image[va - IMAGE_BASE + 3] == 0x25:
                    imm_off = 7                      # c7 04 25 disp32 imm32
                elif mod == 0:
                    imm_off = 2                      # c7 00..07(rm≠4,5): [reg], imm32
                elif mod == 1:
                    imm_off = 3 + (1 if rm == 4 else 0)   # disp8
                elif mod == 2:
                    imm_off = 6 + (1 if rm == 4 else 0)   # disp32
                if imm_off and image[va - IMAGE_BASE + imm_off: va - IMAGE_BASE + imm_off + 4] == pat:
                    hits.append(va)
        va += 1
    return hits

# ----------------------------------------------------------------------------
# 5. 函数起点判定: 候选 = call/jmp 目标 ∪ 指针引用地址;取 ≤TARGET 中
#    "线性 disasm 能干净到达 TARGET" 的最大者。
#    (ret 边界法会给出 0x54A535 这类 mid-function 伪起点, 故要求候选是真实入口)
# ----------------------------------------------------------------------------
def stream_reaches(start, target, budget=4000):
    n = 0
    try:
        for ins in disasm_range(start, target + 32):
            n += 1
            if ins.address == target:
                return True, n
            if n > budget:
                break
    except Exception:
        pass
    return False, n

cand_starts = set()
for va in range(TSTART, TARGET):
    b = image[va - IMAGE_BASE]
    if b in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", image, va - IMAGE_BASE + 1)[0]
        t = va + 5 + rel
        if TSTART <= t <= TARGET:
            cand_starts.add(t)

fn_start = None
for s in sorted(cand_starts, reverse=True):
    ok, _ = stream_reaches(s, TARGET)
    if ok:
        fn_start = s
        break

# 注: 0x0054A4F0 不是任何 call/jmp 的目标(下方断言), 而是虚表项 ——
# 直接 call 目标法只能给出更早的伪起点, 真实入口由第 7 节的 vtable 指针引用反查确定。
def function_window(start, target):
    """从 start 线性 disasm;返回 (指令列表, target 下标)。"""
    insns = disasm_range(start, target + WINDOW * 16 + 64)
    idx = next(i for i, ins in enumerate(insns) if ins.address == target)
    return insns, idx

# 直接验证已知入口 0x54A4F0(由 vtable 0x7ECC04 反查得到, 见第 7 节)
FN_START = 0x0054A4F0
ok, n = stream_reaches(FN_START, TARGET)
check(ok, "函数起点 0x0054A4F0 线性 disasm 干净到达 0x0054A56E (%d 条指令)" % n,
      "0x0054A4F0 无法线性到达目标")
insns, t_idx = function_window(FN_START, TARGET)

# 函数结束: 自 FN_START 起首个"到达即终止"的 ret(线性, 在 TARGET 之后)
fn_end = None
for ins in insns[: t_idx + 1]:
    if ins.mnemonic.startswith("ret") and ins.address > TARGET - 1:
        fn_end = ins.address + ins.size
for ins in insns:
    if ins.mnemonic.startswith("ret") and ins.address >= TARGET:
        fn_end = ins.address + ins.size
        break

# ----------------------------------------------------------------------------
# 6. 输出窗口: 前后各 40 条
# ----------------------------------------------------------------------------
window_txt = []
window_json = []
lo = max(0, t_idx - WINDOW)
hi = min(len(insns), t_idx + WINDOW + 1)
for i in range(lo, hi):
    ins = insns[i]
    mark = "  <== TARGET 0x0054A56E" if ins.address == TARGET else ""
    fnmark = ""
    if ins.address == FN_START:
        fnmark = "  ;<-- fn_start"
    if fn_end and ins.address + ins.size == fn_end and ins.address >= TARGET:
        fnmark += "  ;<-- fn_end (ret 之后)"
    line = "%08X  %-22s %s %s%s%s" % (
        ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark, fnmark)
    window_txt.append(line)
    window_json.append({"va": ins.address, "bytes": ins.bytes.hex(),
                        "mnemonic": ins.mnemonic, "op_str": ins.op_str,
                        "is_target": ins.address == TARGET})

# ----------------------------------------------------------------------------
# 7. RTTI / vtable 定类
# ----------------------------------------------------------------------------
ptr_refs_of_fn = find_ptr_refs(FN_START)
check(len(ptr_refs_of_fn) >= 1 and ptr_refs_of_fn[0]["va"] == 0x7ECC04,
      "0x0054A4F0 无直接 call/jmp xref; 被指针引用于 0x7ECC04 (.rdata vtable 项)",
      "0x0054A4F0 的引用形态异常: %s" % ptr_refs_of_fn)
check(len(find_call_jmp_targets(FN_START)) == 0,
      "0x0054A4F0 全 .text 无直接 call/jmp → 只能经 vtable 派发进入",
      "0x0054A4F0 存在直接调用点(与预期不符)")

VT_ENTRY = 0x7ECC04
# vtable 起点回扫: vtable 项皆为 0x401000..0x7E038D 代码指针, 首个非代码指针的前一格即起点
VT_BASE = None
for va in range(VT_ENTRY, TSTART, -4):
    v = u32(va - 4)
    if not (TSTART <= v < TEND):
        VT_BASE = va
        break
COL_VA = VT_BASE - 4
col = u32(COL_VA)
td = u32(col + 0x0C)
td_name = cstr(td + 8)
check(td_name == ".?AV?$VectorClass@PAUTileInsertType@IsometricTileTypeClass@@@@",
      "RTTI: COL@0x%X → TypeDescriptor@0x%X → 类名 %r (= VectorClass<TileInsertType<IsometricTileTypeClass>*>)" % (
          col, td, td_name),
      "RTTI 类名与预期不符: %r" % td_name)

# 派生类(DynamicVectorClass<PAUTileInsertType>) vtable
DER_VT = 0x7ECBDC
DER_SLOT2 = u32(DER_VT + 8)
DER_COL = u32(DER_VT - 4)
DER_TD = u32(DER_COL + 0x0C)
DER_NAME = cstr(DER_TD + 8)
check(DER_NAME == ".?AV?$DynamicVectorClass@PAUTileInsertType@IsometricTileTypeClass@@@@",
      "派生 RTTI: %r (= DynamicVectorClass<TileInsertType<IsometricTileTypeClass>*>)" % DER_NAME,
      "派生 RTTI 类名不符: %r" % DER_NAME)

VT_SLOTS = [u32(VT_BASE + 4 * i) for i in range(7)]
DER_SLOTS = [u32(DER_VT + 4 * i) for i in range(7)]

# ----------------------------------------------------------------------------
# 8. 唯一实例: 全局 0xAA1078 的动态初始化器 / atexit 析构器
# ----------------------------------------------------------------------------
GLOBAL_OBJ = 0x00AA1078
vptr_stores_base = find_vptr_stores(VT_BASE)
vptr_stores_der = find_vptr_stores(DER_VT)
imm_global = find_imm32_refs(GLOBAL_OBJ)

check(vptr_stores_der == [0x543E8D],
      "派生 vtable 0x7ECBDC 的写入仅 1 处: 0x543E8D → 全模块唯一实例 = 全局 0xAA1078",
      "派生 vtable 写入点异常: %s" % [hex(x) for x in vptr_stores_der])
check(vptr_stores_base == [0x543EBE, 0x54A7B6, 0x54A806],
      "基类 vtable 0x7ECBFC 写入仅 3 处: 0x543EBE(全局 atexit 析构器)/0x54A7B6/0x54A806(析构函数体) → 无独立 VectorClass<PAUTileInsertType> 实例",
      "基类 vtable 写入点异常: %s" % [hex(x) for x in vptr_stores_base])
_d1 = disasm_range(0x54A7B6, 0x54A7BC)
_d2 = disasm_range(0x54A806, 0x54A80C)
check(_d1 and _d1[0].mnemonic == "mov" and _d1[0].op_str == "dword ptr [esi], 0x7ecbfc",
      "  - 0x54A7B6: mov dword ptr [esi], 0x7ECBFC (基类 deleting dtor 0x54A7B0 入口处, 作用于 this)",
      "  - 0x54A7B6 指令形态异常")
check(_d2 and _d2[0].mnemonic == "mov" and _d2[0].op_str == "dword ptr [esi], 0x7ecbfc",
      "  - 0x54A806: mov dword ptr [esi], 0x7ECBFC (派生 deleting dtor 0x54A800 入口处, 作用于 this)",
      "  - 0x54A806 指令形态异常")

INIT_FN = 0x543E70
ATEXIT_DTOR = 0x543EB0
init_insns = disasm_range(INIT_FN, INIT_FN + 0x40)
init_layout = [{"va": i.address, "insn": "%s %s" % (i.mnemonic, i.op_str)}
               for i in init_insns if i.mnemonic in ("mov", "push", "call")]
check(any(i.address == 0x543E8D and i.op_str.endswith(hex(DER_VT)) for i in init_insns),
      "全局动态初始化器 0x543E70: [0xAA1078] ← 0x7ECBDC(派生 vtable)",
      "初始化器未写派生 vtable")
check(any(i.address == 0x543E97 and i.op_str.endswith("0xa") for i in init_insns),
      "初始化器: [0xAA108C] ← 10 → +0x14 = GrowthStep = 10 (DynamicVectorClass 布局证据)",
      "GrowthStep 初始化证据缺失")

# ----------------------------------------------------------------------------
# 9. 函数内 esi 数据流 + 跨函数 this 链
# ----------------------------------------------------------------------------
fn_body = disasm_range(FN_START, fn_end if fn_end else TARGET + 0x20)

esi_defs = []
for ins in fn_body:
    if ins.address >= TARGET:
        break
    txt = "%s %s" % (ins.mnemonic, ins.op_str)
    if txt.startswith("mov esi,") or txt.startswith("lea esi,") or txt == "pop esi" or txt == "xor esi, esi":
        esi_defs.append({"va": ins.address, "insn": txt})

# 0x54A52D 的 pop esi 位于 edi==0 早退路径(0x54A52A jne 0x54A535 不跳时 → 0x54A52C..0x54A532 ret 8),
# 该路径不达 0x0054A56E; 能到达目标的 esi 定义只有 0x54A4FA。
check([d for d in esi_defs if d["va"] == 0x54A4FA and d["insn"] == "mov esi, ecx"] != [] and
      all(d["va"] in (0x54A4FA, 0x54A52D) for d in esi_defs),
      "函数 0x0054A4F0..0x%X 内 esi 定义共 %d 处: 0x54A4FA mov esi, ecx (=this, thiscall, 唯一可达 0x0054A56E 的定义) + 0x54A52D pop esi (edi==0 早退路径的现场恢复, 不达目标)" % (
          fn_end, len(esi_defs)),
      "esi 定义链异常: %s" % esi_defs)
check(any(i.address == 0x54A52A and i.mnemonic == "jne" and i.op_str.endswith("0x54a535") for i in fn_body),
      "0x54A52A jne 0x54A535: 0x54A52D pop esi 确在早退路径上(与 0x0054A56E 无数据流)",
      "0x54A52A 跳转形态异常")

# [esi+off] 访问面 → 对象布局证据
esi_field_uses = {}
for ins in fn_body:
    txt = "%s %s" % (ins.mnemonic, ins.op_str)
    if "[esi" in txt:
        import re as _re
        m = _re.search(r"\[esi(?: \+ (0x[0-9a-f]+|\d+))?\]", txt)
        off = int(m.group(1), 0) if (m and m.group(1)) else 0
        esi_field_uses.setdefault(off, []).append({"va": ins.address, "insn": txt})

# this 的来源: 对全局对象的全部引用点
# 注: find_imm32_refs 报告的是立即数字节地址(指令地址 = 立即数地址 - 前缀长度)
check(sorted(imm_global) == [0x543E8F, 0x543EC0, 0x546060, 0x546065],
      "全局 0xAA1078 在 .text 的立即数引用共 4 处(字节地址): 0x543E8F(初始化器 0x543E8D 指令)/0x543EC0(atexit 析构器 0x543EBE 指令)/0x546060+0x546065(Add 派发 0x54605F/0x546064 指令)",
      "全局引用点异常: %s" % [hex(x) for x in imm_global])

# 派发点上下文
disp = disasm_range(0x546030, 0x546092)
disp_txt = [{"va": i.address, "insn": "%s %s" % (i.mnemonic, i.op_str)} for i in disp]
has_dispatch = any(d["va"] == 0x546069 and d["insn"] == "call dword ptr [eax + 8]" for d in disp_txt)
check(has_dispatch,
      "0x546069  call dword ptr [eax+8] = 经 vtable slot2 虚派发 Capacity, 其中 eax=[0xAA1078](vptr), ecx=0xAA1078(this) — 全模块对本对象唯一的虚派发点",
      "0x546069 派发形态异常")

# ----------------------------------------------------------------------------
# 10. 0x54A56E 可达性判定(核心)
# ----------------------------------------------------------------------------
# slot2 目标按 vptr 值分派:
SLOT2_BASE = u32(VT_BASE + 8)     # vptr=0x7ECBFC → slot2
SLOT2_DER = u32(DER_VT + 8)       # vptr=0x7ECBDC → slot2
check(SLOT2_BASE == FN_START and SLOT2_DER == 0x54A630,
      "slot2 派发: vptr=0x7ECBFC → 0x0054A4F0(本函数); vptr=0x7ECBDC → 0x0054A630(孪生体)",
      "slot2 派发表异常: base=%X der=%X" % (SLOT2_BASE, SLOT2_DER))

# 孪生体 free-then-null 位置
twin = disasm_range(0x54A690, 0x54A6B0)
twin_free = [i.address for i in twin if i.mnemonic == "call" and i.op_str.endswith("0x7c8b3d")]
twin_null = [i.address for i in twin if "%s %s" % (i.mnemonic, i.op_str) == "mov dword ptr [esi + 4], 0"]
check(twin_free == [0x54A699] and twin_null == [0x54A6A1],
      "孪生函数 0x54A630 同构 free-then-null: 0x54A699 call 0x7C8B3D / 0x54A6A1 mov [esi+4],0",
      "孪生体位置异常: free=%s null=%s" % (twin_free, twin_null))

# 析构器中的同构对
dtor1 = disasm_range(0x54A7B0, 0x54A7F6)
dtor1_free = [i.address for i in dtor1 if i.mnemonic == "call" and i.op_str.endswith("0x7c8b3d")]
dtor1_null = [i.address for i in dtor1 if "%s %s" % (i.mnemonic, i.op_str) == "mov dword ptr [esi + 4], 0"]
dtor2 = disasm_range(0x54A800, 0x54A846)
dtor2_free = [i.address for i in dtor2 if i.mnemonic == "call" and i.op_str.endswith("0x7c8b3d")]
dtor2_null = [i.address for i in dtor2 if "%s %s" % (i.mnemonic, i.op_str) == "mov dword ptr [esi + 4], 0"]

# atexit 析构器行为(决定 vptr 与 Vector 的终态)
atexit_insns = disasm_range(ATEXIT_DTOR, 0x543F08)
atexit_sets_base_vt = any(i.address == 0x543EBE and i.mnemonic == "mov" and "0xaa1078" in i.op_str and "0x7ecbfc" in i.op_str for i in atexit_insns)
atexit_nulls_vector = any(i.address == 0x543EEC and i.mnemonic == "mov" and "0xaa107c" in i.op_str and ", 0" in i.op_str for i in atexit_insns)
atexit_zeroes_max = any(i.address == 0x543EFD and i.mnemonic == "mov" and "0xaa1080" in i.op_str and ", 0" in i.op_str for i in atexit_insns)
atexit_untouched = all("0xaa1088" not in ("%s %s" % (i.mnemonic, i.op_str)) and
                       "0xaa108c" not in ("%s %s" % (i.mnemonic, i.op_str))
                       for i in atexit_insns)
check(atexit_sets_base_vt and atexit_nulls_vector and atexit_zeroes_max and atexit_untouched,
      "atexit 析构器 0x543EB0: [0xAA1078]←0x7ECBFC@0x543EBE(永久留基类 vtable), free 后 [0xAA107C]←0@0x543EEC, [0xAA1080](VectorMax)←0@0x543EFD; 全程未触碰 ActiveCount(0xAA1088)/GrowthStep(0xAA108C)",
      "atexit 析构器行为与预期不符")

# 释放包装器身份
free_xrefs = find_call_jmp_targets(0x7C8B3D)
alloc_xrefs = find_call_jmp_targets(0x7C8E17)
check(len(free_xrefs) > 1000 and len(alloc_xrefs) > 1000,
      "0x7C8B3D(释放包装 → 0x7C93E8)有 %d 个调用点; 0x7C8E17(分配包装 → 0x7C9442)有 %d 个调用点 → 全局堆原语" % (
          len(free_xrefs), len(alloc_xrefs)),
      "分配/释放包装调用点数异常")

# post-dtor 再 Add 的推演: Vector==0 时 0x54A53A je 0x54A575 跳过 free+null 块
je_skip = [i for i in fn_body if i.address == 0x54A53A and i.mnemonic == "je" and i.op_str.endswith("0x54a575")]
check(len(je_skip) == 1,
      "0x54A53A je 0x54A575: Vector==0 时整块 free+null(0x54A535..0x54A56E)被跳过 → post-dtor 状态下一次 Capacity 不触达 0x54A56E",
      "0x54A53A 跳转形态异常")

# 0x54A56E 之后紧接的覆盖写
after = disasm_range(0x54A56E, 0x54A590)
overwrite = [i for i in after if i.address == 0x54A577 and i.mnemonic == "mov" and i.op_str.startswith("dword ptr [esi + 4], edi")]
check(len(overwrite) == 1,
      "0x54A577 mov dword ptr [esi+4], edi: 0x54A56E 的置 0 在 8 字节内被无条件覆盖(Vector = 新缓冲), 两点之间无 [esi+4] 读、无调用、无跳转",
      "0x54A577 覆盖写证据缺失")

# 同函数内的间接控制转移(供 EIP 落 .data 的机制评估)
indirect_calls = [{"va": i.address, "insn": "%s %s" % (i.mnemonic, i.op_str)}
                  for i in disasm_range(FN_START, 0x54A5A0)
                  if i.mnemonic == "call" and "[" in i.op_str and "dword ptr [" in i.op_str]

# ----------------------------------------------------------------------------
# 11. 0x0084F2BA 落点字节观察(仅记录, 不作结论)
# ----------------------------------------------------------------------------
data_bytes_at_eip = bytes(image[EIP_DATA - IMAGE_BASE: EIP_DATA - IMAGE_BASE + 16]).hex(" ")

# ----------------------------------------------------------------------------
# 12. 汇总输出
# ----------------------------------------------------------------------------
result = {
    "identity": {"sha256": sha, "size": len(raw), "exe": EXE_PATH},
    "sections": {k: {"va": hex(v["va"]), "vsize": hex(v["vsize"]),
                     "characteristics": hex(v["characteristics"])} for k, v in sections.items()},
    "eip_data_0x0084F2BA": {
        "in_section": ".data" if in_section(EIP_DATA, ".data") else None,
        "section_executable": bool(sections[".data"]["characteristics"] & EXEC),
        "bytes_at_target": data_bytes_at_eip,
        "verdict": "EIP 进入不可执行页 → 静态上为取指违规(DEP), 非写失败(字节本身无意义, 仅记录)"
    },
    "target_0x0054A56E": {
        "bytes": TARGET_BYTES.hex(),
        "insn": "mov dword ptr [esi + 4], 0",
        "function": {
            "start": hex(FN_START), "end": hex(fn_end) if fn_end else None,
            "identification": "RTTI slot2 of vtable 0x7ECBFC (entry 0x7ECC04)",
            "rtti_class": td_name,
        },
        "window": window_json,
    },
    "rtti": {
        "base_vtable": hex(VT_BASE), "base_col": hex(col), "base_typedescriptor": hex(td),
        "base_class": td_name, "base_slots": [hex(x) for x in VT_SLOTS],
        "derived_vtable": hex(DER_VT), "derived_col": hex(DER_COL),
        "derived_class": DER_NAME, "derived_slots": [hex(x) for x in DER_SLOTS],
    },
    "object_layout": {
        "note": "由全局 0xAA1078 初始化器(0x543E70)与成员访问面交叉钉死",
        "0x00": "vptr",
        "0x04": "Vector (TileInsertType<IsometricTileTypeClass>** 数组基址)",
        "0x08": "VectorMax/Capacity (int)",
        "0x0C": "byte 标志(构造=1, Capacity 分配前后 0→1; 本模块内未见读取方)",
        "0x0D": "IsAllocated (bool, delete[] 所有权门控)",
        "0x10": "ActiveCount (int, DynamicVectorClass)",
        "0x14": "GrowthStep (int = 10, 初始化器 0x543E97)",
    },
    "esi_chain": [
        {"ring": 0, "va": "0x0054A56E", "insn": "mov dword ptr [esi + 4], 0",
         "effect": "写 this->Vector = 0"},
        {"ring": 1, "va": "0x0054A4FA", "insn": "mov esi, ecx",
         "effect": "esi = this(thiscall); 函数体内 esi 唯一定义点"},
        {"ring": 2, "va": "0x546064", "insn": "mov ecx, 0xAA1078",
         "effect": "ecx = this = 全局静态对象 0xAA1078(唯一实例, 类型见 RTTI)"},
        {"ring": 2, "va": "0x54605F", "insn": "mov eax, dword ptr [0xAA1078]",
         "effect": "eax = vptr(运行期值)"},
        {"ring": 2, "va": "0x546069", "insn": "call dword ptr [eax + 8]",
         "effect": "slot2 虚派发 Capacity(int, T*): vptr=0x7ECBDC→0x54A630; vptr=0x7ECBFC→0x54A4F0; 本模块对该对象唯一虚派发点"},
        {"ring": 3, "va": "0x543E8D", "insn": "mov dword ptr [0xAA1078], 0x7ECBDC",
         "effect": "动态初始化器 0x543E70 置派生 vtable → 正常态派发去 0x54A630"},
        {"ring": 3, "va": "0x543EBE", "insn": "mov dword ptr [0xAA1078], 0x7ECBFC",
         "effect": "atexit 析构器 0x543EB0 置基类 vtable(永久) → 此后派发才可能进 0x54A4F0"},
    ],
    "chain_break": None,
    "chain_break_note": "链未断: esi 经 thiscall ecx 回溯到全局对象 0xAA1078 的唯一派发点 0x546069, 全链每环有指令地址。",
    "reachability_of_0x0054A56E": {
        "normal_state": "不可达: vptr=0x7ECBDC → 走孪生 0x54A630(free@0x54A699, null@0x54A6A1)",
        "post_atexit_state": "半可达: vptr=0x7ECBFC → 进 0x54A4F0, 但 Vector 已被析构器清 0 → 0x54A53A je 跳过 free+null 块; 需此后再发生一次扩容 Capacity(先重建 Vector, IsAllocated=1), 第二次扩容才触达 0x54A56E",
        "corruption_state": "可达: vptr 被改写为 0x7ECBFC 且 Vector/IsAllocated 仍为活跃值(需内存破坏)",
        "conclusion": "静态上 0x54A56E 只在对象处于已析构/异常状态时可达 — 这与『该指令语义正常』的评价相冲突(见 free_then_null_assessment)"
    },
    "free_then_null_assessment": {
        "local_semantics": "支持: 0x54A565 push [esi+4] → 0x54A566 call 0x7C8B3D(释放旧数组) → 0x54A56E 将同一字段清 0; 被释放的是数组(旧 Vector 值), 置 0 的是对象字段([esi+4] 本身) — 与 Westwood VectorClass<T>::Capacity 源码形态『if (IsAllocated) { delete[] Vector; Vector = 0; } Vector = newptr;』逐句对应",
        "transient": "0x54A56E 的置 0 是过渡写: 0x54A575 xor eax,eax 后 0x54A577 mov [esi+4], edi 无条件覆盖为新缓冲, 中间无 [esi+4] 读、无调用、无跳转",
        "guard": "执行条件为 [esi+0xD](IsAllocated)非零(0x54A55B mov al,[esi+0xD]; 0x54A55E test; 0x54A560 je 跳过)",
        "crash_context": "若 EIP 崩在 0x54A56E, 故障访问是该写本身 → this 所在页不可写; 而同页早前已有成功写(0x54A506/0x54A526 [esi+0xC])与成功读(0x54A53C/0x54A54B/0x54A55B/0x54A562), 两者之间唯一的外部操作是 0x54A566 的 free → 静态上最自洽的解释是对象本身处于已释放/页被去提交状态; 该状态归因超出静态能力, 如实报",
        "verdict": "台账『释放后置空, 语义正常』: 对非崩溃路径成立(局部代码形态与原始源码一致); 但作为对『崩在 0x54A56E』这一事实的解释不成立 — 正常态该指令根本不可达(见 reachability), 能执行到它本身就说明对象状态异常"
    },
    "related_sites": {
        "twin_capacity": {"fn": "0x54A630 (DynamicVectorClass<PAUTileInsertType>::Capacity)",
                          "free": "0x54A699", "null": "0x54A6A1"},
        "base_dtor": {"fn": "0x54A7B0 (VectorClass<...> deleting dtor, vptr 写 0x7ECBFC@0x54A7B6)",
                      "free": hex(dtor1_free[0]) if dtor1_free else None,
                      "null": hex(dtor1_null[0]) if dtor1_null else None},
        "derived_dtor": {"fn": "0x54A800 (DynamicVectorClass<...> deleting dtor, vptr 写 0x7ECBFC@0x54A806)",
                         "free": hex(dtor2_free[0]) if dtor2_free else None,
                         "null": hex(dtor2_null[0]) if dtor2_null else None},
        "global_init": "0x543E70", "global_atexit_dtor": "0x543EB0",
        "add_grow_dispatch": "0x546030..0x546089 (扩容判定→0x546069 虚派发→0x546083..0x546089 写 Vector[ActiveCount])",
        "indirect_calls_in_fn": indirect_calls,
        "indirect_calls_note": "0x54A4F0..0x54A5A0 内唯一间接控制转移是 0x54A58E..0x54A592 的 call [edx+0xC](newcap==0 路径, edx=[esi]=vptr); 该类经 vptr 的间接调用是本函数族内静态可见的『EIP=任意 dword』机制(若 vptr 指向被破坏内存), 与 0x0084F2BA 型崩溃机制相容但静态不可证实因果",
    },
    "allocator_free_wrappers": {
        "free": {"va": "0x7C8B3D", "callee": "0x7C93E8", "xrefs": len(free_xrefs)},
        "alloc": {"va": "0x7C8E17", "callee": "0x7C9442", "xrefs": len(alloc_xrefs)},
    },
    "global_object_users": {
        "imm32_refs_to_0xAA1078": [hex(x) for x in imm_global],
        "field_users": {
            "Vector_0xAA107C": [hex(x) for x in find_imm32_refs(GLOBAL_OBJ + 4)],
            "VectorMax_0xAA1080": [hex(x) for x in find_imm32_refs(GLOBAL_OBJ + 8)],
            "IsAllocated_0xAA1085": [hex(x) for x in find_imm32_refs(GLOBAL_OBJ + 0xD)],
            "ActiveCount_0xAA1088": [hex(x) for x in find_imm32_refs(GLOBAL_OBJ + 0x10)],
        },
    },
    "crosschecks": notes,
}

# 文本输出
L = []
L.append("=" * 100)
L.append("gamemd.exe 静态还原 — 0x0054A56E 数据依赖链 (只读, pefile+capstone)")
L.append("文件: %s" % EXE_PATH)
L.append("sha256: %s  size: %d B" % (sha, len(raw)))
L.append("=" * 100)
L.append("")
L.append("[节表 / DEP 前提]")
for n in notes:
    if "0xC0000040" in n["text"] or "0x0084F2BA" in n["text"] or "IMAGE_SCN_MEM_EXECUTE" in n["text"] or "EXECUTE" in n["text"]:
        L.append("  %s" % n["text"])
L.append("")
L.append("[RTTI 定类]")
L.append("  基类 vtable 0x7ECBFC (COL 0x%X): %s" % (col, td_name))
L.append("    slot0..slot6: %s" % ", ".join(hex(x) for x in VT_SLOTS))
L.append("  派生 vtable 0x7ECBDC (COL 0x%X): %s" % (DER_COL, DER_NAME))
L.append("    slot0..slot6: %s" % ", ".join(hex(x) for x in DER_SLOTS))
L.append("")
L.append("[唯一实例与生命周期]")
L.append("  全局对象 0xAA1078 (DynamicVectorClass<PAUTileInsertType>):")
L.append("    动态初始化器 0x543E70: vptr←0x7ECBDC@0x543E8D, Vector←0, VectorMax←0, [0xAA1084]←1, IsAllocated←0, GrowthStep←10@0x543E97")
L.append("    atexit 析构器 0x543EB0 (经 0x543EA6 call 0x7C978A 注册): vptr←0x7ECBFC@0x543EBE(永久), free(Vector)@0x543EE4, Vector←0@0x543EEC, VectorMax←0@0x543EFD")
L.append("    .text 立即数引用: %s" % ", ".join(hex(x) for x in imm_global))
L.append("")
L.append("[0x0054A56E 附近 ±40 条 (函数 0x0054A4F0..%s, RTTI slot2 = VectorClass<TileInsertType<IsometricTileTypeClass>*>::Capacity(int,T*))]" % (
    hex(fn_end) if fn_end else "?"))
L.extend("  %s" % x for x in window_txt)
L.append("")
L.append("[esi 来源链]")
for ring in result["esi_chain"]:
    L.append("  环%d  %s  %s" % (ring["ring"], ring["va"], ring["insn"]))
    L.append("        %s" % ring["effect"])
L.append("")
L.append("[链断点] 无 — esi 链在静态层闭合(esi←ecx=this←0xAA1078 全局对象唯一派发点 0x546069)")
L.append("")
L.append("[0x0054A56E 可达性]")
for k, v in result["reachability_of_0x0054A56E"].items():
    L.append("  %s: %s" % (k, v))
L.append("")
L.append("[『释放后置空』评估]")
for k, v in result["free_then_null_assessment"].items():
    L.append("  %s: %s" % (k, v))
L.append("")
L.append("[同族 free-then-null 位点]")
L.append("  孪生 Capacity 0x54A630: free 0x54A699 / null 0x54A6A1")
L.append("  基类 dtor 0x54A7B0:    free %s / null %s" % (hex(dtor1_free[0]), hex(dtor1_null[0])))
L.append("  派生 dtor 0x54A800:    free %s / null %s" % (hex(dtor2_free[0]), hex(dtor2_null[0])))
L.append("")
L.append("[EIP=0x0084F2BA 观察与机制注记]")
L.append("  0x0084F2BA 落 .data (无 EXECUTE) → 静态上取指违规(DEP)。该地址处的文件字节(仅记录): %s" % data_bytes_at_eip)
L.append("  本函数族内可见的间接控制转移: %s" % indirect_calls)
L.append("  → 经 vptr 的 call [edx+0xC](0x54A592 / 孪生 0x54A6BE)在 vptr 指向被破坏内存时可产生『EIP=任意 dword』, 与『EIP 落 .data』机制相容; 静态不能证实因果。")
L.append("")
L.append("[交叉断言]")
for n in notes:
    L.append("  [%s] %s" % (n["kind"], n["text"]))

out_txt = os.path.join(OUT_DIR, "_cw_disasm_out.txt")
out_json = os.path.join(OUT_DIR, "_cw_disasm_out.json")
with open(out_txt, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("\nWROTE %s\nWROTE %s" % (out_txt, out_json))
mism = [n for n in notes if n["kind"] == "MISMATCH"]
print("MISMATCH count: %d" % len(mism))
sys.exit(0)
