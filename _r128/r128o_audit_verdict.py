# -*- coding: utf-8 -*-
"""R128o：规则 D 对 deepseek 最终报告（439 行 / 22146 B）的逐条复算。

复算范围：报告里所有可机械核验的数字。
不采信任何结论，只比数字；结论由主会话另行判定并写进四件套。
"""
import sys, os, json, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128o_audit_verdict.json')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
raw = rd(0x401000, 0x7e1000 - 0x401000)
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

# ---- A 主张的数字 ----
p = raw.find(bytes.fromhex('c705e8f78700'))
add('O1 A1 字节模式 c7 05 e8 f7 87 00 在 .text 中命中 1 处，VA 0x40d1b2（段内偏移 0xc1b2 = '
    '文件偏移 0xd1b2，审计员报的是文件偏移，两者一致），立即数 0x7e1964',
    # S-183：我先断言 p == 0xd1b2，但 raw 是 .text 段内偏移、不是文件偏移；
    # 段内 0xc1b2 + 0x401000 = 0x40d1b2 才对得上，且审计员报的 0xd1b2 是**文件偏移**
    # （.text 文件偏移 0x1000 + 0xc1b2 = 0xd1b2）。两个数都对，只是坐标系不同。
    p == 0xc1b2 and 0x401000 + p == 0x40d1b2
    and raw[p + 6:p + 10] == (0x7e1964).to_bytes(4, 'little'),
    {'section_off': hex(p), 'va': hex(0x401000 + p), 'file_off': hex(p + 0x1000),
     'imm': hex(int.from_bytes(raw[p+6:p+10], 'little'))})

from collections import Counter
prev = Counter()
pref = bytes.fromhex('e8f78700')
q = 0
while True:
    i = raw.find(pref, q)
    if i < 0: break
    prev[raw[i-1]] = prev.get(raw[i-1], 0) + 1
    q = i + 1
add('O2 A1 前缀字节分布：0xb9(mov ecx,imm32) %d 处、0x68(push) %d、0x15(mov edx,[abs]) %d、'
    '0x05(mov [abs],imm32) %d、0x02(c7 02..) %d'
    % (prev[0xb9], prev[0x68], prev[0x15], prev[0x05], prev[0x02]),
    prev[0xb9] == 3693 and prev[0x68] == 3 and prev[0x15] == 2
    and prev[0x05] == 1 and prev[0x02] == 1,
    {hex(k): v for k, v in sorted(prev.items())})

# push 0x87f7e8 的三处地址（它报 0x429339/0x429346/0x6bd940）
pushes = []
for a, sz, m, o in md.disasm_lite(raw, 0x401000):
    if m == 'push' and o.strip() == '0x87f7e8':
        pushes.append(hex(a))
add('O3 A1 报告说 push 0x87f7e8 三处 = 0x429339/0x429346/0x6bd940 —— 复算得到 %s'
    % pushes,
    pushes == ['0x429339', '0x429346', '0x6bd940'], pushes)

# 它测出的第三处 push 0x87f7e8（0x6bd940）是我先前只报两处时漏掉的 —— 单独核上下文
c6 = [(a, m, o) for a, sz, m, o in md.disasm_lite(rd(0x6bd934, 0x16), 0x6bd934)]
c6 = [x for x in c6 if x[0] <= 0x6bd947 and x[1] != '.byte']
add('O3b A1 采纳审计员一条我漏的事实：0x6bd940 是第三处 push 0x87f7e8，'
    '上下文是 push 0x840a74 / push 1 / push 0x7e9520 / push 0x87f7e8 / call ebx —— '
    '四个实参，最后一个为该全局单例地址',
    [o.strip() for a, m, o in c6] == ['0x840a74', '1', '0x7e9520', '0x87f7e8', 'ebx',
                                      'eax, 0xffffffff'],
    [(hex(a), m, o) for a, m, o in c6])

edxload = [hex(a) for a, sz, m, o in md.disasm_lite(raw, 0x401000)
           if m == 'mov' and o == 'edx, dword ptr [0x87f7e8]']
add('O4 A1 报告说 mov edx,[0x87f7e8] 两处 = 0x429331/0x6933a4 —— 复算得到 %s' % edxload,
    edxload == ['0x429331', '0x6933a4'], edxload)

