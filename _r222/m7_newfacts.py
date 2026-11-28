# -*- coding: utf-8 -*-
"""R222 m7：四条新结论的独立复算 + 反控。

N1 0x7c62ac 是「内联式解码器」（吃 packed nibble、吐样本），不是编码器：
   - 入口读 byte ptr [esi]（每次 1 B，含 2 个 nibble），写 word/byte ptr [edi]（样本），
   - 用 dword[ebx+0x10] 的 bit0 选择「取低半字节 / 取高半字节」，
   - 全程不引用差分表 0x879b30（引用 0 条），delta 由 test eax,4/2/1 + shr 3 + test eax,8 内联算出。
N2 0x8758d4「0 次字面引用」≠ 死数据：0x8758c4+2*nibble（nibble 0..15）跨到 0x8758d4，
   即两处 16 B 合起来是一张 16 项索引表 = IDX[n&7] 的显式复制。
N3 0x7c6752 与 0x7c7371 是两个接受集不同的分派器：前者只收 (16bit,1ch)，后者收 (16bit,1ch) 与 (16bit,2ch)。
N4 0x7c62ac 内有三份展开副本（各带自己的 0x8758c4/0x8758e4 引用），对应 3 次字面引用。
反控：
  R1 若把 nibble 当成 0..7（只查 8 项），则 0x8758d4 永不参与 → 但与实测 nibble 上界 15 冲突。
  R2 若 0x7c69ad 是活分支（不是尾声），则它必须有 in-edge 之外的出口 → 实测它是否 pop/ret。
"""
import sys, re, struct, hashlib
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
fails = []


def ck(n, c, d=''):
    if not c:
        fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))


def dis(lo, hi):
    o = P.r2o(lo)
    b = P.RAW[o:o + (hi - lo)]
    return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(b, lo)]


print('sha256 =', hashlib.sha256(P.RAW).hexdigest())

# ---- N1 ----
seq = dis(0x7c62ac, 0x7c63ea)
nib_src = [(a, mn, op) for a, b, mn, op in seq if mn == 'mov' and op == 'al, byte ptr [esi]']
out16 = [(a, mn, op) for a, b, mn, op in seq if mn == 'mov' and op == 'word ptr [edi], ax']
out8 = [(a, mn, op) for a, b, mn, op in seq if mn == 'mov' and op == 'byte ptr [edi], ah']
sel = [(a, mn, op) for a, b, mn, op in seq if mn == 'test' and op.startswith('dword ptr [ebx + 0x10]')]
sh4 = [(a, mn, op) for a, b, mn, op in seq if mn == 'shr' and op == 'eax, 4']
ck('N1a 0x7c62ac 入口读 byte[esi]（1 B = 2 nibble）', len(nib_src) == 1, nib_src)
ck('N1b 出口写样本 word[edi],ax（16 位路径）', len(out16) == 1, out16)
ck('N1c 出口写样本 byte[edi],ah（8 位路径，xor ah,0x80 后）', len(out8) == 1, out8)
ck('N1d 用 test dword[ebx+0x10],1 选半字节 + shr eax,4 取高半字节', len(sel) == 1 and len(sh4) == 1, (sel, sh4))
# nibble 上界 = 0xf
d = [(a, mn, op) for a, b, mn, op in seq]
ck('N1e nibble 被 and eax,0xf 截到 0..15',
   any(mn == 'and' and op == 'eax, 0xf' for a, mn, op in d), [x for x in d if x[1] == 'and'])
# 整个 0x7c62ac 函数体内 0x879b30 引用数
refs = [a for a, b, mn, op in dis(0x7c62ac, 0x7c6620) if '0x879b30' in op]
ck('N1f 0x7c62ac 全函数 0x879b30 引用 0 条（in-line delta）', refs == [], refs)

# ---- N2 ----
base = 0x8758c4
lo_addr = base + 2 * 0
hi_addr = base + 2 * 15
ck('N2a nibble 15 的查表地址 >= 0x8758d4', hi_addr >= 0x8758d4, hex(hi_addr))
ck('N2b nibble 0..7 落在 0x8758c4..0x8758d3', base + 2 * 7 + 1 <= 0x8758d3, hex(base + 2 * 7 + 1))
T16 = [struct.unpack_from('<h', P.RAW, P.r2o(base) + 2 * k)[0] for k in range(16)]
T8 = [struct.unpack_from('<h', P.RAW, P.r2o(0x8758c4) + 2 * k)[0] for k in range(8)]
ck('N2c 16 项 = IDX[n&7] 两遍', T16 == T8 + T8, T16)
ck('N2d 0x8758d4 处 16 B 与 0x8758c4 处 16 B 逐字节相同',
   P.RAW[P.r2o(0x8758c4):P.r2o(0x8758c4) + 16] == P.RAW[P.r2o(0x8758d4):P.r2o(0x8758d4) + 16])
