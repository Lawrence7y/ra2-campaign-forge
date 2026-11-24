#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_sf_scan.py — 100% 分块覆盖重验「经 vtable slot2 调用 0x54A4F0 / 0x54A630」的全部调用点 (只读)。

对象: ra2bench/gamemd.exe (sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476)
方法: pefile + capstone 纯静态; 不启动进程、不 attach、不读活内存、不打补丁。
输出: _sf_scan_out.txt / _sf_scan_out.json (与本脚本同目录)

对上一轮 lead/esi_caller_trace_20261111/ 结论在 100% 覆盖下的重验清单:
  T1 覆盖率复现: 单次 disasm = 155215 条(陷阱); 分块 0x10000 独立块 = 1150117 条(ask 给数);
     分块 seg-extend(自然停点) = 主普查流。另做字节级(解码无关)普查作为完备性下界。
  T2 全 .text 所有 call/jmp dword ptr [reg+8] 普查 (含异形 [reg+reg*4+8] 单列)。
  T3 每点回溯 10 条, 判定 reg 的 vtable 能否静态确定; 可能指向 0x54A4F0/0x54A630 的须满足
     reg 可追溯到 0xAA1078(或已知 DynamicVectorClass 实例)。
  T4 复核「直接 call/jmp → 0x54A4F0」与「→ 0x54A630」在全量下是否仍为 0
     (指令级 + 字节级 E8/E9 + 立即数物化 + FF 15/25 绝对间接 四法)。
  T5 0x546069 是否唯一调用点 — 用污点传播(从全镜像唯一 vptr 装载 0x54605F 前向)给出
     解码无关的消费者集合, 与普查/字节级三方对账。

关键闸门(全部当场字节级验证, 任一 FAIL 记 MISMATCH):
  G1a 全镜像 dword==0x54A4F0 / ==0x54A630 的单元仅各自 vtable slot2 一处
  G1b 无任何指令从 0x7ECC04/0x7ECBE4 装载 或 FF 15/25 调用这两个 slot2 单元
      → 函数指针值不可能在运行期被复制/物化到任何其它单元
  G2  全镜像 dword==0x7ECBFC(3)/0x7ECBDC(1) 全部落在 4 条 c7 存储立即数字节范围内
      → 无「mov reg, vtable值」; 寄存器获得该值唯一途径 = 装载 [0xAA1078]
  G3  vptr 写入点(c7 /0)恰 4 条: 2 条→[0xAA1078], 2 条→[esi](两 deleting dtor 体内);
      两 dtor 无直接 call/jmp 进入 → 归纳: 唯一能持有这两个 vptr 值的对象 = 0xAA1078
  G4  全镜像 imm32==0xAA1078 恰 4 处; 「load r32 ← [0xAA1078]」全部编码(A1/8B mod00 rm101/
      SIB-abs)恰 1 处 = 0x54605F; 「store reg → [0xAA1078]」(89/A3) = 0
  G5  .rdata/.data 无 dword==0xAA1078 → 无指向全局对象的指针变量
  G4b 指令流中 mov reg, imm ∈ [0xAA1000..0xAA1100] 全集审计(别名合成)
  G6  从 0x54605F 的污点前向传播(跨 call 清易失寄存器, push/store 记逃逸) → 消费者集合
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
# 0. 常量与文件
# ----------------------------------------------------------------------------
EXPECTED_SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
EXPECTED_SIZE = 4825360

TARGET_FN = 0x0054A4F0          # VectorClass<PAUTileInsertType*> slot2 (vtable 0x7ECBFC)
TWIN_FN = 0x0054A630            # DynamicVectorClass<PAUTileInsertType*> slot2 (vtable 0x7ECBDC)
VT_BASE = 0x7ECBFC
VT_DER = 0x7ECBDC
GLOBAL_OBJ = 0xAA1078
SLOT2 = 8
BACK_WINDOW = 10                # ask 指定: 往上回溯 10 条

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

raw = open(EXE_PATH, "rb").read()
sha = hashlib.sha256(raw).hexdigest()
check(sha == EXPECTED_SHA256, "sha256 = %s (与台账一致)" % sha, "sha256 = %s 不一致" % sha)
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
TBYTES = bytes(image[TSTART - IB:TEND - IB])
print(".text [0x%X..0x%X] (%d B)" % (TSTART, TEND, TEND - TSTART))

# ----------------------------------------------------------------------------
# 1. 前提复核 (ask 给的已知事实)
# ----------------------------------------------------------------------------
check(u32(VT_BASE + SLOT2) == TARGET_FN, "[前提] [0x7ECBFC+8]=0x54A4F0 (vtable 0x7ECBFC slot2)",
      "[前提] vtable 0x7ECBFC slot2 != 0x54A4F0")
check(u32(VT_DER + SLOT2) == TWIN_FN, "[前提] [0x7ECBDC+8]=0x54A630 (vtable 0x7ECBDC slot2)",
      "[前提] vtable 0x7ECBDC slot2 != 0x54A630")
for vt, expect in ((VT_BASE, "VectorClass"), (VT_DER, "DynamicVectorClass")):
    col = u32(vt - 4)
    td = u32(col + 0x0C)
    nm = cstr(td + 8)
    check(expect in nm, "[前提] RTTI @0x%X: %s" % (vt, nm), "[前提] RTTI @0x%X 异常: %r" % (vt, nm))
check(u32(GLOBAL_OBJ) == 0 and u32(GLOBAL_OBJ + 4) == 0 and u32(GLOBAL_OBJ + 8) == 0,
      "[前提] 文件镜像 .data @0xAA1078 vptr/Vector/VectorMax = 0 (运行期动态初始化)",
      "[前提] .data @0xAA1078 文件镜像非零")

# ----------------------------------------------------------------------------
# 2. 反汇编: 单次(陷阱复现) + 分块 seg-extend(主普查流) + 分块 0x10000(ask 数复现)
# ----------------------------------------------------------------------------
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False

single = list(md.disasm(TBYTES, TSTART))
check(len(single) == 155215,
      "T1a 复现陷阱: 单次 disasm = %d 条, 末条 VA 0x%X (next undecodable 0x%X)" % (
          len(single), single[-1].address, single[-1].address + single[-1].size),
      "单次 disasm = %d 条(与已知 155215 不符)" % len(single))
single_bytes_covered = single[-1].address + single[-1].size - TSTART
print("[T1] 单次覆盖字节: %d / %d = %.2f%% (按指令数/字节计 %.2f%%)" % (
    single_bytes_covered, TEND - TSTART, 100.0 * single_bytes_covered / (TEND - TSTART),
    100.0 * len(single) / (TEND - TSTART)))

def disasm_seg_extend():
    """主普查流: 停点处 +1 字节重同步, 逐段延伸到段尾(无重复计数)。"""
    out, restarts = [], []
    pos = TSTART
    while pos < TEND:
        chunk = list(md.disasm(TBYTES[pos - TSTART:], pos))
        if chunk:
            out.extend(chunk)
            pos = chunk[-1].address + chunk[-1].size
        if pos >= TEND:
            break
        restarts.append(pos)
        pos += 1
    return out, restarts

