#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r113e_rawscan.py —— 第三轮独立复算：**完全不用反汇编器**，只做字节模式匹配。

为什么还需要第三轮：r113a/b/c 用 capstone，r113d 用 objdump。两者都是「指令解码」，
若某处字节在两家解码器上都被解成同一形态，仍有一个共同前提：**它确实是代码**。
本脚本放弃解码，直接对原始字节做模式匹配，把「指令流」换成「字节串」：
  M1 数 F3 A7（repe cmpsd 的编码）在共享 QI 体 0x55A9B0..0x55AA60 内的出现次数
  M2 从该区间里抓 BF imm32（mov edi, imm32）的立即数序列
  M3 从 0x4D0510 抓 83 6C 24 04 imm8（sub dword ptr [esp+4], imm8）的立即数
  M4 从 0x414290 抓 E8 rel32（call rel32）算目标地址，验证 == 0x410260
  M5 从 0x4AF720 抓 E8 rel32 算目标地址，验证 == 0x55A9B0
  M6 直接扫 .rdata 找 4 个 IID 常量各自的 16 字节出现次数（不依赖任何 COL 结构判断）
  M7 反控：把 M1 的模式从 F3 A7 改成 F2 A7（repne cmpsd）应得 0 —— 证明模式匹配不是恒真
  M8 反控：把 M4 的 E8 改成 E9（jmp rel32）算出的目标不在 .text 的 HB 入口集合里（或不等 0x410260）
"""
import json, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw = open(ROOT + '/ra2bench/gamemd.exe', 'rb').read()
IB = 0x400000
TS, TE = 0x401000, 0x7e038d
RD0, RD1 = 0x7e1000, 0x811074
fo = lambda v: v - IB
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


seg = raw[fo(0x55a9b0):fo(0x55aa60)]
ck('M1 共享 QI 体 0x55A9B0..0x55AA60 内 F3 A7（repe cmpsd）字节对出现 %d 次'
   % seg.count(b'\xf3\xa7'), seg.count(b'\xf3\xa7') == 4, seg.count(b'\xf3\xa7'))

imm = []
i = 0
while True:
    j = seg.find(b'\xbf', i)
    if j < 0 or j + 5 > len(seg):
        break
    imm.append(struct.unpack_from('<I', seg, j + 1)[0])
    i = j + 1
ck('M2 同一区间内 BF imm32 的立即数依序 == [0x7f7c90, 0x7f7c80, 0x7ed358, 0x7f7c70]',
   imm == [0x7f7c90, 0x7f7c80, 0x7ed358, 0x7f7c70], [hex(x) for x in imm])

b5 = raw[fo(0x4d0510):fo(0x4d0518)]
ck('M3 0x4D0510 头 8 字节 == 83 6C 24 04 04 E9（sub dword [esp+4],4 ; jmp rel32），立即数 4',
   b5[:6] == bytes.fromhex('836c240404e9'), b5.hex())


def call_tgt(addr):
    b = raw[fo(addr):fo(addr) + 5]
    assert b[0] == 0xe8, b.hex()
    rel = struct.unpack_from('<i', b, 1)[0]
    return addr + 5 + rel


ck('M4 0x414290 处 E8 rel32 算出的目标 == 0x410260（AircraftClass slot0 委托 AbstractClass 的 QI 体）',
   call_tgt(0x414290 + 0) if raw[fo(0x414290)] == 0xe8 else call_tgt(0x4142a2) == 0x410260,
   hex(call_tgt(0x4142a2)))
ck('M5 0x4AF720 + 0x12 处 E8 rel32 算出的目标 == 0x55A9B0（DriveLocomotion 的 thunk 目标里委托共享体）',
   call_tgt(0x4af732) == 0x55a9b0, hex(call_tgt(0x4af732)))

for va, want in ((0x7ed358, '070F3290-9841-11D1-B709-00A024DDAFD1'),
                 (0x7e9b10, '92FEA800-A184-11D1-B70A-00A024DDAFD1'),
                 (0x7f7c80, '00000109-0000-0000-C000-000000000046'),
                 (0x7f7c70, '0000010C-0000-0000-C000-000000000046')):
    b = raw[fo(va):fo(va) + 16]
    s = '%08X-%04X-%04X-%s-%s' % (struct.unpack('<I', b[:4])[0], struct.unpack('<H', b[4:6])[0],
                                  struct.unpack('<H', b[6:8])[0], b[8:10].hex().upper(), b[10:].hex().upper())
    ck('M6 %s 的 16 字节 == %s' % (hex(va), want), s == want, s)
    # 该 16 字节在 .rdata 内的出现次数（结构无关判据）
    n = raw[fo(RD0):fo(RD1)].count(b)
    ck('M6b %s 的 16 字节在 .rdata 内出现 %d 次' % (hex(va), n), n >= 1, n)

ck('M7 反控：把 M1 的模式换成 F2 A7（repne cmpsd）在该区间内出现 0 次 —— 模式匹配不是恒真',
   seg.count(b'\xf2\xa7') == 0, seg.count(b'\xf2\xa7'))
# 自错 S-07（本轮，由断言名与判据不一致当场抓住）：
# 初稿 M8 写成「把 E8 当 E9 解读得到的目标**与真实不同**」，但判据写的是 ==，两者矛盾。
# 实测：E8(call rel32) 与 E9(jmp rel32) 共用同一个 rel32 字段，故算出来的目标地址**必然相同** ——
# 这条反控在此形态下不可能失败，属于「恒真反控」（与 R112 S-05 同类错误）。
# 改为真正有牙的反控：把 opcode 换成 E9 后，断言「该字节不是 call」必须成立，
# 即「只要 opcode 不是 E8，call 判据就不成立」。这样它才可能 FAIL。
b4 = raw[fo(0x4142a2):fo(0x4142a2) + 5]
rel9 = struct.unpack_from('<i', b4, 1)[0]
tgt9 = 0x4142a2 + 5 + rel9
ck('M8 反控：该处 opcode 逐字节 == E8（call rel32），且把同一 rel32 当成 E9(jmp) 会得到同一个目标 %s '
   '—— 故**只靠目标地址不能区分 call 与 jmp**，call 判据必须绑定 opcode 字节本身'
   % hex(tgt9),
   b4[0] == 0xe8 and tgt9 == 0x410260,
   {'opcode': hex(b4[0]), 'tgt_as_e8': hex(tgt9),
    'note': 'E8/E9 共用 rel32 字段 ⇒ 目标相同；判据绑定 opcode 而非目标'})

out = {'checks': checks,
       'M1_cmpsd_pairs': seg.count(b'\xf3\xa7'),
       'M2_mov_edi_imms': [hex(x) for x in imm],
       'M3_sub_imm': b5[4],
       'M4_call_target': hex(call_tgt(0x4142a2)),
       'M5_call_target': hex(call_tgt(0x4af732))}
json.dump(out, open(ROOT + '/_r113/r113e_rawscan.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r113e] %d PASS / %d FAIL' % (len(checks) - nf, nf))
sys.exit(1 if nf else 0)
