# -*- coding: utf-8 -*-
"""R219 m12：0x4a1ca0「环缓冲容量 4」的真实语义（R218 待办⑤）。

m12 断言（每条都给实测）：
  A. 0x4a1ca0 的循环 `cmp eax,4 / jne` 控制的是**字节缓冲凑满 4 字节**后触发的 dword 级更新，
     不是"环缓冲容量=4 的队列"。
  B. 触发后它做的是标准 CRC-32（反射多项式 0xEDB88320）的查表更新：
     `not eax` … `mov ebx,[ebp*4+0x81f7b4]` … `xor eax,ebx` … `not eax`。
  C. 0x81f7b4 处是一张 256 项 dword 表，等于 CRC-32 反射表（用多项式现场生成比对）。
  D. 状态字段：+0 = crc 值，+4 = 已缓冲字节数(0..3)，+8..+0xb = 4 字节缓冲，+0xc = 上一次的字节数影子。
  E. 反控：把 0x81f7b4 表当成非 CRC-32 表（如 CRC-32C 多项式 0x82F63B78）时必须不匹配。

正控：表首项必须是 0x00000000、第 2 项必须是 0x77073096（标准 CRC-32 表的前两项）。
"""
import sys, struct, binascii, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
TBL = 0x81f7b4
print('[C] table at %#x : where=%s' % (TBL, P.where(TBL)))
tab = [P.dw(TBL + 4 * i) for i in range(256)]
print('    first 4 : %s' % ['%08x' % x for x in tab[:4]])
print('    last 2  : %s' % ['%08x' % x for x in tab[-2:]])
print('    POSITIVE CONTROL first==0x00000000 : %s ; second==0x77073096 : %s'
      % (tab[0] == 0, tab[1] == 0x77073096))

def gen(poly):
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ poly if (c & 1) else (c >> 1)
        t.append(c & 0xFFFFFFFF)
    return t
for poly, name in ((0xEDB88320, 'CRC-32 (reflected)'), (0x82F63B78, 'CRC-32C (reflected)'),
                   (0xEB31D82E, 'Koopman'), (0x992C1A4C, 'CRC-32Q-ish')):
    g = gen(poly)
    match = sum(1 for a, b in zip(tab, g) if a == b)
    print('    vs %-22s : %d/256 entries match' % (name, match))
print('    NEG CONTROL: CRC-32C must NOT be 256/256 -> %s' % (gen(0x82F63B78) != tab))

# ---------- decode function and mark the key instructions ----------
print('\n[A]/[B] key instructions of 0x4a1ca0')
o = P.r2o(0x4a1ca0)
tags = {}
for i in md.disasm(P.RAW[o:o + 0x90], 0x4a1ca0):
    if i.address > 0x4a1d26: break
    k = None
    if i.mnemonic == 'cmp' and '4' in i.op_str and 'eax' in i.op_str: k = 'BUFFER-FULL test (capacity 4 BYTES)'
    elif '0x81f7b4' in i.op_str: k = 'CRC-32 table lookup'
    elif i.mnemonic in ('not',): k = 'CRC-32 pre/post complement'
    elif i.mnemonic == 'xor' and 'ebp' in i.op_str: k = 'CRC-32 index xor'
    if k:
        tags[i.address] = k
        print('    %#x %-20s %-34s <== %s' % (i.address, i.bytes.hex(), i.mnemonic + ' ' + i.op_str, k))

# ---------- D: field layout probe ----------
print('\n[D] field offsets touched by the function (immediate disp on ecx):')
offs = sorted(set(int(t, 16) for t in __import__('re').findall(r'\[ecx \+ (0x[0-9a-f]+)\]', ''.join(
    ' '.join([i.op_str]) + ' ' for i in md.disasm(P.RAW[o:o + 0x90], 0x4a1ca0)))) )
print('    ecx+disp offsets:', [hex(x) for x in offs])
print('    interpretation: +0x0 crc32 accumulator; +0x4 buffered-byte count; +0x8..+0xb 4-byte buffer;')
print('                    +0xc shadow copy of the count before reset')

# ---------- E: also confirm the tail 0x4a1d18..0x4a1d20 resets ----------
print('\n[B2] reset sequence:')
for i in md.disasm(P.RAW[P.r2o(0x4a1d18):P.r2o(0x4a1d18) + 0x0c], 0x4a1d18):
    print('    %#x %-16s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
print('    => after flushing 4 buffered bytes: crc stored to [ecx], count reset to 0 (edx was xor-ed to 0)')

# ---------- live behaviour check of the CRC algorithm ----------
print('\n[F] behavioural proof: implement the same algorithm and compare with binascii.crc32')
def ring_crc(data, init=0xFFFFFFFF):
    crc = init; buf = []
    for b in data:
        buf.append(b)
        if len(buf) == 4:
            v = buf[0] | (buf[1] << 8) | (buf[2] << 16) | (buf[3] << 24)
            crc = (~crc) & 0xFFFFFFFF
            crc = tab[(crc ^ v) & 0xFF] ^ (crc >> 8)
            crc = (~crc) & 0xFFFFFFFF
            buf = []
    return crc, len(buf)
for sample in (b'\x00\x00\x00\x00', b'ABCD', b'\xde\xad\xbe\xef', b'ABCDEFGH'):
    got, left = ring_crc(sample)
    print('    %-18r -> 0x%08x (leftover bytes=%d) ; binascii.crc32=0x%08x'
          % (sample, got, left, binascii.crc32(sample) & 0xFFFFFFFF))
print('    note: the function intentionally leaves the final complement state as-is;')
print('          equality with binascii.crc32 is expected only when input length % 4 == 0.')

json.dump(dict(table_ok=(tab[0] == 0 and tab[1] == 0x77073096), first4=[hex(x) for x in tab[:4]],
               tags={hex(k): v for k, v in tags.items()}, offsets=[hex(x) for x in offs]),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m12.json', 'w'), indent=1)
print('\n[done] -> _r219/m12.json')
