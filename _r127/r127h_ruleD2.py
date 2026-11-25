# -*- coding: utf-8 -*-
"""R127h：规则 D —— 逐条复算 hy4 审计员（task 257）报告里的数字，并裁决一处分歧。

审计员报告 /tmp/r127_audit_hy4.md。它的 1/2/3/4/5/7b/8 与我一致；6 与 7 它自己报错
（ValueError('-0x400000')，三处宿主全判 unknown），与我的 r127d D2/D3 冲突。
本卡按审计卡 R127-AUDIT-IPERSIST-V2.md 的 8 条逐条重算，并对 6/7 的分歧给出裁决。

  H1  导入表两个槽的地址与 DLL（复算审计第 1 条）
  H2  四组 IID 字节与 GUID 文本、两对相等、跨对不等（第 2 条）
  H3  0x820270 的 8 个 push 站点与正向扫描命中（第 3 条）
  H4  0x818858 的 16 个站点与 0x7f7c70 的 0 个站点、命中数（第 4 条）
  H5  三个 vtable 槽值与两个函数体内的 0x7f7c90（第 5 条）
  H6  裁决分歧：0x7f4108 的 RTTI 解析。审计员用 u32(RTTI-0xc) 取 COL，报 0 并抛异常；
      我用 u32(vtable-4) 直接当 COL 指针。用第三种独立判据定谁对：MSVC 的
      RTTICompleteObjectLocator 在 +20 处有 pSelf 字段，其值必须等于 COL 自身地址。
  H7  裁决分歧：三个入口是否落在 vtable 槽上。审计员判「否 / unknown」，我判「是」。
      用不依赖 RTTI 的判据：若某地址 P 是 vtable 的槽 k，则 u32(P - 4k - 4) 指向的 COL
      的 pSelf 自指，且该 COL 的 pTypeDescriptor 名字以 .?AV 或 .?AU 开头。
  H8  两个 IID 在 .text 里的全部出现位置（审计员报 5 处与 2 处），逐个核前一字节
"""
import os, sys, json, struct, hashlib

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
AUDIT = '/tmp/r127_audit_hy4.md'
OUT = os.path.join(ROOT, '_r127', 'r127h_ruleD2.json')
SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

h = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
add('H0 exe sha256 与本轮钉住的构建相符', h == SHA, h)

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
S = {s.Name.rstrip(b'\x00').decode(): s for s in pe.sections}
TX = S['.text']
T_LO = TX.VirtualAddress + IB
T_HI = T_LO + TX.Misc_VirtualSize
raw = pe.get_data(TX.VirtualAddress, TX.Misc_VirtualSize)
md = Cs(CS_ARCH_X86, CS_MODE_32)

def rx(va, n):
    return pe.get_data(va - IB, n)
def u32(va):
    if va is None or va < IB:
        return None
    b = rx(va, 4)
    return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rx(va, 4)
    return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=200):
    b = rx(va, n)
    e = b.find(b'\x00')
    return (b[:e] if e >= 0 else b).decode('latin1')
def in_img(v):
    return v is not None and IB <= v < 0xB80000

# ---- H1 ----
rows = []
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll = e.dll.decode() if isinstance(e.dll, bytes) else str(e.dll)
    for imp in e.imports:
        if imp.name and imp.name.decode() in ('OleSaveToStream', 'OleLoadFromStream'):
            rows.append((imp.address, dll, imp.name.decode()))
SAVE_VA = [a for a, d, n in rows if n == 'OleSaveToStream'][0]
LOAD_VA = [a for a, d, n in rows if n == 'OleLoadFromStream'][0]
add('H1 复算审计第 1 条：OleSaveToStream 在 0x7e15f4、OleLoadFromStream 在 0x7e15f8，'
    '都在 ole32.dll —— 与审计员报告一致',
    SAVE_VA == 0x7e15f4 and LOAD_VA == 0x7e15f8
    and all(d.lower().startswith('ole32') for _, d, _ in rows),
    [(hex(a), d, n) for a, d, n in rows])

# ---- H2 ----
PAIRS = [(0x7f7c80, 0x820270, '0109'), (0x7f7c70, 0x818858, '010C')]
def guid_text(va):
    d1, d2, d3 = struct.unpack('<IHH', rx(va, 8))
    d4 = rx(va + 8, 8)
    return '{%08X-%04X-%04X-%02X%02X-%s}' % (
        d1, d2, d3, d4[0], d4[1], d4[2:].hex().upper())
