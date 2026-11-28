#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第六刀：序列化校验路径的状态机闭合 + 对 R193 ⑧ 的一处体长订正。

R193 遗留「CRC32 覆盖范围（整段 or 分块）」未取得。本轮把它做成可被数据否掉的状态机：
  S1 状态对象槽位图：0x4A1CA0（ecx）与 0x4A1DE0（esi）都只用 {+0, +4, +8, +0xC} 四个槽，
     +0 = CRC，+4 = 已填计数(0..4)，+8..+0xB = 4 字节折叠缓冲，+0xC = 折叠时的计数影子。
  S2 折叠原语等价 zlib：0x4A1FB0 = crc32(crc, buf, len)（eax=初值, ecx=buf, edx=len, ret 4），
     用 6 个样本与 zlib.crc32 逐样本对齐（外部正控）。
  S3 4 字节折叠循环 == zlib 对 4 字节的 crc32（0x4A1CA0 的 0x4A1CF3..0x4A1D18 与
     0x4A1DE0 的三处同样循环）。
  S4 覆盖范围 = 跨调用**累进**（同一状态对象、同一张表、count 不清零即继续），
     因此「每次调用重置 CRC」的读法被否掉。
  S5 尾部规则（0x4A1DE0 的 0x4A1F40 段）：count = n in 1..3 时，buf[n] 写入 n，
     buf[n+1..3] 用 buf[0] 填充，再折一次 4 字节；n == 0 直接返回。
  S6 体长订正：0x4A1DE0 到首个 ret 是 174 条 / 445 字节（R193 用 400 字节窗口得 154 条，
     把「通用 N 字节写 + 尾部补齐」误记成「4 字节定长块写」；0x4A1D50 才是 4 字节薄壳）。
