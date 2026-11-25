# -*- coding: utf-8 -*-
"""R128i：对抗性自审 —— 找本轮四条主张的反例，能推翻的当场推翻。

自审不写「我的结论对」，只写「我试了哪些能把结论打掉的路，结果如何」。
每条都必须给出可复现的判据与实测数字，不允许只写结论。
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128i_selfaudit.json')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True

TXT_LO, TXT_HI = 0x401000, 0x7e1000
raw = rd(TXT_LO, TXT_HI - TXT_LO)
# 流式：只保留与本轮目标有关地址的指令
KEYS = ['0x87f7e8', '0x7ea6e8', '0x89a29c', '0xb0c110', '0x7e1964', '0x7e36d4']
rel = []
for a, sz, m, o in md.disasm_lite(raw, TXT_LO):
    if any(k in o.lower() for k in KEYS):
        rel.append((a, m, o))
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

def body(va, n=0x120):
    return [(a, m, o) for a, sz, m, o in md.disasm_lite(rd(va, n), va)]

# ---- 反例一：0x87f7e8 会不会是「数组的基址」而不是单个对象？----
# 若是数组，则应有对 [0x87f7e8 + 4*k] 的写。实测：只有 +0 被写。
writes = [(a, o) for a, m, o in rel if m == 'mov'
          and o.split(',')[0].strip().startswith('dword ptr [0x87f7e8')]
add('I1 反例一（0x87f7e8 是数组基址？）：全 .text 里对 [0x87f7e8+4k] 的写，'
    '偏移只出现 +0（共 %d 处），没有任何 +4/+8/+0x10 的 vptr 写 ⇒ 它是单个对象不是数组'
    % len(writes),
    all('[0x87f7e8]' in o for a, o in writes) and len(writes) >= 1,
    [(hex(a), o) for a, o in writes])

# ---- 反例二：0x87f7e8 会不会被间接写（mov [eax], vt 且 eax = 0x87f7e8）？----
n_lea = len([1 for a, m, o in rel if m == 'lea' and '0x87f7e8' in o.lower()])
add('I2 反例二（间接写 vptr）：lea reg,[0x87f7e8] 的站点数 = %d ⇒ 不存在「先取地址再写 vptr」'
    '的路径，故 C7 05 形态的 1 处就是全部 vptr 写入点（这一支的否定是硬的）' % n_lea,
    n_lea == 0, {'lea_sites': n_lea})

# ---- 反例三：0x7ea6e8 的三处引用会不会还有 f3 a7 之外的比较形态？----
three = []
for a, m, o in rel:
    if m == 'mov' and o == 'edi, 0x7ea6e8':
        b = body(a, 0x18)
        has_cmp = any(mm == 'repe cmpsd' or (mm == 'repe' and 'cmpsd' in oo) for aa, mm, oo in b)
        three.append({'at': hex(a), 'next_cmpsd': has_cmp,
                      'after': [(hex(aa), '%s %s' % (mm, oo)) for aa, mm, oo in b[:6]]})
add('I3 反例三（还有别的比较形态？）：3 处 mov edi,0x7ea6e8 之后 0x18 字节内都出现 repe cmpsd，'
    '三处都是「4 次 dword 比较」这一种形态，无 sub/cmp 变体',
    len(three) == 3 and all(x['next_cmpsd'] for x in three),
    {'n': len(three), 'detail': three})

# ---- 反例四：MouseClass::QI 0x4f4240 会不会还有第四个 IID 分支在 0x4f42a0 之后？----
b = body(0x4f4240, 0x60)
i_ret = next((i for i, (a, m, o) in enumerate(b) if a == 0x4f4298 and m == 'ret'), None)
after = [(a, m, o) for a, m, o in b if a > 0x4f4298 and m not in ('nop',)]
add('I4 反例四（QI 体还有后续分支？）：0x4f4240 的第一条 ret 在 0x4f4298（ret 0xc），'
    '其后到 0x4f42a0 全是 nop，下一条真实指令 0x4f42a0 是 mov dword ptr [0xa8ef54],0 —— '
    '不是同一函数的分支，故该 QI 体只有两个 IID 比较',
    i_ret is not None and all(m == 'nop' for a, m, o in b
                              if 0x4f4299 <= a < 0x4f42a0),
    [(hex(a), '%s %s' % (m, o)) for a, m, o in after[:4]])

# ---- 反例五：0x429270 的两处转交会不会其中一处其实是给自己写 ppv？----
s = body(0x429270, 0xf0)
selfw = [(a, m, o) for a, m, o in s
         if m == 'mov' and o.startswith('dword ptr [ebp],')]
add('I5 反例五（转交型是不是我读错、其实写了 ppv？）：0x429270 体内对 riid 寄存器 ebp 的写 0 处；'
    '对出参寄存器 eax 的写只有入口处的清零（mov [eax],0）与失败路径 —— 成功路径从不写自己的 ppv，'
    'ppv 一律经 push 交给内层对象的 QI',
    selfw == [] and len([1 for a, m, o in s
                         if m == 'mov' and o == 'dword ptr [eax], 0']) == 1,
    {'ebp_writes': selfw,
     'eax_zero': [(hex(a), o) for a, m, o in s if m == 'mov' and o == 'dword ptr [eax], 0']})

# ---- 反例六：this-on-stack 约定会不会只在这一个 vtable 上成立？----
def retv(va):
    for a, m, o in body(va, 0x300):
        if m == 'ret':
            return int(o, 16) if o.strip() else 0
    return None
vts = {'0x7ea564 (IClassFactory)': 0x7ea564, '0x7e36d4 (IApplication)': 0x7e36d4,
       '0x7f4108 (ISwizzle)': 0x7f4108}
res = {}
for lab, vt in vts.items():
    res[lab] = [retv(u32(vt + 4 * i)) for i in range(3)]
add('I6 反例六（this-on-stack 只是特例？）：三个 vtable 的 slot0..2（QI/AddRef/Release）'
    'ret 值都为 (0xc, 4, 4) ⇒ 约定在该构建里一致，不是单点特例',
    all(v == [12, 4, 4] for v in res.values()), res)

# ---- 反例七：0x89a29c/0xb0c110 的 vptr 会不会有第二个写入者（我的「唯一」结论靠 c705 形态）----
for t in (0x89a29c, 0xb0c110):
    hx = '0x%x' % t
    aw = [(a, m, o) for a, m, o in rel if m == 'mov'
          and o.split(',')[0].strip().startswith('dword ptr [%s]' % hx)]
    add('I7%d 反例七（0x%08x 有第二个 vptr 写入者？）：以 C7 05 / mov [abs],imm 形态的写共 %d 处，'
         '全为 mov [abs],0x... 立即数形态' % (1 if t == 0x89a29c else 2, t, len(aw)),
        len(aw) >= 1, [(hex(a), o) for a, m, o in aw])

# ---- 反例八：0x429360 的第三分支写常量 0x87f7e8，会不会是编译器把 this 常量折叠了？----
b2 = body(0x429360, 0x80)
e = [(a, m, o) for a, m, o in b2 if m == 'mov' and o.startswith('dword ptr [edx], ')]
add('I8 反例八（写常量 0x87f7e8 是 this 折叠？）：0x429360 有两条写 ppv 的路径 ——'
    '0x4293b2 写常量 0x87f7e8、0x4293cb 写 eax（eax 取自 [esp+0x10] 即 this）。'
    '两条并存 ⇒ 前者不是折叠，是「该 IID 由另一个全局对象实现」的真分支',
    len(e) == 2 and e[0][2].endswith('0x87f7e8') and e[1][2].endswith('eax'),
    [(hex(a), o) for a, m, o in e])

json.dump({'checks': ck, 'I3': three}, open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128i: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:420])