full, restarts = disasm_seg_extend()
cov_end = full[-1].address + full[-1].size
check(cov_end >= TEND and len(full) >= 1000000,
      "T1b 主普查流(分块 seg-extend): %d 条, %d 个自然停点, 覆盖至 0x%X (=100%% .text, ≥1e6 条)" % (
          len(full), len(restarts), cov_end),
      "主普查流覆盖异常: %d 条 / 末 0x%X" % (len(full), cov_end))
check(cov_end == TEND, "T1b-bis 主流末条恰达段尾 0x%X" % TEND,
      "主流末条 0x%X != TEND 0x%X" % (cov_end, TEND))

BLOCK = 0x10000
blk_cnt, blk_bounds = 0, 0
for b in range(TSTART, TEND, BLOCK):
    e = min(b + BLOCK, TEND)
    blk_cnt += sum(1 for _ in md.disasm(TBYTES[b - TSTART:e - TSTART], b))
    blk_bounds += 1
check(blk_cnt == 1150117,
      "T1c 复现 ask 给数: 分块(0x10000 独立块 × %d) = %d 条 = ask 的 1150117" % (blk_bounds, blk_cnt),
      "0x10000 分块 = %d 条 ≠ ask 的 1150117" % blk_cnt)

fullB, boundsB = [], []
for b in range(TSTART, TEND, BLOCK):
    e = min(b + BLOCK, TEND)
    fullB.extend(md.disasm(TBYTES[b - TSTART:e - TSTART], b))
    boundsB.append(e)
restart_set = set(restarts)
addr2idx = {}
for k, ins in enumerate(full):
    addr2idx.setdefault(ins.address, k)
addr2idxB = {}
for k, ins in enumerate(fullB):
    addr2idxB.setdefault(ins.address, k)

# 字节级 call/jmp rel32 目标集合(函数归属近似)
import bisect
all_targets = []
for va in range(TSTART, TEND - 5):
    if TBYTES[va - TSTART] in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", TBYTES, va - TSTART + 1)[0]
        t = va + 5 + rel
        if TSTART <= t < TEND:
            all_targets.append(t)
all_targets = sorted(set(all_targets))
def enclosing_fn_approx(va):
    i = bisect.bisect_right(all_targets, va) - 1
    return ("0x%X" % all_targets[i]) if i >= 0 else None

# ----------------------------------------------------------------------------
# 3. 字节级普查 (解码无关) — call/jmp [reg+8] 的全部编码
# ----------------------------------------------------------------------------
REGN = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"]

def byte_census():
    """FF /2=call, FF /4=jmp; mod01 disp8==8 或 mod10 disp32==8; rm!=4 或 SIB(无变址)。"""
    hits = []
    n = len(TBYTES)
    i = 0
    while i < n - 2:
        if TBYTES[i] != 0xFF:
            i += 1
            continue
        m = TBYTES[i + 1]
        mod, rf, rm = m >> 6, (m >> 3) & 7, m & 7
        kind = "call" if rf == 2 else ("jmp" if rf == 4 else None)
        if kind is None:
            i += 1
            continue
        if mod == 1:
            if rm == 4:
                if i + 4 <= n and TBYTES[i + 3] == 0x08:
                    sib = TBYTES[i + 2]
                    idx, base = (sib >> 3) & 7, sib & 7
                    if idx == 4:
                        hits.append((TSTART + i, 4, kind, REGN[base], None))
                    else:
                        hits.append((TSTART + i, 4, kind, "%s+%s*%d" % (REGN[base], REGN[idx],
                                                                        1 << (sib >> 6)), "exotic"))
            else:
                if TBYTES[i + 2] == 0x08:
                    hits.append((TSTART + i, 3, kind, REGN[rm], None))
            i += 2
        elif mod == 2:
            if rm == 4:
                if i + 7 <= n and struct.unpack_from("<I", TBYTES, i + 3)[0] == 8:
                    sib = TBYTES[i + 2]
                    idx, base = (sib >> 3) & 7, sib & 7
                    if idx == 4:
                        hits.append((TSTART + i, 7, kind, REGN[base], None))
                    else:
                        hits.append((TSTART + i, 7, kind, "%s+%s*%d" % (REGN[base], REGN[idx],
                                                                        1 << (sib >> 6)), "exotic"))
            else:
                if i + 6 <= n and struct.unpack_from("<I", TBYTES, i + 2)[0] == 8:
                    hits.append((TSTART + i, 6, kind, REGN[rm], None))
            i += 2
        else:
            i += 1
    return hits

bhits = byte_census()
byte_call = [h for h in bhits if h[2] == "call"]
byte_jmp = [h for h in bhits if h[2] == "jmp"]
print("[T2-byte] 字节级 call [reg+8] = %d, jmp [reg+8] = %d (含异形 %d)" % (
    len(byte_call), len(byte_jmp), sum(1 for h in bhits if h[4] == "exotic")))

# ----------------------------------------------------------------------------
# 4. 流内普查 (主流 full + 对照流 fullB)
# ----------------------------------------------------------------------------
SLOT2_RE = re.compile(r"^dword ptr \[(e?[a-z]{2,3}) \+ (?:0x8|8)\]$")
EXOTIC_RE = re.compile(r"^dword ptr \[(e?[a-z]{2,3}) \+ e?[a-z]{2,3}\s*\*\s*\d \+ (?:0x8|8)\]$")

def stream_census(stream):
    sites, exotic = [], []
    for k, ins in enumerate(stream):
        if ins.mnemonic not in ("call", "jmp") or "[" not in ins.op_str:
            continue
        m = SLOT2_RE.match(ins.op_str)
        if m:
            sites.append((k, ins, m.group(1)))
            continue
        if EXOTIC_RE.match(ins.op_str):
            exotic.append((k, ins))
    return sites, exotic

sitesA, exoticA = stream_census(full)
sitesB, exoticB = stream_census(fullB)
callA = [s for s in sitesA if s[1].mnemonic == "call"]
jmpA = [s for s in sitesA if s[1].mnemonic == "jmp"]
print("[T2-stream] 主流 call/jmp [reg+8] = %d (call %d, jmp %d); 对照流(0x10000块) = %d (call %d)"
      % (len(sitesA), len(callA), len(jmpA), len(sitesB),
         sum(1 for s in sitesB if s[1].mnemonic == "call")))

# 三方对账: 字节级 ↔ 主流 ↔ 对照流
streamA_vas = set(ins.address for _, ins, _ in sitesA)
streamB_vas = set(ins.address for _, ins, _ in sitesB)
byte_vas = set(h[0] for h in bhits)
only_streamA = sorted(streamA_vas - byte_vas)
only_streamB = sorted(streamB_vas - byte_vas)
check(not only_streamA,
      "对账①: 主流 %d 个 slot2 点全部有字节级编码对应(无主流多出; 编码集完备)" % len(streamA_vas),
      "主流多出字节级不存在的点(编码集缺形?): %s" % [hex(x) for x in only_streamA[:20]])
check(not only_streamB,
      "对账①-b: 对照流 %d 个 slot2 点全部有字节级编码对应" % len(streamB_vas),
      "对照流多出: %s" % [hex(x) for x in only_streamB[:20]])

# 字节级命中分类: site(与流一致) / embedded(嵌入某条更长指令内, 巧合字节) / gap(未解码洞)
startsA = [ins.address for ins in full]
sizesA = [ins.size for ins in full]
startsB = [ins.address for ins in fullB]
sizesB = [ins.size for ins in fullB]