h2 = {}
for a, b, lab in PAIRS:
    h2[lab] = {'a': hex(a), 'b': hex(b), 'guid': guid_text(a),
               'equal': rx(a, 16) == rx(b, 16)}
cross = rx(0x7f7c80, 16) != rx(0x7f7c70, 16)
add('H2 复算审计第 2 条：两对的 16 字节逐字节相同、跨对不同；GUID 文本为 '
    '00000109-0000-0000-C000-000000000046 与 0000010C-...（与审计员逐字节输出一致）',
    all(v['equal'] for v in h2.values()) and cross
    and h2['0109']['guid'] == '{00000109-0000-0000-C000-000000000046}'
    and h2['010C']['guid'] == '{0000010C-0000-0000-C000-000000000046}', h2)

# ---- H3 / H4 ----
def push_sites(iid):
    pat = b'\x68' + struct.pack('<I', iid)
    out, st = [], 0
    while True:
        j = raw.find(pat, st)
        if j < 0:
            break
        st = j + 1
        out.append(T_LO + j)
    return out
def fed_forward(site_va, maxb=0x400):
    start = site_va + 5
    for i in md.disasm(raw[start - T_LO:start - T_LO + maxb], start):
        if i.mnemonic == 'call' and i.op_str == 'dword ptr [0x%x]' % SAVE_VA:
            return i.address
        if i.mnemonic in ('ret', 'retf'):
            return None
    return None
p109d = push_sites(0x820270)
f109d = [(s, fed_forward(s)) for s in p109d]
add('H3 复算审计第 3 条：0x820270 的 push 站点 8 个，逐个正向扫到 ret，'
    '全部命中 call [0x7e15f4]；站点地址与命中地址与审计员报告逐个相同',
    len(p109d) == 8 and all(f is not None for _, f in f109d),
    {'sites': [(hex(s), hex(f) if f else None) for s, f in f109d]})
AUD3 = {0x4af856: 0x4af8a5, 0x4b6313: 0x4b6364, 0x4db76a: 0x4db7be,
        0x50469e: 0x5046c9, 0x54b83c: 0x54b88b, 0x69ef66: 0x69efb5,
        0x719d96: 0x719de5, 0x75c756: 0x75c7a5}
add('H3b 审计员报告里给的 8 对 (push, 命中) 地址与我实测逐个相等 —— 无一条分歧',
    dict((s, f) for s, f in f109d) == AUD3, {'mine': {hex(k): hex(v) for k, v in dict(f109d).items()},
                                             'audit': {hex(k): hex(v) for k, v in AUD3.items()}})

p010c_d = push_sites(0x818858)
p010c_r = push_sites(0x7f7c70)
f010c = [(s, fed_forward(s)) for s in p010c_d + p010c_r]
add('H4 复算审计第 4 条：0x818858 的 push 站点 16 个、0x7f7c70 的 0 个，'
    '全部 16 个站点正向扫到 ret 都不命中 call [0x7e15f4] —— 与审计员一致',
    len(p010c_d) == 16 and len(p010c_r) == 0
    and all(f is None for _, f in f010c),
    {'n_818858': len(p010c_d), 'n_7f7c70': len(p010c_r),
     'hits': sum(1 for _, f in f010c if f)})

# ---- H5 ----
VTS = {(0x7e36d4, 0): 0x429360, (0x7e36d4, 3): 0x429420,
       (0x7ea564, 3): 0x429270, (0x7f4108, 0): 0x6cf430}
h5 = {}
for (vt, k), want in VTS.items():
    got = u32(vt + 4 * k)
    h5['%s@slot%d' % (hex(vt), k)] = {'got': hex(got) if got else None,
                                      'want': hex(want), 'ok': got == want}
unk = {}
for body in (0x429360, 0x429270):
    unk[hex(body)] = b'\xbf' + struct.pack('<I', 0x7f7c90) in rx(body, 0x200)
add('H5 复算审计第 5 条：0x7e36d4 slot0=0x429360、slot3=0x429420、'
    '0x7ea564 slot3=0x429270、0x7f4108 slot0=0x6cf430；0x429360 与 0x429270 体内都含 '
    '0x7f7c90 的比较 —— 与审计员一致（它也明确核出 +0xc 是 0x429420，'
    '这正好证明我第一版审计卡第 5 条写错了，S-173）',
    all(v['ok'] for v in h5.values()) and all(unk.values()),
    {'slots': h5, 'cmp_7f7c90': unk})

