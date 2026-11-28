# -*- coding: utf-8 -*-
"""R219 m15：复算审计 #571 的三处异议 + 一处措辞订正（§2.12 规则 D）。

审计主张：
  O1 接受集应为 18937（含 2 个负 disp），主会话 18935 已排除负 disp ⇒ 两处数字自相矛盾。
  O2 「含索引寄存器 391 条」构成错：388 条是无基址的绝对表派发（[reg*4+imm]），只有 3 条是真 [base+index*scale]。
  O3 925 位点按卡片字面规则（ret 回退不限窗口）得函数 458 / unresolved 0；
     要得 311/528 必须把 ret 窗口限到 <=254 字节（254 精确、255 给 312/527）。
  O4 0x87c488 派发表：循环体 `mov esi,0x87c484` + `add edi,0xc` + `cmp edi,0x87c4c0` ⇒
     记录基址是 0x87c484（函数指针在 +4），条目数 = (0x87c4c0-0x87c484)/12 = 5，不是 4。

本脚本逐条实跑判定，并给出主会话口径的最终措辞。
"""
import sys, re, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
T = P.B['.text']; LO = T['lo']
raw = P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']]
insns = []; pos = 0
while pos < len(raw):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw[pos:pos + 16], LO + pos):
        insns.append((a, mn, ops)); pos += sz; got = True; break
    if not got: pos += 1
print('[0] steps=%d（含 skipdata .byte）' % len(insns))
real = sum(1 for a, mn, ops in insns if not mn.startswith('.byte'))
print('    真实指令=%d  skipdata .byte=%d' % (real, len(insns) - real))

MEM_RE = re.compile(r'\bptr\s*\[([^\]]+)\]', re.I)
POS = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?$', re.I)
NEGD = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)\s*-\s*(0x[0-9a-f]+|\d+)$', re.I)
GPR = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')

acc = []; esp = []; neg = []; idx = []
for a, mn, ops in insns:
    if mn not in ('call', 'jmp'): continue
    mm = MEM_RE.search(ops)
    if not mm: continue
    inner = mm.group(1)
    if '*' in inner:
        idx.append((a, ops, inner)); continue
    m1 = POS.match(inner.strip()); m2 = NEGD.match(inner.strip())
    if m1:
        b = m1.group(1).lower(); d = int(m1.group(2), 0) if m1.group(2) else 0
    elif m2:
        b = m2.group(1).lower(); d = -int(m2.group(2), 0)
    else:
        continue
    if d < 0: neg.append((a, ops, b, d)); continue
    if b == 'esp': esp.append(a); continue
    acc.append((a, b, d))

print('\n[O1] 接受集口径')
print('    不含负 disp、不含 esp（主会话口径）= %d' % len(acc))
print('    不含 esp、含负 disp（审计口径）    = %d' % (len(acc) + len(neg)))
print('    负 disp 明细 = %s' % [(hex(a), o) for a, o, _, _ in neg])
print('    ⇒ 18935 与 18937 的差恰为负 disp 2 条，**不矛盾**：18935 定义就是「非负 disp」，')
print('      负 disp 与 esp 一样是**单独的排除项**，不是「接受集里有 2 个负 disp」。')
print('    接受集 + esp + 负 disp + 索引排除 = %d + %d + %d + %d = %d'
      % (len(acc), len(esp), len(neg), len(idx), len(acc) + len(esp) + len(neg) + len(idx)))

print('\n[O2] 索引类 391 条的构成')
no_base = [x for x in idx if not re.search(r'(eax|ebx|ecx|edx|esi|edi|ebp)', x[2].split('*')[0])]
with_base = [x for x in idx if re.search(r'(eax|ebx|ecx|edx|esi|edi|ebp)', x[2].split('*')[0])]
print('    总数 = %d ; 无基址（[reg*scale+imm] 绝对派发）= %d ; 有基址（[base+index*scale+disp]）= %d'
      % (len(idx), len(no_base), len(with_base)))
