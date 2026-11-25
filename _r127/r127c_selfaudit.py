# -*- coding: utf-8 -*-
"""R127c：对 r127a / r127b 的结论做对抗性自审（规则 D，主会话亲自复算）。

本卡只做三件事，都不复用前两张卡的中间量：
  S1  换一套**完全不同**的方法重算 L2：不用符号执行，只在原始字节里找
      「push <IID> ... call [OleSaveToStream]」的字节窗口，数两种 IID 各出现几次。
      两套方法给出同一个 8/35 与 0/0 才算 L2 站得住。
  S2  反控：把 IID 换成已知会被别处使用的 IID（IUnknown 0x7f7c90），
      同一套「喂 OleSaveToStream」判据应给出 0 —— 证明判据不是恒真。
  S3  对 B 卡的两条定名做反例搜索：是否存在第二处接受点把 mdisp 判据引到别的名字。
"""
import os, sys, json, struct, hashlib, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r127', 'r127c_selfaudit.json')

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
S = {s.Name.rstrip(b'\x00').decode(): s for s in pe.sections}
TX = S['.text']
raw = pe.get_data(TX.VirtualAddress, TX.Misc_VirtualSize)
T_LO = TX.VirtualAddress + IB

IAT = {}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        IAT[imp.address] = imp.name.decode() if imp.name else '?'

# ---- S1：纯字节窗口法（不用反汇编，不用符号执行）----
# 形态：68 <IID32> ... E8/FF15 <call> ；这里只找「68 IID32」后 16 字节内出现
# FF 15 <OleSaveToStream 绝对地址>。这一步刻意不看指令边界。
SAVE_ABS = struct.pack('<I', [va for va, n in IAT.items() if n == 'OleSaveToStream'][0])
def byte_window_hits(iid):
    pat = b'\x68' + struct.pack('<I', iid)
    hits, fed = [], []
    st = 0
    while True:
        k = raw.find(pat, st)
        if k < 0: break
        st = k + 1
        hits.append(T_LO + k)
        seg = raw[k:k + 40]
        j = seg.find(b'\xff\x15' + SAVE_ABS)
        if j > 0:
            fed.append((T_LO + k, T_LO + k + j))
    return hits, fed

res = {}
for iid, lab in ((0x820270, '0109.d'), (0x7f7c80, '0109.r'),
                 (0x818858, '010C.d'), (0x7f7c70, '010C.r'),
                 (0x7f7c90, 'IUnknown.r')):
    h, f = byte_window_hits(iid)
    res[lab] = {'push_hits': len(h), 'fed_in_40B': len(f)}
add('S1 用纯字节窗口（68 <IID32>）独立重算 push 站点计数，与 L2/L2c 的计数必须一致：'
    '0109.d 8、0109.r 60、010C.d 16、010C.r 0。喂入数（fed_in_40B）只对'
    '「push 之后 40 字节内直接 FF 15 <OleSaveToStream>」这一形态有意义 —— 0109.r 的 35 个'
    '调用正是这一形态；0109.d 的 8 个是「先存 ppv 槽、之后从槽取出再 push」的两跳形态，'
    '40 字节窗口天然看不见，故这一项不拿 fed_in_40B 当 0109.d 的判据（如实声明）',
    res['0109.d']['push_hits'] == 8 and res['0109.r']['push_hits'] == 60
    and res['0109.r']['fed_in_40B'] == 35
    and res['010C.d']['push_hits'] == 16 and res['010C.r']['push_hits'] == 0
    and res['010C.d']['fed_in_40B'] == 0,
    res)
add('S2 反控：同一套字节窗口判据对 IID_IUnknown（0x7f7c90）给出的喂入数是 0，'
    '说明这条判据不是「怎么查都能中」',
    res['IUnknown.r']['fed_in_40B'] == 0,
    {'IUnknown push_hits': res['IUnknown.r']['push_hits'],
     'fed_in_40B': res['IUnknown.r']['fed_in_40B']})

# ---- S3：B 卡定名的反例搜索 ----
# 对 0x7e36c0 / 0x7e9b20，枚举所有 vtable 的所有槽，找出「体内比较该 IID」的全部
# (vtable, slot, class)。若某个类的 RTTI 在 mdisp 0 处给出两个以上非 IUnknown 接口名，
# 则 mdisp 判据对该类无效，必须从候选里剔除。
RD = S['.rdata']; RD_LO = RD.VirtualAddress + IB; RD_HI = RD_LO + RD.Misc_VirtualSize
def rd(va, n): return pe.get_data(va - IB, n)
def u32(va):
    try: b = rd(va, 4)
    except Exception: return None
    return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4)
    return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=200):
    b = rd(va, n); e = b.find(b'\x00')
    return (b[:e] if e >= 0 else b).decode('latin1')