# ---- H6：复算审计第 6 条（追读最终版后已无分歧）----
# 过程如实记：我第一次读到的是审计员**中途**写下的 7215 字节版本，那一版第 6 条报
# ValueError('-0x400000')、三处宿主全判 unknown。我据此写了「裁决分歧」的 H6/H7。
# 随后 re-tool wait_subagents 返回的最终版（/tmp/r127_audit_hy4.md，273 行 / 11111 字节，
# 已收进 _r127/audit/r127_audit_hy4.md）第 6、7 条它自己改成了正确解析，结论与我一致。
# 所以「分歧」这个前提不成立，本卡改为逐条比对，不虚构分歧。
#
# S-177（本轮第三条自错）：我第一版 H6 用「COL 的 +20 处 pSelf 必须等于 COL 自身地址」
# 当判据，但实测该构建所有 COL 的 +20 都是 0，判据恒假。pSelf 在这个构建不可用。
COL_FIELDS = ('sig', 'ptd', 'pchd', 'class')
def col_at(va):
    if not in_img(va):
        return None
    sig = u32(va)
    if sig not in (0, 1):
        return None
    ptd, chd = u32(va + 12), u32(va + 16)
    if not in_img(ptd) or not in_img(chd):
        return None
    nm = cstr(ptd + 8, 200)
    if not (nm.startswith('.?AV') or nm.startswith('.?AU')):
        return None
    n = u32(chd + 8)
    arr = u32(chd + 12)
    if n is None or n > 64 or not in_img(arr):
        return None
    return {'col': va, 'sig': sig, 'pTypeDescriptor': ptd, 'pClassDescriptor': chd,
            'class': nm, 'n_base': n, 'bases_arr': arr, 'pSelf': u32(va + 20)}

VT_E6 = 0x7f4108
colp = u32(VT_E6 - 4)
col = col_at(colp) if colp else None
# 审计员最终版给的四个数，逐个数比对
AUD6 = {'vtable_minus_4': 0x80b730, 'pTypeInfo': 0x842730,
        'CHD': 0x80b720, 'nBaseClasses': 3, 'pBaseClassArray': 0x80b710}
mine6 = {'vtable_minus_4': colp, 'pTypeInfo': col['pTypeDescriptor'] if col else None,
         'CHD': col['pClassDescriptor'] if col else None,
         'nBaseClasses': col['n_base'] if col else None,
         'pBaseClassArray': col['bases_arr'] if col else None}
add('H6 复算审计第 6 条（最终版）：0x7f4108 的 vtable-4 = 0x80b730、pTypeInfo = 0x842730、'
    'CHD = 0x80b720、nBaseClasses = 3、pBaseClassArray = 0x80b710、类名 '
    '.?AVSwizzleManagerClass@@ —— 与审计员最终版的五个数逐个相同，无分歧',
    mine6 == AUD6, {'mine': {k: (hex(v) if isinstance(v, int) else v)
                             for k, v in mine6.items()},
                    'audit': {k: (hex(v) if isinstance(v, int) else v)
                              for k, v in AUD6.items()},
                    'pSelf_is_zero': col is not None and col['pSelf'] == 0})
# 基类三条逐条比对（审计员给 BCD、name、ncb(BCD+4)、mdisp(BCD+8)）
AUD6B = [(0x80b6f8, '.?AVSwizzleManagerClass@@', 2, 0),
         (0x80b6e0, '.?AUISwizzle@@', 1, 0),
         (0x7fa9e8, '.?AUIUnknown@@', 0, 0)]
mine6b = []
for i in range(col['n_base']):
    bcd = u32(col['bases_arr'] + 4 * i)
    td = u32(bcd)
    mine6b.append((bcd, cstr(td + 8, 200), u32(bcd + 4), i32(bcd + 8)))
add('H6b 复算审计第 6 条的基类表三条：BCD 地址、类名、ncb(BCD+4)、mdisp(BCD+8) '
    '四列逐条与审计员相同',
    mine6b == AUD6B,
    {'mine': [(hex(a), n, c, m) for a, n, c, m in mine6b],
     'audit': [(hex(a), n, c, m) for a, n, c, m in AUD6B]})