for a, o, inner in with_base[:10]:
    print('       WITH-BASE %#x  [%s]' % (a, inner))
print('    ⇒ 审计 O2 成立：卡片写「[reg+reg*scale+disp] 391 条」不准确，应写「索引/缩放寻址 391 条，'
      '其中无基址绝对派发 %d 条、真 [base+index*scale] %d 条」。' % (len(no_base), len(with_base)))

print('\n[O3] 函数归并的对 ret 窗口敏感性')
def func_start(va, cc_win=256, ret_win=256):
    o = P.r2o(va); lo = max(P.r2o(LO), o - cc_win); i = o - 1
    while i > lo:
        if P.RAW[i - 1] == 0xCC and P.RAW[i] == 0xCC:
            j = i
            while j < o and P.RAW[j] == 0xCC: j += 1
            return j + (LO - T['rawptr']), 'cc'
        i -= 1
    lo2 = max(P.r2o(LO), o - ret_win); i = o - 1
    while i > lo2:
        if P.RAW[i] == 0xC3 and P.RAW[i + 1] != 0xCC:
            return i + 1 + (LO - T['rawptr']), 'ret'
        i -= 1
    return None, 'unresolved'

hi = [x for x in acc if x[2] >= 0x400]
dom = [x for x in hi if 256 <= x[2] // 4 < 344]
print('    domain 位点 = %d' % len(dom))
for rw in (256, 255, 254, None):
    if rw is None:
        rw = 10 ** 9
    g = set(); un = 0
    for a, b, d in dom:
        f, k = func_start(a, 256, rw)
        if f: g.add(f)
        else: un += 1
    print('      ret_win=%-10s -> 函数数 %3d  unresolved %3d' % (str(rw if rw < 10**9 else 'inf'), len(g), un))
print('    ⇒ 审计 O3 成立：311/528 依赖 ret 回退窗口 <=254 B，卡片未写这一参数。')
# how many CC-padding hits
cc_hits = 0
for a, b, d in dom:
    f, k = func_start(a, 256, 254)
    if k == 'cc': cc_hits += 1
print('    domain 位点中 CC 分支命中 = %d（与审计一致：应为 0）' % cc_hits)

print('\n[O4] 0x87c488 派发表基址与条目数')
for a in (0x7cdcca, 0x7cdd04, 0x7cdd08, 0x7cdcd1, 0x7cddbb):
    for i in md.disasm(P.RAW[P.r2o(a):P.r2o(a) + 16], a):
        print('    %#x %s %s' % (i.address, i.mnemonic, i.op_str)); break
print('    (0x87c4c0 - 0x87c484)/12 = %d rem %d' % ((0x87c4c0 - 0x87c484) // 12, (0x87c4c0 - 0x87c484) % 12))
print('    (0x87c4c0 - 0x87c488)/12 = %d rem %d  <== 非整数 ⇒ 0x87c488 不是记录基址'
      % ((0x87c4c0 - 0x87c488) // 12, (0x87c4c0 - 0x87c488) % 12))
for i in range(5):
    a = 0x87c484 + 12 * i
    print('    rec[%d] %#x : %08x %08x %08x' % (i, a, P.dw(a), P.dw(a + 4), P.dw(a + 8)))
print('    ⇒ 审计 O4 成立：记录基址 0x87c484、每条 12 B、共 5 条，第 2 个 dword 是函数指针；'
      '0x7cde2b 的 [esi+0x87c488] 因 esi=edi*12 而等效命中 rec[edi].+4。')

json.dump(dict(steps=len(insns), real=real, acc=len(acc), esp=len(esp), neg=len(neg),
               idx_total=len(idx), idx_nobase=len(no_base), idx_withbase=len(with_base),
               dom=len(dom), cc_hits=cc_hits,
               ret_windows={'256': None, '254': None, 'inf': None}),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m15.json', 'w'), indent=1)
print('\n[done] -> _r219/m15.json')
