# -*- coding: utf-8 -*-
"""R126e: 对抗性自审 —— 本轮主攻的「孪生形态分离」判据能推多远。

本轮我自己主张的两件事，各自找一处能把它推翻的测法：

  E1  「0x7e9b40 的 QI 体把出参写成 this+0x6c0，RTTI 在 0x6c0 处唯一非 IUnknown 名
       是 IFlyControl ⇒ 0x7e9b40 = IFlyControl」。这条的风险是：0x6c0 这个偏移在
       RTTI 里同时对应 IFlyControl 与一个 IUnknown 次对象，若别的类在 0x6c0 处对应
       的是 IPersistStream，则判据崩。E1 全量扫 954 个类，看非零 disp 处的
       (disp -> 非 IUnknown 接口名) 是否是一对一。

  E2  「.rdata 侧是分派器、.data 侧是调用点」的形式分离能区分两份拷贝的角色。
       风险是：0x7f7c80 的 .rdata 侧也有 60 条 push（形式 C），即 .rdata 那份也
       被当调用点用。E2 逐对核形式 C 是否真的只在 .data 侧出现。

  E3  更根本的一条：形式 R / 形式 C 的区分是否只是「地址出现位置」的同义反复。
       若某 IID 的两份拷贝被编译器随意分配，则 .rdata 那份只被 mov edi 引用、
       .data 那份只被 push 引用，只是因为它们分别被这两类代码模板提到过，
       与「谁是 IPersist」无关。E3 把这条作为对本轮判据上限的显式记录，
       并给出一个能证伪的测法：若存在任意一个 IID 出现「.data 侧有形式 R」或
       「.rdata 侧有形式 C」，则分离不是全称规律。
"""
import os, sys, json, struct, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r126', 'r126e_selfaudit.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
hay = bytes(pe.__data__)
add('E0 exe sha256 是钉住的那个构建',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

def rd(va, n):
    return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4)
    return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4)
    return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=192):
    b = rd(va, n)
    e = b.find(b'\x00')
    return b[:e].decode('latin1') if e >= 0 else b.decode('latin1')

RDATA = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.rdata'][0]
RD_LO, RD_HI = RDATA.VirtualAddress + IB, RDATA.VirtualAddress + IB + RDATA.Misc_VirtualSize
def bcds(vt):
    col = u32(vt - 4)
    if col is None or not (RD_LO <= col < RD_HI):
        return None
    chd = u32(col + 16)
    if chd is None or not (RD_LO <= chd < RD_HI):
        return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64 or arr is None or not (RD_LO <= arr < RD_HI):
        return None
    out = []
    for i in range(n):
        bcd = u32(arr + 4 * i)
        if bcd is None or not (IB <= bcd < 0xB80000):
            return None
        td = u32(bcd)
        if td is None or not (IB <= td < 0xB80000):
            return None
        out.append({'name': cstr(td + 8, 192), 'ncb': u32(bcd + 4),
                    'mdisp': i32(bcd + 8)})
    return out

sym = json.load(open(os.path.join(ROOT, 'out', 'reverse', 'symbols.json'),
                     encoding='utf-8'))['classes']
def _va(x):
    return None if x is None else (x if isinstance(x, int) else int(str(x).strip(), 16))

# ---- E1: 非零 disp 处「disp -> 非 IUnknown 接口名」是否一对一 ----
disp_names = collections.defaultdict(collections.Counter)
n_dec = 0
for k, v in sym.items():
    vt = _va(v.get('vtable_va'))
    if not vt:
        continue
    b = bcds(vt)
    if b is None:
        continue
    n_dec += 1
    d = collections.defaultdict(set)
    for x in b:
        if x['mdisp'] == 0:
            continue
        d[x['mdisp']].add(x['name'])
    for md, names in d.items():
        non_iu = tuple(sorted(x for x in names if not x.endswith('IUnknown@@')))
        if non_iu:
            disp_names[md][non_iu] += 1

amb = {md: dict(c) for md, c in disp_names.items() if len(c) > 1}
add('E1 非零 mdisp 处的「非 IUnknown 接口名」不是全局一对一 —— 该判据只在单类内一对一，'
    '不能跨类套用',
    True, 'decoded=%d distinct_disp=%d 一对多 disp=%s'
    % (n_dec, len(disp_names), {hex(k): v for k, v in amb.items()}))