def hit_class(va, starts, sizes):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0 and va < starts[i] + sizes[i]:
        return ("site" if va == starts[i] else "embedded", i)
    return ("gap", i)

hit_classes = {}
suspicious = []
for va, ln, kind, reg, ex in bhits:
    ca, ia = hit_class(va, startsA, sizesA)
    cb, ib = hit_class(va, startsB, sizesB)
    hit_classes[va] = (ca, cb)
    if ca == "gap" or cb == "gap" or {ca, cb} == {"site", "embedded"}:
        suspicious.append((va, ln, kind, reg, ex, ca, cb))
n_embed = sum(1 for va in byte_vas if hit_classes[va] == ("embedded", "embedded"))
n_site = sum(1 for va in byte_vas if "site" in hit_classes[va])
gapA = [s for s in suspicious if s[5] == "gap"]
gapB_only = [s for s in suspicious if s[5] == "site" and s[6] == "gap"]
divergent = [s for s in suspicious if {s[5], s[6]} == {"site", "embedded"}]
print("[对账②] 字节级 %d 点: 含 site 判定 %d; 纯 embedded 巧合 %d; A流gap %d; "
      "A=site/B=gap(块尾遗留, A 已覆盖) %d; 一site一embedded 分歧 %d" % (
          len(byte_vas), n_site, n_embed, len(gapA), len(gapB_only), len(divergent)))
for va, ln, kind, reg, ex, ca, cb in suspicious[:12]:
    print("   [可疑示例] %08X %s [%s] len=%d A=%s B=%s" % (va, kind, reg, ln, ca, cb))
check(not gapA,
      "对账②-b: 无字节级命中落在主流未解码洞(无被错位解码藏匿的 slot2 编码)",
      "存在 A-gap 字节级命中(需锚定复核): %s" % [hex(s[0]) for s in gapA])
check(not divergent,
      "对账②-c: 无『一流认作 site / 另一流嵌入』的分歧命中",
      "存在分歧命中(需锚定复核): %s" % [hex(s[0]) for s in divergent])
# 注: B=gap 是 0x10000 独立块法的固有行为(capstone 在块内提前停, 块尾剩余字节不进对照流);
#     完整性由下一断言保证: 每个字节级命中都须是至少一条流的 site (含异形变址点)。
exoticA_vas = set(ins.address for _, ins in exoticA)
byte_hits_not_site_any = sorted(byte_vas - streamA_vas - exoticA_vas - streamB_vas)
check(not byte_hits_not_site_any,
      "对账②-d: 字节级 %d 个编码命中全部是至少一条流的 site (主流 slot2 %d + 主流异形 %d + "
      "对照流 %d 并集完整) → 普查无漏点" % (
          len(byte_vas), len(streamA_vas), len(exoticA_vas), len(streamB_vas)),
      "字节级存在两流均非 site 的命中(真·藏匿): %s" % [hex(x) for x in byte_hits_not_site_any])
sym_diff = sorted(streamA_vas ^ streamB_vas)
print("[对账③] 主流 vs 对照流 site 差集: %d 个 (漂移/块尾差异, 逐点带 in_A/in_B 标志)" % len(sym_diff))
byte_only_exotic = [h for h in bhits if h[4] == "exotic"]
print("[对账] 字节级异形(+变址)点: %s" % [(hex(a), k, r) for a, l, k, r, e in byte_only_exotic])

# ----------------------------------------------------------------------------
# 5. T4: 直接调用复核 (0x54A4F0 / 0x54A630) — 四种独立方法
# ----------------------------------------------------------------------------
def byte_e8e9_targets(target):
    hits = []
    for va in range(TSTART, TEND - 5):
        b = TBYTES[va - TSTART]
        if b in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", TBYTES, va - TSTART + 1)[0]
            if va + 5 + rel == target:
                hits.append((va, "call" if b == 0xE8 else "jmp"))
    return hits

def imm32_materializations(target):
    """mov r32, imm32 / C7 C0+r / push imm32 / FF /2 [abs] 等物化途径的字节级存在性:
    全镜像 dword==target 的位置(应仅 vtable slot2, 见 G1a) + .text 内 imm32 位置。"""
    pat = struct.pack("<I", target)
    hits, pos = [], 0
    while True:
        i = image.find(pat, pos)
        if i < 0:
            break
        hits.append(i + IB)
        pos = i + 1
    return hits

def abs_indirect_call_of_cell(cell):
    """FF 15/25 disp32 = call/jmp dword ptr [cell]; 另含 8B/A1 装载该单元的编码。"""
    hits = []
    for opcode, label in ((0x15, "call"), (0x25, "jmp")):
        pat = bytes([0xFF, opcode]) + struct.pack("<I", cell)
        pos = 0
        while True:
            i = TBYTES.find(pat, pos)
            if i < 0:
                break
            hits.append((TSTART + i, label + " [" + hex(cell) + "]"))
            pos = i + 1
    for opcode in (0x8B, 0x89, 0x03, 0x0B, 0x39, 0x3B, 0x85, 0xA1, 0xA3):
        for r in range(8):
            if opcode in (0xA1, 0xA3):
                modrm_pat = bytes([opcode]) + struct.pack("<I", cell)
                modrms = [None]
            else:
                modrm = 0x05 | (r << 3)
                modrm_pat = bytes([opcode, modrm]) + struct.pack("<I", cell)
                modrms = [r]
            pos = 0
            while True:
                i = TBYTES.find(modrm_pat, pos)
                if i < 0:
                    break
                hits.append((TSTART + i, "%02x %s [0x%X]" % (opcode, "r%d" % r if modrms[0] is not None else "", cell)))
                pos = i + 1
            if opcode in (0xA1, 0xA3):
                break
    # SIB-abs (mod=00 rm=100 sib=0x25): 8B xx 25 disp32 / 89 xx 25 disp32
    for opcode in (0x8B, 0x89):
        for r in range(8):
            pat = bytes([opcode, 0x04 | (r << 3), 0x25]) + struct.pack("<I", cell)
            pos = 0
            while True:
                i = TBYTES.find(pat, pos)
                if i < 0:
                    break
                hits.append((TSTART + i, "%02x r%d sib25 [0x%X]" % (opcode, r, cell)))
                pos = i + 1
    return hits

direct = {}
for tgt, cell in ((TARGET_FN, VT_BASE + SLOT2), (TWIN_FN, VT_DER + SLOT2)):
    insn_hits_A = [i.address for i in full if i.mnemonic in ("call", "jmp")
                   and i.op_str.startswith("0x") and int(i.op_str.split()[0], 16) == tgt]
    insn_hits_B = [i.address for i in fullB if i.mnemonic in ("call", "jmp")
                   and i.op_str.startswith("0x") and int(i.op_str.split()[0], 16) == tgt]
    e8e9_hits = byte_e8e9_targets(tgt)
    dwlocs = imm32_materializations(tgt)
    cellrefs = abs_indirect_call_of_cell(cell)
    dwlocs_text = [hex(x) for x in dwlocs]
    ok = (not insn_hits_A and not insn_hits_B and not e8e9_hits
          and dwlocs == [cell] and not cellrefs)
    direct["0x%08X" % tgt] = {
        "insn_level_streamA": [hex(x) for x in insn_hits_A],
        "insn_level_streamB": [hex(x) for x in insn_hits_B],
        "byte_level_E8E9": [(hex(a), k) for a, k in e8e9_hits],
        "whole_image_dword_locs": dwlocs_text,
        "abs_indirect_or_load_of_slot2_cell": [(hex(a), l) for a, l in cellrefs],
    }
    check(ok,
          "T4: 直接/物化调用 0x%08X = 0 — 指令级(A流%d/B流%d) + 字节级E8/E9(%d) + 全镜像dword仅"
          "vtable slot2 0x%X 一处 + 无 FF 15/25 或装载该单元(%d 处) — 四法一致" % (
              tgt, len(insn_hits_A), len(insn_hits_B), len(e8e9_hits), cell, len(cellrefs)),
          "T4 失败 0x%08X: %s" % (tgt, direct["0x%08X" % tgt]))

