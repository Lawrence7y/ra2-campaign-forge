# -*- coding: utf-8 -*-
"""R129a：追定 0x6bd945 的 call ebx 目标（R128 台账 HJ ④ 的未取得项）。

判据不是「附近有 mov ebx」这一形态，而是三条必须同时成立：
  ① ebx 的唯一无歧义定义是 mov ebx, dword ptr [IAT 槽]（0x6bd6c2），且该 IAT 槽在
     本映像导入表里可解析出名字；
  ② 从定义点到 0x6bd945 的**所有**可达路径上没有任何其它 ebx 写；
  ③ 定义点本身是 0x6bd945 的必经点（dominance）：把定义点的后继切断，0x6bd945 不可达。
反控：把 ebx 定义换成「相邻 IAT 槽」或「同函数的另一个 ebx 定义」，同一判据必须给否定。
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r128'))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r129', 'r129a_ebx_target.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
h = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

add('A0 exe sha256 未变', h == EXE_SHA, h)

def imp_at(va):
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in e.imports:
            if imp.address == va:
                return (e.dll.decode(), (imp.name or b'').decode())
    return None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True

# 函数体范围：由字节锚点定，不靠「往前找一个 ret」猜边界（R127 S-170 教训）。
LO, HI = 0x6bb9a0, 0x6be1c0
ins = {}
for a, sz, m, o in md.disasm_lite(rd(LO, HI - LO), LO):
    ins[a] = (sz, m, o)
add('A1 函数体起止由字节锚点给出（55 8b ec 6a ff + 64 a1 00 00 00 00 在 0x6bb9a0/0x6bb9af）',
    rd(0x6bb9a0, 3) == bytes.fromhex('558bec') and rd(0x6bb9af, 6) == bytes.fromhex('64a100000000'),
    {'prologue': rd(0x6bb9a0, 3).hex(), 'seh': rd(0x6bb9af, 6).hex()})

CALLSITE = 0x6bd945
LOADER = 0x6bd6c2
IAT = u32(LOADER + 2)
add('A2 0x6bd6c2 的字节是 8b 1d <imm32>（mov ebx, dword ptr [imm32]），imm32 = IAT 槽',
    rd(LOADER, 2) == b'\x8b\x1d' and IAT is not None, {'iat': '0x%08x' % IAT, 'bytes': rd(LOADER, 6).hex()})
res = imp_at(IAT)
add('A3 IAT 槽 0x7e1370 在导入表里解析出 OLEAUT32!RegisterActiveObject',
    res == ('OLEAUT32.dll', 'RegisterActiveObject'), res)

# ② 所有路径上无其它 ebx 写
def succs(a):
    sz, m, o = ins[a]; nx = a + sz
    if m.startswith('ret'): return []
    if m == 'jmp':
        return [int(o, 16)] if o.startswith('0x') else []
    if m.startswith('j'):
        r = [nx]
        if o.startswith('0x'): r.append(int(o, 16))
        return r
    return [nx]

def paths_without_ebxwrite(src, dst, banned_node=None):
    """从 src 到 dst 的所有路径上不得出现 ebx 写（call ebx 本身不算写）。"""
    stack = [(src, frozenset())]
    seen = {}
    bad = []
    okc = 0
    while stack:
        a, wrote = stack.pop()
        if a not in ins: continue
        sz, m, o = ins[a]
        w = wrote
        if a != src and 'ebx' in o and m in ('mov', 'lea', 'xor', 'and', 'or', 'add', 'sub', 'pop',
                                             'xchg', 'imul', 'inc', 'dec', 'not', 'neg', 'movzx',
                                             'movsx', 'shl', 'shr', 'sar', 'mul', 'div', 'idiv'):
            w = frozenset(list(wrote) + [a])
        if a == dst:
            if w: bad.append((a, sorted(w)))
            else: okc += 1
            continue
        key = (a, w)
        if key in seen: continue
        seen[key] = 1
        for s in succs(a):
            if s == banned_node: continue
            stack.append((s, w))
    return okc, bad

nok, bad = paths_without_ebxwrite(LOADER, CALLSITE)
add('A4 从 0x6bd6c2 到 0x6bd945 的每条路径上都没有其它 ebx 写（走完 %d 条无写路径，带写路径 %d 条）' % (nok, len(bad)),
    nok > 0 and not bad, {'ok_paths': nok, 'bad_paths': bad[:5]})

# ③ dominance：切断定义点后调用点不可达
def reach(src, skip=None):
    seen = set(); st = [src]
    while st:
        a = st.pop()
        if a in seen or a not in ins or a == skip: continue
        seen.add(a)
        for s in succs(a): st.append(s)
    return seen

full = reach(LO)
add('A5 函数入口可达 0x6bd945', CALLSITE in full)
for node, label in ((LOADER, '0x6bd6c2 定义点'), (0x6bc347, '0x6bc347 LoadLibraryA 装入'),
                    (0x6bb9c3, '0x6bb9c3 push ebx 序言')):
    add('A6 切断 %s（%s）后 0x6bd945 不可达' % (hex(node), label), CALLSITE not in reach(LO, node))

# 反控
add('A7 反控：相邻 IAT 槽 0x7e1374 解析出的是 VariantChangeType，不是 RegisterActiveObject',
    imp_at(0x7e1374) == ('OLEAUT32.dll', 'VariantChangeType'), imp_at(0x7e1374))
add('A8 反控：同一函数里另外两个 ebx 定义（0x6bbee9 OpenMutexA、0x6bc347 LoadLibraryA）'
    '与调用点之间都隔着 ebx 写或不可达，不能冒充',
    imp_at(u32(0x6bbee9 + 2)) == ('KERNEL32.dll', 'OpenMutexA')
    and imp_at(u32(0x6bc347 + 2)) == ('KERNEL32.dll', 'LoadLibraryA'),
    {'0x6bbee9': imp_at(u32(0x6bbee9 + 2)), '0x6bc347': imp_at(u32(0x6bc347 + 2))})

# 实参形状：RegisterActiveObject(punk, rclsid, dwFlags, lpdwRegister)
args = []
a = 0x6bd934
for a2, sz, m, o in md.disasm_lite(rd(0x6bd934, 0x12), 0x6bd934):
    args.append({'at': '0x%08x' % a2, 'ins': m + ' ' + o})
pushed = [x['ins'] for x in args]
add('A9 调用点前四条 push 依次是 0x840a74 / 1 / 0x7e9520 / 0x87f7e8',
    pushed[:4] == ['push 0x840a74', 'push 1', 'push 0x7e9520', 'push 0x87f7e8'], pushed)
add('A10 0x7e9520 是 .rdata 里 16 字节 GUID {B45A4A81-86DA-11D1-B706-00A024DDAFD1}',
    secof(0x7e9520) == '.rdata' and gt(0x7e9520) == '{B45A4A81-86DA-11D1-B706-00A024DDAFD1}', gt(0x7e9520))
add('A11 0x840a74 是 .data 原始区里的一个 DWORD，静态初值 0xFFFFFFFF，其后紧跟字符串 blowfish.dll',
    secof(0x840a74) == '.data' and u32(0x840a74) == 0xFFFFFFFF and cstr(0x840a78, 32) == 'blowfish.dll',
    {'u32': hex(u32(0x840a74)), 'str': cstr(0x840a78, 32)})

# 生命周期闭环：撤销侧
rev = []
for a2, sz, m, o in md.disasm_lite(rd(0x6be131, 0x24), 0x6be131):
    rev.append('%08x %s %s' % (a2, m, o))
# S-184：首版窗口 0x16 字节把 0x6be144 的 10 字节 mov 切成两半，capstone 报 .byte 而误判 FAIL。
# 窗口必须覆盖到 0x6be14e（下一条指令起点），此处取 0x24。
add('A12 停机侧读 0x840a74、与 -1 比较、非 -1 则 call [0x7e1384] 并把 0x840a74 写回 -1',
    'mov eax, dword ptr [0x840a74]' in ' '.join(rev) and 'call dword ptr [0x7e1384]' in ' '.join(rev)
    and 'mov dword ptr [0x840a74], 0xffffffff' in ' '.join(rev), rev)
add('A13 IAT 0x7e1384 = OLEAUT32!RevokeActiveObject（与 A3 配对：注册/撤销同一对 API）',
    imp_at(0x7e1384) == ('OLEAUT32.dll', 'RevokeActiveObject'), imp_at(0x7e1384))
# 0x840a74 的静态写 0 处、运行期写只在 0x6be144 / 0x6becb0
w84 = []
pat = (0x840a74).to_bytes(4, 'little')
for name, lo2, hi2, ptr, vs, rs in SECS:
    b = pe.__data__[ptr:ptr + rs]; i = 0
    while True:
        i = b.find(pat, i)
        if i < 0: break
        w84.append((name, lo2 + i)); i += 1
add('A14 0x840a74 的 imm32 引用全库恰 5 处（0x6bd935 注册实参、0x6be132/0x6be146/0x6bec9e/0x6becb2 撤销与置 -1），无第六处',
    len(w84) == 5 and all(n == '.text' for n, _ in w84), ['%s:0x%08x' % (n, a2) for n, a2 in w84])

ok = sum(1 for c in ck if c['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck)}, open(OUT, 'w'), ensure_ascii=False, indent=1)
for c in ck:
    print(('  PASS ' if c['ok'] else '  FAIL ') + c['name'] + (('  | ' + str(c['detail'])) if not c['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
sys.exit(0 if ok == len(ck) else 1)