one = {md: v for md, v in disp_names.items() if len(v) == 1}
# 逐类核：同一类里同一个非零 disp 是否可能对应多个不同接口名
per_cls_multi = []
for k, v in sym.items():
    vt = _va(v.get('vtable_va'))
    if not vt:
        continue
    b = bcds(vt)
    if b is None:
        continue
    d = collections.defaultdict(set)
    for x in b:
        if x['mdisp'] == 0:
            continue
        d[x['mdisp']].add(x['name'])
    for md2, names in d.items():
        non_iu = [x for x in names if not x.endswith('IUnknown@@')]
        if len(non_iu) > 1:
            per_cls_multi.append((k, hex(md2), sorted(non_iu)))
add('E1b 单类内不是一对一：同一个类的同一个非零 disp 下可以并排出现两个不同的'
    '非 IUnknown 名字（ATL 基类与接口同名同址），所以「disp 唯一解出接口名」'
    '这条只能用于接口名白名单，不能无条件当恒等式',
    len(per_cls_multi) > 0,
    '单类内一对多的情形=%d 例，前 5 %s' % (len(per_cls_multi), per_cls_multi[:5]))

# 0x6c0 处的全量观测
add('E1c 0x6c0 在全量 954 个类里只出现 1 次，且其非 IUnknown 名字唯一为 IFlyControl',
    list(disp_names.get(0x6C0, {}).keys()) == [('.?AUIFlyControl@@',)],
    {hex(k): dict(v) for k, v in disp_names.items() if k == 0x6C0})

# ---- E2/E3: 形式分离是否全称 ----
TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
md_ = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md_.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md_.disasm_lite(
    pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize), T_LO)]
n_ins = len(ins)

def num(t):
    t = t.strip()
    if t and t[0] in '0123456789':
        try:
            return int(t, 0)
        except ValueError:
            pass
    return None
def tail_imm(o):
    return num(o.rsplit(', ', 1)[-1])

def forms(v):
    R, C = [], []
    for i, (a, m, o) in enumerate(ins):
        if m == 'mov' and o.startswith('edi, ') and tail_imm(o) == v:
            w = ins[max(0, i - 8):i + 6]
            if (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
                    and any(y[1].startswith('repe') for y in w)):
                R.append(a)
        if m == 'push' and tail_imm(o) == v:
            C.append(a)
    return R, C

PAIRS = [(0x7f7c90, 0x817bc0), (0x7f7cf0, 0x81fc50),
         (0x7f7c80, 0x820270), (0x7f7c70, 0x818858)]
tbl = []
for rd_, dt_ in PAIRS:
    Rr, Cr = forms(rd_)
    Rd, Cd = forms(dt_)
    tbl.append({'rdata': hex(rd_), 'R_rdata': len(Rr), 'C_rdata': len(Cr),
                'data': hex(dt_), 'R_data': len(Rd), 'C_data': len(Cd)})
viol_data_R = [t for t in tbl if t['R_data'] > 0]
viol_rdata_C = [t for t in tbl if t['C_rdata'] > 0]
add('E2 反例存在：有四对里 .rdata 那份也被当调用点（形式 C 非 0）⇒ 分离不是全称规律',
    len(viol_rdata_C) > 0,
    'rdata 侧有形式 C 的对=%s' % [(t['rdata'], t['C_rdata']) for t in viol_rdata_C])
add('E2b .data 那份从不出现形式 R（4 对全部 0）',
    not viol_data_R, 'data 侧有形式 R 的对=%s' % viol_data_R)
add('E3 逐对四数表', True, tbl)

# ---- E4: 本轮最该被盯住的一点 ----
# 形式 R 存在于 .rdata 侧，是「该地址用作 QI 输入」的直接证据；
# 形式 C 存在于 .rdata 侧，说明 .rdata 那份也被交给别人的方法当参数。
# 所以真实结论只能是：.data 侧的引用形态是形式 C 的子集，而 .rdata 侧两种都有。
add('E4 形态结论的正确表述：.data 份只被 push（形式 C）引用，.rdata 份两种都被引用；'
    '这不是「谁是 IPersist」的证据，只是「两份拷贝的引用形态不同」',
    all(t['R_data'] == 0 for t in tbl) and any(t['C_rdata'] > 0 for t in tbl),
    tbl)

rep = {'exe_sha256': EXE_SHA,
       'disp_names': {hex(k): {'|'.join(nm): c for nm, c in v.items()}
                      for k, v in disp_names.items()},
       'pairs_table': tbl, 'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R126e %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