def in_img(v): return v is not None and IB <= v < 0xB80000
def rtti(vt):
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
        bases.append({'name': cstr(td + 8, 200), 'mdisp': i32(bcd + 8)})
    return {'class': cstr(ptd + 8, 200), 'bases': bases}
VT = {}
for p in range(RD_LO, RD_HI - 4, 4):
    r = rtti(p)
    if r and (r['class'].startswith('.?AV') or r['class'].startswith('.?AU')):
        f = u32(p)
        if f is not None:
            VT[p] = r
add('S3 vtable 索引规模（.rdata 里 u32(P-4) 能解出 .?AV/.?AU 类名的起点数）',
    len(VT) > 1000, 'vtables=%d' % len(VT))

# 找出所有「mdisp 0 处非 IUnknown 接口名 >= 2」的类 —— 这些类上 mdisp 判据无效
amb = [(vt, r['class'], [b['name'] for b in r['bases']
                         if b['mdisp'] == 0 and b['name'].startswith('.?AU')
                         and not b['name'].endswith('IUnknown@@')])
       for vt, r in VT.items()]
bad_cls = [(hex(vt), c, n) for vt, c, n in amb if len(n) >= 2]
# 第一版把这条写成「全库 0 个模糊类」，实测有 348 个 vtable 在 mdisp 0 处同时挂着
# IPersistStream 与 IPersist —— 这不是缺陷，而是 L1 记录过的事实（两者恒同 mdisp）。
# 正确的用法是：只在「接受点的宿主类」上要求 mdisp 0 单值，全库的不单值不影响本卡结论。
add('S4 如实记：全库有 %d 个 vtable 在 mdisp 0 处挂了 >= 2 个非 IUnknown 接口名'
    '（典型是 IPersistStream + IPersist 同时挂 mdisp 0）—— 所以 mdisp 判据不能全库通用，'
    '只能用在「该类 mdisp 0 恰好单值」的宿主上；这不是反例，是判据的适用范围'
    % len(bad_cls), len(bad_cls) > 0, 'examples=%s' % bad_cls[:4])

# 两个目标 IID 的全部接受点（S-168/S-169/S-170 三次修正后的口径）。
#
# 走过的三条错路，如实记在案：
#   S-168 用 rd(f, 300) 从 vtable 槽函数的入口读固定 300 字节窗口 —— 跨过函数边界，
#        0x429210 的窗口覆盖到 0x4292ab 与 0x42937f，把 0x429210/0x6cf410 也算进来，
#        S5/S6 假 FAIL（那是判据错，不是二进制事实）。
#   S-169 改用「向前找 0xC2/0xC3 字节 + 后接连续 >=2 个 90/CC」求函数入口 —— 0xC2/0xC3
#        会以立即数字节形式出现（0x429210 之前的 c7 05 9c a2 89 00 d4 36 7e 00 c3），
#        仍算错。
#   S-170 改用 disasm_lite 的指令对齐求入口 —— .text 里嵌着数据（.byte 伪指令 65 处），
#        线性反汇编在数据上错位，求出的函数入口与末端都不可靠。
# 最终口径：**不自己求函数边界**。只做两件纯字节的事 ——
#   (1) 正向枚举 bf <IID32> 站点，并筛出其后 40 字节内含 F3 A7 的那些；
#   (2) 把这批站点集合与 r127b 独立得出的站点集合做双向差集，必须都为空。
# 函数的归属交给 r127b 那一侧（它走的是 vtable 槽 -> 函数入口，与字节枚举正交）。
def bf_sites(iid):
    """纯字节枚举 bf <IID32> 站点，并标注其后 40 字节内是否出现 F3 A7。"""
    pat = b'\xbf' + struct.pack('<I', iid)
    out, st = [], 0
    while True:
        j = raw.find(pat, st)
        if j < 0:
            break
        st = j + 1
        out.append({'site': T_LO + j,
                    'has_cmpsd': b'\xf3\xa7' in raw[j:j + 40]})
    return out

BY = {lab: bf_sites(iid) for iid, lab in
      ((0x7e36c0, '0x7e36c0'), (0x7e9b20, '0x7e9b20'))}
BYS = {k: {x['site'] for x in v if x['has_cmpsd']} for k, v in BY.items()}

# r127b 的站点来自它自己的 vtable 槽 -> 函数入口 -> 体内 mov edi,<IID> + repe cmpsd 路径，
# 与本卡的纯字节枚举正交。这里直接读它的产物文件，不抄写常量。
_d = json.load(open(os.path.join(ROOT, '_r127', 'r127b_qi_owners.json'),
                    encoding='utf-8'))
REF = {lab: {int(x['site'], 16) for x in rows}
       for lab, rows in _d['acceptors'].items()}
