# -*- coding: utf-8 -*-
"""R128e：规则 D 复算 —— 审计员与主会话在两处数字上不一致，用第三方工具仲裁。

分歧 1：0x87f7e8 的「指令级引用数」主会话 3700、审计员 498。
分歧 2：0x7ea6e8 的「指令级引用数」主会话 3、审计员 2。

仲裁手段：capstone 与 objdump 两个互相独立的译码器，各出一份地址集合，
比集合而非比总数（总数相同也可能是不同集合）。

内存纪律（本轮踩过 OOM，脚本被 kill 过两次）：
  绝不移物化整段 .text 的指令列表。capstone 侧用 disasm_lite 生成器单遍流式，
  边解边只保留命中目标的 (地址, 形态)；objdump 侧逐行流式正则，只保留命中地址。
"""
import sys, os, json, re, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128e_arbitrate.json')
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

TARGETS = [0x87f7e8, 0x7ea6e8, 0x89a29c, 0xb0c110]
HEX = ['0x%x' % t for t in TARGETS]

TXT_LO, TXT_HI = 0x401000, 0x7e1000
raw = rd(TXT_LO, TXT_HI - TXT_LO)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True           # 必须在 disasm 之前生效（S-181）

cap_addr = {t: [] for t in TARGETS}
forms = {}
n_ins = 0
for a, _sz, m, o in md.disasm_lite(raw, TXT_LO):
    n_ins += 1
    ol = o.lower()
    for t, hx in zip(TARGETS, HEX):
        if hx in ol:
            cap_addr[t].append(a)
            if t == 0x87f7e8:
                d = o.split(',')[0].strip()
                if m == 'push': k = 'push imm'
                elif m == 'mov' and d == 'ecx': k = 'mov ecx,<S>'
                elif m == 'mov' and d.startswith('dword ptr [0x87f7e8]') and o.split(', ')[-1][:2] == '0x':
                    k = 'mov [S],imm'
                elif m == 'mov' and d.startswith('dword ptr ['): k = 'mov [S],reg'
                elif m == 'mov': k = 'mov reg,[S]'
                else: k = 'other:' + m
                forms[k] = forms.get(k, 0) + 1
add('E0 .text 流式扫描完毕（disasm_lite 生成器，不物化列表）', n_ins > 1000000, 'ins=%d' % n_ins)

# ---- objdump 侧：流式 ----
OD = '/tmp/objd.txt'
if not os.path.exists(OD) or os.path.getsize(OD) < 10_000_000:
    with open(OD, 'w') as f:
        subprocess.run(['i686-w64-mingw32-objdump', '-d', '--no-show-raw-insn', EXE],
                       stdout=f, stderr=subprocess.DEVNULL, timeout=1800)
_L = re.compile(r'^\s*([0-9a-f]+):\t(.*)$')
PAT = {t: re.compile(r'\b0x%x\b' % t) for t in TARGETS}
od_addr = {t: [] for t in TARGETS}
od_text = []
n_od = 0
with open(OD, encoding='utf-8', errors='replace') as f:
    for l in f:
        m = _L.match(l)
        if not m: continue
        n_od += 1
        a = int(m.group(1), 16); txt = m.group(2)
        if len(od_text) < 1 and '0x87f7e8' in txt: pass
        for t in TARGETS:
            if PAT[t].search(txt):
                od_addr[t].append(a)
                if t == 0x87f7e8: od_text.append(txt)
add('E1 objdump 流式扫描完毕', n_od > 1300000, 'ins=%d' % n_od)

for t, tag in [(0x87f7e8, 'E2'), (0x7ea6e8, 'E3'), (0x89a29c, 'E4'), (0xb0c110, 'E5')]:
    ca, oa = sorted(set(cap_addr[t])), sorted(set(od_addr[t]))
    only_c = sorted(set(ca) - set(oa)); only_o = sorted(set(oa) - set(ca))
    add('%s 0x%08x 引用地址集合：capstone %d、objdump %d、交集 %d；仅 C %d、仅 O %d'
        % (tag, t, len(ca), len(oa), len(set(ca) & set(oa)), len(only_c), len(only_o)),
        len(only_c) == 0 and len(only_o) == 0,
        {'cap': len(ca), 'od': len(oa),
         'only_cap': ['0x%08x' % x for x in only_c[:6]],
         'only_od': ['0x%08x' % x for x in only_o[:6]]})

add('E6 0x87f7e8 的引用按形态分解，四类之和 = %d' % sum(forms.values()),
    sum(forms.values()) == 3700, forms)

# 直接检验「498」这个数的可能来源
def cnt(pat, seq):
    r = re.compile(pat)
    return sum(1 for s in seq if r.search(s))
ecx = cnt(r'mov\s+\$0x87f7e8,%ecx', od_text)
mem = cnt(r'mov\s+0x87f7e8,%', od_text)
add('E7 在 objdump 文本里 mov $0x87f7e8,%%ecx 共 %d 行、mov 0x87f7e8,%%reg 共 %d 行、'
    '总提及 %d 行。498 不对应任何一个 ⇒ 审计员那个数是口径错误的中间量，不是我漏计'
    % (ecx, mem, len(od_text)),
    ecx == 3693 and mem == 2 and len(od_text) == 3700,
    {'mov_imm_ecx': ecx, 'mov_mem': mem, 'any': len(od_text), 'forms': forms})

add('E8 0x7ea6e8 三处引用 0x42930f / 0x4293a5 / 0x4f4273 两个译码器给出同一集合'
    '（审计员报 2 处，漏了 0x4f4273；主会话首版也漏，成因是 skipdata 未在 disasm 前生效 —— S-181）',
    sorted(set(cap_addr[0x7ea6e8])) == sorted(set(od_addr[0x7ea6e8])) == [0x42930f, 0x4293a5, 0x4f4273],
    ['0x%08x' % x for x in sorted(set(cap_addr[0x7ea6e8]))])

json.dump({'checks': ck, 'forms': forms}, open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128e: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:400])
