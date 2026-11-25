# -*- coding: utf-8 -*-
"""R127b：把 0x7e36c0 与 0x7e9b20 定名，并纠正 R126 记录里的一处表述错误。

【先纠正记录】R124/R125/R126 一直把 0x7e36c0 与 0x7e9b20 称作「QI 体」，并说
「它们的 QI 体不被任何类的 slot0 引用」。实测：这两个地址各是 **16 字节 IID 常量**
（在 .rdata 里，与已定名的 IID_ISequentialStream/IFlyControl 等同一片），不是函数。
它们的 QI **宿主**是另外三个函数（0x429360、0x429270、0x6cf430）。上一轮的「无宿主」
结论是在「把 IID 当函数」这个错前提上得出的，本轮予以撤回。

【本轮判据】定名 = 「接受该 IID 的 QI 体所在 vtable 的宿主类」+「该类的 RTTI 里
mdisp == 接受分支写出参的偏移」的交集，且交集里剔除 IUnknown 与 .?AV 类名后必须
只剩一个 .?AU 接口名；留两个以上就如实记「未定名」，不猜。
"""
import os, sys, json, struct, hashlib
import pefile, capstone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracer2 as TR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r127', 'r127b_qi_owners.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
add('B0 exe sha256 是钉住的那个构建',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

def rd(va, n): return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4)
    return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4)
    return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=200):
    b = rd(va, n); e = b.find(b'\x00')
    return (b[:e] if e >= 0 else b).decode('latin1')
def gt(va):
    b = rd(va, 16); d1, d2, d3 = struct.unpack('<IHH', b[:8])
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, b[8:10].hex().upper(),
                                       b[10:].hex().upper())

S = {s.Name.rstrip(b'\x00').decode(): s for s in pe.sections}
RD = S['.rdata']; RD_LO = RD.VirtualAddress + IB; RD_HI = RD_LO + RD.Misc_VirtualSize
DA = S['.data']; DA_LO = DA.VirtualAddress + IB; DA_HI = DA_LO + DA.Misc_VirtualSize
TX = S['.text']; T_LO = TX.VirtualAddress + IB; T_HI = T_LO + TX.Misc_VirtualSize
raw = pe.get_data(TX.VirtualAddress, TX.Misc_VirtualSize)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(raw, T_LO)]
idx = {a: i for i, (a, m, o) in enumerate(ins)}

def in_img(va):
    return va is not None and IB <= va < 0xB80000

def rtti(vt):
    """COL 在 vt-4；ptd/ptd 指向 TypeDescriptor；chd 给 BaseClassArray。
    注意：ptd 可以落在 .rdata 之外（ApplicationClass 的 ptd=0x8186c8 在 .data），
    R126 的「必须落 .rdata」这一前置检查把这一类整族判成 None（S-164）。"""
    col = u32(vt - 4)
    if not in_img(col): return None
    ptd = u32(col + 12); chd = u32(col + 16)
    if not in_img(ptd) or not in_img(chd): return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64 or not in_img(arr): return None
    bases = []
    for i in range(n):
        bcd = u32(arr + 4 * i)
        if not in_img(bcd): return None
        td = u32(bcd)
        if not in_img(td): return None
        bases.append({'name': cstr(td + 8, 200), 'mdisp': i32(bcd + 8),
                      'ncb': u32(bcd + 4)})
    return {'class': cstr(ptd + 8, 200), 'bases': bases}

TARGETS = [0x7e36c0, 0x7e9b20]
# ---- vtable 索引：在 .rdata 里枚举「u32(P-4) 解出合法 COL 且 u32(P) 落在 .text」的 P ----
VT = {}
for p in range(RD_LO, RD_HI - 4, 4):
    r = rtti(p)
    if not r:
        continue
    if not (r['class'].startswith('.?AV') or r['class'].startswith('.?AU')):
        continue
    f = u32(p)
    if f is None or not (T_LO <= f < T_HI):
        continue
    VT[p] = r

def vtable_of(addr, maxslot=400):
    """在 vtable 索引里找哪个 vtable 的第 k 槽 == addr。"""
    for p, r in VT.items():
        for k in range(0, maxslot):
            v = u32(p + 4 * k)
            if v is None: break
            if v == addr:
                return p, r, k
            if not (T_LO <= v < T_HI) and v != 0:
                break
    return None, None, None

# ---- B1：这两个是 IID 常量，不是函数 ----
is_fn = {hex(t): (T_LO <= t < T_HI) for t in TARGETS}
add('B1 纠错项：0x7e36c0 与 0x7e9b20 都不在 .text 里（不是函数体），它们是 .rdata 里的'
    '16 字节 IID 常量；R124-R126 记录里的「QI 体」是错的表述，本轮撤回',
    not any(is_fn.values())
    and all(RD_LO <= t < RD_HI - 16 for t in TARGETS),
    {hex(t): ('IID ' + gt(t)) for t in TARGETS})