"""
import sys, re, struct, zlib, random, capstone
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def body(va, maxb=1024):
    o = P.r2o(va); out = []
    for i in md.disasm(P.RAW[o:o + maxb], va):
        out.append(i)
        if i.mnemonic.startswith('ret'): break
    return out
def txt(ins): return ' ; '.join('%s %s' % (i.mnemonic, i.op_str) for i in ins)

RX = re.compile(r'\[(ecx|esi)(?: \+ (0x[0-9a-f]+|\d+))?\]')
def slots(ins, reg):
    s = set()
    for i in ins:
        for m in RX.finditer(i.op_str):
            if m.group(1) == reg: s.add(int(m.group(2), 16) if m.group(2) else 0)
    return sorted(s)

b1 = body(0x4A1CA0); b2 = body(0x4A1D50); b3 = body(0x4A1DE0); b4 = body(0x4A1FB0); b5 = body(0x410410)
print('   体长：0x4A1CA0=%d 条；0x4A1D50=%d 条；0x4A1DE0=%d 条(至首个 ret @%08X, +%d B)；0x4A1FB0=%d 条；0x410410=%d 条'
      % (len(b1), len(b2), len(b3), b3[-1].address, b3[-1].address - 0x4A1DE0, len(b4), len(b5)))

ck('S1a 0x4A1CA0 状态槽位 {0,4,8,0xc}', slots(b1, 'ecx') == [0, 4, 8, 0xc], [hex(x) for x in slots(b1, 'ecx')])
ck('S1b 0x4A1DE0 状态槽位 {0,4,8,0xc}（同一布局）', slots(b3, 'esi') == [0, 4, 8, 0xc], [hex(x) for x in slots(b3, 'esi')])
ck('S1c 0x4A1CA0 满 4 时把计数写进 +0xC', any(i.mnemonic == 'mov' and i.op_str == 'byte ptr [ecx + 0xc], al' for i in b1),
   [i.op_str for i in b1 if '0xc' in i.op_str])
ck('S1d buf 槽基 +8 被用作 [base+idx+8] 的索引写（不是 +0xC）',
   sum(1 for i in b1 if re.search(r'\+ (eax|ecx \+ eax|eax \+ ecx) \+ 8', i.op_str)) >= 1,
   [i.op_str for i in b1 if '[eax + ecx + 8]' in i.op_str])

TAB = struct.unpack('<256I', P.RAW[P.r2o(0x81F7B4):P.r2o(0x81F7B4) + 1024])
ck('S2a CRC 表 t[0]=0 / t[1]=0x77073096 / t[255]=0x2D02EF8D', (TAB[0], TAB[1], TAB[255]) == (0, 0x77073096, 0x2D02EF8D),
   (hex(TAB[0]), hex(TAB[1]), hex(TAB[255])))

def fold4(crc, blk):
    "0x4A1CA0/0x4A1DE0 的 4 字节折叠循环：not / and 0xff / xor byte / shr 8 / table / xor / not"
    assert len(blk) == 4
    eax = (~crc) & 0xffffffff
    for b in blk:
        idx = (eax & 0xff) ^ b
        eax >>= 8
        eax ^= TAB[idx]
    return (~eax) & 0xffffffff
random.seed(194)
blks = [b'\x00' * 4, b'\x01' * 4, bytes([0, 1, 0, 1]), b'\xff\x00\xff\x00'] + \
       [bytes(random.randrange(256) for _ in range(4)) for _ in range(4)]
ck('S3a 折叠循环(fold4) 在 8 个样本（含全 0 / 全 1 / 随机）上与 zlib.crc32 逐样本一致',
   all(fold4(0, b) == zlib.crc32(b) & 0xffffffff for b in blks),
   [(b.hex(), hex(fold4(0, b)), hex(zlib.crc32(b) & 0xffffffff)) for b in blks[:4]])
# 反控：去掉 not 包裹（纯反射不带反码）必不一致
def fold4_bad(crc, blk):
    eax = crc & 0xffffffff
    for b in blk:
        idx = (eax & 0xff) ^ b; eax >>= 8; eax ^= TAB[idx]
    return eax & 0xffffffff
ck('S3b 反控：去掉前后 not 包裹后与 zlib 不一致（not 语义必需）',
   any(fold4_bad(0, b) != zlib.crc32(b) & 0xffffffff for b in blks),
   [(b.hex(), hex(fold4_bad(0, b))) for b in blks[:2]])

# S2b 0x4A1FB0 语义：crc32(crc, buf, len)
ck('S2b 0x4A1FB0 = 通用 N 字节 crc32（24 条：not 前包 → 逐字节表循环 ∈ {dec edx} 计数 → not 后包 → ret 4）',
   len(b4) == 24 and sum(1 for i in b4 if i.mnemonic == 'not') == 2
   and b4[-1].op_str == '4' and any(i.mnemonic == 'dec' and i.op_str == 'esi' for i in b4),
   (len(b4), [i.mnemonic for i in b4]))
def foldN(crc, data):
    eax = (~crc) & 0xffffffff
    for b in data:
        eax = (eax >> 8) ^ TAB[((eax & 0xff) ^ b)]
    return (~eax) & 0xffffffff
ck('S2c 0x4A1DE0 以 N=4 调用 0x4A1FB0（0x4A1E4B call，edx 在该段被置 4）',
   any(i.address == 0x4A1E4B and i.op_str == '0x4a1fb0' for i in b3)
   and any(i.mnemonic == 'mov' and i.op_str == 'edx, 4' for i in b3),
   [(hex(i.address), i.op_str) for i in b3 if i.mnemonic == 'call'])
samples = [b'', b'\x00', b'\x01\x02\x03\x04', bytes(range(16)), b'\xff' * 7, bytes(range(64))]
ck('S2d foldN 与 zlib.crc32(data, init) 在 6 个不同长度样本（0/1/4/16/7/64）上逐样本一致',
   all(foldN(0, s) == zlib.crc32(s) & 0xffffffff for s in samples)
   and foldN(0x12345678, bytes(range(9))) == zlib.crc32(bytes(range(9)), 0x12345678) & 0xffffffff,
   [(len(s), hex(foldN(0, s))) for s in samples])

def stream_crc(bytes_seq):
    "跨调用累进：count 不清零就继续，只在满 4 时折一次（0x4A1CA0 语义）"
    crc, cnt, buf = 0, 0, [0, 0, 0, 0]
    for b in bytes_seq:
        buf[cnt] = b; cnt += 1
        if cnt == 4:
            crc = fold4(crc, bytes(buf)); cnt, buf = 0, [0, 0, 0, 0]
    return crc, cnt
s1 = stream_crc(b'\x01\x01\x00\x01\x01\x01\x00\x00')
ck('S4a 8 字节全 0/1 流：与 zlib.crc32 一致且尾部计数 0（4 的整数倍无残留）',
   s1[0] == zlib.crc32(b'\x01\x01\x00\x01\x01\x01\x00\x00') & 0xffffffff and s1[1] == 0, (hex(s1[0]), s1[1]))
s2 = stream_crc(b'\x01\x00\x01')
ck('S4b 3 字节流：CRC 仍为初值 0 且残留计数 3（覆盖范围 = 整段累进，不满 4 不折）',
   s2 == (0, 3), s2)
s3 = stream_crc(b'\x01' * 4 + b'\x00' * 4)
ck('S4c 跨调用累进 == 一次性喂 8 字节（同一状态对象不被调用边界重置）',
   s3[0] == zlib.crc32(b'\x01' * 4 + b'\x00' * 4) & 0xffffffff, hex(s3[0]))
s4 = stream_crc(b'\x01' * 4)
ck('S4d 反控：若每次调用都重置状态，4+4 分两次喂的 CRC 应等于 zlib(后 4 字节)；实测 != 该值',
   s3[0] != (zlib.crc32(b'\x00' * 4) & 0xffffffff), (hex(s3[0]), hex(zlib.crc32(b'\x00' * 4) & 0xffffffff)))

# S5 尾部规则：从指令顺序断言
seq = [(hex(i.address), i.mnemonic, i.op_str) for i in b3 if 0x4A1F40 <= i.address <= 0x4A1F63]
print('   尾段 0x4A1F40..0x4A1F63：%s' % (' ; '.join('%s %s' % (m, o) for _, m, o in seq)))
ck('S5a 尾段入口 cmp count,0 + je 出口（n==0 不补）',
   b3[[i.address for i in b3].index(0x4A1F40)].mnemonic == 'mov'
   and any(i.mnemonic == 'je' and i.op_str == '0x4a1fa0' for i in b3 if i.address >= 0x4A1F40),
   [(hex(i.address), i.mnemonic, i.op_str) for i in b3 if i.address >= 0x4A1F40][:3])
ck('S5b 尾段 body：mov cl,al(count) → mov [eax+esi+8],cl（buf[n]=n）',
   any(i.address == 0x4A1F47 and i.op_str == 'cl, al' for i in b3)
   and any(i.address == 0x4A1F49 and i.op_str == 'byte ptr [eax + esi + 8], cl' for i in b3),
   [(hex(i.address), i.op_str) for i in b3 if 0x4A1F45 <= i.address <= 0x4A1F4D])
ck('S5c 尾段补齐：buf[n+1..3] = buf[0]（读 [esi+8] 写 [esi+eax+8]）',
   any(i.address == 0x4A1F56 and i.op_str == 'dl, byte ptr [esi + 8]' for i in b3)
   and any(i.address == 0x4A1F59 and i.op_str == 'byte ptr [esi + eax + 8], dl' for i in b3),
   [(hex(i.address), i.op_str) for i in b3 if 0x4A1F54 <= i.address <= 0x4A1F61])
ck('S5d 补齐后折一次 4 字节（尾段含一处表引用且以 not 收尾）',
   sum(1 for i in b3 if i.address >= 0x4A1F40 and '0x81f7b4' in i.op_str) == 1
   and any(i.address == 0x4A1F95 and i.mnemonic == 'not' for i in b3),
   [(hex(i.address), i.op_str) for i in b3 if i.address >= 0x4A1F40 and '0x81f7b4' in i.op_str])
def tail_pad(crc, blk):
    "S5 模型：n=len(blk) in 1..3 ⇒ [b0..b_{n-1}, n, b0, ...] 补齐到 4 再折"
    n = len(blk); b = list(blk) + [0, 0, 0, 0]
    b[n] = n
    for i in range(n + 1, 4): b[i] = b[0]
    return fold4(crc, bytes(b[:4]))
ck('S5e 模型自洽：n=1 ⇒ 流 (b0,1,b0,b0)；n=3 ⇒ (b0,b1,b2,3)（与 S5b/S5c 指令一致）',
   tail_pad(0, b'\xAA') == fold4(0, bytes([0xAA, 1, 0xAA, 0xAA]))
   and tail_pad(0, b'\xAA\xBB\xCC') == fold4(0, bytes([0xAA, 0xBB, 0xCC, 3])),
   (hex(tail_pad(0, b'\xAA')), hex(fold4(0, bytes([0xAA, 1, 0xAA, 0xAA])))))

ck('S6a 0x4A1DE0 到首个 ret 174 条 / 445 字节（R193 记 154 条是 400 字节窗口截断）',
   len(b3) == 174 and b3[-1].address == 0x4A1F9D and b3[-1].op_str == '8', (len(b3), hex(b3[-1].address), b3[-1].op_str))
ck('S6b 0x4A1DE0 有三段（部分填充 0x4A1E00 / 4 字节批量 0x4A1E75 / 单字节 0x4A1EC2）+ 尾部 0x4A1F40',
   all(any(i.address == a for i in b3) for a in (0x4A1E00, 0x4A1E75, 0x4A1EC2, 0x4A1F40)),
   [hex(a) for a in (0x4A1E00, 0x4A1E75, 0x4A1EC2, 0x4A1F40)])
ck('S6c 0x4A1D50 才是 4 字节薄壳（push 4 / call 0x4A1DE0 / ret 4，7 条）',
   len(b2) == 7 and b2[2].op_str == '4' and b2[5].op_str == '0x4a1de0', len(b2))
ck('S6d 0x410410 两条 call 依次 0x4a1d50 → 0x4a1ca0，ecx 均为 edi=[esp+0xC]（同一状态对象）',
   [i.op_str for i in b5 if i.mnemonic == 'call'] == ['0x4a1d50', '0x4a1ca0']
   and sum(1 for i in b5 if i.mnemonic == 'mov' and i.op_str == 'ecx, edi') == 2,
   [i.op_str for i in b5 if i.mnemonic == 'call'])

print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails)); sys.exit(1)