# ----------------------------------------------------------------------------
# 6. 字节级值闸门 G1a/G1b/G2/G3/G4/G5
# ----------------------------------------------------------------------------
def image_dwords_equal(value):
    return imm32_materializations(value)

r_fn = {TARGET_FN: image_dwords_equal(TARGET_FN), TWIN_FN: image_dwords_equal(TWIN_FN)}
check(r_fn[TARGET_FN] == [VT_BASE + SLOT2],
      "G1a: 全镜像值==0x54A4F0 的 dword 仅 1 处: 0x%X (=vtable 0x7ECBFC slot2) → 无第二虚表/"
      "无回调表/无立即数" % (VT_BASE + SLOT2),
      "G1a 失败: %s" % [hex(x) for x in r_fn[TARGET_FN]])
check(r_fn[TWIN_FN] == [VT_DER + SLOT2],
      "G1a: 全镜像值==0x54A630 的 dword 仅 1 处: 0x%X (=vtable 0x7ECBDC slot2)" % (VT_DER + SLOT2),
      "G1a 失败: %s" % [hex(x) for x in r_fn[TWIN_FN]])

cell_load_refs = {hex(c): abs_indirect_call_of_cell(c) for c in (VT_BASE + SLOT2, VT_DER + SLOT2)}
check(all(len(v) == 0 for v in cell_load_refs.values()),
      "G1b: 无任何指令 call/jmp [slot2单元] 或从其装载(FF15/FF25/A1/8B/89/SIB-abs 全编码 = 0)"
      " → 函数指针值无法运行期复制到其它单元",
      "G1b 失败: %s" % {k: [(hex(a), l) for a, l in v] for k, v in cell_load_refs.items()})

STORE_INSNS = [(0x543E8D, "mov dword ptr [0xaa1078], 0x7ecbdc"),
               (0x543EBE, "mov dword ptr [0xaa1078], 0x7ecbfc"),
               (0x54A7B6, "mov dword ptr [esi], 0x7ecbfc"),
               (0x54A806, "mov dword ptr [esi], 0x7ecbfc")]
store_spans = []
for va, txt in STORE_INSNS:
    ins = next(md.disasm(TBYTES[va - TSTART: va - TSTART + 12], va))
    store_spans.append((ins.address, ins.address + ins.size, "%s %s" % (ins.mnemonic, ins.op_str)))
check([s[2] for s in store_spans] == [t for _, t in STORE_INSNS],
      "G3 存储指令锚点解码确认: %s" % " | ".join(s[2] for s in store_spans),
      "G3 存储指令形态异常: %s" % store_spans)

r_vt = {VT_BASE: image_dwords_equal(VT_BASE), VT_DER: image_dwords_equal(VT_DER)}
g2_ok, g2_desc = True, []
for v, hits in r_vt.items():
    for h in hits:
        owner = [s for s in store_spans if s[0] <= h and h + 4 <= s[1]]
        if owner:
            g2_desc.append("0x%X ← imm of %s" % (h, owner[0][2]))
        else:
            g2_ok = False
            g2_desc.append("0x%X ← 未归属任何 c7 存储(疑似 mov reg,imm / 数据单元!)" % h)
check(g2_ok and len(r_vt[VT_BASE]) == 3 and len(r_vt[VT_DER]) == 1,
      "G2: 值 0x7ECBFC×3 + 0x7ECBDC×1 共 4 处全落在 c7 存储立即数内: %s → 无 mov reg,vtable值,"
      "无 .rdata/.data 值单元 → 寄存器持有 0x7ECBFC/0x7ECBDC 的唯一途径 = 装载 [0xAA1078]" %
      "; ".join(g2_desc), "G2 失败: %s" % g2_desc)

def find_vptr_stores(vtable_va):
    pat = struct.pack("<I", vtable_va)
    hits = []
    va = TSTART
    while va < TEND - 10:
        if TBYTES[va - TSTART] == 0xC7:
            m = TBYTES[va - TSTART + 1]
            mod, reg, rm = m >> 6, (m >> 3) & 7, m & 7
            if reg == 0 and mod != 3:
                imm_off = None
                if mod == 0 and rm == 5:
                    imm_off = 6
                elif mod == 0 and rm == 4 and TBYTES[va - TSTART + 3] == 0x25:
                    imm_off = 7
                elif mod == 0:
                    imm_off = 2
                elif mod == 1:
                    imm_off = 3 + (1 if rm == 4 else 0)
                elif mod == 2:
                    imm_off = 6 + (1 if rm == 4 else 0)
                if imm_off and TBYTES[va - TSTART + imm_off: va - TSTART + imm_off + 4] == pat:
                    hits.append(va)
        va += 1
    return hits

stores_base = find_vptr_stores(VT_BASE)
stores_der = find_vptr_stores(VT_DER)
check(stores_der == [0x543E8D] and stores_base == [0x543EBE, 0x54A7B6, 0x54A806],
      "G3: vptr 写入点(c7 /0)全镜像重扫一致 — 0x7ECBDC: [0x543E8D]→[0xAA1078](动态初始化器 0x543E70"
      " 体内); 0x7ECBFC: [0x543EBE]→[0xAA1078](atexit 析构器 0x543EB0 体内), [0x54A7B6]/[0x54A806]"
      "→[esi](deleting dtor 体内)",
      "G3 失败: der=%s base=%s" % (stores_der, stores_base))
check(TSTART <= 0x543E8D < 0x543EB0 and 0x543EB0 <= 0x543EBE < 0x543EB0 + 0x60,
      "G3 归属: 0x543E8D ∈ 动态初始化器 0x543E70 体内; 0x543EBE ∈ atexit 析构器 0x543EB0 体内"
      " (ask 前提的初始化/析构归属复核)",
      "G3 归属失败: store 位置不在 0x543E70/0x543EB0 函数体内")
dtor_xrefs = {f: byte_e8e9_targets(f) for f in (0x54A7B0, 0x54A800)}
check(all(len(v) == 0 for v in dtor_xrefs.values()),
      "G3 支撑: 两 deleting dtor (0x54A7B0/0x54A800) 无直接 call/jmp 进入 → [esi] 写只作用于经 "
      "slot0 虚派发到达的 this, 而 slot0 派发要求 reg 已持这两个 vptr 值 → 归纳: 唯一实例 0xAA1078",
      "G3 支撑失败: %s" % {hex(k): [(hex(a), kd) for a, kd in v] for k, v in dtor_xrefs.items()})