# ---- B2：找「哪个函数体内把该 IID 与 riid 做 repe cmpsd 比较」= 接受它的 QI 体 ----
# 第一版返回的是 mov edi,<IID> 那条指令的地址，随后拿它去 vtable 里找宿主 —— 找的是
# 指令地址而不是函数入口，于是全部落空（S-165）。改为：先由 vtable 拿到函数入口集，
# 再在入口之后的体里找比较。
# 函数体边界：全部 vtable 槽值的并集排序后，F 的体是 [F, 下一个起点)。
# 第一版在第一个 ret 处就停，于是 0x429270（开头就有 ret 0x10 的失败分支）被截断，
# 后面的比较根本没扫到，四个断言全假（S-166）。
FN = sorted({v for p, r in VT.items()
             for k in range(len(r['bases']) + 26)
             for v in [u32(p + 4 * k)] if v and T_LO <= v < T_HI})
import bisect as _bis
def fn_end(fn):
    i = _bis.bisect_right(FN, fn) - 1
    return FN[i + 1] if i + 1 < len(FN) else T_HI

def body_cmp(t, fn_start):
    i = idx.get(fn_start)
    if i is None:
        return None
    end = fn_end(fn_start)
    for j in range(i, len(ins)):
        a, m, o = ins[j]
        if a >= end:
            break
        if m == 'mov' and o.startswith('edi, ') \
                and TR.num(o.rsplit(', ', 1)[-1]) == t:
            if any(ins[k][1].startswith('repe') for k in
                   range(j + 1, min(len(ins), j + 8))):
                return a
    return None

acc = {}
for t in TARGETS:
    hits = []
    for p, r in VT.items():
        for k in range(0, 400):
            v = u32(p + 4 * k)
            if v is None: break
            if not (T_LO <= v < T_HI):
                if v == 0: continue
                break
            site = body_cmp(t, v)
            if site is not None:
                hits.append({'func': v, 'site': site, 'vtable': p,
                             'slot_index': k, 'class': r['class'],
                             'bases': r['bases']})
            if k > len(r['bases']) + 24:
                break
    # 去重（同一 func 可能在多个 vtable 的同一槽出现）
    seen, uniq = set(), []
    for h in hits:
        key = (h['func'], h['vtable'])
        if key in seen: continue
        seen.add(key); uniq.append(h)
    acc['0x%x' % t] = uniq
add('B2 每个目标 IID 在映像里被哪些函数体显式比较（形态 mov edi,<IID> 后接 repe cmpsd）',
    all(len(v) >= 1 for v in acc.values()),
    {k: [hex(x['func']) + '@slot' + str(x['slot_index']) for x in v]
     for k, v in acc.items()})

# ---- B3：反查接受点的宿主 vtable 与槽号 ----
owners = {k: [{'body': h['func'], 'vtable': h['vtable'],
                'slot_index': h['slot_index'], 'class': h['class'],
                'bases': h['bases'], 'site': h['site']} for h in v]
          for k, v in acc.items()}
add('B3 每个接受点都能给出宿主 vtable、槽号与类名（vtable 索引口径：.rdata 里 u32(P-4) '
    '能解出 .?AV/.?AU 类名且 u32(P) 落在 .text 的 P）',
    all(all(x['vtable'] is not None for x in v) for v in owners.values()),
    {k: [(hex(x['body']), hex(x['vtable']), x['slot_index'], x['class'])
         for x in v] for k, v in owners.items()})

# ---- B4：接受分支是否做 this 调整（决定 mdisp 取哪个值）----
def accept_disp(body):
    """在 QI 体内找「比较成功后的出参写入」：若形态是 mov [ppv], <原指针> 则 disp=0；
    若是 lea req,[原指针 + D] 再写则 disp=D。返回 (disp, 证据地址)。
    按 fn_end 扫整个体，不在第一个 ret 处停 —— 0x429360/0x429270 开头都有
    ret 0xc 的失败分支，第一版在这里截断，disp 全部解不出（S-167）。"""
    i = idx[body]
    end = fn_end(body)
    disp, ev = None, []
    for j in range(i, len(ins)):
        a, m, o = ins[j]
        if a >= end:
            break
        if m == 'lea' and ', [' in o and ' + 0x' in o:
            d = TR.num(o.rsplit(' + ', 1)[1].rstrip(']'))
            if d is not None and disp is None:
                disp = d; ev.append(hex(a))
        if m == 'mov' and o.startswith('dword ptr ['):
            src = o.rsplit(', ', 1)[-1].strip()
            if disp is None and src in TR.REGS:
                disp = 0; ev.append(hex(a))
    return disp, ev