only_byte = {k: sorted(hex(x) for x in BYS[k] - REF.get(k, set())) for k in BYS}
only_ref = {k: sorted(hex(x) for x in REF.get(k, set()) - BYS[k]) for k in BYS}
add('S5 纯字节枚举 bf <IID32> 且其后 40 字节内出现 F3 A7（repe cmpsd）的站点，'
    '与 r127b 走 vtable 槽反查得到的站点集合双向差集都为空'
    '（0x7e36c0: 0x4292ab/0x42937f；0x7e9b20: 0x6cf44e）',
    all(len(v) > 0 for v in BYS.values())
    and not any(only_byte.values()) and not any(only_ref.values()),
    {'byte_sites': {k: sorted(hex(x) for x in v) for k, v in BYS.items()},
     'ref_sites': {k: sorted(hex(x) for x in v) for k, v in REF.items()},
     'only_in_byte': only_byte, 'only_in_ref': only_ref})

# S5b 如实记：这两个 IID 的 bf 站点**全部**在 40 字节内含 F3 A7（筛掉 0 个）。
# 这说明本判据在这两个 IID 上没有筛除力 —— 它只能证「站点集合相同」，不能证「哪个是 QI 体」。
add('S5b 如实记判据上限：两个 IID 的 bf 站点集合与筛后集合完全相同（筛掉 0 个），'
    '故此判据只证集合一致，不能单独区分 QI 体与普通比较',
    all(len(BYS[k]) == len(BY[k]) for k in BY),
    {k: {'bf_sites': len(BY[k]), 'after_cmpsd_filter': len(BYS[k])} for k in BY})

# S5c 反控：同一字节判据对 0x7f7ca0 / 0x7ea6e8 / 0x7f7c90 给出量级完全不同的站点集合，
# 且三个互不相同 —— 判据不是恒真（这一条用的是同样 40 字节窗口，没有放宽）。
ctl = {hex(i): bf_sites(i) for i in (0x7f7ca0, 0x7ea6e8, 0x7f7c90)}
ctls = {k: {x['site'] for x in v if x['has_cmpsd']} for k, v in ctl.items()}
add('S5c 反控：同一判据对 0x7f7ca0（IClassFactory）/ 0x7ea6e8 / 0x7f7c90（IUnknown）'
    '给出的筛后站点集合两两不同，且量级与两个目标 IID 不同 —— 判据不是恒真',
    len({frozenset(v) for v in ctls.values()}) == 3
    and all(len(v) >= 1 for v in ctls.values())
    and len({len(v) for v in ctls.values()} | {len(v) for v in BYS.values()}) > 1,
    {k: {'bf': len(ctl[k]), 'after_filter': len(ctls[k])} for k in ctl})

# S6 定名唯一性（与 S5 用互补信息）：r127b 给出的三个宿主 vtable，其 RTTI 在 mdisp 0 处
# 必须恰有一个非 IUnknown 接口名。
def mdisp0_of(vt):
    r = rtti(vt)
    if r is None:
        return None, None
    return r['class'], [b['name'] for b in r['bases']
                        if b['mdisp'] == 0 and b['name'].startswith('.?AU')
                        and not b['name'].endswith('IUnknown@@')]
uni = {}
for lab, rows in _d['owners'].items():
    for x in rows:
        vt = int(x['vtable'], 16)
        cname, cand = mdisp0_of(vt)
        uni['%s@slot%d' % (hex(vt), x['slot_index'])] = {
            'slot0_body': x['body'], 'class': cname,
            'mdisp0_nonIUnknown': cand}
all_single = (len(uni) == 3
              and all(len(r['mdisp0_nonIUnknown']) == 1 for r in uni.values()))
add('S6 三个宿主 vtable（0x7e36d4 / 0x7ea564 / 0x7f4108）的 RTTI 在 mdisp 0 处'
    '恰有一个非 IUnknown 接口名 ⇒ 定名唯一，不存在第二个候选',
    all_single, uni)

# ---- S7：把 r127a / r127b 的断言数逐项列出，确认没有「永远为真」的断言 ----
taut = []
for f in ('r127a_ipersist.json', 'r127b_qi_owners.json'):
    p = os.path.join(ROOT, '_r127', f)
    d = json.load(open(p, encoding='utf-8'))
    for c in d['checks']:
        det = c['detail']
        if det in ('',) and c['ok'] and 'sha256' not in c['name']:
            taut.append((f, c['name']))
add('S7 自查：两张卡里没有「结论恒真」的空断言（detail 为空的 PASS 一律列出）',
    len(taut) == 0, taut)

rep = {'byte_window': res, 'ambiguous_mdisp0_classes': bad_cls,
       'bf_sites': {k: [{'site': hex(x['site']), 'has_cmpsd': x['has_cmpsd']}
                        for x in v] for k, v in BY.items()},
       'control_iids': {k: {'bf': len(ctl[k]), 'after_filter': len(ctls[k]),
                            'sites': sorted(hex(x) for x in ctls[k])}
                        for k in ctl},
       'naming_uniqueness': uni,
       'tautologies': taut, 'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R127c %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