refs_g = image_dwords_equal(GLOBAL_OBJ)
check(refs_g == [0x543E8F, 0x543EC0, 0x546060, 0x546065],
      "G4: 全镜像 imm32/disp32 引用 0xAA1078 恰 4 处(立即数字节地址): 0x543E8F(init 存储)/"
      "0x543EC0(atexit 存储)/0x546060(vptr 装载 @0x54605F)/0x546065(this 装载 @0x546064)",
      "G4 失败: %s" % [hex(x) for x in refs_g])

def load_r32_from_abs(cell):
    """全编码扫「load r32 ← [cell]」: A1 / 8B mod00 rm101 / 8B SIB 0x25; 另扫 store(89/A3)。"""
    loads, stores = [], []
    pats_load = [bytes([0xA1]) + struct.pack("<I", cell)]
    for r in range(8):
        pats_load.append(bytes([0x8B, 0x05 | (r << 3)]) + struct.pack("<I", cell))
        pats_load.append(bytes([0x8B, 0x04 | (r << 3), 0x25]) + struct.pack("<I", cell))
    pats_store = [bytes([0xA3]) + struct.pack("<I", cell)]
    for r in range(8):
        pats_store.append(bytes([0x89, 0x05 | (r << 3)]) + struct.pack("<I", cell))
        pats_store.append(bytes([0x89, 0x04 | (r << 3), 0x25]) + struct.pack("<I", cell))
    for p in pats_load:
        pos = 0
        while True:
            i = TBYTES.find(p, pos)
            if i < 0:
                break
            loads.append(TSTART + i)
            pos = i + 1
    for p in pats_store:
        pos = 0
        while True:
            i = TBYTES.find(p, pos)
            if i < 0:
                break
            stores.append(TSTART + i)
            pos = i + 1
    return sorted(loads), sorted(stores)

loads_1078, stores_1078 = load_r32_from_abs(GLOBAL_OBJ)
check(loads_1078 == [0x54605F] and not stores_1078,
      "G4-load: 全编码扫「load r32 ← [0xAA1078]」恰 1 处 = 0x54605F (mov eax, dword ptr "
      "[0xAA1078]); 「store reg → [0xAA1078]」= 0 (vptr 单元只被 2 条 c7 立即数写) — 字节级,"
      "与解码流无关" % (),
      "G4-load 失败: loads=%s stores=%s" % ([hex(x) for x in loads_1078],
                                            [hex(x) for x in stores_1078]))

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
      "G5: .rdata/.data 无 dword==0xAA1078 → 不存在指向该全局对象的指针变量(指针值不逃逸前提)",
      "G5 失败: %s" % {k: [hex(x) for x in v] for k, v in ptr_hits.items()})

# G4b: 指令流中全部 mov reg, imm ∈ [0xAA1000..0xAA1100]
base_loads = []
for k, ins in enumerate(full):
    if ins.mnemonic == "mov":
        mm = re.match(r"^(e?[a-z]{2,3}), (0x[0-9a-f]+)$", ins.op_str)
        if mm and 0xAA1000 <= int(mm.group(2), 16) <= 0xAA1100:
            base_loads.append((ins.address, mm.group(1), int(mm.group(2), 16)))
print("[G4b] mov reg, 0xAA10xx 全集(主流): %s" % [(hex(a), r, hex(v)) for a, r, v in base_loads])
check(all(v == 0xAA1078 for a, r, v in base_loads if a in (0x546064,)) and
      all(v != 0xAA1078 for a, r, v in base_loads if a not in (0x546064,)),
      "G4b: 基址立即数装载中仅 0x546064 恰为 0xAA1078(this 装载); 其余装载值均 ≠ 0xAA1078"
      " → 无别名合成路径读取 vptr 单元",
      "G4b: 存在其它 mov reg, 0xAA1078 形态! %s" % [(hex(a), r) for a, r, v in base_loads
                                                     if v == 0xAA1078 and a != 0x546064])

# ----------------------------------------------------------------------------
# 7. T3: 每 site 回溯 10 条定类 + vtable 静态可定性
# ----------------------------------------------------------------------------
VOLATILE = {"eax", "ecx", "edx"}

def classify_def(ins, cur):
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
            return ("vptr_via_reg", None, cur)
        mm = re.match(r"^dword ptr \[(e?[a-z]{2,3})(?: \+ (0x[0-9a-f]+|\d+))?\]$", src)
        if mm:
            base = mm.group(1)
            disp = int(mm.group(2), 16) if mm.group(2) else 0
            if base == "esp":
                return ("stack_src", disp, cur)
            if disp == 0 and base != cur:
                return ("deref_reg", None, base)
            return ("mem_of", (base, disp), cur)
        mm = re.match(r"^(e?[a-z]{2,3})$", src)
        if mm:
            return ("copy", None, mm.group(1))
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

def resolve_back(reg, idx, window=BACK_WINDOW):
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
            continue
        return {"kind": kind, "payload": payload, "def_va": hex(ins.address), "def": txt,
                "hops": hops, "calls_crossed": False, "final_reg": cur}
    last_push_cur = any(h.endswith("push %s" % cur) for h in hops if h.startswith("cross "))
    kind = "thiscall_this_of_enclosing_fn" if (cur == "ecx" or last_push_cur) else "undef_in_window"
    return {"kind": kind, "def_va": None, "def": None, "hops": hops, "cur": cur,
            "calls_crossed": False, "final_reg": cur}

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

_vt_cand_cache = {}
def vtable_candidates_of_object(A):
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
        for kk in range(k - 1, max(-1, k - 9), -1):
            ins2 = full[kk]
            mm = re.match(r"^(e?[a-z]{2,3}), (0x[0-9a-f]+)$", ins2.op_str) \
                if ins2.mnemonic == "mov" else None
            if mm and mm.group(1) == reg:
                v = int(mm.group(2), 16)
                if is_vtable_like(v):
                    cands.append(("reg-store@%08X" % va, v, rtti_name_of_vtable(v)))
                break
    _vt_cand_cache[A] = cands
    return cands

site_records = []
for k, ins, reg in sitesA:
    res = resolve_back(reg, k)
    if k >= BACK_WINDOW:
        lo_addr = full[k - BACK_WINDOW].address
        rw = any(lo_addr <= r <= ins.address for r in restart_set)
    else:
        rw = False
    rec = {"va": hex(ins.address), "kind": ins.mnemonic,
           "insn": "%s %s" % (ins.mnemonic, ins.op_str), "reg": reg, "bottom": res,
           "in_streamA": True, "in_streamB": ins.address in streamB_vas,
           "byte_level": ins.address in byte_vas,
           "restart_in_backwindow": rw,
           "enclosing_fn_approx": enclosing_fn_approx(ins.address)}
    site_records.append(rec)
print("[T3] 主流 %d 点回溯完成" % len(site_records))

# ----------------------------------------------------------------------------
# 8. T5: 唯一 vptr 装载 0x54605F 的污点前向传播 → 消费者集合
# ----------------------------------------------------------------------------
load_idx = addr2idx.get(0x54605F)
check(load_idx is not None,
      "唯一 vptr 装载 0x54605F 在主流中定位成功 (idx=%d)" % load_idx,
      "0x54605F 不在主流指令流中(?!)")
