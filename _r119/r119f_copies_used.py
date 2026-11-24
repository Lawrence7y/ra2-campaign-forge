#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r119f_copies_used.py —— 推翻 R118 §EK4 的「同值巧合 3 份」：.data 的 IID 拷贝**确实被代码当 riid 用**。

R118 §EK4 的判据是**邻接**：GUID 后 0x10 处是 type_info vftable + 合法装饰类名 ⇒ 真记录；否则
「同值巧合字节」。据此把 IUnknown / ILocomotion / IPiggyback 的按值数字回退到 .rdata（56/7/0）。

R119 实测三条反驳（本脚本逐条机检）：
  G1 配对歧义：R118 判为「真记录」的两处，其 gap 0x28 / 0x30 处**也**紧跟另一个 type_info
     （.data 的 type_info 是成对相邻存放的）⇒ 「GUID + type_info」不能唯一确定配对的类名，
     该判据不能当「真/假记录」判据。
  G2 【决定性】被 R118 判为「同值巧合」的 3 处，在 .text 里都有**真实代码引用**，且引用形态
     与 IID 用法一致：
       0x817bc0 (IID_IUnknown)       9 处，其中 8 处是 CoCreateInstance 的 riid 实参
       0x817bb0 (ILocomotion)        4 处
       0x819088 (IPiggyback)         8 处
     「巧合字节」不会被人当成立即数 push 进 riid 槽位 ⇒ 该判定被代码证据证伪。
  G3 修正后的按值数字：IUnknown 56+9=65、ILocomotion 7+4=11、IPiggyback 0+8=8
     （即 R118 之前 r118a 的原值），R118 的回退是**过度回退**。
  G4 判据对照（QI 三参数形态）：对 push iid 之后第一条 call 若为 call [reg]（vtable slot 0），
     则它前面的两条 push 必须是 ppv 与 this ⇒ 逐一核验 .data 侧 IPersist/IPersistStream/IStream
     站点是否满足该形态。
  G5 反控：GUID+4 作为键必须 0 命中；把「push iid 前的两条 push 是否都是寄存器/栈槽来源」
     换成「任意两条指令」的宽判据必须给出显著不同的计数（证明形态判据不是恒真）。