# 反控 R1：若按 8 项口径（nibble&7）建模，与 16 项口径结果相同 —— 说明「0 字面引用」不等于「无作用」
same = all(T16[n] == T8[n & 7] for n in range(16))
ck('N2e 16 项表语义等价于 IDX[n&7]（反控：字面引用 0 但确被读到）', same)
k = [a for a, b, mn, op in dis(0x7c639b, 0x7c63a0)]
ins = [(a, mn, op) for a, b, mn, op in dis(0x7c6397, 0x7c63a2)]
ck('N2f 读取指令为 mov ax,word[ecx+0x8758c4]，ecx=2*nibble（shl ecx,1）',
   any(mn == 'shl' and op == 'ecx, 1' for a, mn, op in ins) and
   any(mn == 'mov' and op == 'ax, word ptr [ecx + 0x8758c4]' for a, mn, op in ins), ins)

# ---- N3 ----
a = [(x, mn, op) for x, b, mn, op in dis(0x7c6765, 0x7c67a4)]
b = [(x, mn, op) for x, bb, mn, op in dis(0x7c7384, 0x7c73c3)]
ck('N3a 0x7c6752 (cx==8,dx==2) -> 0x7c69ad',
   [op for x, mn, op in a if x == 0x7c6771] == ['0x7c69ad'], [op for x, mn, op in a if x == 0x7c6771])
ck('N3b 0x7c6752 (cx==8,dx==1) -> 0x7c69ad',
   [op for x, mn, op in a if x == 0x7c6780] == ['0x7c69ad'], [op for x, mn, op in a if x == 0x7c6780])
ck('N3c 0x7c6752 (cx==0x10,dx==2) -> 0x7c69ad（拒 stereo）',
   [op for x, mn, op in a if x == 0x7c6795] == ['0x7c69ad'], [op for x, mn, op in a if x == 0x7c6795])
tail = [(x, len(bb) // 2, mn, op) for x, bb, mn, op in dis(0x7c679a, 0x7c67b0)]
ck('N3d 0x7c6752 (cx==0x10,dx==1) 顺序落入 0x7c67a4（0x7c679e jne 6 B 后即 0x7c67a4）',
   any(x == 0x7c679e and ln == 6 and mn == 'jne' and x + ln == 0x7c67a4 for x, ln, mn, op in tail),
   [(hex(x), ln, mn, op) for x, ln, mn, op in tail])
ck('N3e 0x7c7371 (cx==0x10,dx==2) -> 0x7c7788（收 stereo）',
   [op for x, mn, op in b if x == 0x7c73b4] == ['0x7c7788'], [op for x, mn, op in b if x == 0x7c73b4])
ex = [(x, mn, op) for x, bb, mn, op in dis(0x7c69ad, 0x7c69c0)]
print('   0x7c69ad 内容:', [(hex(x), mn, op) for x, mn, op in ex][:8])
ck('N3f 0x7c69ad 是尾声（pop/leave/ret 序列，不是解码分支）',
   any(mn in ('leave', 'ret') for x, mn, op in ex), [(hex(x), mn) for x, mn, op in ex][:6])

# ---- N4 ----
idxs = [a for a, bb, mn, op in dis(0x7c62ac, 0x7c6620) if '0x8758c4' in op]
steps = [a for a, bb, mn, op in dis(0x7c62ac, 0x7c6620) if '0x8758e4' in op]
ck('N4a 0x7c62ac 内 0x8758c4 引用 3 条', len(idxs) == 3, [hex(x) for x in idxs])
ck('N4b 0x7c62ac 内 0x8758e4 引用 3 条', len(steps) == 3, [hex(x) for x in steps])
pro = [0x7c62ac + 0 for _ in range(1)]
# 三份展开副本的循环回边
backs = [(x, op) for x, bb, mn, op in dis(0x7c62ac, 0x7c6620)
         if mn in ('jne',) and op.startswith('0x') and int(op, 16) < x]
ck('N4c 三条 jne 回边 => 三份展开副本', len(backs) == 3, [(hex(x), op) for x, op in backs])

# ---- 附加：块1 分派器与块2 分派器的解引用表 ----
for t, n in ((0x7c6b58, 8), (0x7c6b38, 8), (0x7c6b78, 4)):
    v = [struct.unpack_from('<I', P.RAW, P.r2o(t) + 4 * k)[0] for k in range(n)]
    good = sum(1 for x in v if P.sec_of(x) == '.text')
    print('   table %08x: %s  有效 %d/%d' % (t, [hex(x) for x in v], good, n))
ck('N5a 0x7c6b58 只有前 4 项是地址', sum(1 for k in range(4) if P.sec_of(struct.unpack_from('<I', P.RAW, P.r2o(0x7c6b58) + 4 * k)[0]) == '.text') == 4 and
   sum(1 for k in range(4, 8) if P.sec_of(struct.unpack_from('<I', P.RAW, P.r2o(0x7c6b58) + 4 * k)[0]) == '.text') == 0)
ck('N5b 0x7c6b38 八项全是地址',
   all(P.sec_of(struct.unpack_from('<I', P.RAW, P.r2o(0x7c6b38) + 4 * k)[0]) == '.text' for k in range(8)))

print()
print('FAIL 数 =', len(fails), fails)
if fails:
    raise SystemExit(1)