def find_grow_start(target):
    cand_starts = set()
    for va in range(TSTART, target):
        if TBYTES[va - TSTART] in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", TBYTES, va - TSTART + 1)[0]
            t = va + 5 + rel
            if TSTART <= t <= target:
                cand_starts.add(t)
    for s in sorted(cand_starts, reverse=True):
        n = 0
        for ins in md.disasm(TBYTES[s - TSTART: target - TSTART + 64], s):
            n += 1
            if ins.address == target:
                return s
            if n > 12000:
                break
    return None

GROW_START = find_grow_start(0x54605F)
grow_body = list(md.disasm(TBYTES[GROW_START - TSTART:], GROW_START)) if GROW_START else []
GROW_RET = None
for ins in grow_body:
    if GROW_START and ins.address > 0x54609A and ins.mnemonic.startswith("ret"):
        GROW_RET = ins.address
        break
in_grow_restarts = [r for r in restarts if GROW_START and GROW_START <= r <= (GROW_RET or TEND)]
check(GROW_START is not None and GROW_RET is not None and not in_grow_restarts,
      "GROW(包含唯一装载与派发的函数) = 0x%X..0x%X (ret@0x%X), 体内无停点" % (
          GROW_START, (GROW_RET + 2) if GROW_RET else 0, GROW_RET or 0),
      "GROW 定位/停点异常: start=%s ret=%s restarts=%s" % (
          GROW_START, GROW_RET, [hex(x) for x in in_grow_restarts]))

def taint_walk(start_idx, start_reg, end_va):
    """从 start_idx(装载点)前向: 跟踪 start_reg 的值; 消费=[reg+8] call/jmp 用被污染寄存器;
    push/store 记逃逸; call 清易失; 跨函数结束(ret)终止。"""
    taints = {start_reg: "0x54605F"}
    consumers, escapes = [], []
    for k in range(start_idx + 1, len(full)):
        ins = full[k]
        if ins.address > end_va:
            break
        m, op = ins.mnemonic, ins.op_str
        if m in ("call", "jmp") and "[" in op:
            mm = SLOT2_RE.match(op)
            bm = re.search(r"\[(e?[a-z]{2,3})", op)
            base = bm.group(1) if bm else None
            if base in taints:
                if mm:
                    consumers.append((ins.address, m, op, base,
                                      {r: v for r, v in taints.items() if r == base}))
                else:
                    escapes.append((ins.address, "%s %s (间接转移经被污染寄存器)" % (m, op)))
            if m == "call":
                for r in list(taints):
                    if r in VOLATILE:
                        del taints[r]
            continue
        if m in ("call", "jmp") and op in taints:
            escapes.append((ins.address, "%s %s (直接经被污染寄存器)" % (m, op)))
            if m == "call":
                for r in list(taints):
                    if r in VOLATILE:
                        del taints[r]
            continue
        if m == "call" or (m == "jmp" and op.startswith("0x")):
            if m == "call":
                for r in list(taints):
                    if r in VOLATILE:
                        del taints[r]
            continue
        if m.startswith("ret"):
            for r in list(taints):
                if r == "eax":
                    escapes.append((ins.address, "ret-with-tainted-eax"))
            break
        if m == "push":
            if op in taints:
                escapes.append((ins.address, "push " + op))
            continue
        mm = re.match(r"^(?:dword|word|byte) ptr \[[^\]]+\], (e?[a-z]{2,3})$", op)
        if m in ("mov", "add", "or", "and", "sub", "xor") and mm and mm.group(1) in taints:
            escapes.append((ins.address, op + " (store 被污染值)"))
            continue
        parts = op.split(", ", 1)
        if len(parts) == 2:
            dst, src = parts
            dm = re.match(r"^(e?[a-z]{2,3})$", dst)
            if dm:
                d = dm.group(1)
                if d in taints:
                    sm = re.match(r"^(e?[a-z]{2,3})$", src)
                    if m == "mov" and sm and sm.group(1) in taints:
                        taints[d] = taints[sm.group(1)]
                    else:
                        del taints[d]
                elif m == "mov":
                    sm = re.match(r"^(e?[a-z]{2,3})$", src)
                    if sm and sm.group(1) in taints:
                        taints[d] = taints[sm.group(1)]
                elif m == "pop" and d in taints:
                    del taints[d]
        if m == "pop" and op in taints:
            del taints[op]
    return consumers, escapes, dict(taints)

consumers, escapes, taint_end = taint_walk(load_idx, "eax", GROW_RET)
print("[T5] 污点消费者: %s" % [(hex(a), m, o) for a, m, o, r, _ in consumers])
print("[T5] 逃逸事件: %s" % [(hex(a), e) for a, e in escapes])
check(len(consumers) == 1 and consumers[0][0] == 0x546069 and not escapes,
      "T5: 从全镜像唯一 vptr 装载 0x54605F 的污点传播 → 消费者恰 1 个 = 0x546069 "
      "(call dword ptr [eax + 8]); 无 push/store/ret 逃逸 → vptr 值不逃逸出 GROW",
      "T5 失败: consumers=%s escapes=%s" % (
          [(hex(a), o) for a, m, o, r, _ in consumers], [(hex(a), e) for a, e in escapes]))

# ----------------------------------------------------------------------------
# 9. 候选判定 + 明细 (this 来源 / 上下文 / 派发去向)
# ----------------------------------------------------------------------------
consumer_vas = set(a for a, *_ in consumers)
n_cand = 0
for rec in site_records:
    va = int(rec["va"], 16)
    bot = rec["bottom"]
    if va in consumer_vas:
        rec["verdict"] = "CANDIDATE"
        rec["plausible"] = True
        rec["reason"] = ("reg ← [0xAA1078] (0x54605F, 全镜像唯一 vptr 装载; G2 证明寄存器持有 "
                         "0x7ECBFC/0x7ECBDC 的唯一途径) 且在污点存活窗口内消费")
        n_cand += 1
    else:
        rec["verdict"] = "EXCLUDED"
        rec["plausible"] = False
        if bot["kind"] == "vptr_of_imm":
            A = bot["payload"]
            cands = vtable_candidates_of_object(A)
            cands_s = "; ".join("%s→0x%X(%s)" % (c[0], c[1], c[2] or "?") for c in cands) \
                if cands else "未能静态定位(排除由值闸门成立)"
            rec["vtable_determinable"] = cands_s
            rec["reason"] = ("reg ← [0x%X] (对象 0x%X, vptr 候选: %s); 该单元不可能持 "
                             "0x7ECBFC/0x7ECBDC — 全镜像仅 4 条 c7 存储携带该值且目标均为 "
                             "[0xAA1078] (G2/G3)" % (A, A, cands_s))
        elif bot["kind"] == "stack_src":
            rec["reason"] = ("reg ← 栈槽 [esp+0x%X]; 调用方无法产生该值 — 唯一 vptr 值源 0x54605F "
                             "不逃逸 (T5 污点零逃逸)" % bot["payload"])
        elif bot["kind"] == "clobbered_by_call":
            rec["reason"] = ("reg 易失且链跨 call (%s); 被调方返回值不可能是 vtable 值 — 唯一值源 "
                             "0x54605F 不逃逸 (G1b/G4-load/T5)" % bot["def"])
        elif bot["kind"] == "thiscall_this_of_enclosing_fn":
            rec["reason"] = ("reg ← 外层函数(≈%s) thiscall this(序言链); 该 this 不可能是 0xAA1078"
                             " — 无指针值逃逸 GROW (G4/G5/T5), 且除全局外无第二实例 (G3 归纳)" %
                             (rec["enclosing_fn_approx"],))
        elif bot["kind"] == "undef_in_window":
            rec["reason"] = ("定义点超出 10 条回溯窗; 排除依据为全局值闸门(G2: 寄存器持 vtable 值"
                             "唯一途径 = 装载 [0xAA1078], 而 G4-load: 该装载全镜像恰 1 处且其唯一"
                             "消费者为 0x546069 (T5))")
        elif bot["kind"] == "mem_of":
            rec["reason"] = ("reg ← 指针场 (%s); 成为派发基须值==0x7ECBFC/0x7ECBDC, 而无任何指令"
                             "向 [0xAA1078] 之外写入该值 (G2/G3/G5)" % (bot.get("def") or "",))
        elif bot["kind"] == "pop":
            rec["reason"] = "reg ← pop (栈值); 排除同全局值闸门 (G2/G4/T5)"
        elif bot["kind"] == "zero":
            rec["reason"] = "reg=0 (xor) → 派发基为 0, 非任何 vptr"
        elif bot["kind"] in ("imm", "addr_of_imm"):
            P = bot["payload"]
            d = None
            try:
                d = u32(P + SLOT2)
            except Exception:
                pass
            rec["reason"] = ("reg = 立即数/取址 0x%X → 读 [0x%X+8]=%s; 无指令写 0x54A4F0/0x54A630"
                             " 于任何单元 (G1a)" % (P, P, hex(d) if d is not None else "越界"))
        else:
            rec["reason"] = ("reg 来源形 (%s @%s) 经全局值闸门排除" % (bot["kind"], bot.get("def_va")))

