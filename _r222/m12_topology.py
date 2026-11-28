# -*- coding: utf-8 -*-
"""R222 m12：0x7c62ac 的单/双声道拓扑（copy1 = 单声道；copy2 -> copy3 = 双声道两声道各一遍）。

命题：
  T1 0x7c62df cmp word[ebx+0x3a],2 / je 0x7c63ea：声道数 == 2 时跳到 copy2，否则顺序走 copy1。
  T2 copy1 尾部 jmp 0x7c6609（函数返回）；copy2 尾部 0x7c64ea..0x7c6506 重建指针后 jmp 0x7c6509（进 copy3）。
  T3 copy3 的入口偏置：esi = [ebx]+1、edi = [ebx+4]+1，16 位模式再 inc edi => edi = +2（第二声道右声道偏移 2 B）。
  T4 copy3 尾部 sub dword[ebp-8],2 / jne 0x7c6509 后落到 0x7c6609 返回。
  T5 输出步进：copy1 edi += 2（16 位）/ inc（8 位）；copy2、copy3 edi += 4（16 位）/ += 2（8 位）=> 交错。
反控：
  R1 若声道数为 1 也走 copy2/copy3，则 copy1 的入口地址不应出现在 0x7c62ea 的顺序落入位置。
  R2 若 copy3 入口无 +2 偏置，则 0x7c6505 inc edi 不存在。
"""
import sys, re
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


head = [(a, mn, op) for a, b, mn, op in dis(0x7c62c0, 0x7c62ea)]
ck('T1a 0x7c62df cmp word[ebx+0x3a],2 + je 0x7c63ea（声道数分派）',
   any(a == 0x7c62df and mn == 'cmp' and op == 'word ptr [ebx + 0x3a], 2' for a, mn, op in head) and
   any(a == 0x7c62e4 and mn == 'je' and op == '0x7c63ea' for a, mn, op in head),
   [(hex(a), mn, op) for a, mn, op in head])
je = [(a, len(b) // 2, mn, op) for a, b, mn, op in dis(0x7c62e4, 0x7c62ec)][0]
ck('R1 反控：0x7c62e4 je 长 6 B，不成立时顺序落入 0x7c62ea（copy1 入口）',
   je[0] == 0x7c62e4 and je[1] == 6 and je[3] == '0x7c63ea' and je[0] + je[1] == 0x7c62ea, je)

t1 = [(a, mn, op) for a, b, mn, op in dis(0x7c63d8, 0x7c63ea)]
ck('T2a copy1 尾部 jmp 0x7c6609（返回）',
   any(a == 0x7c63e5 and mn == 'jmp' and op == '0x7c6609' for a, mn, op in t1),
   [(hex(a), mn, op) for a, mn, op in t1])
t2 = [(a, mn, op) for a, b, mn, op in dis(0x7c64e0, 0x7c6509)]
ck('T2b copy2 尾部重建 esi/edi 并 jmp 0x7c6509（进 copy3）',
   any(a == 0x7c64f0 and mn == 'mov' and op == 'esi, dword ptr [ebx]' for a, mn, op in t2) and
   any(a == 0x7c64f2 and mn == 'mov' and op == 'edi, dword ptr [ebx + 4]' for a, mn, op in t2) and
   any(a == 0x7c6501 and mn == 'jmp' and op == '0x7c6509' for a, mn, op in t2),
   [(hex(a), mn, op) for a, mn, op in t2])

t3 = [(a, mn, op) for a, b, mn, op in dis(0x7c64f0, 0x7c6509)]
ck('T3a copy3 入口 esi+1 / edi+2（16 位）或 edi+1（8 位）',
   any(a == 0x7c64f5 and mn == 'inc' and op == 'esi' for a, mn, op in t3) and
   any(a == 0x7c64f6 and mn == 'inc' and op == 'edi' for a, mn, op in t3) and
   any(a == 0x7c6505 and mn == 'inc' and op == 'edi' for a, mn, op in t3),
   [(hex(a), mn, op) for a, mn, op in t3])
ck('R2 反控：0x7c6505 inc edi 存在（否则无水声偏移 2 B）',
   any(a == 0x7c6505 and mn == 'inc' and op == 'edi' for a, b, mn, op in dis(0x7c6500, 0x7c6509)))
t4 = [(a, mn, op) for a, b, mn, op in dis(0x7c65f5, 0x7c6609)]
ck('T4 copy3 尾部 sub [ebp-8],2 / jne 0x7c6509，然后落 0x7c6609',
   any(a == 0x7c65ff and mn == 'sub' and op == 'dword ptr [ebp - 8], 2' for a, mn, op in t4) and
   any(a == 0x7c6603 and mn == 'jne' and op == '0x7c6509' for a, mn, op in t4),
   [(hex(a), mn, op) for a, mn, op in t4])
v = [(a, mn, op) for a, b, mn, op in dis(0x7c6609, 0x7c6613)]
ck('T4b 0x7c6609 是三者共享的返回块（mov eax,[ebp-4] + 五个 pop + leave + ret）',
   v[0][0] == 0x7c6609 and v[0][1] == 'mov' and any(mn == 'ret' for a, mn, op in v), v)


def estep(lo, hi):
    r = {'edi': [], 'esi': []}
    for a, b, mn, op in dis(lo, hi):
        for reg in ('edi', 'esi'):
            m = re.match(re.escape(reg) + r', ([0-9a-fx]+)$', op)
            if mn == 'add' and m:
                r[reg].append(int(m.group(1), 0))
            if mn == 'inc' and op == reg:
                r[reg].append(1)
    return r


s1 = estep(0x7c62ea, 0x7c63e8)
s2 = estep(0x7c63ea, 0x7c6509)
s3 = estep(0x7c6509, 0x7c6609)
print('copy1 steps', s1)
print('copy2 steps', s2)
print('copy3 steps', s3)
ck('T5a copy1 edi 步进含 2 与 1（16/8 位），无 4',
   2 in s1['edi'] and 1 in s1['edi'] and 4 not in s1['edi'], s1['edi'])
ck('T5b copy2 edi 步进含 4 与 2（16/8 位，交错）',
   4 in s2['edi'] and 2 in s2['edi'], s2['edi'])
ck('T5c copy3 edi 步进含 4 与 2', 4 in s3['edi'] and 2 in s3['edi'], s3['edi'])
ck('T5d copy1 源步进含 1（每字节 2 nibble 复用）', 1 in s1['esi'], s1['esi'])
ck('T5e copy2/copy3 源步进含 2（16 位）', 2 in s2['esi'] and 2 in s3['esi'], (s2['esi'], s3['esi']))
ck('T5f 反控：单声道输出步进 2 < 双声道步进 4 ⇒ 双声道写入隔字交错',
   max(s1['edi']) < max(s2['edi']) == max(s3['edi']) == 4, (s1['edi'], s2['edi'], s3['edi']))

print()
print('FAIL 数 =', len(fails), fails)
if fails:
    raise SystemExit(1)