# ---- H7：复算审计第 7 条（同样已无分歧）----
# 判据（MSVC x86 标准布局）：vtable[-1] 存 COL 指针，故 P 属于 vtable B 当且仅当
# B <= P、u32(B-4) 是有效 COL、且取**最近**那个（向前扫更远会扫进相邻的前一张虚表而
# 得到别的类名：实测 0x7ea570 向前 11 个槽会得到 VectorClass，那是另一张虚表）。
def as_vtable_slot(p_va):
    best = None
    for k in range(0, 64):
        base = p_va - 4 * k
        cp = u32(base - 4)
        if not in_img(cp):
            continue
        c = col_at(cp)
        if c is None:
            continue
        best = {'vtable': base, 'slot': k, 'class': c['class'], 'col': cp}
        break
    return best
h7 = {}
for p in (0x7e36d4, 0x7ea570, 0x7f4108):
    h7[hex(p)] = as_vtable_slot(p)
ctl7 = {hex(p): as_vtable_slot(p) for p in (0x429580, 0x40f000)}
AUD7 = {'0x7e36d4': (0x7e36d4, 0, '.?AVApplicationClass@@'),
        '0x7ea570': (0x7ea564, 3, '.?AVTiberianSunClassFactory@@'),
        '0x7f4108': (0x7f4108, 0, '.?AVSwizzleManagerClass@@')}
mine7 = {k: (v['vtable'], v['slot'], v['class']) if v else None for k, v in h7.items()}
add('H7 复算审计第 7 条（最终版）：0x7e36d4 是 vtable 0x7e36d4 的 slot0'
    '（.?AVApplicationClass@@）、0x7ea570 是 vtable 0x7ea564 的 slot3'
    '（.?AVTiberianSunClassFactory@@）、0x7f4108 是 vtable 0x7f4108 的 slot0'
    '（.?AVSwizzleManagerClass@@）—— 与审计员最终版的三个宿主逐个相同，无分歧；'
    '反控：0x429580 与 0x40f000 给 None',
    mine7 == AUD7 and all(v is None for v in ctl7.values()),
    {'mine': {k: (hex(a), b, c) if x else None for k, x in
              ((k, v) for k, v in mine7.items()) for a, b, c in ([x] if x else [])},
     'control': ctl7,
     'note': '只取最近前置 COL'})

# ---- H8：两个 IID 在 .text 的全部出现位置 ----
h8 = {}
for iid, want_n in ((0x7e36c0, 5), (0x7e9b20, 2)):
    pat = struct.pack('<I', iid)
    occ, st = [], 0
    while True:
        j = raw.find(pat, st)
        if j < 0:
            break
        st = j + 1
        occ.append({'at': T_LO + j,
                    'prev_byte': raw[j - 1] if j > 0 else None,
                    'op': {0xbf: 'bf', 0x68: '68'}.get(raw[j - 1], 'other')})
    h8[hex(iid)] = occ
add('H8 复算审计第 8(ii) 条：0x7e36c0 在 .text 出现 5 次（bf 2 处 0x4292ac、0x429380；'
    '68 3 处 0x42940a、0x42948a、0x4f6937），0x7e9b20 出现 2 次（68 1 处 0x429556、'
    'bf 1 处 0x6cf44f）—— 与审计员点位逐个一致；第二处 QI 体候选为 0',
    len(h8['0x7e36c0']) == 5 and len(h8['0x7e9b20']) == 2
    and sum(1 for x in h8['0x7e36c0'] if x['op'] == 'bf') == 2
    and sum(1 for x in h8['0x7e9b20'] if x['op'] == 'bf') == 1,
    {k: [(hex(x['at']), x['op']) for x in v] for k, v in h8.items()})