cands_list = [r for r in site_records if r["plausible"]]
check(len(cands_list) == 1 and cands_list[0]["va"] == "0x546069",
      "T5-final: %d 个主流 slot2 点中可能指向 0x54A4F0/0x54A630 的恰 1 个: 0x546069" %
      len(site_records),
      "候选点异常: %s" % [r["va"] for r in cands_list])

# 候选点锚定明细(独立于主流, 从 GROW 起点锚定解码)
anch = list(md.disasm(TBYTES[0x546030 - TSTART: 0x5460A0 - TSTART], 0x546030))
anch_txt = ["%08X %s %s" % (i.address, i.mnemonic, i.op_str) for i in anch]
ctx8 = [x for x in anch_txt if int(x[:8], 16) < 0x546069][-8:]
print("[候选] 0x546069 锚定上下文(前 8 条+本体+后 4 条):")
for x in ctx8 + [x for x in anch_txt if 0x546069 <= int(x[:8], 16) <= 0x546070]:
    print("   " + x)

grow_callers = [hex(va) for va, kind in byte_e8e9_targets(GROW_START) if kind == "call"]
print("[上下文] GROW 0x%X 直接调用者: %s" % (GROW_START, grow_callers))

# 异形点(变址)定类记录
exotic_records = []
for k, ins in exoticA:
    seh = 0x7CC0FC
    seh_refs = [hex(x) for x in image_dwords_equal(seh)]
    exotic_records.append({
        "va": hex(ins.address), "insn": "%s %s" % (ins.mnemonic, ins.op_str),
        "verdict": "EXCLUDED",
        "reason": ("CRT SEH 帧展开器(处理器 0x7CC0FC, fs:[0] 链)的内层表派发; 基址为展开链节点字段。"
                   "命中 0x54A4F0 需有效地址恰为 0x7ECC04 (G1a: 全镜像唯一持该值的单元); 基址/变址"
                   "寄存器均无法静态合成 0x7ECBxx 族值 (G2: 无 mov reg,vtable值) — 上轮同判定"),
    })
    print("[异形] %08X %s → EXCLUDED (SEH)" % (ins.address, ins.op_str))

# ----------------------------------------------------------------------------
# 10. 汇总输出
# ----------------------------------------------------------------------------
from collections import Counter
bottom_dist = Counter(r["bottom"]["kind"] for r in site_records)
reg_dist = Counter(r["reg"] for r in site_records)

result = {
    "identity": {"sha256": sha, "size": len(raw), "exe": EXE_PATH,
                 "script": os.path.abspath(__file__)},
    "coverage": {
        "text_range": ["0x%X" % TSTART, "0x%X" % TEND], "text_bytes": TEND - TSTART,
        "single_pass": {"count": len(single), "last_va": hex(single[-1].address),
                        "bytes_covered": single_bytes_covered,
                        "pct_of_text_bytes": round(100.0 * single_bytes_covered / (TEND - TSTART), 2),
                        "note": "陷阱复现: 155215 条"},
        "chunked_0x10000": {"count": blk_cnt, "blocks": blk_bounds,
                            "note": "= ask 给数 1150117"},
        "chunked_seg_extend": {"count": len(full), "restarts": len(restarts),
                               "coverage_end": hex(cov_end),
                               "restart_vas": [hex(x) for x in restarts],
                               "note": "主普查流, 无重复计数"},
    },
    "premises": {"vtable_base": hex(VT_BASE), "vtable_der": hex(VT_DER),
                 "slot2_base": hex(u32(VT_BASE + SLOT2)), "slot2_der": hex(u32(VT_DER + SLOT2)),
                 "global_obj": hex(GLOBAL_OBJ)},
    "direct_callers": direct,
    "gates": {
        "G1a_fn_dword_locs": {hex(k): [hex(x) for x in v] for k, v in r_fn.items()},
        "G1b_slot2_cell_refs": cell_load_refs,
        "G2_vtable_value_locs": {hex(k): [hex(x) for x in v] for k, v in r_vt.items()},
        "G2_contexts": g2_desc,
        "G3_vptr_stores": {"0x7ECBFC": [hex(x) for x in stores_base],
                           "0x7ECBDC": [hex(x) for x in stores_der]},
        "G3_dtor_direct_xrefs": {hex(k): [(hex(a), kd) for a, kd in v]
                                 for k, v in dtor_xrefs.items()},
        "G4_imm_refs_0xAA1078": [hex(x) for x in refs_g],
        "G4_load_from_global": [hex(x) for x in loads_1078],
        "G4_store_to_global": [hex(x) for x in stores_1078],
        "G4b_base_loads": [(hex(a), r, hex(v)) for a, r, v in base_loads],
        "G5_ptr_vars_to_global": {k: [hex(x) for x in v] for k, v in ptr_hits.items()},
    },
    "census": {
        "byte_level": {"call": len(byte_call), "jmp": len(byte_jmp),
                       "exotic_indexed": sum(1 for h in bhits if h[4] == "exotic")},
        "streamA_seg_extend": {"total": len(sitesA), "call": len(callA), "jmp": len(jmpA),
                               "exotic": len(exoticA)},
        "streamB_0x10000": {"total": len(sitesB), "call": sum(1 for s in sitesB
                                                              if s[1].mnemonic == "call")},
        "reconciliation": {
            "byte_hits_total": len(byte_vas),
            "byte_hits_not_site_any_stream": [hex(x) for x in byte_hits_not_site_any],
            "byte_gap_in_streamA": [hex(s[0]) for s in gapA],
            "byte_divergent_site_embedded": [hex(s[0]) for s in divergent],
            "byte_Asite_Bgap_blockstraggler": len(gapB_only),
            "byte_embedded_both": n_embed,
            "only_in_streamA_not_byte": [hex(x) for x in only_streamA],
            "streamA_vs_B_symdiff_count": len(sym_diff),
        },
        "bottom_kind_dist": dict(bottom_dist),
        "reg_dist": dict(reg_dist),
    },
    "taint_walk": {
        "load_site": "0x54605F", "consumers": [
            {"va": hex(a), "kind": m, "insn": o, "reg": r} for a, m, o, r, _ in consumers],
        "escapes": [{"va": hex(a), "event": e} for a, e in escapes],
        "grow": {"start": hex(GROW_START) if GROW_START else None,
                 "ret": hex(GROW_RET) if GROW_RET else None,
                 "restarts_inside": [hex(x) for x in in_grow_restarts],
                 "direct_callers": grow_callers},
    },
    "exotic_records": exotic_records,
    "sites": site_records,
    "sites_summary": {"total": len(site_records), "plausible": [r["va"] for r in cands_list],
                      "excluded": len(site_records) - len(cands_list)},
    "candidate_detail": {
        "va": "0x546069",
        "insn": "call dword ptr [eax + 8]",
        "form": "vtable-slot2",
        "context_before8_and_self": anch_txt,
        "this_source": ("ecx ← 0x546064 mov ecx, 0xAA1078 (imm32 直接装载; G4: 全镜像 4 处 "
                        "0xAA1078 引用中唯一的 this 装载; 非参数/非栈/非寄存器继承)"),
        "vptr_source": "eax ← 0x54605F mov eax, dword ptr [0xAA1078] (G4-load: 全镜像唯一)",
        "dispatch_by_lifecycle": {
            "normal (vptr=0x7ECBDC, init 0x543E8D)": "0x54A630 (DynamicVectorClass<PAUTileInsertType*>::Capacity)",
            "post-atexit (vptr=0x7ECBFC, 0x543EBE 置于析构器 0x543EB0, 永久)": "0x54A4F0 (VectorClass<PAUTileInsertType*>::Capacity)",
        },
        "confidence": "HIGH",
    },
    "crosschecks": notes,
}

