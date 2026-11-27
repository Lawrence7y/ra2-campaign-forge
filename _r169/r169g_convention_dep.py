#!/usr/bin/env python3
"""R169 G：65 个「线性解码洞」这个数对**相位口径**敏感吗？

先纠正一处：_r167/r167d_holes_semantics_final.json 里的 bounds 是**整数** 1,392,592（计数），
不是地址清单；地址清单来自 a2_sites.json（不在现盘）。所以「bounds − S 差集」**不可重算**，
只能重算 65 的**定义侧**：洞 = 线性扫描时 capstone 在该位置解不出、游标只能前进 1 字节的位置。

本轮把洞的生成器按两个相位口径各跑一遍：
  C = 连续相位（r143lib / R168 口径，off += consumed），正控应得 65
  D = 64KB 边界重置（审计员 #397 提出的第二口径，起点数 1,392,568）
断言：
  H1 口径 C 下洞数 == 65（正控，与 R167/R168 落盘一致）
  H2 口径 D 下洞数（不预设，只报）
  H3 两口径洞集合的对称差与交集
  H4 口径 C 的洞集合与 R167 落盘的 65 条**逐条相同**（不是只数目相同）
  H5 0x7d0cba 在两口径下都是洞
  H6 定位：口径 D 与 C 的洞差是否全部贴着 64KB 边界（差值 < 64 B 内）
"""
import sys, json
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = B.IB + text[1]; T_VSZ_HI = T_LO + text[2]
CH = 65536
RAW0, RAW1, VS = text[3], text[3] + text[4], text[1]

def scan(hi, boundary_reset=False):
    starts = {}
    holes = []
    if boundary_reset:
        blocks = [(RAW0 + k * CH, min(RAW0 + (k + 1) * CH, RAW1))
                  for k in range(0, (RAW1 - RAW0 + CH - 1) // CH)]
    else:
        blocks = [(RAW0, RAW1)]
    for b0, b1 in blocks:
        cur = b0
        while cur < b1:
            c = B.data[cur:b1]
            base = B.IB + (VS + (cur - RAW0))
            consumed = 0
            for a, sz, mn, op in md.disasm_lite(c, base):
                if a - base + sz > len(c):
                    break
                consumed = a - base + sz
                if a < hi:
                    starts[a] = sz
            if consumed:
                cur += consumed
            else:
                if base < hi:
                    holes.append(base)
                cur += 1
    return starts, holes

SA, hA = scan(T_VSZ_HI, False)
SB, hB = scan(T_VSZ_HI, True)
print('C: starts=%d holes=%d' % (len(SA), len(hA)))
print('D: starts=%d holes=%d' % (len(SB), len(hB)))

r167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
ref = sorted(int(x, 16) for x in r167['holes'])
setA = set(hA); setB = set(hB); setR = set(ref)

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('H1 口径 C 洞数 == 65（正控）', len(hA) == 65, len(hA))
chk('H2 口径 D 洞数（不预设）', True, {'holes_D': len(hB), 'starts_D': len(SB)})
chk('H3 两口径洞集合：交集 / 对称差', True,
    {'both': len(setA & setB), 'A_only': len(setA - setB), 'B_only': len(setB - setA),
     'A_only_list': [hex(x) for x in sorted(setA - setB)],
     'B_only_list': [hex(x) for x in sorted(setB - setA)]})
chk('H4 口径 C 的洞集合与 R167 落盘 65 条逐条相同', setA == setR,
    {'equal': setA == setR, 'A_only': [hex(x) for x in sorted(setA - setR)],
     'R_only': [hex(x) for x in sorted(setR - setA)]})
chk('H5 0x7d0cba 在两口径下都是洞', 0x7d0cba in setA and 0x7d0cba in setB,
    {'in_C': 0x7d0cba in setA, 'in_D': 0x7d0cba in setB})

def near_boundary(va, tol=64):
    rel = (B.va2off(va) - RAW0) % CH
    return min(rel, CH - rel) <= tol
diff = sorted(setA ^ setB)
chk('H6 两口径洞差是否都贴着 64KB 边界（±64 B）', True,
    [{'va': hex(x), 'in_C': x in setA, 'in_D': x in setB, 'near_boundary': near_boundary(x)} for x in diff])

out = {'starts_C': len(SA), 'holes_C': len(hA), 'starts_D': len(SB), 'holes_D': len(hB),
       'both': len(setA & setB), 'A_only': sorted(hex(x) for x in setA - setB),
       'B_only': sorted(hex(x) for x in setB - setA),
       'matches_r167': setA == setR,
       'diff_detail': [{'va': hex(x), 'near_boundary': near_boundary(x)} for x in diff],
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r169/r169g_convention_dep.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:340])
print('FAIL count =', out['fail'])