# ---- H10：审计员第 8b 节 68 立即数上下文里的一条新证据（我原来漏了）----
# 审计员把 5 处 68 立即数的上下文都贴出来了，其中两处不是「把 IID 交给别人的 QI」，
# 而是**直接 call 目标 QI 体**：
#   0x4f6930  push ecx ; lea eax,[esp] ; push eax ; push 0x7e36c0 ; push 0x89a29c
#             ; call 0x429360 ; mov eax,[esp] ; pop ecx ; ret 4
#   0x429550  mov eax,[esp+8] ; push eax ; push 0x7e9b20 ; push 0xb0c110
#             ; call 0x6cf430 ; ret 8
# 这两个是 QI 体的「固定参数包装器」：IID 与对象都写死，只有出参是变量。
# 它们比 vtable 槽更硬 —— 直接证「这个 IID 就是交给这个 QI 体比的」。
def wrapper_at(lo, want_push, want_obj, want_call):
    """核一处包装器：函数体内是否恰有 push <IID>、push <obj>、call <目标>。"""
    ins = list(md.disasm(raw[lo - T_LO:lo - T_LO + 0x40], lo))
    seq = [(i.address, i.mnemonic, i.op_str) for i in ins]
    has_push = any(m == 'push' and o == '0x%x' % want_push for _, m, o in seq)
    has_obj = any(m == 'push' and o == '0x%x' % want_obj for _, m, o in seq)
    has_call = any(m == 'call' and o == '0x%x' % want_call for _, m, o in seq)
    # 顺序：push <obj> 之前必须出现 push <IID>（stdcall 从右往左压栈）
    ai = next((k for k, (_, m, o) in enumerate(seq)
               if m == 'push' and o == '0x%x' % want_push), None)
    ao = next((k for k, (_, m, o) in enumerate(seq)
               if m == 'push' and o == '0x%x' % want_obj), None)
    return {'has_iid_push': has_push, 'has_obj_push': has_obj,
            'has_call': has_call, 'iid_before_obj': ai is not None and ao is not None
            and ai < ao, 'seq': [(hex(a), m, o) for a, m, o in seq]}
W1 = wrapper_at(0x4f6930, 0x7e36c0, 0x89a29c, 0x429360)
W2 = wrapper_at(0x429550, 0x7e9b20, 0xb0c110, 0x6cf430)
add('H10 复算审计员第 8b 节里我原来漏掉的一条硬证据：存在两个「固定参数包装器」'
    '直接 call QI 体 —— 0x4f6930 把 0x7e36c0 与对象 0x89a29c 压栈后 call 0x429360；'
    '0x429550 把 0x7e9b20 与对象 0xb0c110 压栈后 call 0x6cf430。'
    '这两处比 vtable 槽更直接：证明这两个 IID 确实是交给这两个 QI 体去比的',
    all(v[k] for v in (W1, W2) for k in
        ('has_iid_push', 'has_obj_push', 'has_call', 'iid_before_obj')),
    {'wrapper_0x4f6930': W1, 'wrapper_0x429550': W2})

# 反控：同一判据对两个「非包装器」地址必须给否
C1 = wrapper_at(0x429480, 0x7e36c0, 0x89a29c, 0x429360)   # 0x429480 是 IClassFactory 包装器
add('H10b 反控：同一判据对 0x429480 给「没有 push 0x89a29c、没有 call 0x429360」——'
    '它是 IClassFactory::CreateInstance 的包装器（push 0x7e36c0 + call [ecx]），'
    '不是固定参数包装器，判据不是恒真',
    not C1['has_obj_push'] and not C1['has_call'] and C1['has_iid_push'], C1)

# ---- H9：审计员报告本身的形态（零反引号、行数）----
if os.path.exists(AUDIT):
    txt = open(AUDIT, encoding='utf-8').read()
    add('H9 审计报告 /tmp/r127_audit_hy4.md 存在、%d 行、零反引号' % len(txt.split('\n')),
        '`' not in txt and len(txt.split('\n')) > 20,
        {'lines': len(txt.split('\n')), 'bytes': len(txt.encode('utf-8'))})
else:
    add('H9 审计报告存在性', False, AUDIT + ' 不存在')

rep = {'sha': h, 'h2': h2, 'h3': {'sites': [(hex(s), hex(f) if f else None)
                                            for s, f in f109d]},
       'h4': {'n_818858': len(p010c_d), 'n_7f7c70': len(p010c_r)},
       'h5': {'slots': h5, 'cmp_7f7c90': unk},
       'h6_col_recalc': mine6, 'h6b_bases': [(hex(a), n, c, m) for a, n, c, m in mine6b],
       'h7_slot_recalc': {k: (hex(v[0]), v[1], v[2]) if v else None
                          for k, v in mine7.items()},
       'h10_wrappers': {'0x4f6930': W1, '0x429550': W2, 'ctl_0x429480': C1},
       'h8_occurrences': {k: [(hex(x['at']), x['op']) for x in v]
                          for k, v in h8.items()},
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R127h %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'][:300] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