# ---- 它的一条我漏的旁证：0x40d1bc 写 0x884d00 <- 0x7e195c ----
b = rd(0x40d1b0, 0x30)
add('O5 A3 它列出 0x40d1bc 的 mov dword ptr [0x884d00], 0x7e195c —— 复算字节 %s'
    % b.hex(),
    b[0xc:0xc+10] == bytes.fromhex('c705004d8800') + (0x7e195c).to_bytes(4, 'little'),
    b.hex())

# ---- B 主张：三个 GUID 的文本 ----
g = {'0x7ea6e8': gt(0x7ea6e8), '0x7e36c0': gt(0x7e36c0), '0x7f7c90': gt(0x7f7c90)}
add('O6 B 三个 GUID 文本逐字符与它的表相同',
    g['0x7ea6e8'] == '{96F02EC7-6FE8-11D1-B6FD-00A024DDAFD1}'
    and g['0x7e36c0'] == '{96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}'
    and g['0x7f7c90'] == '{00000000-0000-0000-C000-000000000046}', g)

# ---- C 主张：3 处 + 每条后接 f3 a7 ----
three = [a for a, sz, m, o in md.disasm_lite(raw, 0x401000)
         if m == 'mov' and o == 'edi, 0x7ea6e8']
add('O7 C 三处 mov edi,0x7ea6e8 = %s（它报 0x42930f/0x4293a5/0x4f4273）'
    % [hex(x) for x in three],
    three == [0x42930f, 0x4293a5, 0x4f4273], [hex(x) for x in three])

# ---- D 主张：0x429270 的两条 call dword ptr [reg]、4 条 push imm ----
body = [(a, m, o) for a, sz, m, o in md.disasm_lite(rd(0x429270, 0xf0), 0x429270)]
calls = [(hex(a), o) for a, m, o in body if m == 'call' and o.startswith('dword ptr [')]
add('O8 D call dword ptr [reg] 共 2 条，都在 edx 上，文本 dword ptr [edx]',
    calls == [('0x4292f1', 'dword ptr [edx]'), ('0x42933e', 'dword ptr [edx]')], calls)
pi = [(hex(a), o) for a, m, o in body if m == 'push' and o.strip().startswith('0x')]
add('O9 D push 立即数共 4 条：0x4292ec/0x4292f9 -> 0x89a29c、0x429339/0x429346 -> 0x87f7e8',
    pi == [('0x4292ec', '0x89a29c'), ('0x4292f9', '0x89a29c'),
           ('0x429339', '0x87f7e8'), ('0x429346', '0x87f7e8')], pi)
edxw = [hex(a) for a, m, o in body if m in ('mov', 'xor') and o.split(',')[0].strip() == 'edx']
add('O10 D 函数内 edx 写入点 5 处：0x4292b2/0x4292c9/0x4292e4/0x429316/0x429331',
    edxw == ['0x4292b2', '0x4292c9', '0x4292e4', '0x429316', '0x429331'], edxw)

# 它报的 ff 12 字节
add('O11 D 两条 call 的字节都是 ff 12',
    rd(0x4292f1, 2) == b'\xff\x12' and rd(0x42933e, 2) == b'\xff\x12',
    [rd(0x4292f1, 2).hex(), rd(0x42933e, 2).hex()])

# ---- 它的 ApplicationClass RTTI 数字与我的对照 ----
c = col_of(0x7e36d4)
add('O12 D 旁证：0x7e36d4 的 COL=0x7fbc18、TD=0x8186c8、类名 .?AVApplicationClass@@、'
    'numBaseClasses=3、slot0=0x429360 —— 复算 %s / %s / %d / 0x%08x'
    % ('0x%08x' % u32(0x7e36d0), '0x%08x' % c['pTypeDescriptor'], c['n'], u32(0x7e36d4)),
    u32(0x7e36d0) == 0x7fbc18 and c['pTypeDescriptor'] == 0x8186c8
    and c['type_desc'] == '.?AVApplicationClass@@' and c['n'] == 3
    and u32(0x7e36d4) == 0x429360,
    {'COL': '0x%08x' % u32(0x7e36d0), 'TD': '0x%08x' % c['pTypeDescriptor'],
     'n': c['n'], 'slot0': '0x%08x' % u32(0x7e36d4)})

json.dump({'checks': ck, 'prev': {hex(k): v for k, v in prev.items()}},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128o: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:400])
