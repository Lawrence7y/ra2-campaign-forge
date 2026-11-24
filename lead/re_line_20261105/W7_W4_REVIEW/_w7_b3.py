# -*- coding: utf-8 -*-
# W7 / B3 独立复核只读探针
# 目的：为 Q4_REDLINE.md 的 C2/C1/C4 判据，以及 C1「部分能」与 card_0087E8E0.md 的
#       字节事实一致性，真反汇编核对 ra2youli/gamemd.exe 字节。
# 纪律：python -I -X utf8；零真机、零注入、只读；不修改任何既有文件。
# 输出：由外层 shell 重定向到 W7_W4_REVIEW/_w7_b3_out.txt
import sys
import hashlib
import datetime

ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine  # noqa: E402

W4 = ROOT + r"\lead\re_line_20261105\W4_FIELD_SPEC\sections"


def banner(t):
    print("=" * 78)
    print("## " + t)
    print("=" * 78)


def sha_size(p):
    d = open(p, "rb").read()
    return hashlib.sha256(d).hexdigest(), len(d)


def show(e, va, n, tag):
    print("---- DISASM %s  @ 0x%X  len=0x%X ----" % (tag, va, n))
    for a, b, m, o in e.disasm(va, n):
        print("0x%08X  %-20s  %-7s %s" % (a, b, m, o))


def xref_e8e9(e, target):
    """扫 .text 全流，返回直接相对调用/跳转到 target 的 (va, mnem, op_str)。"""
    out = []
    for i in e.stream:
        if i.mnemonic not in ("call", "jmp"):
            continue
        try:
            ops = i.operands
        except Exception:
            continue
        if ops and ops[0].type == 2 and (i.address & 0xFFFFFFFF) and ops[0].imm == target:
            out.append((i.address, i.mnemonic, i.op_str))
    return out


def raw_count(e, pat):
    """在 .text 原始字节里数 4/5 字节立即数模式，返回 VA 列表。"""
    tb = e.raw[e.TB:e.TB + e.TSZ]
    res = []
    k = 0
    while True:
        j = tb.find(pat, k)
        if j < 0:
            break
        res.append(e.TLO + j)
        k = j + 1
    return res


banner("B3-0  被核对象与依赖文件 SHA256 / 字节数（自算）")
print("READ_TIME =", datetime.datetime.now().isoformat())
for label, p in [
    ("Q4_REDLINE.md", W4 + r"\Q4_REDLINE.md"),
    ("card_0087E8E0.md", W4 + r"\card_0087E8E0.md"),
    ("card_00B0CE88.md", W4 + r"\card_00B0CE88.md"),
    ("card_00A8EC34.md", W4 + r"\card_00A8EC34.md"),
    ("card_00A8ED50.md", W4 + r"\card_00A8ED50.md"),
    ("RULING_D19.md", ROOT + r"\lead\re_line_20261105\D19_RULING\RULING_D19.md"),
    ("FACTBASE_D19.md", ROOT + r"\lead\re_line_20261105\D19_RULING\FACTBASE_D19.md"),
]:
    h, s = sha_size(p)
    print("%-24s SHA256=%s  SIZE=%d" % (label, h, s))

e = Engine()
print()
banner("B3-1  Engine 自证")
print("EXE_SHA256 =", e.sha, " (EXPECT 73201cc...f67476)")
print("ImageBase  =", hex(e.IB))
print("coverage   =", e.coverage)
print("FO_87E8E0  =", e.fo(0x87E8E0), "(None => .data BSS 尾，无文件字节)")
print("FO_87E8B8  =", e.fo(0x87E8B8))
print("disp_hits(0x87E8E0) =", e.disp_hits(0x87E8E0))
print("disp_hits(0x87E8B8) =", e.disp_hits(0x87E8B8))
print("TOTAL_[reg+0x28] =", len(e.disp_hits_field(0x28)))

print()
banner("B3-2  C1 关键字节 A：ResetWorkspace 0x42A5B0..0x42A690 全函数")
show(e, 0x42A5B0, 0xE0, "ResetWorkspace 全函数（含 W1/G1/W2/tail ret）")
# 机械核对 W1 之前是否存在 ret，或存在跳过 W1 直达 0x42A688 的条件分支
seq = [i for i in e.stream if 0x42A5B0 <= i.address < 0x42A690]
rets_before_W1 = [(i.address, i.mnemonic, i.op_str) for i in seq
                  if i.mnemonic.startswith("ret") and i.address < 0x42A5FB]
print("RET before W1(0x42A5FB) =", rets_before_W1)
# 找所有以 0x42A688（W1/W2 后的收口）为目标的分支（若存在从 W1 之前跳过 W1 的则破坏「每次调用必 +1」）
skip = []
for i in seq:
    try:
        if i.mnemonic.startswith("j") and i.operands and i.operands[0].type == 2:
            t = i.operands[0].imm
            if i.address < 0x42A5FB and t >= 0x42A688:
                skip.append((i.address, i.mnemonic, hex(t)))
    except Exception:
        pass