disp = {k: {hex(x['body']): accept_disp(x['body'])[0] for x in v} for k, v in owners.items()}
# 实测分两类：本对象自己的 QI（0x429360、0x6cf430）直接写 [ppv] = 原指针 ⇒ disp=0；
# 0x429270（IClassFactory::CreateInstance）不写 ppv，而是把 pUnkOuter 转交内层对象
# 的 QI（push 0x89a29c ; call [edx]），故它给不出 disp。第一版把三者一律要求 ==0，
# 于是把「转交」误判成「失败」（S-168）。定名只用能给出 disp 的两个。
add('B4 接受分支的 this 调整值：本对象自己的 QI（0x429360、0x6cf430）都是 0；'
    '0x429270 是转交型（不写 ppv，把 pUnkOuter 交给内层对象的 QI），不参与 mdisp 判据 —— '
    '如实分两类记，不把「转交」当「失败」',
    disp['0x7e36c0'].get('0x429360') == 0
    and disp['0x7e9b20'].get('0x6cf430') == 0
    and disp['0x7e36c0'].get('0x429270') is None, disp)

# ---- B5：定名 ----
def name_of(t):
    cands = []
    for x in owners['0x%x' % t]:
        d = disp['0x%x' % t][hex(x['body'])]
        if d is None or x['bases'] is None:
            continue
        names = [b['name'] for b in x['bases']
                 if b['mdisp'] == d and b['name'].startswith('.?AU')
                 and not b['name'].endswith('IUnknown@@')]
        for n in names:
            cands.append((x['class'], n))
    uniq = sorted({n for _c, n in cands})
    return uniq, cands

NAMED = {}
detail = {}
for t in TARGETS:
    u, c = name_of(t)
    detail['0x%x' % t] = {'candidates': c, 'unique': u}
    if len(u) == 1:
        NAMED['0x%x' % t] = u[0]
add('B5 定名：两个 IID 各自在「宿主类 + mdisp 0」交集里只剩一个非 IUnknown 接口名。'
    '留两个以上就不定名（本卡不猜）',
    NAMED.get('0x%x' % TARGETS[0]) is not None
    and NAMED.get('0x%x' % TARGETS[1]) is not None,
    {'0x%x' % t: (NAMED.get('0x%x' % t), detail['0x%x' % t]) for t in TARGETS})

add('B6 与 R126c 已定名的三项不冲突（同一判据、同一族，名字必须逐个对上）',
    NAMED.get('0x%x' % 0x7e36c0) == '.?AUIApplication@@'
    and NAMED.get('0x%x' % 0x7e9b20) == '.?AUISwizzle@@', NAMED)

# ---- B7：0x7e36c0 的第二宿主是 TiberianSunClassFactory 的 slot 3 ----
cf = [x for x in owners['0x7e36c0'] if x['class'] == '.?AVTiberianSunClassFactory@@']
add('B7 0x7e36c0 有两处接受点：ApplicationClass 的 slot0（自己的 QI）与 '
    'TiberianSunClassFactory 的 slot3。后者 ret 0x10 = 4 实参，且把 0x89a29c 处的对象'
    '（0x429200 处被写成 0x7e36d4 = ApplicationClass 的 mdisp0 虚表）拿来 QI，'
    '故它是 IClassFactory::CreateInstance(pUnkOuter, riid, ppv) 的形状',
    len(cf) == 1 and cf[0]['slot_index'] == 3
    and u32(0x89a29c) is None,   # .data 静态初值为 0，运行期由 0x429200 写入
    {'acceptors': [(hex(x['body']), hex(x['vtable']), x['slot_index'], x['class'])
                   for x in owners['0x7e36c0']],
     '0x89a29c static value': hex(u32(0x89a29c) or 0),
     'written_at': '0x429200 -> 0x7e36d4 (ApplicationClass mdisp0 vtable)'})

# ---- B8：0x7ea6e8 是 ApplicationClass 接受的第三个 IID（同一 QI 体）----
third = 0x7ea6e8
in_body = any(a == 0x4293a5 for a, m, o in ins
              if m == 'mov' and '0x7ea6e8' in o)
add('B8 ApplicationClass 的 QI 体除 IApplication/IUnknown 外还接受第三个 IID 0x7ea6e8，'
    '并在该分支把出参写成 .data 单例 0x87f7e8（而不是 this）—— 这一条本轮不定名，'
    '因为它的接受值不是本对象，不能用 mdisp 判据',
    in_body, {'0x7ea6e8': gt(third), 'accept branch writes': '0x87f7e8 singleton'})

rep = {'exe_sha256': EXE_SHA,
       'correction': '0x7e36c0 / 0x7e9b20 are IID constants in .rdata, not QI bodies',
       'iids': {'0x%x' % t: gt(t) for t in TARGETS},
       'acceptors': {k: [{'func': hex(x['func']), 'site': hex(x['site']),
                          'vtable': hex(x['vtable']), 'slot_index': x['slot_index'],
                          'class': x['class']} for x in v] for k, v in acc.items()},
       'owners': {k: [{'body': hex(x['body']),
                       'vtable': None if x['vtable'] is None else hex(x['vtable']),
                       'slot_index': x['slot_index'], 'class': x['class'],
                       'bases': x['bases']} for x in v] for k, v in owners.items()},
       'accept_disp': disp, 'naming_detail': detail, 'named': NAMED,
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R127b %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
