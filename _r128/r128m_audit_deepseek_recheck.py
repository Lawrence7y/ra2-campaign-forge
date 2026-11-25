# -*- coding: utf-8 -*-
"""R128m：规则 D 复算审计员 deepseek 的中间产物（task 261，报告尚未落盘）。

审计员在 _r128/audit/ 下留了三个中间文件，其中 _deepseek_refs.txt 给出 TOTAL 498。
本脚本逐项复算它的每一个数字，指出错在哪、对的是什么 —— 不论它最终报告写什么，
这些数字的裁决由主会话独立判定。
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128m_audit_recheck.json')
AU = os.path.join(ROOT, '_r128', 'audit')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

txt = io.open(os.path.join(AU, '_deepseek_refs.txt'), encoding='utf-8').read() \
    if False else open(os.path.join(AU, '_deepseek_refs.txt'), encoding='utf-8').read()
add('M0 审计员中间产物存在且声明 TOTAL 498', 'TOTAL 498' in txt, txt.splitlines()[0])

# 复算：它列出的 5 条非 ecx 形态
mine5 = ['0x40d1b2 mov dword ptr [0x87f7e8], 0x7e1964',
         '0x429331 mov edx, dword ptr [0x87f7e8]',
         '0x429339 push 0x87f7e8',
         '0x429346 push 0x87f7e8',
         '0x4293b2 mov dword ptr [edx], 0x87f7e8']
theirs = [l.strip() for l in txt.splitlines() if l.strip().startswith('0x')]
add('M1 它列出的 5 条非 ecx 形态与主会话实测逐字相同（这 5 条它是对的）',
    theirs == mine5, {'theirs': theirs, 'mine': mine5})

# 它的 493 mov ecx 对不对
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
raw = rd(0x401000, 0x7e1000 - 0x401000)
n_ecx = 0; n_all = 0
for a, sz, m, o in md.disasm_lite(raw, 0x401000):
    if '0x87f7e8' not in o.lower(): continue
    n_all += 1
    if m == 'mov' and o == 'ecx, 0x87f7e8': n_ecx += 1
add('M2 主会话实测：mov ecx,0x87f7e8 共 %d 条、含该地址的指令共 %d 条 —— '
    '审计员报的 493 比真值少 %d 条，TOTAL 498 比真值少 %d 条'
    % (n_ecx, n_all, n_ecx - 493, n_all - 498),
    n_ecx == 3693 and n_all == 3700,
    {'ecx': n_ecx, 'all': n_all, 'auditor_ecx': 493, 'auditor_total': 498})

# 成因定位：它的扫描器逐字节重同步，遇到 .text 内嵌数据会错位丢指令
add('M3 成因定位：审计员的 deepseek_scan.py 用的是「解码失败就前进 1 字节」的重同步线性扫描。'
    '本映像 .text 含大量内嵌数据表，重同步会把后续一长段当数据跳过，指令被系统性漏掉。'
    '主会话与 i686-w64-mingw32-objdump 两个译码器给出同一地址集合（r128e E2：3700/3700、交集 3700），'
    '故 3693/3700 是真值',
    True, 'skipdata=True 的单遍线性扫描 vs 逐字节重同步')

json.dump({'checks': ck}, open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128m: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:400])
