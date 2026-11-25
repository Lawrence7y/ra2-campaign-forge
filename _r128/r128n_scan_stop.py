# -*- coding: utf-8 -*-
"""R128n：规则 D 复算 deepseek 报的一处**对我不利**的事实 ——
「按最省事的写法 md.disasm(text, 0x401000) 迭代，单遍扫描会在 0x46f59d 停住」。

若成立，意味着本仓大量历史脚本的「全 .text 线性扫描」都只覆盖前半段，
这是比本轮任何定名都更严重的方法学问题。必须亲自量。

三种口径都测：
  口径 1  md.disasm(raw, base) 且 md.skipdata = False（最省事写法）
  口径 2  md.disasm(raw, base) 且 md.skipdata = True
  口径 3  md.disasm_lite(raw, base) 且 md.skipdata = True（本轮一直在用的）
  口径 4  逐字节重同步（deepseek 自己用的）
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128n_scan_stop.json')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

TXT_LO, TXT_HI = 0x401000, 0x7e1000
raw = rd(TXT_LO, TXT_HI - TXT_LO)
add('N0 .text 原始字节数 = 0x%x（S-182：我先按 Misc_VirtualSize 0x3df38d 断言，实测按 raw 读到 0x3e0000，'
    '两者差 0xc73 是对齐尾巴；本脚本用 raw 长度，故断言改成 raw 界）' % len(raw),
    len(raw) == 0x3e0000, {'raw': hex(len(raw)), 'vsize': '0x3df38d'})

def measure(lite, skipdata):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = skipdata
    n = 0; last = None; firstdata = None
    gen = md.disasm_lite(raw, TXT_LO) if lite else md.disasm(raw, TXT_LO)
    for item in gen:
        if lite:
            a = item[0]; mn = item[2]
        else:
            a = item.address; mn = item.mnemonic
        n += 1; last = a
        if mn == '.byte' and firstdata is None:
            firstdata = a
    return {'n': n, 'last': last, 'first_byte_at': firstdata,
            'coverage': (last - TXT_LO) / len(raw) if last else 0}

r1 = measure(False, False)
r2 = measure(False, True)
r3 = measure(True, True)

add('N1 口径 1（disasm + skipdata=False，最省事写法）：解出 %d 条，最后一条在 0x%08x，'
    '只覆盖 .text 的 %.1f%%' % (r1['n'], r1['last'], r1['coverage'] * 100),
    True, r1)

add('N2 口径 2（disasm + skipdata=True）：解出 %d 条，最后一条在 0x%08x，覆盖 %.1f%%；'
    '首个 .byte 出现在 0x%08x'
    % (r2['n'], r2['last'], r2['coverage'] * 100,
       r2['first_byte_at'] or 0),
    True, r2)

add('N3 口径 3（disasm_lite + skipdata=True，本轮全程在用）：解出 %d 条，最后一条在 0x%08x，'
    '覆盖 %.1f%%，首个 .byte 在 0x%08x'
    % (r3['n'], r3['last'], r3['coverage'] * 100, r3['first_byte_at'] or 0),
    True, r3)

add('N4 复算 deepseek 的这条主张：「单遍 disasm_lite 会在 0x46f59d 停住、只解码 155215 条」。'
    '实测：那个 155215/0x46f59d 恰好是**口径 1（skipdata=False）**的结果（见 N1），'
    '而口径 3（disasm_lite + skipdata=True）给 1394186 条、最后一条 0x7e0fff。'
    '它把两种口径混成一谈 —— 结论「必须重同步才能找全」对 skipdata=False 成立、'
    '对 skipdata=True 不成立',
    r1['n'] == 155215 and r1['last'] == 0x46f59d and r3['n'] == 1394186,
    {'auditor_claimed': {'n': 155215, 'stop': '0x46f59d'},
     'measured_no_skipdata': {'n': r1['n'], 'stop': hex(r1['last'])},
     'measured_lite_skipdata': {'n': r3['n'], 'stop': hex(r3['last'])}})

# 但它的核心关切是真的：disasm 遇数据会停。核 r1 到底停在哪
add('N5 它关心的机制确实存在：口径 1（无 skipdata）只覆盖 %.1f%% 就停住了 —— '
    '这不是全 .text 扫描，但本仓历史脚本用的是口径 3（有 skipdata），'
    'r128a/r128b/r128d/r128e 的 A1 断言都显式写了「skipdata = True 的 disasm_lite」'
    % (r1['coverage'] * 100),
    r1['coverage'] < 0.9, {'coverage_pct': round(r1['coverage'] * 100, 2)})

# 关键：口径 3 的覆盖是否真的是 100%
add('N6 口径 3 的覆盖率 %.2f%%，最后一条指令在 0x%08x，.text 结束于 0x%08x —— '
    '差额 %d 字节是尾部对齐填充，不是漏扫'
    % (r3['coverage'] * 100, r3['last'], TXT_HI, TXT_HI - r3['last']),
    r3['coverage'] > 0.9999, {'tail_gap': TXT_HI - r3['last']})

json.dump({'checks': ck, 'r1': r1, 'r2': r2, 'r3': r3},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128n: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:300])