print("branches BEFORE W1 that jump to/after 0x42A688 (would skip W1) =", skip)
by = e.by()
for va in (0x42A5FB, 0x42A5FE, 0x42A5FF, 0x42A602, 0x42A67F, 0x42A683,
           0x42A685, 0x42A688, 0x42A68D):
    i = by.get(va)
    print("CHECK 0x%08X = %s" % (va, (i.bytes.hex(), i.mnemonic, i.op_str) if i else "MISSING"))

print()
banner("B3-3  C1 关键字节 B：构造 0x42A6D0（W3 初值 -1）")
show(e, 0x42A6D0, 0x40, "CTOR head")
for va in (0x42A6D8, 0x42A6DC, 0x42A701, 0x42A704):
    i = by.get(va)
    print("CHECK 0x%08X = %s" % (va, (i.bytes.hex(), i.mnemonic, i.op_str) if i else "MISSING"))

print()
banner("B3-4  C1 关键字节 C：同步重试 G2 / 递增早于失败检查 G5")
show(e, 0x42CC6C, 0x40, "FindPath 同步重试层 0x42CC72/0x42CC80/0x42CC91/0x42CC9B")
show(e, 0x42D170, 0x20, "另一入口 0x42D170 head")
show(e, 0x42D17D, 0x14, "0x42D17D call 0x42A5B0")
show(e, 0x42D220, 0x14, "G5: call 0x42C290 -> test al,al -> je 失败(0x42D452)")
show(e, 0x42D450, 0x0C, "0x42D452 失败收口 mov eax,0x7fffffff")

print()
banner("B3-5  C1 关键字节 D：SearchCore 的「已展开节点数」是栈局部 [esp+0x28]")
show(e, 0x429AB0, 0x10, "0x429AB6 c7442428... 栈局部清零")
show(e, 0x429D6D, 0x14, "0x429D71 mov eax,[esp+0x28] 节点轮数")
show(e, 0x42A3D0, 0x10, "0x42A3D4 894c2428 栈局部")
show(e, 0x42A3DE, 0x14, "0x42A3DE mov ecx,[esp+0x28]; cmp ecx,0x2710")

print()
banner("B3-6  入口覆盖范围：xref 计数 / 单例立即数计数")
for t in (0x42A5B0, 0x42C900, 0x42D170, 0x42A6D0, 0x42A690, 0x42C290):
    x = xref_e8e9(e, t)
    print("XREF_E8E9 0x%08X count=%d  %s" % (t, len(x), ["0x%X:%s" % (a, m) for a, m, _ in x]))
pat = b"\xb9\xb8\xe8\x87\x00"  # mov ecx, 0x87e8b8
lst = raw_count(e, pat)
print("PATTERN 'b9 b8 e8 87 00' (mov ecx,0x87e8b8) in .text count =", len(lst))
print("VAs =", ["0x%X" % a for a in lst])
# 写点普查：路径簇内 [reg+0x28] 的写指令
w = [(a, m, o) for (a, rw, m, o) in e.disp_hits_field(0x28)
     if rw == "W" and 0x429000 <= a < 0x42E000]
print("PATHFINDER_CLUSTER [reg+0x28] WRITE count =", len(w))
for x in w:
    print("   W 0x%08X %s %s" % (x[0], x[1], x[2]))

print()
banner("B3-7  C4 支撑字节：Greatest_Threat 0x6F8DF0 入口读/增/写回 + 早退")
show(e, 0x6F8DF0, 0x60, "Greatest_Threat entry")
for va in (0x6F8DF3, 0x6F8E04, 0x6F8E09, 0x6F8E41):
    i = by.get(va)
    print("CHECK 0x%08X = %s" % (va, (i.bytes.hex(), i.mnemonic, i.op_str) if i else "MISSING"))
print("disp_hits(0xA8EC34) =", e.disp_hits(0xA8EC34))

print()
banner("B3-8  C2 支撑字节：0x6D3DF5 是 jne、test 在 0x6D3DFF；脏矩形 Count")
show(e, 0x6D3DF0, 0x18, "Render 判脏序列")
for va in (0x6D3DF0, 0x6D3DF5, 0x6D3DFF, 0x6D3E01):
    i = by.get(va)
    print("CHECK 0x%08X = %s" % (va, (i.bytes.hex(), i.mnemonic, i.op_str) if i else "MISSING"))
print("disp_hits(0xB0CE88) =", e.disp_hits(0xB0CE88))
print("disp_hits(0xB0CE78) =", e.disp_hits(0xB0CE78))

print()
banner("B3-DONE")
print("END_TIME =", datetime.datetime.now().isoformat())