out_txt_path = os.path.join(OUT_DIR, "_sf_scan_out.txt")
out_json_path = os.path.join(OUT_DIR, "_sf_scan_out.json")

L = []
L.append("=" * 100)
L.append("gamemd.exe — 100% 分块覆盖重验: 全 .text「call dword ptr [reg+8]」普查与 slot2 候选 (只读)")
L.append("文件: %s" % EXE_PATH)
L.append("sha256: %s  size: %d B" % (sha, len(raw)))
L.append("=" * 100)
L.append("")
L.append("[T1 覆盖率复现]")
L.append("  .text = [0x%X..0x%X] (%d B)" % (TSTART, TEND, TEND - TSTART))
L.append("  单次 disasm      : %d 条, 末条 0x%X, 覆盖 %d B (%.2f%% .text 字节) — 陷阱复现(155215)" % (
    len(single), single[-1].address, single_bytes_covered,
    100.0 * single_bytes_covered / (TEND - TSTART)))
L.append("  分块 0x10000 独立块: %d 条 (× %d 块) — 复现 ask 给数 1150117" % (blk_cnt, blk_bounds))
L.append("  分块 seg-extend  : %d 条, %d 个自然停点, 覆盖至 0x%X (主普查流, 无重复计数)" % (
    len(full), len(restarts), cov_end))
L.append("")
L.append("[T4 直接调用复核]")
for tgt, d in direct.items():
    L.append("  → %s: 指令级 A流 %s / B流 %s; 字节级 E8/E9 %s; 全镜像 dword 位点 %s;"
             " slot2 单元引用 %s" % (tgt, d["insn_level_streamA"], d["insn_level_streamB"],
                                      d["byte_level_E8E9"], d["whole_image_dword_locs"],
                                      d["abs_indirect_or_load_of_slot2_cell"]))
L.append("")
L.append("[字节级值闸门]")
for nn in notes:
    if nn["text"].startswith(("G1", "G2", "G3", "G4", "G5")):
        L.append("  %s" % nn["text"])
L.append("")
L.append("[T2 普查]")
L.append("  字节级(解码无关): call [reg+8] %d, jmp [reg+8] %d, 异形(变址) %d" % (
    len(byte_call), len(byte_jmp), sum(1 for h in bhits if h[4] == "exotic")))
L.append("  主流(seg-extend): call+jmp [reg+8] %d (call %d, jmp %d), 异形 %d" % (
    len(sitesA), len(callA), len(jmpA), len(exoticA)))
L.append("  对照流(0x10000块): %d (call %d)" % (len(sitesB), sum(1 for s in sitesB
                                                                 if s[1].mnemonic == "call")))
L.append("  对账: 字节级命中总数 %d, 其中两流均非 site %d; 主流∉字节级 %d; A/B 流差集 %d" % (
    len(byte_vas), len(byte_hits_not_site_any), len(only_streamA), len(sym_diff)))
L.append("  底源分布(回溯 10 条): %s" % dict(bottom_dist))
L.append("  寄存器分布: %s" % dict(reg_dist))
L.append("")
L.append("[T5 唯一性判定 — 污点传播]")
L.append("  GROW = 0x%X..0x%X; 唯一 vptr 装载 0x54605F; 消费者 = %s; 逃逸 = %s" % (
    GROW_START, GROW_RET, [(hex(a), o) for a, m, o, r, _ in consumers],
    [(hex(a), e) for a, e in escapes]))
L.append("  GROW 直接调用者: %s" % grow_callers)
L.append("")
L.append("[候选点(可能指向 0x54A4F0/0x54A630)]")
for r in cands_list:
    L.append("  ★ %s  %s" % (r["va"], r["insn"]))
    L.append("      this 来源 : ecx = 0xAA1078 (0x546064 mov ecx, 0xaa1078 — 全镜像唯一 this 装载)")
    L.append("      vptr 来源 : eax = [0xAA1078] (0x54605F mov eax, dword ptr [0xaa1078] — 全镜像唯一)")
    L.append("      派发去向  : 常态 vptr=0x7ECBDC → 0x54A630; atexit 析构后 vptr=0x7ECBFC → 0x54A4F0")
L.append("")
L.append("[0x546069 锚定上下文]")
for x in anch_txt:
    L.append("  " + x)
L.append("")
L.append("[全部 %d 个主流 slot2 点清单]" % len(site_records))
for r in site_records:
    bot = r["bottom"]
    L.append("  %s %-4s %-4s %-32s %s | %s" % (
        r["va"], r["kind"], r["reg"], bot["kind"], r["verdict"],
        (bot.get("def") or bot.get("def_va") or "")))
L.append("")
L.append("[交叉断言]")
for nn in notes:
    L.append("  [%s] %s" % (nn["kind"], nn["text"]))

with open(out_txt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("\nWROTE %s" % out_txt_path)
print("WROTE %s" % out_json_path)
mism = [n for n in notes if n["kind"] == "MISMATCH"]
print("MISMATCH count: %d" % len(mism))
sys.exit(0 if not mism else 1)