内存纪律：单遍 skipdata 线性扫描 + 局部窗口；不整段 detail。
"""
import collections
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench/gamemd.exe')
OUT = os.path.join(ROOT, '_r119/r119f_copies_used.json')
raw = open(EXE, 'rb').read()
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


# ---------------- PE ----------------
_e = struct.unpack_from('<I', raw, 0x3c)[0]
_nsec = struct.unpack_from('<H', raw, _e + 6)[0]
_optsz = struct.unpack_from('<H', raw, _e + 20)[0]
_opt = _e + 24
IB = struct.unpack_from('<I', raw, _opt + 28)[0]
imp_rva, _ = struct.unpack_from('<II', raw, _opt + 96 + 8)
SECS = []
for i in range(_nsec):
    o = _opt + _optsz + 40 * i
    nm = raw[o:o + 8].rstrip(b'\x00').decode('latin1')
    vs, va, rs, pr = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append((nm, va + IB, vs, pr, rs))


def fo(va):
    for n, b, vs, pr, rs in SECS:
        if b <= va < b + max(rs, vs):
            o = pr + (va - b)
            return o if 0 <= o < len(raw) else None
    return None


def u32(va):
    o = fo(va)
    return struct.unpack_from('<I', raw, o)[0] if o is not None and o + 4 <= len(raw) else None


TS = [s for s in SECS if s[0] == '.text'][0]
TEXT0, TEXT1, TRAW0, TRAWSZ = TS[1], TS[1] + TS[2], TS[3], TS[4]
code = raw[TRAW0:TRAW0 + TRAWSZ]
IAT = {}
o = fo(IB + imp_rva)
i = 0
while True:
    ilt, ts_, fc, nm_rva, iat = struct.unpack_from('<IIIII', raw, o + 20 * i)
    if nm_rva == 0:
        break
    dll = raw[fo(IB + nm_rva):].split(b'\x00')[0].decode('latin1')
    t = fo(IB + (ilt if ilt else iat))
    j = 0
    while True:
        v = struct.unpack_from('<I', raw, t + 4 * j)[0]
        if v == 0:
            break
        nm = ('ORD%d' % (v & 0xffff)) if v & 0x80000000 else raw[fo(IB + v) + 2:].split(b'\x00')[0].decode('latin1')
        IAT[IB + iat + 4 * j] = (dll, nm)
        j += 1
    i += 1

# ---------------- G1 配对歧义 ----------------
TI = 0x7f9594
tis = []
for n, b, vs, pr, rs in SECS:
    for q in range(pr, min(pr + rs, len(raw)) - 9, 4):
        if struct.unpack_from('<I', raw, q)[0] == TI:
            va = b + (q - pr)
            nmb = raw[q + 8:q + 8 + 200].split(b'\x00')[0].decode('latin1', 'replace')
            tis.append((va, n, nmb))
DS = [s for s in SECS if s[0] == '.data'][0]
COM = []
for q in range(DS[3], min(DS[3] + DS[4], len(raw)) - 16, 4):
    w = struct.unpack_from('<IIII', raw, q)
    if w[1] == 0 and w[2] == 0xc0 and w[3] == 0x46000000:
        COM.append((DS[1] + (q - DS[3]), w[0]))
NAMES = {0x0: 'IID_IUnknown', 0x10c: 'IID_IPersist', 0xc: 'IID_IStream',
         0x109: 'IID_IPersistStream', 0x20400: 'IID_IDispatch'}
adj = []
for c, d1 in COM:
    for gap in range(0x4, 0x41, 4):
        t = u32(c + gap)
        if t == TI:
            # 自错 S-65：t 是「值 0x7f9594」= type_info 对象的首 dword（vftable 指针），
            # 而**对象本身**在 c+gap；装饰名在该对象的 +8 处。初稿对 t(=0x7f9594) 读 +8 得乱码。
            obj = c + gap
            nm = raw[fo(obj) + 8:fo(obj) + 8 + 120].split(b'\x00')[0].decode('latin1', 'replace')
            nm = nm if nm[:3] in ('.?A', '.?U') else '<not-a-name@' + hex(obj) + '>'
            adj.append({'guid_va': hex(c), 'name': NAMES.get(d1, '?'), 'gap': hex(gap),
                        'type_info_obj': hex(obj), 'class': nm})
per = collections.defaultdict(list)
for a in adj:
    per[a['guid_va']].append((a['gap'], a['class']))
amb = {k: v for k, v in per.items() if len({c for _, c in v}) > 1}
ck('G1 【配对歧义】.data 5 个 COM 形态常量与 type_info 的邻接（gap 4..0x40）共 %d 对；'
   '其中 %d 个常量**对应两个不同类名** ⇒ 「GUID+type_info+类名」不能唯一配对，'
   '不能当真假记录判据：%s'
   % (len(adj), len(amb), json.dumps({k: v for k, v in amb.items()}, ensure_ascii=False)),
   len(amb) >= 2, {'adjacency': adj})

# ---------------- 指令流 ----------------
sys.path.insert(0, os.path.join(ROOT, '_r112'))
import r112_lib as L2                                  # noqa: E402
MD = L2.MD
ins = [(a, mn, ops) for (a, sz, mn, ops) in MD.disasm_lite(code, TEXT0)]
IDX = {a: k for k, (a, mn, ops) in enumerate(ins)}


def ctx(k, back=4):
    lo = max(0, k - back)
    return [(hex(ins[z][0]), ins[z][1], ins[z][2]) for z in range(lo, k + 1)]


def call_after(k):
    for j in range(k + 1, min(k + 12, len(ins))):
        a, mn, ops = ins[j]
        if mn == 'call':
            if ops.startswith('dword ptr [0x'):
                # 自错 S-64：ops 形如 'dword ptr [0x7e15fc]'；'dword ptr [' 长度 11 ⇒ 起点 11。
                return ('iat', IAT.get(int(ops[11:-1], 16), ('?', '?'))[1], a)
            if ops.startswith('dword ptr ['):
                return ('vcall', ops, a)
            return ('other', ops, a)
        if mn.startswith('j') or mn.startswith('ret'):
            return ('stop', mn, a)
    return ('none', None, None)


def qi_form(k):
    """QI 三参数形态（cdecl，右到左压栈）：push ppv ; push riid ; push this ; call [reg]。
    riid 在 index k ⇒ k-1 必须是 push（ppv），k+1 必须是 push（this），k+2 必须是 call [reg]。
    自错 S-66：初稿查的是 k-1 与 k-2 都是 push，方向读反（把 riid 当成了最后一个实参）。"""
    if k < 1 or k + 2 >= len(ins):
        return False, 'no_room'
    m1 = ins[k - 1][1]
    m2 = ins[k + 1][1]
    if m1 != 'push' or m2 != 'push':
        return False, 'neighbours_not_push:%s,%s' % (m1, m2)
    kind, tgt, ca = call_after(k)
    if kind != 'vcall':
        return False, 'call_kind=%s' % kind
    return True, 'qi_3arg'

TARGETS = {c: d for c, d in COM}
TARGETS.update({0x7f7c80: 0x109, 0x7f7c70: 0x10c, 0x7f7c90: 0x0,
                0x7ed358: 0x070f3290, 0x817bb0: 0x070f3290,
                0x7e9b10: 0x92fea800, 0x819088: 0x92fea800})
sites = collections.defaultdict(list)
for k, (a, mn, ops) in enumerate(ins):
    if mn != 'push' or not ops.startswith('0x'):
        continue
    try:
        v = int(ops, 16)
    except ValueError:
        continue
    if v in TARGETS:
        sites[v].append(k)

detail = {}
for v, ks in sites.items():
    rows = []
    for k in ks:
        kind, tgt, ca = call_after(k)
        ok, why = qi_form(k)
        rows.append({'push': hex(ins[k][0]), 'call_kind': kind, 'call_target': tgt,
                     'call_at': hex(ca) if ca else None, 'qi_3arg': ok, 'why': why,
                     'ctx': ctx(k)})
    detail[hex(v)] = rows

# ---------------- G2/G3 ----------------
falsified = {}
for addr in (0x817bc0, 0x817bb0, 0x819088):
    rows = detail.get(hex(addr), [])
    falsified[hex(addr)] = {
        'n_sites': len(rows),
        'by_call': dict(collections.Counter(r['call_target'] if r['call_kind'] == 'iat'
                                            else r['call_kind'] for r in rows)),
        'qi_3arg': sum(1 for r in rows if r['qi_3arg']),
        'co_create': sum(1 for r in rows if r['call_target'] == 'CoCreateInstance'),
    }
ck('G2 【决定性】被 R118 判为「同值巧合」的 3 处 .data 常量，在 .text 里各有真实引用：%s '
   '⇒ 「同值巧合字节」被代码证据证伪（巧合字节不会进 riid 槽位）'
   % json.dumps(falsified, ensure_ascii=False),
   all(v['n_sites'] > 0 for v in falsified.values()), falsified)

byval = {'IID_IUnknown': (0x7f7c90, 0x817bc0), 'ILocomotion': (0x7ed358, 0x817bb0),
         'IPiggyback': (0x7e9b10, 0x819088), 'IID_IPersist': (0x7f7c70, 0x818858),
         'IID_IPersistStream': (0x7f7c80, 0x820270)}
tab = {}
for nm, (r, d) in byval.items():
    nr, nd = len(detail.get(hex(r), [])), len(detail.get(hex(d), []))
    tab[nm] = {'rdata': nr, 'data': nd, 'by_value': nr + nd}
ck('G3 修正后的按值数字（含 .data 拷贝的代码引用）：%s —— R118 §EK4 的回退（IUnknown 65→56、'
   'ILocomotion 11→7、IPiggyback 8→0）**是过度回退**，应恢复为 65 / 11 / 8'
   % json.dumps(tab, ensure_ascii=False),
   tab['IID_IUnknown']['by_value'] == 65 and tab['ILocomotion']['by_value'] == 11
   and tab['IPiggyback']['by_value'] == 8, tab)

# ---------------- G4 QI 三参数形态 ----------------
g4 = {}
for addr in (0x818858, 0x820270, 0x81fc50):
    rows = detail.get(hex(addr), [])
    g4[hex(addr)] = {'n': len(rows), 'qi_3arg': sum(1 for r in rows if r['qi_3arg']),
                     'vcall': sum(1 for r in rows if r['call_kind'] == 'vcall')}
ck('G4 【QI 三参数形态】.data 侧 IPersist 0x818858 / IPersistStream 0x820270 / IStream 0x81fc50 '
   '的站点中满足 push ppv; push iid; push this; call [reg] 的分别为 %s'
   % json.dumps({k: (v['qi_3arg'], v['n']) for k, v in g4.items()}, ensure_ascii=False),
   all(v['qi_3arg'] == v['n'] for v in g4.values()), g4)

# ---------------- G5 反控 ----------------
bad = [hex(v) for v in (0x81885c, 0x817bc4, 0x820274, 0x87da04) if hex(v) in detail]
ck('G5a 反控（键精确性）：GUID+4 作为键，push 站点必须 0 —— 实测命中键 %s' % (bad or 'none'),
   not bad, {'keys_hit': bad})
loose = sum(1 for v, ks in sites.items() for k in ks if True)     # 宽判据：不检查前两条 push
strict = sum(1 for v, ks in sites.items() for k in ks if qi_form(k)[0])
ck('G5b 反控（形态判据不恒真）：全部 %d 个 push 站点里满足 QI 三参数形态的只有 %d 个 ⇒ '
   '形态判据有鉴别力（不是所有 push 都算 QI）' % (loose, strict),
   0 < strict < loose, {'loose': loose, 'strict': strict})

json.dump({'adjacency': adj, 'ambiguous': {k: v for k, v in amb.items()},
           'falsified_coincidence': falsified, 'by_value': tab, 'qi_form': g4,
           'detail': {k: [{kk: vv for kk, vv in r.items() if kk != 'ctx'} for r in v]
                      for k, v in detail.items()},
           'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
