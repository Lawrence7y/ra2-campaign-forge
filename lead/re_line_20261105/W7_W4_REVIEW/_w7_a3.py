# -*- coding: utf-8 -*-
"""W7 / A3 独立复核探针（只读，零真机，零注入）。

核三项：
  ①-a  `0x00B0CE88` 不是 TacticalClass 成员（是全局静态向量 0xB0CE78 的 +0x10 Count）
  ①-b  `0x6D3DF5` 抄录错：真实为 jne；`test eax,eax` 在 `0x6D3DFF`
  ②    `DrawIfVisible 0x5F4B10` 函数体内零处 `call 0x6D2790`

纪律：用 ra2tool.Engine 的**重同步线性解码**（ra2tool.py:4-9），并另做
**原始字节级 rel32 扫描**与反汇编流交叉验证，不把「某一种查法没查到」当「不存在」。
"""
import sys
import struct
import hashlib

sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104')
from ra2tool import Engine

eng = Engine()
RAW = eng.raw
TLO, THI, TB, TSZ = eng.TLO, eng.THI, eng.TB, eng.TSZ

print("=" * 78)
print("SECTION 0  引擎绑定")
print("=" * 78)
print("EXE_SHA256", eng.sha)
print("ASSERT_MATCH", eng.sha == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")
print("IMAGE_BASE", hex(eng.IB))
print("TEXT", hex(TLO), hex(THI), "raw_ptr", hex(TB), "raw_size", hex(TSZ))
print("COVERAGE", eng.coverage)
print("SECTIONS", [(nm, hex(sva), hex(vsz), hex(rsz)) for nm, sva, vsz, rp, rsz in eng.SEC])
print("fo(0xB0CE88) =", eng.fo(0xB0CE88), " (None => BSS/零填充, 无文件字节)")
print("u32(0x814E94) =", hex(eng.u32(0x814E94)))
print()


def hexat(va, n):
    return eng.rd(va, n).hex()


def show_range(lo, hi, label):
    """从重同步线性解码流打印 [lo,hi) 的全部指令（不重新对齐，避免假零）。"""
    print("-" * 78)
    print("DISASM", label, hex(lo), "..", hex(hi))
    print("-" * 78)
    for ins in eng.stream:
        if lo <= ins.address < hi:
            print("%08X  %-22s  %-8s %s" % (
                ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print()


def raw_find(pat):
    """全镜像原始字节查找；返回 (file_offset, VA or None)。"""
    out = []
    pos = 0
    while True:
        j = RAW.find(pat, pos)
        if j < 0:
            break
        va = (TLO + (j - TB)) if (TB <= j < TB + TSZ) else None
        out.append((j, va))
        pos = j + 1
    return out


def rel32_calls_to(target):
    """原始字节级：全 .text 扫 E8 <rel32>，target == va+5+rel32。返回 call 指令 VA 列表。

    这独立于 capstone 的解码对齐，用来避免「解码没对齐 => 漏掉 call」的假零。
    """
    hits = []
    for off in range(TB, TB + TSZ - 4):
        if RAW[off] != 0xE8:
            continue
        rel = struct.unpack_from("<i", RAW, off + 1)[0]
        va = TLO + (off - TB)
        if va + 5 + rel == target:
            hits.append((va, RAW[off:off + 5].hex()))
    return hits


# ---------------------------------------------------------------- ①-a
print("=" * 78)
print("SECTION 1  ①-a  不是 TacticalClass::DirtyAreas 的字节依据")
print("=" * 78)
print("RAW 0x6D2790 (16B) =", hexat(0x6D2790, 16))
show_range(0x6D2790, 0x6D27C0, "RegisterDirtyArea 0x6D2790 序言（ecx 被覆盖?）")
print("RAW 0x6D1A60 (64B) =", hexat(0x6D1A60, 64))
show_range(0x6D1A60, 0x6D1AA0, "全局向量 CRT 静态构造 0x6D1A60（绝对地址写 vptr/各槽）")
show_range(0x6D2A70, 0x6D2A95, "扩容路径 0x6D2A84 mov ecx,0xB0CE78 + call [edx+8]")
print("RAW 0x6D3DF0 (5B) =", hexat(0x6D3DF0, 5),
      " <- TacticalClass::Render 内也是**绝对地址**读 Count")
print()
print("原始 LE `78 CE B0 00` (= 0xB0CE78 对象基址) 全镜像命中：")
for off, va in raw_find(bytes.fromhex("78CEB000")):
    print("   file_off", hex(off), "VA", hex(va) if va else "OUTSIDE_.text")
print("原始 `B9 78 CE B0 00` (= mov ecx,0xB0CE78) 全镜像命中：")
for off, va in raw_find(bytes.fromhex("B978CEB000")):
    print("   file_off", hex(off), "VA", hex(va) if va else "OUTSIDE_.text")
print()
print("disp_hits(0xB0CE88) 全量普查（绝对 disp32 访存，重同步解码口径）:")
dh = eng.disp_hits(0xB0CE88)
print("   total", len(dh), "W", sum(1 for x in dh if x[1] == "W"),
      "R", sum(1 for x in dh if x[1] == "R"))
for va, wr, mn, op in dh:
    print("   %08X %s %-8s %s" % (va, wr, mn, op))
print()
print("旁证：全 .text 中 [reg+0xD7C]/[reg+0xD7D] 形态的 TacticalClass 成员读（说明成员用 [ebp+off]，向量用绝对地址）：")
by = eng.by()
cnt = 0
for ins in eng.stream:
    try:
        for op in ins.operands:
            if op.type == 3 and op.mem.disp in (0xD7C, 0xD7D) and op.mem.base != 0:
                print("   %08X %-20s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
                cnt += 1
                break
    except Exception:
        pass
print("   count", cnt)
print()


# ---------------------------------------------------------------- ①-b
print("=" * 78)
print("SECTION 2  ①-b  0x6D3DF5 抄录订正（W3 Q3_SAMPLE_PLAN.md:100-102）")
print("=" * 78)
print("RAW 0x6D3DE8 .. 0x6D3E10 (%d B) =" % 0x28, hexat(0x6D3DE8, 0x28))
show_range(0x6D3DE8, 0x6D3E10, "Render 判脏段 0x6D3DE8..0x6D3E10")
print("逐址断言（从重同步解码流取，不从固定偏移猜）：")
expect = {
    0x6D3DF0: ("a188ceb000", "mov", "eax, dword ptr [0xb0ce88]"),
    0x6D3DF5: ("756e", "jne", None),
    0x6D3DF7: ("84c9", "test", "cl, cl"),
    0x6D3DFF: ("85c0", "test", "eax, eax"),
    0x6D3E01: ("7566", "jne", None),
}
for va, (bh, mn, op) in expect.items():
    ins = by.get(va)
    if ins is None:
        print("   %08X  MISSING_IN_STREAM" % va)
        continue
    print("   %08X  bytes=%-12s mnem=%-6s op=%-34s  RAW=%s" %
          (va, ins.bytes.hex(), ins.mnemonic, ins.op_str, hexat(va, len(ins.bytes))))
    print("        expect_bytes=%s expect_mnem=%s" % (bh, mn))
print()
print("W3 原抄录（Q3_SAMPLE_PLAN.md:100-102）: 0x6D3DF5=`85 C0 test eax,eax`; 0x6D3DF7=`75 70 jne 0x6D3E69`")
print("W3_COSTBOUND.md:284 同样写 `0x006D3DF5 test eax, eax`")
print()


# ---------------------------------------------------------------- ②
print("=" * 78)
print("SECTION 3  ②  DrawIfVisible 0x5F4B10 函数体内零处 call 0x6D2790")
print("=" * 78)

RDA = 0x6D2790
all_calls = rel32_calls_to(RDA)
print("全 .text 原始字节级 E8 rel32 -> 0x6D2790 的直接调用点总数 =", len(all_calls))
print("清单（VA, 5字节编码）:")
for va, bh in all_calls:
    print("   %08X  %s" % (va, bh))
print()

# 与重同步解码流交叉核对
stream_calls = []
for ins in eng.stream:
    if ins.mnemonic == "call":
        try:
            if ins.operands and ins.operands[0].type == 2 and ins.operands[0].imm == RDA:
                stream_calls.append(ins.address)
        except Exception:
            pass
print("重同步解码流中 `call 0x6D2790` 总数 =", len(stream_calls))
print("两种口径集合是否一致 =", sorted(a for a, _ in all_calls) == sorted(stream_calls))
print()

# 先定函数边界：把 0x5F4B10..0x5F4D60 的所有 call / ret 打出来
print("-" * 78)
print("DISASM 0x5F4B10..0x5F4D60 中全部 call / ret（用于定函数边界）")
print("-" * 78)
for ins in eng.stream:
    if 0x5F4B10 <= ins.address < 0x5F4D60:
        if ins.mnemonic == "call" or ins.mnemonic.startswith("ret") or ins.mnemonic.startswith("jmp"):
            tgt = ""
            try:
                if ins.operands and ins.operands[0].type == 2:
                    tgt = " -> " + hex(ins.operands[0].imm)
            except Exception:
                pass
            print("   %08X  %-20s %-8s %s%s" %
                  (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, tgt))
print()
print("RAW 0x5F4D0C (8B) =", hexat(0x5F4D0C, 8))
print("RAW 0x5F4D20 (32B) =", hexat(0x5F4D20, 32))
print()

# 函数体内全部 call 指令（含间接），列出并判定有无 0x6D2790
BODY_LO, BODY_HI = 0x5F4B10, 0x5F4D0C + 3  # ret 0xC 落点（含）
print("-" * 78)
print("DrawIfVisible 函数体 [0x5F4B10, 0x5F4D0F) 内全部 call 指令")
print("-" * 78)
body_calls = []
for ins in eng.stream:
    if BODY_LO <= ins.address < BODY_HI and ins.mnemonic == "call":
        body_calls.append(ins)
        print("   %08X  %-20s %-8s %s" %
              (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
print("   body call 总数 =", len(body_calls))
print()

def in_range(lo, hi):
    return [va for va, _ in all_calls if lo <= va < hi]

for lo, hi, tag in [
    (0x5F4B10, 0x5F4D0C, "[0x5F4B10,0x5F4D0C) 严格函数体(ret 0xC 之前)"),
    (0x5F4B10, 0x5F4D0F, "[0x5F4B10,0x5F4D0F) 含 ret 0xC 三字节"),
    (0x5F4B10, 0x5F4D30, "[0x5F4B10,0x5F4D30) 卡 §8.1.3 所用窗口"),
    (0x5F4B10, 0x5F4E90, "[0x5F4B10,0x5F4E90) 宽窗口（含相邻函数）"),
]:
    print("RDA direct callers in %-52s = %s" % (tag, [hex(v) for v in in_range(lo, hi)]))

# 原始字节级：窗口内独立扫 E8->RDA（不依赖 capstone 对齐）
print()
print("独立原始字节级窗口扫描（直接对 [0x5F4B10,0x5F4D30) 的文件字节找 E8->RDA）:")
o_lo = TB + (0x5F4B10 - TLO)
o_hi = TB + (0x5F4D30 - TLO)
win_hits = []
for off in range(o_lo, o_hi - 4):
    if RAW[off] == 0xE8:
        rel = struct.unpack_from("<i", RAW, off + 1)[0]
        va = TLO + (off - TB)
        if va + 5 + rel == RDA:
            win_hits.append((va, RAW[off:off + 5].hex()))
print("   window_hits =", [(hex(v), b) for v, b in win_hits])
print("   窗口字节 =", RAW[o_lo:o_hi].hex())
print()

# 相邻 RDA 调用点在哪（避免把「别处出现过」当成「不存在」）
near = [va for va, _ in all_calls if 0x5F4B00 <= va < 0x5F5300]
print("0x5F4B00..0x5F5300 内的 RDA 直接调用点 =", [hex(v) for v in near])
for v in near:
    print("   %08X RAW %s" % (v, hexat(v, 5)))
print()
print("结论打印见 _w7_a3_out.txt 末尾 SECTION 4")
print()

# ---------------------------------------------------------------- verdicts
print("=" * 78)
print("SECTION 4  机读判定行")
print("=" * 78)
b = eng.by()
def ins_is(va, bh, mn):
    i = b.get(va)
    return i is not None and i.bytes.hex() == bh and i.mnemonic == mn

print("V_1a_global_object_base_4hits =",
      len([1 for off, va in raw_find(bytes.fromhex("78CEB000")) if va is not None]))
print("V_1a_rda_prologue_overwrites_ecx =",
      hexat(0x6D2790, 3) == "83ec58" and hexat(0x6D2793, 6) == "8b0d88ceb000")
print("V_1a_ctor_abs_vptr =", hexat(0x6D1A7D, 10) == "c70578ceb0009c427f00")
print("V_1a_expand_mov_ecx_base =", hexat(0x6D2A84, 5) == "b978ceb000")
print("V_1b_6D3DF5_is_jne =", ins_is(0x6D3DF5, "756e", "jne"))
print("V_1b_6D3DF7_is_test_cl_cl =", ins_is(0x6D3DF7, "84c9", "test"))
print("V_1b_6D3DFF_is_test_eax_eax =", ins_is(0x6D3DFF, "85c0", "test"))
print("V_1b_6D3E01_is_jne =", ins_is(0x6D3E01, "7566", "jne"))
print("V_2_total_direct_RDA_callers =", len(all_calls))
print("V_2_RDA_callers_in_strict_body =", len(in_range(0x5F4B10, 0x5F4D0C)))
print("V_2_RDA_callers_in_card_window =", len(in_range(0x5F4B10, 0x5F4D30)))
print("V_2_two_methods_agree =", sorted(a for a, _ in all_calls) == sorted(stream_calls))
